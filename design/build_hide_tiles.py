#!/usr/bin/env python3
"""Quick Settings tile icons for the 'Hide settings' toggle, one per state.

    off   'Hide settings'    gear + an open eye        settings are visible
    on    'Settings hidden'  gear + the eye struck out  settings are hidden

Siblings of the two tiles already shipped: the gear is lifted verbatim from
ic_services_tile.xml rather than redrawn, so all four tiles are the same gear at the same
size, and only the glyph inside differs.

**How the strike stays visible.** A tile icon is one colour, so the glyph is a hole in
the gear rather than a second colour - and a dark slash laid over a dark eye would simply
vanish into it. Letting even-odd invert the overlap instead was tried and is worse: the bar
comes out striped, alternating light and dark as it crosses the eye and the pupil, and
reads as broken rather than as a line drawn through something.

So the regions are computed rather than XOR-ed. The slash is dilated into a *halo*, the
halo is cut out of the eye, and the slash itself is added back inside it. That leaves a
clean bar with an even margin of gear colour on both sides for as long as it crosses the
eye - which is exactly how a struck-out glyph is drawn by hand, and it needs no second
copy of anything.

Everything is drawn as intersections and buffers rather than by placing arcs, so there are
no sharp corners anywhere: the eye is two circles intersected and then eroded and regrown,
which rounds its two points without touching the curves between them.

Needs shapely and cairosvg. None of this runs during the Android build.
"""
import math
import pathlib
import re

from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
from svgpathtools import parse_path

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / 'design/out'
OUT.mkdir(exist_ok=True)

SERVICES_TILE = REPO / 'app/src/main/res/drawable/ic_services_tile.xml'

_data = re.findall(r'android:pathData="([^"]+)"', SERVICES_TILE.read_text())[0]
GEAR = re.findall(r'M[^M]+', _data)[0].strip()

# Measured from the gear itself rather than assumed: the rim is a wave, and it is the
# valleys that cap how big the glyph may be.
GEAR_VALLEY_R = 8.85
CENTRE = (12.0, 12.0)
MARGIN = 0.85           # least clearance from the glyph to the nearest valley

STEPS = 128


def gear_polygon():
    pts = []
    for seg in parse_path(GEAR):
        for i in range(40):
            z = seg.point(i / 40)
            pts.append((z.real, z.imag))

    return Polygon(pts).buffer(0)


def lens(half_w, half_h, round_by):
    """An eye outline: two circles overlapped, then its two points rounded off.

    A lens is the intersection of two equal circles, which is the shape an eye actually
    is - but it meets at two cusps sharp enough to alias badly at 24dp. Eroding and
    regrowing rounds precisely those two corners and leaves the long curves alone, which
    is what hand-placed corner arcs never quite manage.
    """
    # Circle radius and offset that put the intersection exactly on the wanted box.
    r = (half_w ** 2 + half_h ** 2) / (2 * half_h)
    dy = r - half_h

    top = Point(CENTRE[0], CENTRE[1] + dy).buffer(r, quad_segs=96)
    bottom = Point(CENTRE[0], CENTRE[1] - dy).buffer(r, quad_segs=96)

    return top.intersection(bottom).buffer(-round_by, quad_segs=48).buffer(
        round_by, quad_segs=48,
    )


def slash(width, length, angle_deg):
    """A rounded bar through the centre, at [angle_deg] measured from the x axis."""
    a = math.radians(angle_deg)
    dx, dy = math.cos(a) * length / 2, math.sin(a) * length / 2
    p0 = (CENTRE[0] - dx, CENTRE[1] - dy)
    p1 = (CENTRE[0] + dx, CENTRE[1] + dy)

    return unary_union([
        Point(p0).buffer(width / 2, quad_segs=48),
        Point(p1).buffer(width / 2, quad_segs=48),
        Polygon(_thick_segment(p0, p1, width)),
    ]).buffer(0)


def _thick_segment(p0, p1, width):
    (x0, y0), (x1, y1) = p0, p1
    ux, uy = x1 - x0, y1 - y0
    n = math.hypot(ux, uy)
    nx, ny = -uy / n * width / 2, ux / n * width / 2
    return [(x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)]


