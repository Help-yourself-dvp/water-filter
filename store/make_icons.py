#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор иконок AquaControl Pro.

Создаёт из одного описания сразу четыре согласованных файла, чтобы иконка
одинаково выглядела в лаунчере, в списке «Приложения» настроек телефона,
в шторке уведомлений и в карточке магазина:

    icon.png              1024×1024  мастер, «во весь квадрат» (магазин + старые лаунчеры)
    icon_foreground.png   1024×1024  прозрачный слой для адаптивной иконки Android 8+
    icon_background.png   1024×1024  фон адаптивной иконки (тот же градиент)
    icon_notification.png 1024×1024  белый силуэт капли для значка в шторке
    store/icon-512.png     512×512   иконка для карточки RuStore

Почему foreground меньше мастера:
    Адаптивная иконка Android — слой 108dp, из которого видно только центральные 72dp
    (66.7%). Если рисовать в слое так же крупно, как в мастере, лаунчер обрежет края,
    и иконка в лаунчере окажется крупнее, чем в настройках телефона. Поэтому рисунок
    в foreground уменьшен ровно в 72/108 раза — тогда обе иконки выглядят одинаково.

Запуск:  python3 store/make_icons.py    (из корня репозитория)
Нужен пакет Pillow:  pip install pillow
"""

import math
import os
from PIL import Image, ImageDraw, ImageFilter

# ----------------------------------------------------------------------------- параметры

S = 1024                 # итоговый размер
SS = 4                   # супер-сэмплинг (рисуем крупнее, потом уменьшаем — гладкие края)
W = S * SS

BG_TOP = (2, 132, 199)   # #0284C7
BG_BOTTOM = (0, 27, 92)  # #001B5C
CYAN = (0, 242, 254)     # #00F2FE
TRACK = (12, 52, 110)    # непройденная часть кольца
DROP_TOP = (255, 255, 255)
DROP_BOTTOM = (223, 243, 255)

RING_R = 0.360           # радиус кольца в долях от стороны
RING_W = 0.052           # толщина кольца
RING_START = -90.0       # старт сверху
RING_SWEEP = 262.0       # заполненная часть (~73%)
DROP_H = 0.430           # высота капли в долях от стороны

ADAPTIVE_SCALE = 72.0 / 108.0   # безопасная зона адаптивной иконки


# ----------------------------------------------------------------------------- примитивы

def linear_gradient(size, top, bottom, diagonal=True):
    """Градиент сверху вниз (или по диагонали) без внешних зависимостей."""
    img = Image.new("RGB", (size, size))
    px = img.load()
    for y in range(size):
        for x in range(0, size, 1):
            t = ((x + y) / (2.0 * size)) if diagonal else (y / float(size))
            px[x, y] = (
                int(top[0] + (bottom[0] - top[0]) * t),
                int(top[1] + (bottom[1] - top[1]) * t),
                int(top[2] + (bottom[2] - top[2]) * t),
            )
    return img


def droplet_polygon(cx, cy, height):
    """
    Классическая капля: снизу окружность, сверху остриё, бока — касательные.
    cy — центр нижней окружности, height — полная высота капли.
    """
    # height = d + R, где d — расстояние от центра окружности до острия
    R = height / 3.05
    d = height - R
    L = math.sqrt(max(d * d - R * R, 1e-6))
    apex = (cx, cy - d)

    # точки касания
    tx = R * L / d
    ty = -R * R / d
    a_right = math.degrees(math.atan2(ty, tx))          # ≈ -35°
    a_left = math.degrees(math.atan2(ty, -tx))          # ≈ -145° → 215°
    if a_left < a_right:
        a_left += 360.0

    pts = [apex]
    steps = 240
    for i in range(steps + 1):
        a = math.radians(a_left - (a_left - a_right) * i / steps)
        pts.append((cx + R * math.cos(a), cy + R * math.sin(a)))
    return pts


def draw_ring(layer, cx, cy, radius, width, start, sweep, color, track_color=None):
    d = ImageDraw.Draw(layer)
    box = [cx - radius, cy - radius, cx + radius, cy + radius]
    if track_color is not None:
        d.arc(box, 0, 360, fill=track_color + (255,), width=int(width))
    d.arc(box, start, start + sweep, fill=color + (255,), width=int(width))
    # круглые «шапочки» на концах дуги
    for ang in (start, start + sweep):
        a = math.radians(ang)
        ex, ey = cx + radius * math.cos(a), cy + radius * math.sin(a)
        r = width / 2.0
        d.ellipse([ex - r, ey - r, ex + r, ey + r], fill=color + (255,))


def art_layer(size, scale=1.0, with_glow=True):
    """Прозрачный слой с кольцом и каплей. scale — доля от базового размера."""
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    cx = cy = size / 2.0
    radius = size * RING_R * scale
    width = size * RING_W * scale

    if with_glow:
        glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw_ring(glow, cx, cy, radius, width * 1.15, RING_START, RING_SWEEP, CYAN)
        glow = glow.filter(ImageFilter.GaussianBlur(size * 0.022))
        glow.putalpha(glow.getchannel("A").point(lambda v: int(v * 0.55)))
        layer.alpha_composite(glow)

    draw_ring(layer, cx, cy, radius, width, RING_START, RING_SWEEP, CYAN, TRACK)

    # капля с мягким вертикальным градиентом
    drop_h = size * DROP_H * scale
    drop_cy = cy + drop_h * 0.16
    pts = droplet_polygon(cx, drop_cy, drop_h)

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)

    # мягкая тень под каплей — немного объёма, без «стокового» блеска
    shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    sh_pts = [(x, y + drop_h * 0.045) for (x, y) in pts]
    ImageDraw.Draw(shadow).polygon(sh_pts, fill=(0, 20, 60, 120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(size * 0.016))
    layer.alpha_composite(shadow)

    grad = linear_gradient(size, DROP_TOP, DROP_BOTTOM, diagonal=False).convert("RGBA")
    layer.paste(grad, (0, 0), mask)
    return layer


# ----------------------------------------------------------------------------- сборка

def build():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    store = os.path.join(root, "store")
    os.makedirs(store, exist_ok=True)

    # 1. мастер «во весь квадрат»
    bg = linear_gradient(W, BG_TOP, BG_BOTTOM).convert("RGBA")
    master = bg.copy()
    master.alpha_composite(art_layer(W, 1.0))
    master = master.resize((S, S), Image.LANCZOS)
    master.convert("RGB").save(os.path.join(root, "icon.png"))
    master.convert("RGB").resize((512, 512), Image.LANCZOS).save(os.path.join(store, "icon-512.png"))

    # 2. фон адаптивной иконки
    bg.resize((S, S), Image.LANCZOS).convert("RGB").save(os.path.join(root, "icon_background.png"))

    # 3. передний слой адаптивной иконки — уменьшен под безопасную зону
    fg = art_layer(W, ADAPTIVE_SCALE)
    fg.resize((S, S), Image.LANCZOS).save(os.path.join(root, "icon_foreground.png"))

    # 4. значок для шторки уведомлений: только белый силуэт капли
    notif = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    nd = ImageDraw.Draw(notif)
    nh = W * 0.62
    nd.polygon(droplet_polygon(W / 2.0, W / 2.0 + nh * 0.16, nh), fill=(255, 255, 255, 255))
    notif.resize((S, S), Image.LANCZOS).save(os.path.join(root, "icon_notification.png"))

    print("Готово: icon.png, icon_foreground.png, icon_background.png, "
          "icon_notification.png, store/icon-512.png")


if __name__ == "__main__":
    build()
