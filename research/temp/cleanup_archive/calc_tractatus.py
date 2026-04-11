# -*- coding: utf-8 -*-
import urllib.request
import re

url = "https://www.gutenberg.org/cache/epub/5740/pg5740.txt"
try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    text = urllib.request.urlopen(req).read().decode('utf-8')
    
    lines = text.split('\n')
    counts = {1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0}
    
    current_level = 0
    for line in lines:
        line = line.strip()
        m = re.match(r'^([1-7])((?:\.[0-9]+)*)(?:\s+|$)', line)
        if m:
            prop_num = m.group(1) + m.group(2)
            current_level = len(prop_num.replace('.', ''))
            if current_level in counts:
                counts[current_level] = counts.get(current_level, 0) + len(line)
            else:
                counts[current_level] = len(line)
        elif current_level > 0 and line:
            counts[current_level] += len(line)
            
    with open('NOTAT.md', 'w', encoding='utf-8') as f:
        f.write('# Tractatus Logico-Philosophicus - Analyse av fordeling\n\n')
        f.write('Dette er ei utrekning av fordelinga av teikn basert på proposisjonsnivå (kor djupt nede i hierarkiet proposisjonen ligg) i Wittgensteins Tractatus.\n\n')
        f.write('| Nivå | Døme | Totalt tal teikn | Prosent |\n')
        f.write('|---|---|---|---|\n')
        
        total = sum(counts.values())
        if total > 0:
            for level in sorted(counts.keys()):
                pct = (counts[level] / total) * 100
                example = "1" if level == 1 else "1." + "1"*(level-1)
                f.write(f'| {level} | {example} | {counts[level]} | {pct:.1f}% |\n')
            
            f.write('\n### Konklusjon for FORMLÆRE\n')
            f.write('Wittgenstein la tyngda si i dei midtre nivåa (2, 3 og 4 siffer), medan hovudproposisjonane (nivå 1) er ekstremt korte og aforistiske. Skal `FORMLÆRE` spegle Tractatus formelt, bør brorparten av volumet liggje i utdjupingane (`n.n`, `n.nn`), medan hovudpostulata er destillerte til si reinaste kjerne.\n')
            
    print("NOTAT.md created successfully")
except Exception as e:
    print(f"Failed: {e}")