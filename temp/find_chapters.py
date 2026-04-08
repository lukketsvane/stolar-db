import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from docx import Document
doc = Document(r'C:\Users\Shadow\Documents\GitHub\stolar-db\FORMLÆRE.docx')
CHAPTER_TITLES = {
    '1 Form er ein posisjon i eit rom av moglegheiter.',
    '2 Ikkje alle posisjonar er like sannsynlege.',
    '3 Seleksjonstrykka produserer eit landskap over formrommet.',
    '4 Landskapet er dynamisk.',
    '5 Det finst agentar som responderer på landskapet.',
    '6 Forma oppstår mellom agentane.',
    '7 Ingen form er endeleg.',
    '7 Ingen form er endeleg; navigasjonen held fram.',
}
for i, p in enumerate(doc.paragraphs):
    t = p.text.strip()
    if t in CHAPTER_TITLES:
        style = p.style.name if p.style else '?'
        print(f'[{i}] {style}: {t}')
