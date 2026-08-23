#!/usr/bin/env python3
"""'Revert to default' icon: the app's gear with a revert arrow and a tick inside it.

The gear is not redrawn — it is lifted from the shipped launcher icon and normalised back to
the size it was authored at, so this stays a sibling of the app icon and of the Services
manager icon rather than a lookalike. Only the glyph inside changes.

Two things about the arrow are deliberate and easy to get wrong:

* The arrowhead is isoceles on the ring's *tangent*, not a triangle whose tip sits back on
  the circle. A tip placed on the circle drags the apex inward while the base stays radial,
  which shears the head — it reads as a flag bent off the arc instead of a head sitting on
  it.
* The ring is as large as the gear's flat centre will take. The gear's rim is a wave — 20.6
  units out at each tooth, 15.2 in each valley — and the C sweeps past every valley, so the
  valleys set the ceiling. The containment check at the bottom is what enforces it: an
  overhang is nearly invisible on the coloured icon but cuts a notch out of the gear on the
  tile, where the glyph is a knockout rather than a colour.

Writes the drawables straight into the res tree. Re-runnable: the gear is re-normalised from
whatever the launcher icon currently holds, so this does not compound if the art is rescaled.
"""
import math
import pathlib
import re
import sys

from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union
from svgpathtools import parse_path

# Paths resolve from this script's own location, so it runs from anywhere.
REPO = pathlib.Path(__file__).resolve().parent.parent
RES = REPO / 'app/src/main/res'
OUT = REPO / 'design/out'

CX = CY = 54.0
MINT, GREEN = '#A5DBB9', '#13A75B'
ROUND = dict(cap_style=1, join_style=1, quad_segs=48)

CANON_WIDTH = 38.3823   # what the gear measured when the glyph geometry below was drawn
GROW = float(sys.argv[1]) if len(sys.argv) > 1 else 1.35   # must match scale_app_icons.py

# How large the arrow is drawn inside the gear, as a fraction of the largest that would fit.
# Drawn at 1.0 it touches the gear's inner edge and reads as crowded. Applied to both the
# launcher icon and the tile so they stay the same drawing, and applied *after* the checks
# below — those are about how big the arrow may be, which the gear's rim decides, not about
# how big it is actually drawn.
GLYPH_SHRINK = float(sys.argv[2]) if len(sys.argv) > 2 else 0.88

# ── the arrow, option B1 ─────────────────────────────────────────────────────
R_OUT, BAND, GAP_DEG = 14.2, 3.5, 76.0
SOFT = 0.55             # corner radius on the arrowhead
START_DEG = -144.0      # where the gap opens; nudged off -140 so the head clears a tooth
HEAD_W, HEAD_L, HEAD_BACK = 1.5, 1.9, 0.10

R_MID, R_IN = R_OUT - BAND / 2, R_OUT - BAND
START = math.radians(START_DEG)
END = START + math.radians(360.0 - GAP_DEG)

LICENCE = '''<?xml version="1.0" encoding="utf-8"?><!--
  ~
  ~   Copyright 2026 soul_99 (suIMD)
  ~
  ~   Licensed under the GNU General Public License v3.0 (the "License");
  ~   you may not use this file except in compliance with the License.
  ~   You may obtain a copy of the License at
  ~
  ~       https://www.gnu.org/licenses/gpl-3.0
  ~
  -->
'''


def polar(r, a):
    return CX + r * math.cos(a), CY + r * math.sin(a)


def bbox(d, steps=400):
    p = parse_path(d)
    pts = [p.point(i / steps) for i in range(steps + 1)]

    return (min(c.real for c in pts), min(c.imag for c in pts),
            max(c.real for c in pts), max(c.imag for c in pts))


def rescale(d, k):
    """Uniformly scale an absolute path about the viewport centre."""
    args = {'M': 2, 'L': 2, 'C': 6, 'S': 4, 'Q': 4, 'T': 2, 'H': 1, 'V': 1, 'A': 7, 'Z': 0}
    num = re.compile(r'[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?')
    out, i, cmd = [], 0, None

    while i < len(d):
        if d[i].isalpha():
            cmd = d[i]
            assert cmd in args and cmd.isupper(), f'unhandled command {cmd!r}'
            out.append(cmd)
            i += 1
        elif d[i].isdigit() or d[i] in '-+.':
            vals = []
            for _ in range(args[cmd]):
                m = num.match(d, i)
                vals.append(float(m.group()))
                i = m.end()
                while i < len(d) and d[i] in ', \t\n':
                    i += 1
            if cmd == 'H':
                vals = [CX + (vals[0] - CX) * k]
            elif cmd == 'V':
                vals = [CY + (vals[0] - CY) * k]
            elif cmd == 'A':
                vals = [vals[0] * k, vals[1] * k, vals[2], vals[3], vals[4],
                        CX + (vals[5] - CX) * k, CY + (vals[6] - CY) * k]
            else:
                vals = [(CX if j % 2 == 0 else CY) + (v - (CX if j % 2 == 0 else CY)) * k
                        for j, v in enumerate(vals)]
            out.append(','.join(f'{v:.4f}'.rstrip('0').rstrip('.') for v in vals))
        else:
            i += 1

    return ''.join(t if t.isalpha() or out[j - 1].isalpha() else ' ' + t
                   for j, t in enumerate(out))


