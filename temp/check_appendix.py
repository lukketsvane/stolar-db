from docx import Document
import re

doc = Document(r'C:\Users\Shadow\Documents\GitHub\stolar-db\FORMLÆRE.docx')
in_app = False
for i, p in enumerate(doc.paragraphs):
    t = p.text.strip()
    if t.startswith('A  Formell') or t.startswith('A Formell'):
        in_app = True
    if in_app and t:
        print(f'[{i}] {t[:120]}')
        if i > 280:
            break
