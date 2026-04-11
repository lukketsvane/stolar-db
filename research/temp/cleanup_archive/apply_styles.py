import re

with open('FORMLÆRE.tex', 'r', encoding='utf-8') as f:
    content = f.read()

# Styling enhancements
# Define key terms
content = content.replace("Eit objekt er den enklaste", "Eit \\textbf{objekt} er den enklaste")
content = content.replace("Ein konfigurasjon er ein bestemt", "Ein \\textbf{konfigurasjon} er ein bestemt")
content = content.replace("Formrommet (morphospace)", "\\textbf{Formrommet} (\\textit{morphospace})")
content = content.replace("tilstøytande moglege", "\\textit{tilstøytande moglege}")
content = content.replace("Eit seleksjonstrykk er", "Eit \\textbf{seleksjonstrykk} er")
content = content.replace("Materialaffordansen er", "\\textbf{Materialaffordansen} er")
content = content.replace("Tilpassingslandskapet er", "\\textbf{Tilpassingslandskapet} er")
content = content.replace("Ein stil er", "Ein \\textbf{stil} er")
content = content.replace("Ein agent er ein operator", "Ein \\textbf{agent} er ein operator")
content = content.replace("Den kognitive lyskjegla er", "Den \\textbf{kognitive lyskjegla} er")
content = content.replace("Ein formgrammatikk er", "Ein \\textbf{formgrammatikk} er")
content = content.replace("Nisjekonstruksjon:", "\\textbf{Nisjekonstruksjon}:")

# Ensure the footnote rule is perfectly matched
fn_rule = r"""\renewcommand{\footnoterule}{%
  \vspace*{-3pt}%
  \noindent\llap{\rule{16mm}{0.4pt}}\rule{\linewidth}{0.4pt}%
  \vspace*{2.6pt}%
}"""

if "renewcommand{\\footnoterule}" not in content:
    content = content.replace(r"\usepackage{calc}", fn_rule + "\n\n" + r"\usepackage{calc}")

with open('FORMLÆRE.tex', 'w', encoding='utf-8') as f:
    f.write(content)

print("Styling updated.")