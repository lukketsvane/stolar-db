from docx import Document
doc = Document(r'C:\Users\Shadow\Documents\GitHub\stolar-db\FORMLÆRE.docx')
# Look for "Formell" anywhere
for i, p in enumerate(doc.paragraphs):
    t = p.text
    if 'Formell' in t or t.strip().startswith('A.') or t.strip().startswith('A '):
        print(f'[{i}] style={p.style.name if p.style else "?"} text={t[:100]!r}')
