#!/usr/bin/env python3
"""Generate the 'IMD services' shortcut and Quick Settings tile icons.

The gear is lifted verbatim from app/src/main/res/drawable/ic_launcher_foreground.xml,
so these are literally the app icon's gear with the key swapped for an Android head —
a sibling rather than a lookalike.
"""
import math
import pathlib
import re

# Paths resolve from this script's own location, so it runs from anywhere.
REPO = pathlib.Path(__file__).resolve().parent.parent
ROOT = REPO
OUT = REPO / 'design/out'
OUT.mkdir(exist_ok=True)

MINT = '#A5DBB9'
GREEN = '#13A75B'

# ── the gear, straight out of the shipped launcher icon ──────────────────────
src = (ROOT / 'app/src/main/res/drawable/ic_launcher_foreground.xml').read_text()
GEAR = re.findall(r'android:pathData="(M69\.207[^"]+)"', src)[0]

# ── the Android head, constructed ────────────────────────────────────────────
# Drawn in a 24-unit space (the proportions Material's android glyph uses) and
# mapped into the 108 viewport so it sits where the key used to.
SCALE = 1.25
CX, CY = 54.0, 54.0          # gear centre
HX, HY = 12.0, 9.9           # head bbox centre in the 24-space


def to108(x, y):
    return CX + (x - HX) * SCALE, CY + (y - HY) * SCALE


DOME_CX, DOME_CY = to108(12.0, 15.0)
DOME_R = 8.0 * SCALE
EYE_R = 1.0 * SCALE
ANTENNA_W = 1.35 * SCALE

EYES = [to108(9.0, 11.6), to108(15.0, 11.6)]
ANTENNAE = [(to108(6.6, 5.4), to108(8.8, 8.8)), (to108(17.4, 5.4), to108(15.2, 8.8))]

# Dome: half disc with a flat bottom, corners just softened so it does not read
# as a bitten circle.
CORNER = 1.2


def dome_path():
    left, right = DOME_CX - DOME_R, DOME_CX + DOME_R
    bottom = DOME_CY
    return (
        f'M {left:.3f} {bottom - CORNER:.3f} '
        f'A {DOME_R:.3f} {DOME_R:.3f} 0 0 1 {right:.3f} {bottom - CORNER:.3f} '
        f'L {right:.3f} {bottom - CORNER:.3f} '
        f'A {CORNER:.3f} {CORNER:.3f} 0 0 1 {right - CORNER:.3f} {bottom:.3f} '
        f'L {left + CORNER:.3f} {bottom:.3f} '
        f'A {CORNER:.3f} {CORNER:.3f} 0 0 1 {left:.3f} {bottom - CORNER:.3f} Z'
    )


def circle(cx, cy, r):
    return (
        f'M {cx - r:.3f} {cy:.3f} '
        f'a {r:.3f} {r:.3f} 0 1 0 {2 * r:.3f} 0 '
        f'a {r:.3f} {r:.3f} 0 1 0 {-2 * r:.3f} 0 Z'
    )


def antennae_svg(colour, width):
    out = []
    for (x1, y1), (x2, y2) in ANTENNAE:
        out.append(
            f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" '
            f'stroke="{colour}" stroke-width="{width:.3f}" stroke-linecap="round"/>'
        )
    return '\n  '.join(out)


# ── 1. shortcut icon: filled, in the app icon's own colours ──────────────────
eyes_knockout = ' '.join(circle(x, y, EYE_R) for x, y in EYES)

shortcut_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="108" height="108" viewBox="0 0 108 108">
  <path fill="{MINT}" d="{GEAR}"/>
  {antennae_svg(GREEN, ANTENNA_W)}
  <path fill="{GREEN}" fill-rule="evenodd" d="{dome_path()} {eyes_knockout}"/>
</svg>'''

# ── 2. tile icon: one colour, stroked outlines ───────────────────────────────
# Quick Settings tints the tile icon itself, so it has to be a flat silhouette.
# The gear outline is the same path stroked rather than filled, which keeps the
# two icons recognisably the same drawing.
STROKE = 2.6

tile_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="108" height="108" viewBox="0 0 108 108">
  <path fill="none" stroke="{{c}}" stroke-width="{STROKE}" stroke-linejoin="round" d="{GEAR}"/>
  <path fill="none" stroke="{{c}}" stroke-width="{STROKE}" stroke-linejoin="round" d="{dome_path()}"/>
  {antennae_svg('{c}', STROKE * 0.85)}
  <path fill="{{c}}" d="{' '.join(circle(x, y, EYE_R * 0.95) for x, y in EYES)}"/>
</svg>'''

(OUT / 'shortcut.svg').write_text(shortcut_svg)
(OUT / 'tile_white.svg').write_text(tile_svg.replace('{c}', '#FFFFFF'))
(OUT / 'tile_dark.svg').write_text(tile_svg.replace('{c}', '#1A1C16'))

print('gear path chars:', len(GEAR))
print('dome centre %.2f,%.2f r=%.2f' % (DOME_CX, DOME_CY, DOME_R))
print('head spans x %.1f-%.1f' % (DOME_CX - DOME_R, DOME_CX + DOME_R))
print('wrote shortcut.svg, tile_white.svg, tile_dark.svg')