# Measured off the reference artwork rather than guessed, then written as ratios of the
# eye's own half-width so the whole glyph scales as one drawing:
#
#     eye        654 x 408 px      half-height  0.624
#     pupil      r = 109           0.333
#     slash      54 wide           0.165, laid "\\" - top left to bottom right
#     gap        48 either side    0.147
#     length     ~721              2.20, so it overshoots the eye at both ends
#
# half_w is then capped by the gear: the slash's far cap is the outermost point of the
# whole glyph, at 1.1825 half-widths from centre, and the gear's valleys are at 8.85.
REF = dict(half_h=0.624, pupil_r=0.333, slash_w=0.165, gap=0.147, slash_len=2.20)


def from_reference(half_w, **over):
    v = {k: half_w * r for k, r in REF.items()}
    v['half_w'] = half_w
    v['slash_deg'] = 45
    v['round_by'] = 0.45
    v.update(over)
    return v


VARIANTS = {
    # The reference, as large as the gear's valleys allow.
    'ref': from_reference(6.60),
    # The same drawing with a heavier strike, in case the reference's proportions read
    # too fine once the tile is 24dp rather than a 650px illustration.
    'ref-bold': from_reference(6.55, slash_w=1.50, gap=1.05),
}


def ring_to_path(coords):
    out = f'M{coords[0][0]:.3f},{coords[0][1]:.3f}'
    out += ''.join(f'L{x:.3f},{y:.3f}' for x, y in coords[1:])
    return out + 'Z'


def rings_of(geom):
    geoms = list(geom.geoms) if geom.geom_type == 'MultiPolygon' else [geom]
    out = []
    for g in geoms:
        out.append(list(g.exterior.coords))
        out.extend(list(r.coords) for r in g.interiors)
    return out


def paths_of(geom):
    return [ring_to_path(c) for c in rings_of(geom)]


def check_inside(name, geom):
    """Inside the gear's valleys, or the glyph bites a notch out of the rim.

    Invisible on a two-colour icon; very visible on a tile, where the glyph is a hole
    rather than a second colour and a notch reads as damage.
    """
    room = GEAR_VALLEY_R - max(
        math.hypot(x - CENTRE[0], y - CENTRE[1]) for c in rings_of(geom) for x, y in c
    )
    assert room >= MARGIN, f'{name}: only {room:.2f} of clearance, needs {MARGIN}'

    return room


def emit(dark):
    """Gear filled, every dark region a hole, and any light island inside one filled again.

    Even-odd handles the nesting on its own once the geometry is right: a ring inside a
    hole is solid, which is what puts the pupil back without drawing it twice.
    """
    return ' '.join([GEAR] + paths_of(dark))


def build(name, v):
    eye = lens(v['half_w'], v['half_h'], v['round_by'])
    pupil = Point(CENTRE).buffer(v['pupil_r'], quad_segs=96)

    assert pupil.within(eye.buffer(-0.5)), \
        f'{name}: the pupil touches the rim of the eye'

    room = check_inside(name, eye)

    off = emit(eye.difference(pupil))

    strike = slash(v['slash_w'], v['slash_len'], v['slash_deg'])
    check_inside(name + ' (slash)', strike)

    halo = strike.buffer(v['gap'], quad_segs=48)
    on = emit(unary_union([eye.difference(halo).difference(pupil), strike]))

    for state, path in (('off', off), ('on', on)):
        (OUT / f'eye_{name}_{state}_path.txt').write_text(path)
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" '
            'viewBox="0 0 24 24">\n'
            f'  <path fill="#FFFFFF" fill-rule="evenodd" d="{path}"/>\n</svg>'
        )
        (OUT / f'eye_{name}_{state}.svg').write_text(svg)

    print(f'{name:11s} eye {v["half_w"] * 2:.1f}x{v["half_h"] * 2:.1f}, '
          f'{room:.2f} clear of the rim, {len(on)} path chars')


if __name__ == '__main__':
    for name, v in VARIANTS.items():
        build(name, v)
    print('gear reused verbatim from', SERVICES_TILE.name)
