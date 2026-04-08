import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from docx import Document
doc = Document(r'C:\Users\Shadow\Documents\GitHub\stolar-db\FORMLÆRE.docx')
for i, p in enumerate(doc.paragraphs):
    t = p.text
    if 'Føreord' in t or 'Ordliste' in t or 'Affordanse' in t or 'Kvifor har' in t:
        style = p.style.name if p.style else '?'
        print(f'[{i}] {style}: {t[:100]!r}')
