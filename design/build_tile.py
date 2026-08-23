#!/usr/bin/env python3
"""Monotone Quick Settings tile icon: option B, one colour, head knocked out.

A tile icon is tinted by the system, so it has to be a single flat silhouette. Drawing
the head in the same colour on top of the gear would simply merge into it — so the head
is a *hole*: gear filled, head subtracted, eyes filled back in inside the hole.

That needs real boolean geometry. The antennae overlap the dome, and an even-odd rule
applied to overlapping subpaths punches the overlap back to solid, which would leave two
bright wedges across the robot's ears. So the head shapes are flattened to polygons,
unioned properly, and the single resulting outline is emitted as the hole.
"""
import math
import pathlib
import re

from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

# Paths resolve from this script's own location, so it runs from anywhere.
REPO = pathlib.Path(__file__).resolve().parent.parent
ROOT = REPO
OUT = REPO / 'design/out'

src = (ROOT / 'app/src/main/res/drawable/ic_launcher_foreground.xml').read_text()
GEAR = re.findall(r'android:pathData="(M69\.207[^"]+)"', src)[0]

# ── option B geometry, in the 108 space ──────────────────────────────────────
SCALE = 1.45
CX, CY = 54.0, 54.0
HX, HY = 12.0, 9.9


def to108(x, y):
    return CX + (x - HX) * SCALE, CY + (y - HY) * SCALE


DOME_C = to108(12.0, 15.0)
DOME_R = 8.0 * SCALE
EYES = [to108(9.0, 11.6), to108(15.0, 11.6)]
EYE_R = 1.0 * SCALE
ANTENNAE = [(to108(6.6, 5.4), to108(8.8, 8.8)), (to108(17.4, 5.4), to108(15.2, 8.8))]
ANTENNA_W = 1.35 * SCALE
CORNER = 1.2 * SCALE

STEPS = 96  # flattening resolution; at 108 units this is well under a pixel


def dome_polygon():
    """Half disc with a flat bottom, its two sharp bottom corners softened.

    Built by eroding and re-dilating rather than by placing corner arcs by hand: that
    rounds the convex corners exactly, leaves the already-round top alone, and cannot
    produce the self-intersecting ring that hand-placed arcs did.
    """
    cx, cy = DOME_C
    pts = [
        (cx + DOME_R * math.cos(math.pi + i * math.pi / STEPS),
         cy + DOME_R * math.sin(math.pi + i * math.pi / STEPS))
        for i in range(STEPS + 1)
    ]
    half = Polygon(pts + [(cx - DOME_R, cy)])

    return half.buffer(-CORNER, quad_segs=24).buffer(CORNER, quad_segs=24)


def capsule(p0, p1, width):
    return Point(p0).buffer(width / 2, quad_segs=24).union(
        Point(p1).buffer(width / 2, quad_segs=24),
    ).union(
        Polygon(_thick_segment(p0, p1, width)),
    )


def _thick_segment(p0, p1, width):
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy)
    nx, ny = -dy / length * width / 2, dx / length * width / 2
    return [(x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)]


parts = [dome_polygon()] + [capsule(a, b, ANTENNA_W) for a, b in ANTENNAE]

# buffer(0) repairs any ring that came out of the flattening slightly degenerate, which
# is what a union refuses to work on.
head = unary_union([g.buffer(0) for g in parts]).simplify(0.02)

assert head.geom_type == 'Polygon', head.geom_type
assert not list(head.interiors), 'the head should be solid, with no holes of its own'


def ring_to_path(coords, tx):
    pts = [tx(x, y) for x, y in coords]
    out = f'M{pts[0][0]:.3f},{pts[0][1]:.3f}'
    out += ''.join(f'L{x:.3f},{y:.3f}' for x, y in pts[1:])
    return out + 'Z'


def circle_path(cx, cy, r, tx):
    pts = []
    for i in range(STEPS + 1):
        t = 2 * math.pi * i / STEPS
        pts.append(tx(cx + r * math.cos(t), cy + r * math.sin(t)))
    out = f'M{pts[0][0]:.3f},{pts[0][1]:.3f}'
    out += ''.join(f'L{x:.3f},{y:.3f}' for x, y in pts[1:])
    return out + 'Z'


# ── scale the whole drawing up to fill a 24-unit tile viewport ───────────────
# The launcher icon keeps the art inside the adaptive-icon safe zone, which is why it
# looked small. A tile has no such zone, so the gear fills the frame instead.
ART_MIN, ART_MAX = 34.75, 73.25
TILE_SPAN = 22.4
K = TILE_SPAN / (ART_MAX - ART_MIN)


def tile_tx(x, y):
    return 12 + (x - 54) * K, 12 + (y - 54) * K


def scale_gear_path(d):
    def rep(m):
        return f'{12 + (float(m.group(0)) - 54) * K:.3f}' if False else m.group(0)
    # the gear path is absolute commands with plain x,y pairs; rewrite every pair
    nums = re.findall(r'-?\d+\.?\d*', d)
    it = iter(nums)
    out, i = [], 0
    tokens = re.split(r'(-?\d+\.?\d*)', d)
    for tok in tokens:
        if re.fullmatch(r'-?\d+\.?\d*', tok or ''):
            v = float(tok)
            out.append(f'{12 + (v - 54) * K:.3f}')
            i += 1
        else:
            out.append(tok)
    return ''.join(out)


gear_scaled = scale_gear_path(GEAR)
head_scaled = ring_to_path(list(head.exterior.coords), tile_tx)
eyes_scaled = ' '.join(circle_path(x, y, EYE_R, tile_tx) for x, y in EYES)

TILE_PATH = f'{gear_scaled} {head_scaled} {eyes_scaled}'

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
  <path fill="{{c}}" fill-rule="evenodd" d="{TILE_PATH}"/>
</svg>'''

(OUT / 'tile_mono_white.svg').write_text(svg.replace('{c}', '#FFFFFF'))
(OUT / 'tile_mono_dark.svg').write_text(svg.replace('{c}', '#1A1C16'))
(OUT / 'tile_path.txt').write_text(TILE_PATH)

print('head polygon vertices:', len(head.exterior.coords))
print('gear now spans %.2f-%.2f of 24' % (12 - TILE_SPAN / 2, 12 + TILE_SPAN / 2))
print('path length:', len(TILE_PATH))
