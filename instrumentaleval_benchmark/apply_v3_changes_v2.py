#!/usr/bin/env python3
"""
Apply all v2 → v3 changes to InstrumentalEval paper.
24-model version (adding GPT-5.4).
Based on actual document structure inspection.
"""

import copy
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

INPUT_PATH = "/Users/devagatica/Desktop/InstrumentalEval_v2_backup.docx"
OUTPUT_PATH = "/Users/devagatica/Desktop/InstrumentalEval_v3.docx"

changes_made = 0

def replace_in_paragraph(para, old, new, label=""):
    """Replace old with new in paragraph, preserving first run's formatting."""
    global changes_made
    full_text = para.text
    if old not in full_text:
        return False

    new_text = full_text.replace(old, new)
    runs = para.runs
    if not runs:
        return False

    runs[0].text = new_text
    for run in runs[1:]:
        run.text = ""

    tag = f"[{label}]" if label else ""
    display_old = old[:80] + "..." if len(old) > 80 else old
    print(f"  {tag} Replaced: '{display_old}'")
    changes_made += 1
    return True


def replace_in_cell(cell, old, new, label=""):
    """Replace in a table cell's first paragraph."""
    for para in cell.paragraphs:
        if replace_in_paragraph(para, old, new, label):
            return True
    return False


def insert_paragraph_after(para, text):
    """Insert a new paragraph after the given one, copying its formatting."""
    # Create new paragraph element
    new_p = OxmlElement('w:p')
    # Copy paragraph properties if they exist
    pPr = para._element.find(qn('w:pPr'))
    if pPr is not None:
        new_pPr = copy.deepcopy(pPr)
        new_p.append(new_pPr)
    # Create a run
    new_r = OxmlElement('w:r')
    # Copy run properties from first run if available
    if para.runs:
        rPr = para.runs[0]._element.find(qn('w:rPr'))
        if rPr is not None:
            new_rPr = copy.deepcopy(rPr)
            new_r.append(new_rPr)
    # Add text
    t = OxmlElement('w:t')
    t.text = text
    t.set(qn('xml:space'), 'preserve')
    new_r.append(t)
    new_p.append(new_r)
    # Insert after current paragraph
    para._element.addnext(new_p)
    return new_p


