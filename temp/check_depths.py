import sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from docx import Document
doc = Document(r'C:\Users\Shadow\Documents\GitHub\stolar-db\FORMLÆRE.docx')
PROP_RE = re.compile(r'^(\d+(?:\.\d+)*)\s*([daiot])[\s\t]')
max_depth = 0
depth3 = []
for p in doc.paragraphs:
    m = PROP_RE.match(p.text.strip())
    if m:
        num = m.group(1)
        parts = num.split('.')
        if len(parts) >= 2:
            d = len(parts[-1])
            if d > max_depth:
                max_depth = d
            if d >= 3:
                depth3.append(num)
print(f'max depth (digits after last period): {max_depth}')
print(f'depth-3+ props: {depth3}')
