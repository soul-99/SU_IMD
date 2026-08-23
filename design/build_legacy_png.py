#!/usr/bin/env python3
"""Regenerate the pre-26 PNG icons from the vector drawables.

API 24 and 25 have no adaptive icons, so each launcher entry also needs a flat PNG per
density. These are rendered from the same vectors, at the scale the adaptive mask actually
shows — the middle 72 units of the 108 viewport fill the frame — so the old icon and the new
one are the same picture at the same size, rather than the legacy one being noticeably
smaller as it was.

The corner masks are lifted from the shipped PNGs' own alpha channels rather than redrawn,
so the silhouette stays exactly what it has always been.
"""
import io
import pathlib
import xml.etree.ElementTree as ET

import cairosvg
from PIL import Image

# Paths resolve from this script's own location, so it runs from anywhere.
REPO = pathlib.Path(__file__).resolve().parent.parent
RES = REPO / 'app/src/main/res'
NS = '{http://schemas.android.com/apk/res/android}'
BACKGROUND = '#FFFFFF'          # @color/ic_launcher_background
SAFE = 72.0 / 108.0             # the fraction of the viewport an adaptive mask shows

DENSITIES = {'mdpi': 48, 'hdpi': 72, 'xhdpi': 96, 'xxhdpi': 144, 'xxxhdpi': 192}

# name -> (foreground drawable, which shipped PNG's alpha to use as the mask)
ICONS = {
    'ic_launcher': ('ic_launcher_foreground', 'ic_launcher'),
    'ic_launcher_round': ('ic_launcher_foreground', 'ic_launcher_round'),
    'ic_services': ('ic_services_foreground', 'ic_launcher'),
    'ic_revert': ('ic_revert_foreground', 'ic_launcher'),
}


def to_svg(name):
    root = ET.parse(RES / 'drawable' / f'{name}.xml').getroot()
    body = []
    for p in root.iter('path'):
        fill = p.get(f'{NS}fillColor', '#000000')
        rule = 'evenodd' if p.get(f'{NS}fillType', '').lower() == 'evenodd' else 'nonzero'
        body.append(f'<path fill="{fill}" fill-rule="{rule}" d="{p.get(f"{NS}pathData")}"/>')

    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 108 108" '
            'width="108" height="108">' + ''.join(body) + '</svg>')


for out_name, (fg, mask_src) in ICONS.items():
    svg = to_svg(fg)

    for density, size in DENSITIES.items():
        full = round(size / SAFE)                      # render the whole viewport...
        buf = io.BytesIO()
        cairosvg.svg2png(bytestring=svg.encode(), write_to=buf,
                         output_width=full, output_height=full)
        art = Image.open(buf).convert('RGBA')

        card = Image.new('RGBA', (full, full), BACKGROUND)
        card.alpha_composite(art)

        off = (full - size) // 2                       # ...then crop to what the mask shows
        card = card.crop((off, off, off + size, off + size))

        shipped = RES / f'mipmap-{density}' / f'{mask_src}.png'
        mask = Image.open(shipped).convert('RGBA').split()[3]
        assert mask.size == (size, size), f'{shipped} is {mask.size}, expected {size}'
        card.putalpha(mask)

        card.save(RES / f'mipmap-{density}' / f'{out_name}.png')

    print(f'{out_name:20} regenerated at {", ".join(DENSITIES)}')
