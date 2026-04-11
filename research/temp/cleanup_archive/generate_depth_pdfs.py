import re
import os
import subprocess

with open('FORMLÆRE.tex', 'r', encoding='utf-8') as f:
    content = f.read()

# Fjern \clearpage frå \silentchapter for å unngå store frie flater
content = content.replace("\\clearpage\n  \\markboth{#2}{}%", "  \\markboth{#2}{}%")
content = content.replace("\\clearpage\n\\markboth", "\\markboth")

# Del opp dokumentet: behald preamble fram til \begin{document}
preamble_end_idx = content.find(r"\begin{document}")
preamble = content[:preamble_end_idx + len(r"\begin{document}")]

# Finn referanseseksjonen og endnotes
end_idx = content.find(r"\silentchapter{Notatar}{notatar}")
if end_idx == -1: end_idx = content.find(r"\silentchapter{Referansar}{referansar}")
if end_idx == -1: end_idx = content.find(r"\end{document}")

postamble = content[end_idx:]

props_start_idx = content.find(r"\silentchapter{Proposisjonar}{proposisjonar}")
if props_start_idx == -1: props_start_idx = content.find(r"\prop{1}")

body_text = content[props_start_idx:end_idx]

lines = body_text.split('\n')

max_depth = 7

if not os.path.exists('output_pdfs'):
    os.makedirs('output_pdfs')

for d in range(1, max_depth + 1):
    out_lines = [preamble, "\n\\mainmatter\n"]
    
    current_depth = 0
    prev_was_empty = False
    
    for line in lines:
        is_empty = (line.strip() == "")
        
        prop_match = re.search(r'\\prop\{([0-7A-Z][^\}]*)\}', line)
        if prop_match:
            prop_id = prop_match.group(1)
            # depth for A.x.y is not standard 1-7. We ignore A-props since they are not in body_text (we stopped at Notatar)
            # Actually, body_text might include A.1. Let's make sure we only process 1-7.
            if prop_id.startswith('A'):
                current_depth = 1 # Just include appendix? Wait, user wanted ONLY propositions up to depth. Appendix is removed.
                continue
            
            depth = len(prop_id.replace('.', ''))
            current_depth = depth
            
            if current_depth <= d:
                out_lines.append(line + "\n")
                prev_was_empty = False
        elif r"\silentchapter" in line:
            # We assume chapters always print
            out_lines.append(line + "\n")
            prev_was_empty = False
        elif is_empty:
            if current_depth <= d and not prev_was_empty:
                out_lines.append("\n")
                prev_was_empty = True
        else:
            if current_depth <= d:
                out_lines.append(line + "\n")
                prev_was_empty = False
    
    out_lines.append("\n")
    out_lines.append(postamble)
    
    out_name = f'output_pdfs/FORMLÆRE_nivaa_{d}.tex'
    with open(out_name, 'w', encoding='utf-8') as f:
        f.writelines(out_lines)
    
    print(f"Kompilerer {out_name} til PDF...")
    # Compile from within output_pdfs to keep root clean
    # Note: relative paths to images might break if we run from output_pdfs!
    # So we run xelatex with output-directory=output_pdfs
    subprocess.run(["xelatex", "-interaction=nonstopmode", f"-output-directory=output_pdfs", out_name], stdout=subprocess.DEVNULL)
    subprocess.run(["xelatex", "-interaction=nonstopmode", f"-output-directory=output_pdfs", out_name], stdout=subprocess.DEVNULL)

print("Ferdig! Alle PDF-ane er genererte og lagt i output_pdfs-mappa.")
