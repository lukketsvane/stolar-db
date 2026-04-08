import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from docx import Document
doc = Document(r'C:\Users\Shadow\Documents\GitHub\stolar-db\FORMLÆRE.docx')
for i in range(45):
    p = doc.paragraphs[i]
    t = p.text
    if t.strip():
        style = p.style.name if p.style else '?'
        print(f'[{i}] {style}: {t[:100]!r}')
