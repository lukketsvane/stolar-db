"""Create a reference docx template that matches the LaTeX page setup
for FORMLÆRE: 125 x 200 mm page, narrow margins, EB Garamond body
(with Garamond / Times New Roman as Google-Docs-friendly fallbacks).

Used by export_docx.py via pandoc --reference-doc.
"""
from __future__ import annotations

from pathlib import Path
from docx import Document
from docx.shared import Mm, Pt, RGBColor
from docx.enum.text import WD_LINE_SPACING, WD_ALIGN_PARAGRAPH

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


def set_font(style_obj, name='EB Garamond', size_pt=10, bold=False, italic=False,
             color=(0x1A, 0x1A, 0x1A)):
    f = style_obj.font
    f.name = name
    f.size = Pt(size_pt)
    if bold:
        f.bold = True
    if italic:
        f.italic = True
    f.color.rgb = RGBColor(*color)
    # Force font also for east-asian/complex script tags so Google Docs
    # doesn't fall back to its default font
    rpr = style_obj.element.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rPr')
    if rpr is not None:
        for child in rpr.findall('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rFonts'):
            rpr.remove(child)
        from docx.oxml.ns import qn
        rfonts = rpr.makeelement(qn('w:rFonts'), {})
        rfonts.set(qn('w:ascii'), name)
        rfonts.set(qn('w:hAnsi'), name)
        rfonts.set(qn('w:cs'), name)
        rfonts.set(qn('w:eastAsia'), name)
        rpr.insert(0, rfonts)


styles = doc.styles

# Body
normal = styles['Normal']
set_font(normal, 'EB Garamond', 10)
para = normal.paragraph_format
para.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
para.line_spacing = 1.18
para.space_before = Pt(0)
para.space_after = Pt(3)

# Heading 1 — chapter level (numbered chapters + front/back-matter)
h1 = styles['Heading 1']
set_font(h1, 'EB Garamond', 18, bold=True)
h1.paragraph_format.space_before = Pt(14)
h1.paragraph_format.space_after  = Pt(6)
h1.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
h1.paragraph_format.line_spacing = 1.15
h1.paragraph_format.keep_with_next = True

# Heading 2 — A.6.x sub-sections
h2 = styles['Heading 2']
set_font(h2, 'EB Garamond', 13, bold=True)
h2.paragraph_format.space_before = Pt(10)
h2.paragraph_format.space_after  = Pt(4)
h2.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
h2.paragraph_format.line_spacing = 1.15
h2.paragraph_format.keep_with_next = True

# Heading 3
if 'Heading 3' in styles:
    h3 = styles['Heading 3']
    set_font(h3, 'EB Garamond', 11, bold=True)
    h3.paragraph_format.space_before = Pt(8)
    h3.paragraph_format.space_after  = Pt(3)

# Title (used by \maketitle in the cover block)
if 'Title' in styles:
    t = styles['Title']
    set_font(t, 'EB Garamond', 36, bold=True)
    t.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    t.paragraph_format.space_after = Pt(8)

# Subtitle (date in \maketitle)
if 'Subtitle' in styles:
    s = styles['Subtitle']
    set_font(s, 'EB Garamond', 13, italic=True, color=(0x4A, 0x4A, 0x4A))
    s.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    s.paragraph_format.space_after = Pt(12)

# Body Text
if 'Body Text' in styles:
    bt = styles['Body Text']
    set_font(bt, 'EB Garamond', 10)
    bt.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    bt.paragraph_format.line_spacing = 1.18
    bt.paragraph_format.space_after = Pt(3)

# A small placeholder paragraph so the file has content
doc.add_paragraph(' ')

doc.save(OUT)
print(f'wrote {OUT}')
