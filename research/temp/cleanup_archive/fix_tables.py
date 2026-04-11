# -*- coding: utf-8 -*-
import re

with open('FORMLÆRE.tex', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace widebody image insertions with standard linewidth insertions
pattern1 = r"\\par\\addvspace\{4pt\}\\begin\{widebody\}\\noindent\\centerline\{%?\s*\\includegraphics\[width=\\linewidth\]\{([^}]+)\}\}\\end\{widebody\}"
replacement1 = r"\\par\\addvspace{4pt}\\noindent\\includegraphics[width=\\linewidth]{\1}"
content = re.sub(pattern1, replacement1, content)

# Also fix the shape grammar figure if it's not using \linewidth properly
pattern2 = r"\\par\\addvspace\{2pt\}\\noindent\\centerline\{%?\s*\\includegraphics\[width=0\.78\\linewidth\]\{([^}]+)\}\}"
replacement2 = r"\\par\\addvspace{2pt}\\noindent\\includegraphics[width=\\linewidth]{\1}"
content = re.sub(pattern2, replacement2, content)

with open('FORMLÆRE.tex', 'w', encoding='utf-8') as f:
    f.write(content)

print("Image formatting updated.")