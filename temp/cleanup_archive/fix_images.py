# -*- coding: utf-8 -*-
import re

with open('FORMLÆRE.tex', 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern 1: Widebody with \linewidth images
pattern1 = r"\\par\\addvspace\{4pt\}\\begin\{widebody\}\\noindent\\centerline\{%?\s*\\includegraphics\[width=\\linewidth\]\{([^}]+)\}\}\\end\{widebody\}"
replacement1 = r"\\par\\addvspace{4pt}\\noindent\\includegraphics[width=\\linewidth]{\1}"
content = re.sub(pattern1, replacement1, content)

# Pattern 2: The shape grammar png which is currently 0.78\linewidth and inside centerline but NOT widebody
pattern2 = r"\\par\\addvspace\{2pt\}\\noindent\\centerline\{%?\s*\\includegraphics\[width=0\.78\\linewidth\]\{([^}]+)\}\}"
replacement2 = r"\\par\\addvspace{2pt}\\noindent\\includegraphics[width=\\linewidth]{\1}"
content = re.sub(pattern2, replacement2, content)

with open('FORMLÆRE.tex', 'w', encoding='utf-8') as f:
    f.write(content)

print("Image formatting updated.")