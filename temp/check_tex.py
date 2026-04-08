import re
tex = open(r'C:\Users\Shadow\Documents\GitHub\stolar-db\FORMLÆRE.tex', encoding='utf-8').read()
props = re.findall(r'\\prop\{([^}]+)\}\{([^}]*)\}\{', tex)
foot_count = tex.count(r'\footnote{')
falsif_residual = tex.count('Falsifiseringsvilkår')
print(f'props: {len(props)}')
print(f'footnotes: {foot_count}')
print(f'remaining "Falsifiseringsvilkår" text: {falsif_residual}')
print()
print('first 8 propositions with footnotes:')
n = 0
for m in re.finditer(r'\\prop\{([^}]+)\}\{([^}]*)\}\{[^{}]*\\footnote', tex):
    print('  ', m.group(1), m.group(2))
    n += 1
    if n >= 8:
        break
