#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Собирает PDF с политикой конфиденциальности из текста в store/policy_for_web.txt.

Зачем PDF: магазину нужна ссылка на политику, открывающаяся в браузере.
PDF можно положить на Яндекс Диск, Облако Mail.ru или в любое другое место
и дать публичную ссылку — работает без сайта и без хостинга.

    python3 store/make_policy_pdf.py
"""
import re
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'store' / 'policy_for_web.txt'
OUT = ROOT / 'store' / 'Политика_конфиденциальности_AquaControl.pdf'

pdfmetrics.registerFont(TTFont('DejaVu', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVu-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))

BODY = ParagraphStyle('body', fontName='DejaVu', fontSize=10.5, leading=15,
                      textColor=colors.HexColor('#22303f'), spaceAfter=6)
H1 = ParagraphStyle('h1', fontName='DejaVu-Bold', fontSize=16, leading=20,
                    textColor=colors.HexColor('#0f2338'), spaceAfter=10)
H2 = ParagraphStyle('h2', fontName='DejaVu-Bold', fontSize=11, leading=15,
                    textColor=colors.HexColor('#0284c7'), spaceBefore=10, spaceAfter=4)
META = ParagraphStyle('meta', fontName='DejaVu', fontSize=9.5, leading=13,
                      textColor=colors.HexColor('#5b6b80'), spaceAfter=10)


def main():
    raw = SRC.read_text(encoding='utf-8')
    body = raw.split('=== НАЧАЛО ТЕКСТА ===')[1].split('=== КОНЕЦ ТЕКСТА ===')[0].strip()

    blocks = [b.strip() for b in re.split(r'\n\s*\n', body) if b.strip()]
    story = []
    for i, block in enumerate(blocks):
        text = block.replace('\n', ' ').strip()
        if i == 0:
            story.append(Paragraph(text, H1))
        elif text.startswith('Дата вступления'):
            story.append(Paragraph(block.replace('\n', '<br/>'), META))
        elif text == text.upper() and len(text) < 60:
            story.append(Paragraph(text, H2))
        else:
            story.append(Paragraph(text, BODY))

    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph(
        'Этот же текст доступен внутри приложения без интернета: '
        '«Настройки» → «О приложении» → «Политика конфиденциальности».', META))

    SimpleDocTemplate(str(OUT), pagesize=A4,
                      leftMargin=20 * mm, rightMargin=20 * mm,
                      topMargin=18 * mm, bottomMargin=18 * mm,
                      title='Политика конфиденциальности AquaControl Pro',
                      author='AquaControl').build(story)
    print('готово:', OUT.name, round(OUT.stat().st_size / 1024, 1), 'КБ')


if __name__ == '__main__':
    main()
