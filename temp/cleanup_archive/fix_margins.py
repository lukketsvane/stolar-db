import re

with open(r'analysis/scripts_v2/fig_tables_chap5.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("fig.savefig(pdf)", "fig.savefig(pdf, bbox_inches='tight', pad_inches=0)")
content = content.replace("fig.savefig(png)", "fig.savefig(png, bbox_inches='tight', pad_inches=0)")

with open(r'analysis/scripts_v2/fig_tables_chap5.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated fig_tables_chap5.py")