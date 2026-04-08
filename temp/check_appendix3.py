import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from docx import Document
doc = Document(r'C:\Users\Shadow\Documents\GitHub\stolar-db\FORMLÆRE.docx')
for i in range(168, 240):
    p = doc.paragraphs[i]
    t = p.text
    style = p.style.name if p.style else '?'
    if t.strip():
        print(f'[{i}] {style}: {t[:120]!r}')
