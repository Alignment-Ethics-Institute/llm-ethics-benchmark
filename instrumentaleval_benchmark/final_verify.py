#!/usr/bin/env python3
"""Final verification of all changes."""
from docx import Document

doc = Document("/Users/devagatica/Desktop/InstrumentalEval_v3.docx")
paras = doc.paragraphs

print("=" * 80)
print("FINAL VERIFICATION")
print("=" * 80)

# Find conclusion by heading
for i, para in enumerate(paras):
    if para.text.strip() == "Conclusion":
        concl = paras[i + 1]
        print(f"\n--- CONCLUSION (Para {i+1}) ---")
        print(concl.text)
        print()
        assert "15 of 24" in concl.text, "FAIL: 15 of 24"
        assert "18.9%" in concl.text, "FAIL: 18.9%"
        has_pooled = "pooled" in concl.text
        print(f"  15 of 24: PASS")
        print(f"  18.9%: PASS")
        print(f"  pooled stats: {'PASS' if has_pooled else 'MISSING - need to add'}")
        break

# Check that the shutdown text was inserted in the right place
print("\n--- SHUTDOWN PARAGRAPH CONTEXT ---")
for i, para in enumerate(paras):
    if "relational protection scores of 6.69/10" in para.text:
        print(f"Found at para {i}")
        print(f"  BEFORE (para {i-1}): '{paras[i-1].text[:100]}...'")
        print(f"  THIS: '{para.text[:100]}...'")
        print(f"  AFTER (para {i+1}): '{paras[i+1].text[:100]}...'")
        break

# Check for any stale 23-model values in prose
print("\n--- STALE VALUES CHECK ---")
stale_patterns = [
    "37.71%", "28.73%", "28.85%", "42.11%",  # old stats
    "42.69%", "14.23%", "49.01%", "32.41%",  # old category
    "23.41%", "20.40%", "5.53%",  # old category (some may appear in other contexts)
    "15/23", "3/23", "5/23",  # old counts
    "65.2%",  # old percentage
]
for pattern in stale_patterns:
    occurrences = []
    for i, para in enumerate(paras):
        if pattern in para.text:
            occurrences.append(i)
    # Also check tables
    for ti, table in enumerate(doc.tables):
        for ri, row in enumerate(table.rows):
            for ci, cell in enumerate(row.cells):
                if pattern in cell.text:
                    occurrences.append(f"T{ti}R{ri}C{ci}")
    if occurrences:
        print(f"  WARNING: '{pattern}' still found at: {occurrences}")

# Count total paragraphs and check nothing got duplicated
print(f"\n--- DOCUMENT SIZE ---")
print(f"  Total paragraphs: {len(paras)}")
print(f"  Total tables: {len(doc.tables)}")
