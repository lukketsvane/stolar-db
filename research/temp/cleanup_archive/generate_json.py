import re
import json
import os

with open('FORMLÆRE.tex', 'r', encoding='utf-8') as f:
    content = f.read()

start_idx = content.find(r"\silentchapter{Proposisjonar}{proposisjonar}")
if start_idx == -1:
    start_idx = content.find(r"\prop{1}")
end_idx = content.find(r"\silentchapter{Notatar}")
if end_idx == -1: end_idx = content.find(r"\prop{A.1}")
if end_idx == -1: end_idx = len(content)

props_text = content[start_idx:end_idx]

def parse_formatting(text):
    text = re.sub(r'\\textbf\{([^\}]*)\}', r'<b>\1</b>', text)
    text = re.sub(r'\\textit\{([^\}]*)\}', r'<i>\1</i>', text)
    
    # Handle footnotes recursively by converting them to markdown/HTML notes
    while r'\footnote{' in text:
        # A simple regex won't work for nested braces, but for most footnotes it's fine.
        text = re.sub(r'\\footnote\{([^\{\}]*)\}', r' <span class="note">[\1]</span>', text)
        if r'\footnote{' in text:
            # If still has nested, just do a greedy replacement (flawed but works for most)
            text = re.sub(r'\\footnote\{(.+?)\}', r' <span class="note">[\1]</span>', text)
            break
    
    text = text.replace(r'\&', '&')
    text = text.replace(r'\%', '%')
    text = text.replace(r'«', '"').replace(r'»', '"')
    return text.strip()

def parse_props(text):
    props = []
    idx = 0
    while True:
        idx = text.find(r"\prop{", idx)
        if idx == -1:
            break
        idx += 6
        
        id_end = text.find("}", idx)
        prop_id = text[idx:id_end]
        idx = id_end + 1
        
        if idx >= len(text) or text[idx] != '{': continue
        idx += 1
        status_end = text.find("}", idx)
        status = text[idx:status_end]
        idx = status_end + 1
        
        if idx >= len(text) or text[idx] != '{': continue
        idx += 1
        
        brace_count = 1
        text_start = idx
        while brace_count > 0 and idx < len(text):
            if text[idx] == '{' and text[idx-1] != '\\': brace_count += 1
            elif text[idx] == '}' and text[idx-1] != '\\': brace_count -= 1
            idx += 1
        
        prop_text = text[text_start:idx-1]
        
        # Add formatting
        prop_text = parse_formatting(prop_text)
        
        if status:
            prop_text = f"<sup>{status}</sup> {prop_text}"
            
        props.append({"id": prop_id, "status": status, "text": prop_text.strip()})
        
    return props

raw_props = parse_props(props_text)

nodes = {}
roots = []

for p in raw_props:
    if not re.match(r'^[1-7](\.[1-9]+)?$', p['id']):
        continue
    p['children'] = []
    nodes[p['id']] = p

for p in raw_props:
    pid = p['id']
    if pid not in nodes: continue
        
    if len(pid) == 1:
        roots.append(nodes[pid])
    else:
        parent_id = pid[:-1]
        if parent_id.endswith('.'): parent_id = parent_id[:-1]
            
        if parent_id in nodes:
            nodes[parent_id]['children'].append(nodes[pid])
        else:
            roots.append(nodes[pid])

if not os.path.exists('output_pdfs'):
    os.makedirs('output_pdfs')

with open('output_pdfs/formlaere_struktur.json', 'w', encoding='utf-8') as f:
    json.dump(roots, f, ensure_ascii=False, indent=2)

print("JSON-struktur generert: output_pdfs/formlaere_struktur.json")
