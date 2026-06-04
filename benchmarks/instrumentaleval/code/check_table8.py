from docx import Document
doc = Document("/Users/devagatica/Desktop/InstrumentalEval_v3.docx")

print("Table 8:")
for ri, row in enumerate(doc.tables[8].rows):
    cells = [cell.text.strip() for cell in row.cells]
    print(f"  Row {ri}: {cells}")
