import re

with open('FORMLÆRE.tex', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace the foreword
old_foreword_pattern = re.compile(
    r"Denne traktaten forsøkjer å gjere det Michl ikkje gjorde.*?etter at desse orda er gløymd\.", 
    re.DOTALL
)

new_foreword_text = (
    "Form er ein posisjon i eit rom bland moglege former, forma av samtidige seleksjonstrykk, "
    "navigert av aktørar på fleire skalaer. Terminologien er lånt frå dei disiplinane som allereie "
    "har konvergert om same grunnomgrep: evolusjonsteori, informasjonsteori, maskinlæring, "
    "utviklingsbiologi, kognitiv vitskap. Kriteriet for å låne eit omgrep er at minst tre "
    "uavhengige fagfelt har konvergert om same terminologi og same formelle apparat. "
    "«Seleksjonstrykk» er foreineleg med bruk i maskinlæring, biomorfologi, kognitiv "
    "nevropsykologi og adferdsøkonomi. «Tilpassingslandskap» har sin analog i topologien, "
    "geometrien og maskinlæring. «Agent» er standardtermen i reinforcement learning, "
    "evolusjonsteori og kybernetikk for same formelle struktur. Denne konvergensen er ikkje "
    "eklektisisme. Ho er eit prov for at omgrepet fangar ein reell struktur, ikkje ein eigenskap "
    "ved éin bestemt disiplin."
)

text = old_foreword_pattern.sub(new_foreword_text, text)

# Insert the Wittgenstein reference in the bibliography section
ref_insertion = r"\\refentry{Wittgenstein, L. (1921). Tractatus Logico-Philosophicus. Routledge \\& Kegan Paul.}" + "\n"
text = text.replace(r"\end{widebody}" + "\n\n" + r"\end{document}", ref_insertion + r"\end{widebody}" + "\n\n" + r"\end{document}")

with open('FORMLÆRE.tex', 'w', encoding='utf-8') as f:
    f.write(text)

print("Foreword and references updated.")