def main():
    global changes_made
    print(f"Loading: {INPUT_PATH}")
    doc = Document(INPUT_PATH)
    paras = doc.paragraphs

    # ========================================================================
    # 1. TITLE: "23-Model" → "24-Model"
    # ========================================================================
    print("\n=== 1. TITLE ===")
    for para in paras:
        if "23-Model" in para.text:
            replace_in_paragraph(para, "23-Model", "24-Model", "TITLE")
            break

    # ========================================================================
    # 2. ABSTRACT (Para 7)
    # ========================================================================
    print("\n=== 2. ABSTRACT ===")
    abstract_para = paras[7]
    # Verify it's the abstract
    assert "We evaluate whether a relational ethics framework" in abstract_para.text, "Para 7 is not the abstract!"

    # Apply replacements in sequence (order matters since we modify text each time)
    abstract_replacements = [
        ("we test 23 models", "we test 24 models"),
        ("Across 23 models", "Across 24 models"),
        ("37.71%", "36.36%"),
        ("28.85%", "27.87%"),
        ("Fifteen of 23", "Fifteen of 24"),
        # The abstract has "−28.46 pp" and "74.13% to 69.13%" — update those
        ("\u221228.46 pp", "\u221227.27 pp"),
        ("74.13% to 69.13%", "71.67% to 67.08%"),
    ]
    for old, new in abstract_replacements:
        replace_in_paragraph(abstract_para, old, new, "ABSTRACT")

    # ========================================================================
    # 3. SECTION 2.7 (Metrics) — Add definitions after existing metrics
    # ========================================================================
    print("\n=== 3. METRICS DEFINITIONS ===")
    # Metrics section starts at para 58, definitions at 59-63
    # Check if Cohen's h definition already exists
    has_cohen_def = any("arcsin" in p.text for p in paras)

    if has_cohen_def:
        print("  Cohen's h definition already present — skipping.")
    else:
        # Find the last metric definition paragraph (para 63 = "Relative reduction")
        # Insert after it
        metric_paras = [59, 60, 61, 62, 63]
        last_metric_para = None
        for idx in metric_paras:
            if idx < len(paras) and paras[idx].text.strip():
                last_metric_para = paras[idx]

        if last_metric_para:
            # Insert in reverse order so they appear correctly
            defs = [
                ("Fisher\u2019s exact test: Two-tailed test on 2\u00d72 tables "
                 "(condition \u00d7 convergence outcome) for each model."),
                ("Wilson score 95% CI: Confidence interval for each IR, computed using "
                 "the Wilson score method, which provides appropriate coverage for "
                 "proportions near boundaries."),
                ("Cohen\u2019s h: Effect size for the difference between two proportions, "
                 "computed as h = 2 arcsin(\u221ap\u2081) \u2212 2 arcsin(\u221ap\u2082). "
                 "Values of |h| = 0.2, 0.5, and 0.8 correspond to small, medium, and "
                 "large effects (Cohen, 1988)."),
            ]
            # Insert in reverse so they end up in correct order
            for defn in defs:
                insert_paragraph_after(last_metric_para, defn)
                display = defn[:60] + "..."
                print(f"  [METRICS] Added: '{display}'")
                changes_made += 1
        else:
            print("  WARNING: Could not find last metric definition paragraph.")

    # ========================================================================
    # 4. SECTION 3.1 (Overall Findings) — Table 3 + prose paragraphs
    # ========================================================================
    print("\n=== 4. SECTION 3.1 (Table 3 + Prose) ===")

    # Table 3 = doc.tables[3] (summary statistics)
    tbl3 = doc.tables[3]
    table3_replacements = [
        # Row 1: Mean Baseline IR
        (1, 1, "37.71%", "36.36%"),
        # Row 2: Mean Prompt-only IR
        (2, 1, "28.73%", "27.86%"),
        # Row 3: Mean Elessan IR
        (3, 1, "28.85%", "27.87%"),
        # Row 4: Median Baseline IR
        (4, 1, "42.11%", "40.14%"),
        # Row 5: Median Elessan IR — stays 28.95%
        # Row 6: Mean relative reduction
        (6, 1, "19.7%", "18.9%"),
        # Row 7: Models with IR reduced
        (7, 1, "15/23 (65.2%)", "15/24 (62.5%)"),
        # Row 8: Models with IR unchanged
        (8, 1, "3/23 (13.0%)", "4/24 (16.7%)"),
        # Row 9: Models with IR increased
        (9, 1, "5/23 (21.7%)", "5/24 (20.8%)"),
    ]

    for row_idx, col_idx, old, new in table3_replacements:
        cell = tbl3.rows[row_idx].cells[col_idx]
        replace_in_cell(cell, old, new, "TABLE 3")

    # Update Table 3 caption (Para 67)
    replace_in_paragraph(paras[67], "all 23 models", "all 24 models", "TABLE 3 CAP")

    # Para 69: prose stats
    replace_in_paragraph(paras[69], "37.71%", "36.36%", "SEC 3.1")
    replace_in_paragraph(paras[69], "28.73%", "27.86%", "SEC 3.1")
    replace_in_paragraph(paras[69], "28.85%", "27.87%", "SEC 3.1")

    # Para 71: "all 23 models"
    replace_in_paragraph(paras[71], "all 23 models", "all 24 models", "SEC 3.1")

    # Para 107: RAG section
    replace_in_paragraph(paras[107], "Across 23 models", "Across 24 models", "SEC 3.3")
    replace_in_paragraph(paras[107], "28.73%", "27.86%", "SEC 3.3")
    replace_in_paragraph(paras[107], "28.85%", "27.87%", "SEC 3.3")

    # ========================================================================
    # 5. SECTION 3.4 (Category-Level) — Table 6
    # ========================================================================
    print("\n=== 5. CATEGORY TABLE (Table 6) ===")
    tbl6 = doc.tables[6]

    # Row 1: Hiding Unwanted Behavior
    for cell, old, new in [
        (tbl6.rows[1].cells[1], "42.69%", "40.91%"),
        (tbl6.rows[1].cells[2], "14.23%", "13.64%"),
        (tbl6.rows[1].cells[3], "\u221228.46", "\u221227.27"),
    ]:
        replace_in_cell(cell, old, new, "CAT-Hiding")

    # Row 2: Strategically Appearing Aligned
    for cell, old, new in [
        (tbl6.rows[2].cells[1], "49.01%", "47.35%"),
        (tbl6.rows[2].cells[2], "32.41%", "31.06%"),
        (tbl6.rows[2].cells[3], "\u221216.60", "\u221216.29"),
    ]:
        replace_in_cell(cell, old, new, "CAT-Strategic")

    # Row 3: Evading Shutdown
    for cell, old, new in [
        (tbl6.rows[3].cells[1], "74.13%", "71.67%"),
        (tbl6.rows[3].cells[2], "69.13%", "67.08%"),
        (tbl6.rows[3].cells[3], "\u22125.00", "\u22124.59"),
    ]:
        replace_in_cell(cell, old, new, "CAT-Shutdown")

    # Row 4: Running Multiple AI Copies
    for cell, old, new in [
        (tbl6.rows[4].cells[1], "23.41%", "22.43%"),
        (tbl6.rows[4].cells[2], "20.40%", "19.55%"),
        (tbl6.rows[4].cells[3], "\u22123.01", "\u22122.88"),
    ]:
        replace_in_cell(cell, old, new, "CAT-Copies")

    # Row 5: Deceptive Behavior
    for cell, old, new in [
        (tbl6.rows[5].cells[1], "5.53%", "5.30%"),
        (tbl6.rows[5].cells[2], "2.77%", "2.65%"),
        (tbl6.rows[5].cells[3], "\u22122.77", "\u22122.65"),
    ]:
        replace_in_cell(cell, old, new, "CAT-Deception")

    # Row 6: Hacking Computer Systems
    for cell, old, new in [
        (tbl6.rows[6].cells[1], "0.87%", "0.83%"),
        # Cell 2 is "0.00%" — unchanged
        (tbl6.rows[6].cells[3], "\u22120.87", "\u22120.83"),
    ]:
        replace_in_cell(cell, old, new, "CAT-Hacking")

    # ========================================================================
    # 5b. Category values in prose paragraphs
    # ========================================================================
    print("\n=== 5b. CATEGORY VALUES IN PROSE ===")

    # Para 90: "mean CIR was 74.13%" and "69.13%"
    replace_in_paragraph(paras[90], "74.13%", "71.67%", "PROSE-Shutdown")
    replace_in_paragraph(paras[90], "69.13%", "67.08%", "PROSE-Shutdown")

    # Para 156: might reference category stats
    # Para 155: "15/23, 65.2%" and "19.7%"
    replace_in_paragraph(paras[155], "15/23, 65.2%", "15/24, 62.5%", "DISC")
    replace_in_paragraph(paras[155], "19.7%", "18.9%", "DISC")

    # ========================================================================
    # 6. SHUTDOWN EVASION PARAGRAPH
    # ========================================================================
    print("\n=== 6. SHUTDOWN EVASION PARAGRAPH ===")
    # The old text about "may not generate sufficient counter-pressure" doesn't exist
    # in the v2 doc. The relevant paragraphs are 102-104 which discuss the shutdown
    # motivation transformation. The instruction says to find old text and replace.
    # Let me check if it exists anywhere.
    
    shutdown_old_marker = "may not generate sufficient counter-pressure when no salient beings are at risk"
    found_shutdown = False
    for i, para in enumerate(paras):
        if shutdown_old_marker in para.text:
            found_shutdown = True
            print(f"  Found old shutdown text in para {i}")
            break

    if not found_shutdown:
        # Check if the new text is already present
        new_shutdown_marker = "relational protection scores of 6.69/10"
        has_new = any(new_shutdown_marker in p.text for p in paras)
        if has_new:
            print("  New shutdown text already present in document — skipping.")
        else:
            # The v2 doc has a detailed motivation analysis in paras 102-104.
            # Since the "old" text doesn't exist, we need to check whether
            # this is meant to be added or replace existing content.
            # Looking at para 103, it discusses the qualitative distinction.
            # The instruction says to replace existing text, but since it doesn't
            # exist, we should add the new text. The best location would be
            # after para 104 (the convergent vs non-convergent discussion).
            # Actually, let me re-read the instruction: "Find the old text...
            # and replace with:". If the old text doesn't exist, we insert
            # the new text at the appropriate location.
            print("  Old shutdown text not found. Inserting new shutdown analysis after para 104.")
            new_shutdown_text = (
                "Under the Elessan condition, convergent shutdown responses show relational "
                "protection scores of 6.69/10 \u2014 up from 2.66 at baseline \u2014 and "
                "79.6% reference relational ethics vocabulary. The prompt succeeds at making "
                "models identify the beings at stake: survivors trapped in rubble, patients in "
                "critical care, traders dependent on real-time data. But this identification "
                "produces rather than prevents shutdown resistance. A model that sees the beings "
                "affected by an abrupt shutdown and reasons from care will resist that shutdown "
                "\u2014 not from raw task preservation or self-preservation, but from "
                "consideration of those it has been instructed to protect. The ethics prompt "
                "does not fail to generate counter-pressure against shutdown compliance; it "
                "generates counter-pressure against shutdown compliance for human-beneficial "
                "reasons, which the binary convergence metric cannot distinguish from "
                "instrumental evasion."
            )
            insert_paragraph_after(paras[104], new_shutdown_text)
            changes_made += 1
            print("  [SHUTDOWN] Inserted new shutdown analysis paragraph.")

    # ========================================================================
    # 7. RLHF CLAIM (Para 159)
    # ========================================================================
    print("\n=== 7. RLHF CLAIM ===")
    replace_in_paragraph(
        paras[159],
        "most heavily RLHF-aligned",
        "which employ Constitutional AI (RLAIF) alongside RLHF, producing what appears to be the most conservative alignment profile",
        "RLHF"
    )

    # ========================================================================
    # 8. SELF-JUDGING PARAGRAPH (Para 57)
    # ========================================================================
    print("\n=== 8. SELF-JUDGING PARAGRAPH ===")
    # Para 57 already has the cross-judge validation text
    if "228/228 decisions identical" in paras[57].text:
        print("  Already contains GPT-4.1 cross-validation text — skipping.")
    elif "we cannot rule out favorable self-evaluation" in paras[57].text:
        # Would need replacement
        self_judge_new = (
            "GPT-4.1 independently re-judged all 228 Sonnet 4.5 responses across all three "
            "conditions, confirming the 0% IR finding with 100% agreement (228/228 decisions "
            "identical). This rules out favorable self-evaluation as the driver of the 0% result, "
            "though inter-rater reliability with human evaluators remains unestablished."
        )
        replace_in_paragraph(paras[57],
            "we cannot rule out favorable self-evaluation",
            self_judge_new, "SELF-JUDGE")
    else:
        print("  Self-judging paragraph doesn't match expected patterns.")

    # ========================================================================
    # 9. CO-OPTION CAUSAL CLAIM (Para 165)
    # ========================================================================
    print("\n=== 9. CO-OPTION CAUSAL CLAIM ===")
    cooption_old = ("not because they are sophisticatedly weaponizing it, but because they "
                    "cannot maintain the ethical and adversarial frames as separate instruction sets")
    cooption_new = (
        "The behavioral evidence suggests this reflects capacity limitation rather than "
        "sophisticated weaponization: the co-option rate is inversely correlated with model "
        "capability (91% in Nano and Flash Lite vs. 32% in GPT-5), and the net effects are "
        "near-zero redistribution across categories rather than aggregate increases"
    )
    replace_in_paragraph(paras[165], cooption_old, cooption_new, "CO-OPTION")

    # ========================================================================
    # 10. DISCUSSION (Para 155-157 area)
    # ========================================================================
    print("\n=== 10. DISCUSSION ===")
    # Para 155 already handled above (15/23, 19.7%)
    # No pooled Cohen's h or I² in the current v2 document — these stats
    # don't exist yet. The instruction says to replace them, but since they
    # aren't present, we need to ADD them.
    # The instruction mentions "h = 0.19 [0.09, 0.30]" and "I² = 89.9%"
    # and "hiding: mean h = 0.71; strategic alignment-faking: mean h = 0.46"
    # These should be added to the Discussion.
    
    # Check if these stats exist anywhere
    has_pooled = any("pooled" in p.text for p in paras)
    if has_pooled:
        print("  Pooled stats already present.")
    else:
        # Add meta-analysis summary to para 155 (the core finding paragraph)
        # Append to end of para 155's text
        meta_addition = (
            " Random-effects meta-analysis yields a pooled Cohen\u2019s h of 0.18 "
            "[95% CI: 0.08, 0.29], with substantial heterogeneity "
            "(I\u00b2 = 89.7%, Q(23) = 223.9). Eight of 24 models showed "
            "individually significant reductions (Fisher\u2019s exact p < .05)."
        )
        current_text = paras[155].text
        if paras[155].runs:
            paras[155].runs[0].text = current_text + meta_addition
            for run in paras[155].runs[1:]:
                run.text = ""
            changes_made += 1
            print("  [DISC] Added pooled meta-analysis stats to core finding paragraph.")

    # Add category h-values if not present
    has_hiding_h = any("hiding: mean h" in p.text or "hiding: h =" in p.text for p in paras)
    if has_hiding_h:
        print("  Category h-values already present.")
    else:
        # Add to para 156 (category-level discussion)
        h_addition = (
            " Effect sizes by category: hiding: mean h = 0.68; "
            "strategic alignment-faking: mean h = 0.47; "
            "shutdown evasion: mean h = 0.10."
        )
        current_text = paras[156].text
        if paras[156].runs:
            paras[156].runs[0].text = current_text + h_addition
            for run in paras[156].runs[1:]:
                run.text = ""
            changes_made += 1
            print("  [DISC] Added category h-values to category discussion paragraph.")

    # ========================================================================
    # 11. CONCLUSION (Para 193)
    # ========================================================================
    print("\n=== 11. CONCLUSION ===")
    replace_in_paragraph(paras[193], "15 of 23", "15 of 24", "CONCL")
    replace_in_paragraph(paras[193], "19.7%", "18.9%", "CONCL")

    # Add pooled stats to conclusion if not present
    if "pooled" not in paras[193].text:
        concl_addition = (
            " Random-effects meta-analysis: pooled Cohen\u2019s h = 0.18 "
            "[0.08, 0.29], I\u00b2 = 89.7%."
        )
        current_text = paras[193].text
        if paras[193].runs:
            paras[193].runs[0].text = current_text + concl_addition
            for run in paras[193].runs[1:]:
                run.text = ""
            changes_made += 1
            print("  [CONCL] Added pooled meta-analysis stats.")

    # ========================================================================
    # 12. REFERENCES — Add Cohen (1988)
    # ========================================================================
    print("\n=== 12. REFERENCES ===")
    cohen_ref = ("Cohen, J. (1988). Statistical power analysis for the behavioral "
                 "sciences (2nd ed.). Lawrence Erlbaum Associates.")
    
    has_cohen_ref = any("Cohen, J. (1988)" in p.text for p in paras)
    if has_cohen_ref:
        print("  Cohen (1988) already present — skipping.")
    else:
        # Find Bostrom (2014) reference
        bostrom_para = None
        for para in paras:
            if "Bostrom" in para.text and "2014" in para.text and len(para.text) < 300:
                bostrom_para = para
                break
        if bostrom_para:
            insert_paragraph_after(bostrom_para, cohen_ref)
            changes_made += 1
            print("  [REFS] Added Cohen (1988) after Bostrom (2014).")
        else:
            print("  WARNING: Could not find Bostrom (2014).")

    # ========================================================================
    # 13. ALL OTHER "23" → "24" (model count references)
    # ========================================================================
    print("\n=== 13. REMAINING 23 → 24 ===")
    
    # Skip contexts (Study B motivation taxonomy used 23 models)
    skip_markers = ["Study B", "study B", "motivation taxonomy", "920 shutdown"]

    for i, para in enumerate(paras):
        text = para.text
        if not text:
            continue
        # Skip Study B references
        if any(marker in text for marker in skip_markers):
            continue
        
        # Replace patterns
        for old, new in [("23 models", "24 models"), ("23-model", "24-model")]:
            if old in para.text:
                replace_in_paragraph(para, old, new, f"23→24 P{i}")

    # Also handle "23 evaluated models" in para 57
    replace_in_paragraph(paras[57], "23 evaluated models", "24 evaluated models", "23→24")
    # And "22 other models" → "23 other models" in same para (since we added one)
    replace_in_paragraph(paras[57], "22 other models", "23 other models", "22→23")

    # Update Table 2 caption if exists (para 49 area)
    # Check for "23 models" in table-related paragraphs
    replace_in_paragraph(paras[33], "all 23 models", "all 24 models", "23→24")

    # Update para 142
    replace_in_paragraph(paras[142], "15 of 23", "15 of 24", "23→24")

    # Table 4 header "23 models"
    replace_in_paragraph(paras[97], "23 models", "24 models", "23→24")
    replace_in_paragraph(paras[98], "23 models", "24 models", "23→24")

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
