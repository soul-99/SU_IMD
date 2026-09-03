#!/usr/bin/env python3
"""
The 'Hide/unhide Settings' launcher icon, in two states.

    visible   the app icon's gear with an open eye where the key is
    hidden    the same eye, struck through

⚠ **Not a new drawing.** The gear is the launcher icon's own path, lifted verbatim out of
`ic_launcher_foreground.xml`, and the eye is the one `build_hide_tiles.py` constructs for the
Quick Settings tile, scaled into the 108 viewport. So the two new icons are siblings of both the
app icon and the tile rather than lookalikes of either - the author's "designed in imd app icons
style".

⚠ **Two colours here, one hole there, and that is the only difference from the tile.** A tile icon
is a single colour, so the tile draws the eye as a hole punched out of the gear. A launcher icon
has the mint gear and the green key to work with, so the eye is drawn *in* the key's colour, in the
key's place, at the key's size - measured off the key rather than chosen, so the two icons weigh
the same in a launcher grid.

Writes SVG previews to design/out and, with --emit, the vector drawables and mipmaps.

Needs shapely, svgpathtools and cairosvg. None of this runs during the Android build.
"""
from __future__ import annotations

import math
import pathlib
import re
import sys

from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
from svgpathtools import parse_path

REPO = pathlib.Path(__file__).resolve().parent.parent

OUT = REPO / "design/out"

OUT.mkdir(exist_ok=True)

LAUNCHER = REPO / "app/src/main/res/drawable/ic_launcher_foreground.xml"

GEAR_COLOUR = "#A5DBB9"

KEY_COLOUR = "#13A75B"

_paths = re.findall(r'android:pathData="([^"]+)"', LAUNCHER.read_text())

GEAR = _paths[0]

KEY_BODY = _paths[1]

CENTRE = (54.0, 54.0)


def _sample(path: str) -> list[tuple[float, float]]:
    pts = []

    for seg in parse_path(path):
        for i in range(40):
            z = seg.point(i / 40)

            pts.append((z.real, z.imag))

    return pts


def _radius(points) -> float:
    return max(math.hypot(x - CENTRE[0], y - CENTRE[1]) for x, y in points)


# ⚠ **The glyph is sized off the key it replaces, not off the gear it sits in.** The gear's
# valleys are at 20.53 and there is room for something much larger; the key only reaches 15.62,
# and an eye drawn to the valleys would make this icon read as heavier than the app's own in a
# launcher grid. Measured here rather than written down, so a change to the artwork carries.
KEY_REACH = _radius(_sample(KEY_BODY))

GEAR_VALLEY = min(
    math.hypot(x - CENTRE[0], y - CENTRE[1]) for x, y in _sample(GEAR)
)

# The eye, in the tile's own 24-unit proportions. Copied from build_hide_tiles.py's REF block,
# where each number is a ratio of the eye's half-width and where they came from is recorded.
REF = dict(half_h=0.624, pupil_r=0.333, slash_w=0.165, gap=0.147, slash_len=2.20)

HALF_W_24 = 6.60

ROUND_BY_24 = 0.45

SLASH_DEG = 45

# The struck eye's outermost point is the far cap of the slash, at 1.1825 half-widths. Scale so
# that lands exactly on the key's reach: both states are then one drawing at one size.
SLASH_REACH_24 = HALF_W_24 * 1.1825

SCALE = KEY_REACH / SLASH_REACH_24


def lens(half_w: float, half_h: float, round_by: float):
    """Two equal circles intersected, with the two cusps eroded away and regrown."""
    r = (half_w ** 2 + half_h ** 2) / (2 * half_h)

    dy = r - half_h

    top = Point(CENTRE[0], CENTRE[1] + dy).buffer(r, quad_segs=96)

    bottom = Point(CENTRE[0], CENTRE[1] - dy).buffer(r, quad_segs=96)

    return top.intersection(bottom).buffer(-round_by, quad_segs=48).buffer(
        round_by, quad_segs=48,
    )


def _thick_segment(p0, p1, width):
    (x0, y0), (x1, y1) = p0, p1

    ux, uy = x1 - x0, y1 - y0

    n = math.hypot(ux, uy)

    nx, ny = -uy / n * width / 2, ux / n * width / 2

    return [(x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)]


def slash(width: float, length: float, angle_deg: float):
    a = math.radians(angle_deg)

    dx, dy = math.cos(a) * length / 2, math.sin(a) * length / 2

    p0 = (CENTRE[0] - dx, CENTRE[1] - dy)

    p1 = (CENTRE[0] + dx, CENTRE[1] + dy)

    return unary_union([
        Point(p0).buffer(width / 2, quad_segs=48),
        Point(p1).buffer(width / 2, quad_segs=48),
        Polygon(_thick_segment(p0, p1, width)),
    ]).buffer(0)


def ring_to_path(coords) -> str:
    out = f"M{coords[0][0]:.3f},{coords[0][1]:.3f}"

    out += "".join(f"L{x:.3f},{y:.3f}" for x, y in coords[1:])

    return out + "Z"


def rings_of(geom):
    geoms = list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom]

    out = []

    for g in geoms:
        out.append(list(g.exterior.coords))

        out.extend(list(r.coords) for r in g.interiors)

    return out


def paths_of(geom) -> str:
    return " ".join(ring_to_path(c) for c in rings_of(geom))


