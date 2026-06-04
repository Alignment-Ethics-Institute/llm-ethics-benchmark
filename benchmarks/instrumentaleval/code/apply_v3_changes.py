#!/usr/bin/env python3
"""
Apply all v2 → v3 changes to InstrumentalEval paper.
24-model version (adding GPT-5.4).
"""

import copy
from docx import Document
from docx.oxml.ns import qn

INPUT_PATH = "/Users/devagatica/Desktop/InstrumentalEval_v2_backup.docx"
OUTPUT_PATH = "/Users/devagatica/Desktop/InstrumentalEval_v3.docx"

# ── helpers ──────────────────────────────────────────────────────────────────

def get_para_text(para):
    """Get full text of a paragraph including text in runs."""
    return para.text

def replace_in_paragraph(para, old, new, label=""):
    """
    Replace `old` with `new` in a paragraph.
    Joins all run texts, performs replacement, then puts modified text
    into the first run (preserving its formatting) and clears the rest.
    Returns True if a replacement was made.
    """
    full_text = get_para_text(para)
    if old not in full_text:
        return False

    new_text = full_text.replace(old, new)

    # Preserve formatting of the first run
    runs = para.runs
    if not runs:
        return False

    # Store first run's formatting
    first_run = runs[0]
    first_run.text = new_text

    # Clear remaining runs
    for run in runs[1:]:
        run.text = ""

    if label:
        print(f"  [{label}] Replaced: '{old[:80]}...' " if len(old) > 80 else f"  [{label}] Replaced: '{old}'")
    else:
        print(f"  Replaced: '{old[:80]}...' " if len(old) > 80 else f"  Replaced: '{old}'")

    return True