# The monochrome launcher icon is the gear on its own, so it is the one unambiguous copy of
# the path. Normalise it back to the size the glyph geometry below was drawn against.
mono = (RES / 'drawable/ic_launcher_monochrome.xml').read_text()
gear_now = re.findall(r'pathData="([^"]+)"', mono)[0]
b = bbox(gear_now)
GEAR = rescale(gear_now, CANON_WIDTH / (b[2] - b[0]))


def arc():
    """The C of the revert arrow, stroked with round caps rather than cut square."""
    n = 200
    pts = [polar(R_MID, START + (END - START) * i / n) for i in range(n + 1)]

    return LineString(pts).buffer(BAND / 2, **ROUND)


def arrow_head():
    """An isoceles triangle capping the START end, pointing back along the sweep.

    Erode-and-dilate on a shape this small can shed a sliver at a corner, so only the main
    body is kept; a stray sliver would show up as a spike hanging off the head.
    """
    px, py = polar(R_MID, START)
    tx, ty = math.sin(START), -math.cos(START)      # tangent, pointing back along the sweep
    nx, ny = math.cos(START), math.sin(START)       # radial: the base lies along this
    half, length = BAND * HEAD_W, BAND * HEAD_L
    bx, by = px - tx * length * HEAD_BACK, py - ty * length * HEAD_BACK
    tri = Polygon([
        (bx + nx * half, by + ny * half),
        (bx - nx * half, by - ny * half),
        (bx + tx * length, by + ty * length),
    ])
    soft = tri.buffer(-SOFT, **ROUND).buffer(SOFT, **ROUND)

    if soft.geom_type == 'MultiPolygon':
        soft = max(soft.geoms, key=lambda g: g.area)

    assert soft.area > tri.area * 0.7, 'the rounding ate the arrowhead; lower SOFT'

    return soft


def tick():
    """A checkmark centred in the ring, scaled off the inner radius so it keeps proportion."""
    k = R_IN / 10.6
    pts = [(CX + x * k, CY + y * k) for x, y in ((-5.0, 0.4), (-1.6, 3.9), (5.4, -3.6))]

    return LineString(pts).buffer(BAND * 0.47 * k, **ROUND)


glyph = unary_union([g.buffer(0) for g in (arc(), arrow_head(), tick())])
parts = list(glyph.geoms) if glyph.geom_type == 'MultiPolygon' else [glyph]

# The ring must stay a C, never a closed O — a closed one would gain an interior ring, which
# the knockout renders as a filled disc in the middle of the arrow.
for part in parts:
    assert not list(part.interiors), 'the revert glyph closed on itself; widen the gap'

tick_clear = tick().distance(unary_union([arc(), arrow_head()]))
assert tick_clear > 0.6, f'the tick is crowding the arrow ({tick_clear:.2f})'

gear_poly = Polygon([
    (c.real, c.imag) for c in (parse_path(GEAR).point(i / 1999) for i in range(2000))
]).buffer(0)
gear_clear = glyph.distance(gear_poly.exterior)
assert gear_poly.contains(glyph), 'the glyph overhangs the gear'
assert gear_clear > 0.7, f'the glyph is crowding the gear rim ({gear_clear:.2f})'


def ring_path(coords, tx):
    p = [tx(x, y) for x, y in coords]

    return f'M{p[0][0]:.3f},{p[0][1]:.3f}' + ''.join(f'L{x:.3f},{y:.3f}' for x, y in p[1:]) + 'Z'


ident = (lambda x, y: (x, y))
glyph108 = ' '.join(ring_path(list(p.exterior.coords), ident) for p in parts)

# ── the drawables ────────────────────────────────────────────────────────────
gear_grown = rescale(GEAR, GROW)
glyph_grown = rescale(glyph108, GROW * GLYPH_SHRINK)


def vector(body, size=108):
    return (LICENCE + '<vector xmlns:android="http://schemas.android.com/apk/res/android"\n'
            f'    android:width="{size}dp"\n    android:height="{size}dp"\n'
            f'    android:viewportWidth="{size}"\n    android:viewportHeight="{size}">\n'
            + body + '</vector>\n')


