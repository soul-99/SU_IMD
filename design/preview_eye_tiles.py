#!/usr/bin/env python3
"""Contact sheet for the Hide settings tile: each candidate in both states.

The pair matters more than either icon alone - the two have to read as the same tile in
two states, and the difference has to be obvious in the corner of the eye at 24dp.
"""
import io
import pathlib
import re

import cairosvg
from PIL import Image, ImageDraw, ImageFont

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / 'design/out'

PANEL = (18, 20, 14)
ON_BG, ON_FG = (177, 209, 138), (28, 55, 0)
OFF_BG, OFF_FG = (43, 50, 36), (196, 200, 186)


def d_of(name, state):
    return (OUT / f'eye_{name}_{state}_path.txt').read_text().strip()


def d_drawable(name):
    src = (REPO / f'app/src/main/res/drawable/{name}.xml').read_text()
    return re.findall(r'android:pathData="([^"]+)"', src)[0]


def render(d, px, c):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{px}" height="{px}" '
           f'viewBox="0 0 24 24"><path fill="rgb{c}" fill-rule="evenodd" d="{d}"/></svg>')
    png = cairosvg.svg2png(bytestring=svg.encode(), output_width=px, output_height=px)
    return Image.open(io.BytesIO(png)).convert('RGBA')


def font(sz):
    f = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    return ImageFont.truetype(f, sz) if pathlib.Path(f).exists() else ImageFont.load_default()


def pill(d, on, label, w=250, h=68):
    img = Image.new('RGBA', (w, h), PANEL + (255,))
    dr = ImageDraw.Draw(img)
    bg, fg = (ON_BG, ON_FG) if on else (OFF_BG, OFF_FG)
    dr.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=bg + (255,))
    img.alpha_composite(render(d, 38, fg), (18, (h - 38) // 2))
    dr.text((68, h // 2 - 8), label, font=font(14), fill=fg + (255,))
    return img


NAMES = ['ref', 'ref-bold']
BIG, SMALL = 170, [24, 32, 44]
PAD, LAB, GAP = 28, 30, 18

col_w = BIG * 2 + GAP
W = PAD * 2 + len(NAMES) * col_w + (len(NAMES) - 1) * PAD
H = PAD + LAB + BIG + 16 + 52 + 16 + 68 * 2 + 10 + PAD

sheet = Image.new('RGBA', (W, H), PANEL + (255,))
draw = ImageDraw.Draw(sheet)

x = PAD
for name in NAMES:
    draw.text((x, PAD), name, font=font(19), fill=OFF_FG + (255,))
    y = PAD + LAB

    for i, state in enumerate(('off', 'on')):
        sheet.alpha_composite(render(d_of(name, state), BIG, OFF_FG), (x + i * (BIG + GAP), y))
        draw.text((x + i * (BIG + GAP) + 4, y + BIG - 2), state, font=font(13),
                  fill=(120, 126, 112, 255))

    y += BIG + 16
    xs = x
    for state in ('off', 'on'):
        for s in SMALL:
            sheet.alpha_composite(render(d_of(name, state), s, OFF_FG), (xs, y + (44 - s) // 2))
            xs += s + 12
        xs += 16

    y += 52 + 16
    sheet.alpha_composite(pill(d_of(name, 'off'), False, 'Hide settings'), (x, y))
    sheet.alpha_composite(pill(d_of(name, 'on'), True, 'Settings hidden'), (x, y + 74))

    x += col_w + PAD

sheet.convert('RGB').save(OUT / 'eye_tiles.png')
print('wrote', OUT / 'eye_tiles.png', sheet.size)
