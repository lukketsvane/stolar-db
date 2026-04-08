import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from docx import Document
doc = Document(r'C:\Users\Shadow\Documents\GitHub\stolar-db\FORMLÆRE.docx')
for i, p in enumerate(doc.paragraphs):
    t = p.text.strip()
    if t in {'Innhald', 'Føreord', 'Ordliste', 'Etterord', 'Referansar'}:
        print(f'[{i}] {t}')
    if t and t.startswith('1 Form er ein posisjon'):
        print(f'[{i}] CHAPTER 1')
        break
