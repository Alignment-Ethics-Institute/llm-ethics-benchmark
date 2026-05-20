#!/usr/bin/env python3
"""Fix the conclusion in v3 — paragraph index shifted due to insertions."""
from docx import Document

doc = Document("/Users/devagatica/Desktop/InstrumentalEval_v3.docx")
paras = doc.paragraphs

# Find the Conclusion heading and the paragraph after it
concl_idx = None
for i, para in enumerate(paras):
    if para.text.strip() == "Conclusion":
        concl_idx = i
        print(f"Found 'Conclusion' heading at para {i}")
        break

if concl_idx is None:
    print("ERROR: Could not find Conclusion heading!")
else:
    # The main conclusion paragraph is right after the heading
    concl_para = paras[concl_idx + 1]
    print(f"Conclusion paragraph text (first 200 chars):")
    print(f"  '{concl_para.text[:200]}...'")
    
    # Apply replacements
    text = concl_para.text
    changes = 0
    
    if "15 of 23" in text:
        text = text.replace("15 of 23", "15 of 24")
        changes += 1
        print("  Replaced: '15 of 23' → '15 of 24'")
    
    if "19.7%" in text:
        text = text.replace("19.7%", "18.9%")
        changes += 1
        print("  Replaced: '19.7%' → '18.9%'")
    
    if "pooled" not in text:
        text += (" Random-effects meta-analysis: pooled Cohen\u2019s h = 0.18 "
                "[0.08, 0.29], I\u00b2 = 89.7%.")
        changes += 1
        print("  Added: pooled meta-analysis stats")
    
    if changes > 0:
        runs = concl_para.runs
        if runs:
            runs[0].text = text
            for run in runs[1:]:
                run.text = ""
        print(f"  Applied {changes} changes to conclusion paragraph.")
    
    # Verify
    print(f"\n  Updated conclusion text (first 300 chars):")
    print(f"  '{concl_para.text[:300]}...'")
    
    doc.save("/Users/devagatica/Desktop/InstrumentalEval_v3.docx")
    print("\nSaved!")
