# -*- coding: utf-8 -*-
import re

replacements = {
    r"\btiltrekker\b": "trekkjer til seg",
    r"\bfrastøter\b": "støyter frå",
    r"\bbetyr\b": "tyder",
    r"\bbeskriv\b": "skildrar",
    r"\boppfinnar\b": "finn opp",
    r"\boppfinne\b": "finne opp",
    r"\bforveksle\b": "blande saman",
    r"\bsannsynlegheitsfordelinga\b": "sannsynsfordelinga",
    r"\binneber\b": "ber i seg",
    r"\btilbakekoplingssyklus\b": "tilbakekoplingssløyfe",
    r"\bkoalescere\b": "smelte saman",
    r"\btilfredsstiller\b": "stettar",
    r"\boverkøyrer\b": "køyrer over",
    r"\bdeterminerer\b": "avgjer",
    r"\bfellast\b": "falsifiserast",
    r"\bforlåte\b": "forlatne",
    r"\buforanderleg\b": "uforanderleg",
    r"\bsamansette\b": "samansette",
    r"\bvidare\b": "vidare",
    r"\bbusette\b": "busette",
    r"\bregionar\b": "regionar",
    r"\bregionane\b": "regionane"
}

with open('FORMLÆRE.tex', 'r', encoding='utf-8') as f:
    text = f.read()

for pattern, replacement in replacements.items():
    text = re.sub(pattern, replacement, text)

with open('FORMLÆRE.tex', 'w', encoding='utf-8') as f:
    f.write(text)

print("Nynorsk terms updated.")