def path(d, colour, even_odd=False, comment=None):
    out = f'    {comment}\n' if comment else ''
    out += f'    <path\n        android:fillColor="{colour}"\n'
    if even_odd:
        out += '        android:fillType="evenOdd"\n'

    return out + f'        android:pathData="{d}" />\n'


(RES / 'drawable/ic_revert_foreground.xml').write_text(vector(
    path(gear_grown, MINT) + path(glyph_grown, GREEN, even_odd=True)))

# Themed ("monochrome") icons are a single silhouette the launcher tints, so the glyph has
# to be a hole in the gear rather than a second colour drawn on top of it.
(RES / 'drawable/ic_revert_monochrome.xml').write_text(vector(
    path(f'{gear_grown} {glyph_grown}', '@android:color/white', even_odd=True)))

# A tile has no adaptive-icon safe zone, so the art fills the 24dp frame regardless of how
# big the launcher art is drawn.
SPAN, ART = 22.4, 38.3823
K = SPAN / ART
tile_tx = (lambda x, y: (12 + (x - 54) * K, 12 + (y - 54) * K))
glyph_tx = (lambda x, y: tile_tx(CX + (x - CX) * GLYPH_SHRINK, CY + (y - CY) * GLYPH_SHRINK))
gear24 = ''.join(
    f'{12 + (float(t) - 54) * K:.3f}' if re.fullmatch(r'-?\d+\.?\d*', t or '') else t
    for t in re.split(r'(-?\d+\.?\d*)', GEAR)
)
glyph24 = ' '.join(ring_path(list(p.exterior.coords), glyph_tx) for p in parts)

(RES / 'drawable/ic_revert_tile.xml').write_text(vector(
    path(f'{gear24} {glyph24}', '@android:color/white', even_odd=True, comment=(
        '<!--\n      No android:tint here on purpose. Quick Settings applies its own tint to'
        ' a tile icon\n      to match the panel and the tile\'s state, so a tint set here'
        ' would either be\n      overridden or fight it. The paths are plain white and the'
        ' system colours them.\n    -->')), size=24))

# Three modules need this artwork and none of them can see another's resources: the app for
# the manifest, the notification builder, and the Compose buttons in feature/apps. Rather
# than three hand-kept copies, the app's files are the source and the others are written
# from them here — under distinct names, since identical names in two modules collide when
# resources merge.
GLYPHS = REPO / 'design-system/src/main/res/drawable'
GLYPHS.mkdir(parents=True, exist_ok=True)
for src, dst in (('ic_revert_tile', 'ic_revert_glyph'), ('ic_services_tile', 'ic_services_glyph')):
    (GLYPHS / f'{dst}.xml').write_text((RES / f'drawable/{src}.xml').read_text())

NOTIF = REPO / 'framework/notification-manager/src/main/res/drawable'
(NOTIF / 'ic_revert_notification_large.xml').write_text(vector(
    path(gear_grown, MINT) + path(glyph_grown, GREEN, even_odd=True)))
(NOTIF / 'ic_revert_notification_small.xml').write_text(vector(
    path(f'{gear24} {glyph24}', '@android:color/white', even_odd=True, comment=(
        '<!--\n      A status-bar icon is drawn as a single-colour silhouette and tinted by'
        ' the system,\n      so this is the tile artwork rather than the launcher one: flat,'
        ' and with the glyph\n      as a hole rather than a second colour.\n    -->')),
    size=24))

(RES / 'mipmap-anydpi-v26/ic_revert.xml').write_text(
    LICENCE + '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
    '    <background android:drawable="@color/ic_launcher_background" />\n'
    '    <foreground android:drawable="@drawable/ic_revert_foreground" />\n'
    '    <monochrome android:drawable="@drawable/ic_revert_monochrome" />\n'
    '</adaptive-icon>\n')

# ── preview ──────────────────────────────────────────────────────────────────
(OUT / 'revert_shortcut_final.svg').write_text(
    '<svg xmlns="http://www.w3.org/2000/svg" width="108" height="108" viewBox="0 0 108 108">'
    f'<rect width="108" height="108" fill="#FFFFFF"/><path fill="{MINT}" d="{gear_grown}"/>'
    f'<path fill="{GREEN}" fill-rule="evenodd" d="{glyph_grown}"/></svg>')

print(f'revert: grow x{GROW}  glyph x{GLYPH_SHRINK}  tick_clear={tick_clear:.2f}  '
      f'gear_clear={gear_clear:.2f} at full size  parts={len(parts)}')
print('wrote ic_revert_foreground / _monochrome / _tile, mipmap-anydpi-v26/ic_revert.xml,\n      framework/notification-manager ic_revert_notification_{large,small}.xml,\n'
      '      design-system ic_revert_glyph.xml + ic_services_glyph.xml')
