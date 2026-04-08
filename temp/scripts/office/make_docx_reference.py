"""Create a reference docx template that matches the LaTeX page setup
for FORMLÆRE: 125 x 200 mm page, narrow margins, EB Garamond body.

The output reference.docx is consumed by pandoc via --reference-doc when
exporting FORMLÆRE.tex to docx, so the resulting Word/Google Docs file
inherits page size, margins, and font.
"""
from __future__ import annotations

from pathlib import Path
from docx import Document
from docx.shared import Mm, Pt, RGBColor
from docx.enum.text import WD_LINE_SPACING

OUT = Path(__file__).resolve().parents[3] / 'temp' / 'reference.docx'

doc = Document()

# Page setup — match the LaTeX geometry exactly
section = doc.sections[0]
section.page_width  = Mm(125)
section.page_height = Mm(200)
section.left_margin   = Mm(20)
section.right_margin  = Mm(15)
section.top_margin    = Mm(18)
section.bottom_margin = Mm(16)
section.header_distance = Mm(8)
section.footer_distance = Mm(8)

# Default body style
styles = doc.styles
normal = styles['Normal']
normal.font.name = 'EB Garamond'
normal.font.size = Pt(10)
normal.font.color.rgb = RGBColor(0x1A, 0x1A, 0x1A)
para = normal.paragraph_format
para.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
para.line_spacing = 1.10
para.space_before = Pt(0)
para.space_after = Pt(2)

# Heading styles
for h, sz in (('Heading 1', 16), ('Heading 2', 13),
              ('Heading 3', 11), ('Heading 4', 10)):
    if h in styles:
        s = styles[h]
        s.font.name = 'EB Garamond'
        s.font.size = Pt(sz)
        s.font.bold = True
        s.font.color.rgb = RGBColor(0x1A, 0x1A, 0x1A)
        s.paragraph_format.space_before = Pt(8)
        s.paragraph_format.space_after  = Pt(3)

# Title style
if 'Title' in styles:
    t = styles['Title']
    t.font.name = 'EB Garamond'
    t.font.size = Pt(36)
    t.font.bold = True

# Subtitle
if 'Subtitle' in styles:
    s = styles['Subtitle']
    s.font.name = 'EB Garamond'
    s.font.size = Pt(13)
    s.font.italic = True

# A small placeholder paragraph so the file has content
doc.add_paragraph(' ')

doc.save(OUT)
print(f'wrote {OUT}')