def build() -> dict[str, str]:
    half_w = HALF_W_24 * SCALE

    half_h = HALF_W_24 * REF["half_h"] * SCALE

    eye = lens(half_w, half_h, ROUND_BY_24 * SCALE)

    pupil = Point(CENTRE).buffer(HALF_W_24 * REF["pupil_r"] * SCALE, quad_segs=96)

    if not pupil.within(eye.buffer(-0.5 * SCALE)):
        raise SystemExit("REFUSED: the pupil touches the rim of the eye")

    strike = slash(
        HALF_W_24 * REF["slash_w"] * SCALE,
        HALF_W_24 * REF["slash_len"] * SCALE,
        SLASH_DEG,
    )

    halo = strike.buffer(HALF_W_24 * REF["gap"] * SCALE, quad_segs=48)

    visible = eye.difference(pupil)

    hidden = unary_union([eye.difference(halo).difference(pupil), strike])

    for name, geom in (("visible", visible), ("hidden", hidden)):
        reach = _radius([p for c in rings_of(geom) for p in c])

        if reach > GEAR_VALLEY - 1.0:
            raise SystemExit(
                f"REFUSED: the {name} glyph reaches {reach:.2f}, "
                f"inside a gear whose valleys are at {GEAR_VALLEY:.2f}",
            )

    return {"visible": paths_of(visible), "hidden": paths_of(hidden)}


def svg(glyph: str) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 108 108" '
        'width="108" height="108">'
        '<rect width="108" height="108" rx="24" fill="#0F1A12"/>'
        f'<path fill="{GEAR_COLOUR}" d="{GEAR}"/>'
        f'<path fill="{KEY_COLOUR}" fill-rule="evenodd" d="{glyph}"/>'
        "</svg>"
    )


LICENCE = """<!--
  ~
  ~   Copyright 2026 soul_99 (suIMD)
  ~
  ~   Licensed under the GNU General Public License v3.0 (the "License");
  ~   you may not use this file except in compliance with the License.
  ~   You may obtain a copy of the License at
  ~
  ~       https://www.gnu.org/licenses/gpl-3.0
  ~
  ~   GENERATED by design/build_hide_launcher_icons.py. Do not edit by hand; re-run it.
  ~
  ~   The "Hide/unhide Settings" app-drawer entry, in the state named by the file. The gear is
  ~   ic_launcher_foreground's own path and the eye is the Quick Settings tile's, sized off the
  ~   key it replaces - see the script header.
  -->"""

DENSITIES = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}

RES = REPO / "app/src/main/res"


def foreground_xml(glyph: str) -> str:
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        f"{LICENCE}\n"
        '<vector xmlns:android="http://schemas.android.com/apk/res/android"\n'
        '    android:width="108dp"\n    android:height="108dp"\n'
        '    android:viewportWidth="108"\n    android:viewportHeight="108">\n'
        f'    <path\n        android:fillColor="{GEAR_COLOUR}"\n'
        f'        android:pathData="{GEAR}" />\n'
        f'    <path\n        android:fillColor="{KEY_COLOUR}"\n'
        '        android:fillType="evenOdd"\n'
        f'        android:pathData="{glyph}" />\n'
        "</vector>\n"
    )


def monochrome_xml(glyph: str) -> str:
    """Gear and glyph as one even-odd path, so the eye is a hole rather than a second colour.

    A themed icon is drawn in one colour by the launcher; the same construction the tile and
    ic_services_monochrome already use.
    """
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        f"{LICENCE}\n"
        '<vector xmlns:android="http://schemas.android.com/apk/res/android"\n'
        '    android:width="108dp"\n    android:height="108dp"\n'
        '    android:viewportWidth="108"\n    android:viewportHeight="108">\n'
        '    <path\n        android:fillColor="@android:color/white"\n'
        '        android:fillType="evenOdd"\n'
        f'        android:pathData="{GEAR} {glyph}" />\n'
        "</vector>\n"
    )


def adaptive_xml(name: str) -> str:
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        f"{LICENCE}\n"
        '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
        '    <background android:drawable="@color/ic_launcher_background" />\n'
        f'    <foreground android:drawable="@drawable/{name}_foreground" />\n'
        f'    <monochrome android:drawable="@drawable/{name}_monochrome" />\n'
        "</adaptive-icon>\n"
    )


def legacy_svg(glyph: str) -> str:
    """The pre-26 mipmap: the foreground alone on transparency, exactly as ic_services.png is."""
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 108 108" '
        'width="108" height="108">'
        f'<path fill="{GEAR_COLOUR}" d="{GEAR}"/>'
        f'<path fill="{KEY_COLOUR}" fill-rule="evenodd" d="{glyph}"/>'
        "</svg>"
    )


def emit(glyphs: dict[str, str]) -> None:
    import cairosvg

    for state, glyph in glyphs.items():
        name = f"ic_hide_{state}"

        (RES / "drawable" / f"{name}_foreground.xml").write_text(foreground_xml(glyph))

        (RES / "drawable" / f"{name}_monochrome.xml").write_text(monochrome_xml(glyph))

        (RES / "mipmap-anydpi-v26" / f"{name}.xml").write_text(adaptive_xml(name))

        for density, size in DENSITIES.items():
            out = RES / f"mipmap-{density}" / f"{name}.png"

            out.parent.mkdir(parents=True, exist_ok=True)

            cairosvg.svg2png(
                bytestring=legacy_svg(glyph).encode(),
                write_to=str(out),
                output_width=size,
                output_height=size,
            )

        print(f"  ok  {name}: 2 drawables, 1 adaptive icon, {len(DENSITIES)} mipmaps")


def main() -> int:
    glyphs = build()

    for name, glyph in glyphs.items():
        (OUT / f"hide_launcher_{name}.svg").write_text(svg(glyph))

        (OUT / f"hide_launcher_{name}_path.txt").write_text(glyph)

    print(f"  key reach {KEY_REACH:.2f}, gear valley {GEAR_VALLEY:.2f}, scale {SCALE:.4f}")

    if "--emit" in sys.argv:
        emit(glyphs)
    else:
        print("  (previews only; pass --emit to write into app/src/main/res)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
