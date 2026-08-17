#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Готовит скриншоты для карточки RuStore.

Проблема: RuStore ждёт соотношение 16:9 (для вертикальных — 1080×1920),
а современные телефоны снимают 1080×2400 и длиннее. Если загрузить как есть,
магазин обрежет картинку как захочет.

Что делает скрипт: вписывает снимок целиком в холст 1080×1920 на фирменном фоне
и добавляет короткую подпись сверху. Ничего не обрезается, текст читается
даже в маленькой плитке каталога.

Использование:
    1. Положите снимки с телефона в store/screenshots/raw/
       Имена задают порядок: 1.png, 2.png, 3.png ...
    2. python3 store/make_store_shots.py
    3. Готовые файлы появятся в store/screenshots/ready/

Подписи берутся из словаря CAPTIONS ниже по номеру файла.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / 'store' / 'screenshots' / 'raw'
READY = ROOT / 'store' / 'screenshots' / 'ready'

W, H = 1080, 1920                     # то, что ждёт RuStore (16:9 вертикально)
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

# Фон под фирменный стиль приложения (тёмный неон)
BG_TOP = (7, 18, 38)
BG_BOTTOM = (2, 60, 105)
ACCENT = (0, 242, 254)

# Светлый фон — если решите делать набор под светлое оформление
LIGHT_BG_TOP = (232, 245, 255)
LIGHT_BG_BOTTOM = (176, 214, 240)
LIGHT_TEXT = (10, 39, 64)

CAPTIONS = {
    '1': 'Сколько дней осталось до замены',
    '2': 'Все фильтры сразу: что горит',
    '3': 'Отметить замену в два касания',
    '4': 'Напоминание придёт вовремя',
    '5': 'Расходы и сколько воды очищено',
    '6': 'Светлое оформление на выбор',
}

CAPTION_H = 250        # высота полосы с подписью
SIDE = 60              # поля по бокам
LIGHT_SHOTS = set()    # например {'6'} — эти кадры оформить на светлом фоне


def gradient(top, bottom):
    img = Image.new('RGB', (W, H))
    px = img.load()
    for y in range(H):
        k = y / (H - 1)
        row = (int(top[0] + (bottom[0] - top[0]) * k),
               int(top[1] + (bottom[1] - top[1]) * k),
               int(top[2] + (bottom[2] - top[2]) * k))
        for x in range(W):
            px[x, y] = row
    return img


def wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ''
    for w in words:
        probe = (cur + ' ' + w).strip()
        if draw.textlength(probe, font=font) <= max_w:
            cur = probe
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def build(src_path, caption, light=False):
    shot = Image.open(src_path).convert('RGB')

    canvas = gradient(*( (LIGHT_BG_TOP, LIGHT_BG_BOTTOM) if light else (BG_TOP, BG_BOTTOM) ))
    draw = ImageDraw.Draw(canvas)

    # подпись
    font = ImageFont.truetype(FONT, 56)
    color = LIGHT_TEXT if light else (255, 255, 255)
    lines = wrap(draw, caption, font, W - 2 * SIDE)
    y = 78 if len(lines) > 1 else 100
    for line in lines:
        x = (W - draw.textlength(line, font=font)) / 2
        draw.text((x, y), line, font=font, fill=color)
        y += 68

    # сам снимок — вписываем целиком, ничего не обрезая
    area_h = H - CAPTION_H - 70
    area_w = W - 2 * SIDE
    scale = min(area_w / shot.width, area_h / shot.height)
    new = shot.resize((int(shot.width * scale), int(shot.height * scale)), Image.LANCZOS)

    # мягкая тень под снимком
    pad = 18
    shadow = Image.new('RGBA', (new.width + pad * 2, new.height + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rectangle([pad, pad, pad + new.width, pad + new.height],
                                     fill=(0, 0, 0, 90 if not light else 60))
    from PIL import ImageFilter
    shadow = shadow.filter(ImageFilter.GaussianBlur(16))

    px = (W - new.width) // 2
    py = CAPTION_H + (area_h - new.height) // 2
    canvas.paste(shadow, (px - pad, py - pad + 6), shadow)
    canvas.paste(new, (px, py))
    return canvas


def main():
    if not RAW.exists():
        print('Положите снимки в', RAW)
        RAW.mkdir(parents=True, exist_ok=True)
        return
    READY.mkdir(parents=True, exist_ok=True)

    files = sorted(p for p in RAW.iterdir() if p.suffix.lower() in ('.png', '.jpg', '.jpeg'))
    if not files:
        print('В папке', RAW, 'нет картинок')
        return

    for f in files:
        key = f.stem.strip()
        caption = CAPTIONS.get(key, '')
        out = READY / (key + '.png')
        img = build(f, caption, light=(key in LIGHT_SHOTS))
        img.save(out, format='PNG')
        print('готово:', out.name, img.size, caption or '(без подписи)')

    print()
    print('Всё в папке', READY, '— эти файлы и загружайте в RuStore.')


if __name__ == '__main__':
    main()
