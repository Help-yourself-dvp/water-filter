#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Превращает документ Markdown в PDF.

Зачем: страницы GitHub у владельца открываются не всегда (провайдер, мобильная сеть,
длинное имя ветки). PDF читается в любом просмотрщике и не зависит от сети.

    python3 tools/md_to_pdf.py store/SCREENSHOTS.md store/Instrukciya-skrinshoty.pdf

Поддерживается то, что реально используется в наших документах:
заголовки, списки, нумерованные списки, таблицы, цитаты, код и разделители.
"""
import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

pdfmetrics.registerFont(TTFont('DejaVu', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVu-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
pdfmetrics.registerFont(TTFont('DejaVu-Mono', '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'))

DARK = colors.HexColor('#0f2338')
BODY_C = colors.HexColor('#22303f')
ACCENT = colors.HexColor('#0284c7')
MUTED = colors.HexColor('#5b6b80')

H1 = ParagraphStyle('h1', fontName='DejaVu-Bold', fontSize=17, leading=21, textColor=DARK, spaceAfter=10)
H2 = ParagraphStyle('h2', fontName='DejaVu-Bold', fontSize=13, leading=17, textColor=ACCENT,
                    spaceBefore=14, spaceAfter=6)
H3 = ParagraphStyle('h3', fontName='DejaVu-Bold', fontSize=11, leading=15, textColor=DARK,
                    spaceBefore=10, spaceAfter=4)
BODY = ParagraphStyle('body', fontName='DejaVu', fontSize=10, leading=14.5, textColor=BODY_C, spaceAfter=5)
LI = ParagraphStyle('li', parent=BODY, leftIndent=12, bulletIndent=2, spaceAfter=3)
QUOTE = ParagraphStyle('quote', parent=BODY, leftIndent=12, textColor=MUTED)
CODE = ParagraphStyle('code', fontName='DejaVu-Mono', fontSize=8.5, leading=12,
                      textColor=DARK, backColor=colors.HexColor('#eef3f8'),
                      borderPadding=6, spaceAfter=6)
CELL = ParagraphStyle('cell', fontName='DejaVu', fontSize=8.5, leading=11.5, textColor=BODY_C)
CELL_H = ParagraphStyle('cellh', parent=CELL, fontName='DejaVu-Bold', textColor=DARK)


def inline(s):
    """Жирный, курсив, код и экранирование — в разметку reportlab."""
    s = s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'`(.+?)`', r'<font face="DejaVu-Mono" size="9">\1</font>', s)
    s = re.sub(r'\[(.+?)\]\((.+?)\)', r'\1 (\2)', s)
    return s


def convert(src, out):
    lines = Path(src).read_text(encoding='utf-8').split('\n')
    story, i = [], 0
    while i < len(lines):
        ln = lines[i]
        s = ln.strip()

        if not s:
            i += 1
            continue

        if s.startswith('```'):
            block, i = [], i + 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                block.append(lines[i])
                i += 1
            i += 1
            story.append(Paragraph('<br/>'.join(
                l.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace(' ', '&nbsp;')
                for l in block), CODE))
            continue

        if s.startswith('|') and i + 1 < len(lines) and set(lines[i + 1].strip()) <= set('|-: '):
            rows, header = [], [c.strip() for c in s.strip('|').split('|')]
            i += 2
            while i < len(lines) and lines[i].strip().startswith('|'):
                rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')])
                i += 1
            data = [[Paragraph(inline(c), CELL_H) for c in header]]
            data += [[Paragraph(inline(c), CELL) for c in r] for r in rows]
            n = len(header)
            tbl = Table(data, colWidths=[(170 * mm) / n] * n)
            tbl.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#c8d6e5')),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eaf2fa')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story += [tbl, Spacer(1, 5 * mm)]
            continue

        if s.startswith('---'):
            story.append(HRFlowable(width='100%', color=colors.HexColor('#c8d6e5'), spaceBefore=6, spaceAfter=8))
        elif s.startswith('### '):
            story.append(Paragraph(inline(s[4:]), H3))
        elif s.startswith('## '):
            story.append(Paragraph(inline(s[3:]), H2))
        elif s.startswith('# '):
            story.append(Paragraph(inline(s[2:]), H1))
        elif s.startswith('> '):
            story.append(Paragraph(inline(s[2:]), QUOTE))
        elif re.match(r'^[-*] ', s):
            story.append(Paragraph(inline(s[2:]), LI, bulletText='•'))
        elif re.match(r'^\d+\. ', s):
            num, text = s.split('. ', 1)
            story.append(Paragraph(inline(text), LI, bulletText=num + '.'))
        else:
            story.append(Paragraph(inline(s), BODY))
        i += 1

    SimpleDocTemplate(str(out), pagesize=A4,
                      leftMargin=20 * mm, rightMargin=20 * mm,
                      topMargin=16 * mm, bottomMargin=16 * mm,
                      title=Path(src).stem, author='AquaControl').build(story)
    print('готово:', out, round(Path(out).stat().st_size / 1024, 1), 'КБ')


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    convert(sys.argv[1], sys.argv[2])
