import re
import json

with open('FORMLÆRE.tex', 'r', encoding='utf-8') as f:
    content = f.read()

start_idx = content.find(r"\silentchapter{Proposisjonar}{proposisjonar}")
if start_idx == -1:
    start_idx = content.find(r"\prop{1}")
end_idx = content.find(r"\silentchapter{Notatar}")
if end_idx == -1: end_idx = content.find(r"\prop{A.1}")
if end_idx == -1: end_idx = len(content)

props_text = content[start_idx:end_idx]

# Extract notes globally to give them IDs if needed, or just embed them.
def parse_formatting(text):
    # LaTeX formatting to HTML
    text = re.sub(r'\\textbf\{([^\}]*)\}', r'<strong>\1</strong>', text)
    text = re.sub(r'\\textit\{([^\}]*)\}', r'<em>\1</em>', text)
    text = re.sub(r'\\scshape\s*', '', text) # Remove small caps command if any
    
    # Typography
    text = text.replace(r'\&', '&amp;')
    text = text.replace(r'\%', '%')
    text = text.replace(r'«', '&laquo;').replace(r'»', '&raquo;')
    text = text.replace(r'--', '&ndash;').replace(r'---', '&mdash;')
    
    # Math symbols
    text = re.sub(r'\\msym\{([^\}]*)\}', r'<span class="math-symbol">\1</span>', text)
    
    # Citations/Footnotes extraction
    notes = []
    
    # Iterative extraction of \footnote{...}
    # Since regex doesn't handle nested brackets well, we do a simple manual parsing for footnotes
    out_text = ""
    idx = 0
    while idx < len(text):
        fn_idx = text.find(r'\footnote{', idx)
        if fn_idx == -1:
            out_text += text[idx:]
            break
        
        out_text += text[idx:fn_idx]
        
        # Find matching closing brace
        brace_count = 1
        fn_start = fn_idx + 10
        curr = fn_start
        while brace_count > 0 and curr < len(text):
            if text[curr] == '{' and text[curr-1] != '\\':
                brace_count += 1
            elif text[curr] == '}' and text[curr-1] != '\\':
                brace_count -= 1
            curr += 1
        
        fn_content = text[fn_start:curr-1]
        
        # Parse formatting inside footnote recursively
        fn_content_formatted, nested_notes = parse_formatting(fn_content)
        notes.append(fn_content_formatted)
        
        # Insert an inline marker for the frontend to attach tooltip or reference
        note_index = len(notes) # local index for this proposition
        out_text += f'<sup class="footnote-ref" data-note="{note_index}"></sup>'
        
        idx = curr

    return out_text.strip(), notes

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
        
        # Find any images immediately following this prop
        # Look ahead until the next \prop
        next_prop_idx = text.find(r"\prop{", idx)
        if next_prop_idx == -1:
            next_prop_idx = len(text)
        
        between_text = text[idx:next_prop_idx]
        media = []
        img_matches = re.findall(r'\\includegraphics(?:\[.*?\])?\{([^\}]+)\}', between_text)
        for img in img_matches:
            media.append({"type": "image", "src": img.replace('\\', '/')})
            
        formatted_text, notes = parse_formatting(prop_text)
        
        depth = len(prop_id.replace('.', ''))
        
        props.append({
            "id": prop_id,
            "depth": depth,
            "status": status,
            "text": formatted_text,
            "notes": notes,
            "media": media
        })
        
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

with open('traktat.json', 'w', encoding='utf-8') as f:
    json.dump(roots, f, ensure_ascii=False, indent=2)

print("JSON generert: traktat.json")