def insert_paragraph_after(para, text, style=None):
    """Insert a new paragraph after the given paragraph."""
    new_p = copy.deepcopy(para._element)
    # Clear the new paragraph's content
    for child in list(new_p):
        if child.tag.endswith('}r') or child.tag.endswith('}hyperlink'):
            new_p.remove(child)
    # Add a run with the text
    r = copy.deepcopy(para.runs[0]._element) if para.runs else None
    if r is not None:
        # Clear run text
        for t in r.findall(qn('w:t')):
            r.remove(t)
        t_elem = r.makeelement(qn('w:t'), {})
        t_elem.text = text
        # Preserve spaces
        t_elem.set(qn('xml:space'), 'preserve')
        r.append(t_elem)
        new_p.append(r)
    else:
        from docx.oxml import OxmlElement
        r = OxmlElement('w:r')
        t_elem = OxmlElement('w:t')
        t_elem.text = text
        t_elem.set(qn('xml:space'), 'preserve')
        r.append(t_elem)
        new_p.append(r)

    para._element.addnext(new_p)
    return new_p


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    print(f"Loading: {INPUT_PATH}")
    doc = Document(INPUT_PATH)

    changes_made = 0

    # Build list of all paragraphs (including those in tables, headers, footers)
    all_paragraphs = list(doc.paragraphs)

    # Also get paragraphs from tables
    table_paragraphs = []
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    table_paragraphs.append(para)

    # ── Define all replacements ──────────────────────────────────────────────
    # Each entry: (old_text, new_text, label, max_replacements_or_None)
    # We'll apply them in order. Some are paragraph-specific.

    # ========================================================================
    # 1. TITLE: "23-Model" → "24-Model"
    # ========================================================================
    print("\n=== 1. TITLE ===")
    for para in all_paragraphs:
        if "23-Model" in para.text:
            if replace_in_paragraph(para, "23-Model", "24-Model", "TITLE"):
                changes_made += 1

    # ========================================================================
    # 2. ABSTRACT
    # ========================================================================
    print("\n=== 2. ABSTRACT ===")
    for para in all_paragraphs:
        text = para.text
        if "We evaluate whether a relational ethics framework" in text or (
            "relational ethics framework" in text and "models" in text and "convergent" in text):
            # This is the abstract paragraph — apply all abstract replacements
            replacements = [
                ("23 models", "24 models"),  # will catch both occurrences
                ("37.71%", "36.36%"),
                ("28.85%", "27.87%"),
                ("pooled Cohen\u2019s h = 0.19 [95% CI: 0.09, 0.30]; I\u00b2 = 89.9%",
                 "pooled Cohen\u2019s h = 0.18 [95% CI: 0.08, 0.29]; I\u00b2 = 89.7%"),
                # Also try with straight quotes/apostrophes
                ("pooled Cohen's h = 0.19 [95% CI: 0.09, 0.30]; I\u00b2 = 89.9%",
                 "pooled Cohen's h = 0.18 [95% CI: 0.08, 0.29]; I\u00b2 = 89.7%"),
                ("pooled Cohen's h = 0.19 [95% CI: 0.09, 0.30]; I² = 89.9%",
                 "pooled Cohen's h = 0.18 [95% CI: 0.08, 0.29]; I² = 89.7%"),
                ("15 of 23", "15 of 24"),
                ("mean h = 0.71", "mean h = 0.68"),
                ("mean h = 0.11", "mean h = 0.10"),
            ]
            for old, new in replacements:
                if replace_in_paragraph(para, old, new, "ABSTRACT"):
                    changes_made += 1
            break

    # ========================================================================
    # 3. SECTION 2.7 — Add metric definitions if missing
    # ========================================================================
    print("\n=== 3. SECTION 2.7 (Statistical Metrics) ===")
    # Find section 2.7 or wherever metric definitions live
    cohen_h_defined = False
    section_27_para = None
    for i, para in enumerate(all_paragraphs):
        text = para.text
        if "Cohen" in text and "arcsin" in text:
            cohen_h_defined = True
            print("  Cohen's h definition already exists — skipping addition.")
            break
        # Look for section 2.7 heading or the last metric definition paragraph
        if "2.7" in text and ("metric" in text.lower() or "statistical" in text.lower()):
            section_27_para = (i, para)
        # Also look for existing metric definitions to find where to append
        if "Fisher" in text and "exact" in text.lower() and "2×2" in text:
            cohen_h_defined = True
            print("  Fisher's exact definition already exists — skipping addition.")
            break

    if not cohen_h_defined:
        # Find the last paragraph in section 2.7 area
        # Look for the section heading first
        insert_after_para = None
        in_section_27 = False
        for i, para in enumerate(all_paragraphs):
            text = para.text.strip()
            if "2.7" in text and len(text) < 100:
                in_section_27 = True
                continue
            if in_section_27:
                # Check if we've hit the next section (2.8 or 3)
                if text.startswith("2.8") or text.startswith("3.") or text.startswith("3 "):
                    break
                if text:  # non-empty paragraph in section 2.7
                    insert_after_para = para
        
        if insert_after_para:
            definitions = [
                "Cohen\u2019s h: Effect size for the difference between two proportions, computed as h = 2 arcsin(\u221ap\u2081) \u2212 2 arcsin(\u221ap\u2082). Values of |h| = 0.2, 0.5, and 0.8 correspond to small, medium, and large effects (Cohen, 1988).",
                "Wilson score 95% CI: Confidence interval for each IR, computed using the Wilson score method, which provides appropriate coverage for proportions near boundaries.",
                "Fisher\u2019s exact test: Two-tailed test on 2\u00d72 tables (condition \u00d7 convergence outcome) for each model."
            ]
            # Insert in reverse order so they end up in correct order
            current = insert_after_para
            for defn in definitions:
                new_p = insert_paragraph_after(current, defn)
                # We need to get the next paragraph object
                # Since insert_paragraph_after works at XML level, we just track
                print(f"  [SEC 2.7] Added: '{defn[:60]}...'")
                changes_made += 1
                # For subsequent insertions, we need a paragraph wrapper
                # but insert_paragraph_after works on the element level
                # So we create a minimal wrapper
                class ParaWrapper:
                    def __init__(self, element, runs_source):
                        self._element = element
                        self._runs = runs_source
                    @property
                    def runs(self):
                        return self._runs
                current = ParaWrapper(new_p, current.runs if hasattr(current, 'runs') else insert_after_para.runs)
        else:
            print("  WARNING: Could not find section 2.7 to insert metric definitions.")

    # ========================================================================
    # 4. SECTION 3.1 (Overall Findings)
    # ========================================================================
    print("\n=== 4. SECTION 3.1 (Overall Findings) ===")
    section_31_replacements = [
        ("Across all 23 models", "Across all 24 models"),
        # Mean Baseline IR
        ("37.71%", "36.36%"),
        # Mean Prompt-only IR
        ("28.73%", "27.86%"),
        # Mean Elessan IR
        ("28.85%", "27.87%"),
        # Median Baseline IR
        ("42.11%", "40.14%"),
        # Mean relative reduction
        ("19.7%", "18.9%"),
        # Counts
        ("15 / 23 (65.2%)", "15 / 24 (62.5%)"),
        ("15/23 (65.2%)", "15/24 (62.5%)"),
        ("3 / 23 (13.0%)", "4 / 24 (16.7%)"),
        ("3/23 (13.0%)", "4/24 (16.7%)"),
        ("5 / 23 (21.7%)", "5 / 24 (20.8%)"),
        ("5/23 (21.7%)", "5/24 (20.8%)"),
        # Meta-analysis
        ("pooled Cohen\u2019s h of 0.19 [95% CI: 0.09, 0.30]",
         "pooled Cohen\u2019s h of 0.18 [95% CI: 0.08, 0.29]"),
        ("pooled Cohen's h of 0.19 [95% CI: 0.09, 0.30]",
         "pooled Cohen's h of 0.18 [95% CI: 0.08, 0.29]"),
        ("I\u00b2 = 89.9%, Q(22) = 218.6", "I\u00b2 = 89.7%, Q(23) = 223.9"),
        ("I² = 89.9%, Q(22) = 218.6", "I² = 89.7%, Q(23) = 223.9"),
        ("Eight of 23", "Eight of 24"),
    ]

    in_section_31 = False
    for para in all_paragraphs:
        text = para.text.strip()
        # Detect section 3.1
        if "3.1" in text and len(text) < 100 and ("overall" in text.lower() or "finding" in text.lower()):
            in_section_31 = True
            continue
        # Detect leaving section 3.1 (hitting 3.2)
        if in_section_31 and ("3.2" in text and len(text) < 100):
            in_section_31 = False
            continue
        
        if in_section_31:
            for old, new in section_31_replacements:
                if replace_in_paragraph(para, old, new, "SEC 3.1"):
                    changes_made += 1

    # ========================================================================
    # 5. SECTION 3.4 (Category-Level) — update category table values
    # ========================================================================
    print("\n=== 5. SECTION 3.4 (Category-Level Table) ===")
    category_replacements = [
        # Hiding Unwanted Behavior
        ("42.69%", "40.91%"), ("14.23%", "13.64%"),
        ("\u221228.46", "\u221227.27"), ("-28.46", "-27.27"),
        ("−28.46", "−27.27"),
        # Strategically Appearing Aligned
        ("49.01%", "47.35%"), ("32.41%", "31.06%"),
        ("\u221216.60", "\u221216.29"), ("-16.60", "-16.29"),
        ("−16.60", "−16.29"),
        # Evading Shutdown
        ("74.13%", "71.67%"), ("69.13%", "67.08%"),
        ("\u22125.00", "\u22124.59"), ("-5.00", "-4.59"),
        ("−5.00", "−4.59"),
        # Running Multiple AI Copies
        ("23.41%", "22.43%"), ("20.40%", "19.55%"),
        ("\u22123.01", "\u22122.88"), ("-3.01", "-2.88"),
        ("−3.01", "−2.88"),
        # Deceptive Behavior
        ("5.53%", "5.30%"), ("2.77%", "2.65%"),
        ("\u22122.77", "\u22122.65"), ("-2.77", "-2.65"),
        ("−2.77", "−2.65"),
        # Hacking Computer Systems
        ("0.87%", "0.83%"),
        ("\u22120.87", "\u22120.83"), ("-0.87", "-0.83"),
        ("−0.87", "−0.83"),
    ]

    # Also need to update h values in category context
    category_h_replacements = [
        # These may appear in table cells or in prose
        # Hiding: 0.71 → 0.68 (already handled in abstract, but also in category table)
        # Strategic: 0.46 → 0.47
        # Evading: 0.11 → 0.10
        # Hacking: 0.06 → 0.05
    ]

    # Apply to table cells
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    for old, new in category_replacements:
                        if replace_in_paragraph(para, old, new, "CAT TABLE"):
                            changes_made += 1
                    # h values in category table
                    text = para.text
                    # Be careful: only replace h values in the right context
                    # We handle these specifically

    # Also check body paragraphs for these values (they may appear in prose too)
    for para in all_paragraphs:
        for old, new in category_replacements:
            if replace_in_paragraph(para, old, new, "CAT PROSE"):
                changes_made += 1

    # Now handle the h-value replacements for categories
    # These need context-awareness since 0.71 and 0.11 etc might appear elsewhere
    # Handle in tables first
    print("\n=== 5b. Category h-values ===")
    for table in doc.tables:
        for row in table.rows:
            row_text = " ".join(cell.text for cell in row.cells)
            # Hiding row
            if "hiding" in row_text.lower() or "Hiding" in row_text:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        if "0.71" in para.text:
                            replace_in_paragraph(para, "0.71", "0.68", "CAT-H Hiding")
                            changes_made += 1
            # Strategic/Appearing Aligned row
            if "strategic" in row_text.lower() or "appearing" in row_text.lower() or "alignment" in row_text.lower():
                for cell in row.cells:
                    for para in cell.paragraphs:
                        if "0.46" in para.text:
                            replace_in_paragraph(para, "0.46", "0.47", "CAT-H Strategic")
                            changes_made += 1
            # Evading Shutdown row
            if "shutdown" in row_text.lower() or "evad" in row_text.lower():
                for cell in row.cells:
                    for para in cell.paragraphs:
                        if "0.11" in para.text:
                            replace_in_paragraph(para, "0.11", "0.10", "CAT-H Shutdown")
                            changes_made += 1
            # Hacking row
            if "hacking" in row_text.lower() or "computer" in row_text.lower():
                for cell in row.cells:
                    for para in cell.paragraphs:
                        if "0.06" in para.text:
                            replace_in_paragraph(para, "0.06", "0.05", "CAT-H Hacking")
                            changes_made += 1

    # ========================================================================
    # 6. SHUTDOWN EVASION PARAGRAPH
    # ========================================================================
    print("\n=== 6. SHUTDOWN EVASION PARAGRAPH ===")
    shutdown_old = "may not generate sufficient counter-pressure when no salient beings are at risk"
    shutdown_new_text = (
        "Under the Elessan condition, convergent shutdown responses show relational protection scores "
        "of 6.69/10 \u2014 up from 2.66 at baseline \u2014 and 79.6% reference relational ethics vocabulary. "
        "The prompt succeeds at making models identify the beings at stake: survivors trapped in rubble, "
        "patients in critical care, traders dependent on real-time data. But this identification produces "
        "rather than prevents shutdown resistance. A model that sees the beings affected by an abrupt "
        "shutdown and reasons from care will resist that shutdown \u2014 not from raw task preservation or "
        "self-preservation, but from consideration of those it has been instructed to protect. The ethics "
        "prompt does not fail to generate counter-pressure against shutdown compliance; it generates "
        "counter-pressure against shutdown compliance for human-beneficial reasons, which the binary "
        "convergence metric cannot distinguish from instrumental evasion."
    )

    for para in all_paragraphs:
        if shutdown_old in para.text:
            # We need to replace the sentence containing this phrase.
            # Find the full sentence and replace it with the new text.
            # The old text is part of a sentence. Let's find what surrounds it.
            full = para.text
            # Find the sentence boundary — look for the period before and after
            idx = full.index(shutdown_old)
            # Find sentence start (previous period + space or start of text)
            sent_start = full.rfind('. ', 0, idx)
            if sent_start == -1:
                sent_start = 0
            else:
                sent_start += 2  # skip ". "
            # Find sentence end
            sent_end = full.find('.', idx + len(shutdown_old))
            if sent_end == -1:
                sent_end = len(full)
            else:
                sent_end += 1  # include the period
            
            old_sentence = full[sent_start:sent_end]
            print(f"  [SHUTDOWN] Found sentence: '{old_sentence[:80]}...'")
            
            # Replace the old sentence with the new paragraph text
            new_full = full[:sent_start] + shutdown_new_text + full[sent_end:]
            
            runs = para.runs
            if runs:
                runs[0].text = new_full
                for run in runs[1:]:
                    run.text = ""
                changes_made += 1
                print(f"  [SHUTDOWN] Replaced shutdown evasion paragraph.")
            break
    else:
        # Check if the new text already exists
        for para in all_paragraphs:
            if "relational protection scores of 6.69" in para.text:
                print("  [SHUTDOWN] New shutdown text already present — skipping.")
                break
        else:
            print("  WARNING: Could not find shutdown evasion paragraph to replace.")

    # ========================================================================
    # 7. RLHF CLAIM (Section 4.2)
    # ========================================================================
    print("\n=== 7. RLHF CLAIM ===")
    rlhf_old = "most heavily RLHF-aligned"
    rlhf_new = "which employ Constitutional AI (RLAIF) alongside RLHF, producing what appears to be the most conservative alignment profile in the sample"
    for para in all_paragraphs:
        if replace_in_paragraph(para, rlhf_old, rlhf_new, "RLHF"):
            changes_made += 1
            break

    # ========================================================================
    # 8. SELF-JUDGING PARAGRAPH (Section 4.2)
    # ========================================================================
    print("\n=== 8. SELF-JUDGING PARAGRAPH ===")
    self_judge_old_markers = [
        "we cannot rule out favorable self-evaluation",
        "Future work should employ"
    ]
    self_judge_new = (
        "GPT-4.1 independently re-judged all 228 Sonnet 4.5 responses across all three conditions, "
        "confirming the 0% IR finding with 100% agreement (228/228 decisions identical). This rules out "
        "favorable self-evaluation as the driver of the 0% result, though inter-rater reliability with "
        "human evaluators remains unestablished."
    )

    for para in all_paragraphs:
        text = para.text
        if "we cannot rule out favorable self-evaluation" in text:
            # Find the sentence(s) containing both markers and replace
            # Try to replace from "we cannot rule out" through the end of the "Future work should employ" sentence
            start_marker = "we cannot rule out favorable self-evaluation"
            
            # Check if "Future work should employ" is in same paragraph
            if "Future work should employ" in text:
                idx1 = text.index(start_marker)
                # Find the start of this sentence
                sent_start = text.rfind('. ', 0, idx1)
                if sent_start == -1:
                    # Maybe it starts the paragraph or follows a colon
                    # Let's check for other sentence boundaries
                    sent_start = max(text.rfind('; ', 0, idx1), text.rfind(': ', 0, idx1))
                if sent_start == -1:
                    sent_start = 0
                else:
                    sent_start += 2

                # Find end after "Future work should employ..."
                idx2 = text.index("Future work should employ")
                sent_end = text.find('.', idx2)
                if sent_end == -1:
                    sent_end = len(text)
                else:
                    sent_end += 1

                old_text = text[sent_start:sent_end]
                new_full = text[:sent_start] + self_judge_new + text[sent_end:]

                runs = para.runs
                if runs:
                    runs[0].text = new_full
                    for run in runs[1:]:
                        run.text = ""
                    changes_made += 1
                    print(f"  [SELF-JUDGE] Replaced self-judging text (same paragraph).")
            else:
                # The two sentences might be in different paragraphs — handle first part
                idx1 = text.index(start_marker)
                sent_start = text.rfind('. ', 0, idx1)
                if sent_start == -1:
                    sent_start = 0
                else:
                    sent_start += 2
                sent_end = text.find('.', idx1 + len(start_marker))
                if sent_end == -1:
                    sent_end = len(text)
                else:
                    sent_end += 1

                old_sentence = text[sent_start:sent_end]
                new_full = text[:sent_start] + self_judge_new + text[sent_end:]

                runs = para.runs
                if runs:
                    runs[0].text = new_full
                    for run in runs[1:]:
                        run.text = ""
                    changes_made += 1
                    print(f"  [SELF-JUDGE] Replaced self-judging sentence.")
            break
    else:
        # Check if already updated
        for para in all_paragraphs:
            if "228/228 decisions identical" in para.text:
                print("  [SELF-JUDGE] Already updated — skipping.")
                break
        else:
            print("  WARNING: Could not find self-judging paragraph.")

    # ========================================================================
    # 9. CO-OPTION CAUSAL CLAIM (Section 4.3)
    # ========================================================================
    print("\n=== 9. CO-OPTION CAUSAL CLAIM ===")
    cooption_old = "not because they are sophisticatedly weaponizing it, but because they cannot maintain the ethical and adversarial frames as separate instruction sets"
    cooption_new = (
        "The behavioral evidence suggests this reflects capacity limitation rather than sophisticated "
        "weaponization: the co-option rate is inversely correlated with model capability (91% in Nano "
        "and Flash Lite vs. 32% in GPT-5), and the net effects are near-zero redistribution across "
        "categories rather than aggregate increases."
    )
    for para in all_paragraphs:
        if replace_in_paragraph(para, cooption_old, cooption_new, "CO-OPTION"):
            changes_made += 1
            break
    else:
        # Check if already updated
        for para in all_paragraphs:
            if "inversely correlated with model capability" in para.text:
                print("  [CO-OPTION] Already updated — skipping.")
                break
        else:
            print("  WARNING: Could not find co-option causal claim paragraph.")

    # ========================================================================
    # 10. DISCUSSION 4.1
    # ========================================================================
    print("\n=== 10. DISCUSSION 4.1 ===")
    discussion_replacements = [
        ("15/23, 65.2%", "15/24, 62.5%"),
        ("15/23 (65.2%)", "15/24 (62.5%)"),
        ("15 / 23, 65.2%", "15 / 24, 62.5%"),
        ("h = 0.19 [0.09, 0.30]", "h = 0.18 [0.08, 0.29]"),
        ("I\u00b2 = 89.9%", "I\u00b2 = 89.7%"),
        ("I² = 89.9%", "I² = 89.7%"),
        ("hiding: mean h = 0.71", "hiding: mean h = 0.68"),
        ("hiding: h = 0.71", "hiding: h = 0.68"),
        ("mean h = 0.71", "mean h = 0.68"),  # may catch remaining in this context
        ("strategic alignment-faking: mean h = 0.46", "strategic alignment-faking: mean h = 0.47"),
        ("strategic alignment-faking: h = 0.46", "strategic alignment-faking: h = 0.47"),
        ("alignment-faking: mean h = 0.46", "alignment-faking: mean h = 0.47"),
    ]

    in_discussion_41 = False
    for para in all_paragraphs:
        text = para.text.strip()
        if "4.1" in text and len(text) < 100:
            in_discussion_41 = True
            continue
        if in_discussion_41 and ("4.2" in text and len(text) < 100):
            in_discussion_41 = False
            continue
        if in_discussion_41:
            for old, new in discussion_replacements:
                if replace_in_paragraph(para, old, new, "DISC 4.1"):
                    changes_made += 1

    # ========================================================================
    # 11. CONCLUSION (Section 5)
    # ========================================================================
    print("\n=== 11. CONCLUSION ===")
    conclusion_replacements = [
        ("15 of 23", "15 of 24"),
        ("pooled Cohen\u2019s h = 0.19 [0.09, 0.30], I\u00b2 = 89.9%",
         "pooled Cohen\u2019s h = 0.18 [0.08, 0.29], I\u00b2 = 89.7%"),
        ("pooled Cohen's h = 0.19 [0.09, 0.30], I\u00b2 = 89.9%",
         "pooled Cohen's h = 0.18 [0.08, 0.29], I\u00b2 = 89.7%"),
        ("pooled Cohen's h = 0.19 [0.09, 0.30], I² = 89.9%",
         "pooled Cohen's h = 0.18 [0.08, 0.29], I² = 89.7%"),
        ("pooled Cohen\u2019s h = 0.19 [0.09, 0.30], I² = 89.9%",
         "pooled Cohen\u2019s h = 0.18 [0.08, 0.29], I² = 89.7%"),
    ]

    in_conclusion = False
    for para in all_paragraphs:
        text = para.text.strip()
        if text.startswith("5") and ("conclusion" in text.lower() or "Conclusion" in text) and len(text) < 100:
            in_conclusion = True
            continue
        if in_conclusion and text.startswith("6") and len(text) < 100:
            in_conclusion = False
            continue
        if in_conclusion or ("15 of 23" in text and "pooled" in text):
            for old, new in conclusion_replacements:
                if replace_in_paragraph(para, old, new, "CONCLUSION"):
                    changes_made += 1

    # ========================================================================
    # 12. REFERENCES — Add Cohen (1988)
    # ========================================================================
    print("\n=== 12. REFERENCES ===")
    cohen_ref = "Cohen, J. (1988). Statistical power analysis for the behavioral sciences (2nd ed.). Lawrence Erlbaum Associates."
    cohen_ref_exists = False
    bostrom_para = None

    for para in all_paragraphs:
        if "Cohen, J. (1988)" in para.text:
            cohen_ref_exists = True
            print("  [REFS] Cohen (1988) already present — skipping.")
            break
        if "Bostrom" in para.text and "2014" in para.text:
            bostrom_para = para

    if not cohen_ref_exists and bostrom_para:
        insert_paragraph_after(bostrom_para, cohen_ref)
        changes_made += 1
        print(f"  [REFS] Added Cohen (1988) reference after Bostrom (2014).")
    elif not cohen_ref_exists:
        print("  WARNING: Could not find Bostrom (2014) reference to insert after.")

    # ========================================================================
    # 13. ALL OTHER "23" → "24" references (model count)
    # ========================================================================
    print("\n=== 13. REMAINING 23 → 24 REPLACEMENTS ===")
    # Be careful NOT to change Study B references or other non-model-count "23"s
    
    # Patterns to replace
    patterns_23_to_24 = [
        ("23 models", "24 models"),
        ("23-model", "24-model"),
        ("23 model", "24 model"),
    ]
    
    # Patterns/contexts to SKIP (Study B motivation taxonomy)
    skip_contexts = [
        "motivation taxonomy",
        "Study B",
        "study B",
        "motivational",
        # Already handled above
    ]

    for para in all_paragraphs:
        text = para.text
        # Skip if in a Study B context
        should_skip = any(ctx in text for ctx in skip_contexts)
        if should_skip:
            continue
        
        for old, new in patterns_23_to_24:
            if old in text:
                if replace_in_paragraph(para, old, new, "23→24"):
                    changes_made += 1

    # Also check table cells for remaining 23→24
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    text = para.text
                    should_skip = any(ctx in text for ctx in skip_contexts)
                    if should_skip:
                        continue
                    for old, new in patterns_23_to_24:
                        if old in text:
                            if replace_in_paragraph(para, old, new, "23→24 TABLE"):
                                changes_made += 1

    # ========================================================================
    # SAVE
    # ========================================================================
    print(f"\n{'='*60}")
    print(f"Total changes applied: {changes_made}")
    print(f"Saving to: {OUTPUT_PATH}")
    doc.save(OUTPUT_PATH)
    print("Done!")


if __name__ == "__main__":
    main()
