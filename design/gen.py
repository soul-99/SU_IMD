"""Builds the app icon's vector geometry from measurements of the supplied PNG.

Two different problems, solved two different ways.

The **key** is constructed: it is made of rounded rectangles, and saying so exactly is
better than approximating it. Its bow and the hole in it are rounded rectangles with
fully-rounded ends, not ellipses — the source's bow has a dead-straight right edge for
fifty-odd rows, which no ellipse does. That model fits the traced outline to 0.16px rms;
the best superellipse manages only 0.85px.

The **gear** is measured. It is drawn art, not a textbook gear, and every attempt to model
it (tangent lobe circles, superellipse, cos(6t) lobes) was visibly wrong in the tooth
flanks. `trace.py` samples the real outline, averages the six rotational copies, mirrors
about the tooth axis, and fits one 60-degree sector with cubic Beziers, which this file
rotates six times. See geometry.py for the fitted control points.

Run `verify.py` to re-render all of it in the source PNG's own coordinates and diff.
"""
import math

import geometry

# --- gear placement ---------------------------------------------------------------
SRC_CX, SRC_CY = geometry.GEAR_CENTRE

# The adaptive-icon canvas is 108x108. This is sized against upstream Geto rather than
# against the safe zone, so the two sit together on a home screen: Geto's gear measures
# 36.20 units across the same viewport (mean of its 35.30 x 37.10 bounding box), and this
# one is set 10% above that. A crest radius of 20.7 gives a 39.4-unit mean extent.
VIEW = 108.0
R_OUT = 20.7
S = R_OUT / geometry.GEAR_CREST
CX = CY = VIEW / 2

def tx(x): return CX + (x - SRC_CX) * S
def ty(y): return CY + (y - SRC_CY) * S
def sc(v): return v * S
def f(v): return f"{v:.3f}".rstrip("0").rstrip(".")

def gear_path(sides=6):
    """The fitted sector, rotated into place `sides` times."""
    out = []
    for k in range(sides):
        a = 2 * math.pi * k / sides
        ca, sa = math.cos(a), math.sin(a)

        def place(p):
            dx, dy = p[0] - SRC_CX, p[1] - SRC_CY
            return tx(SRC_CX + dx * ca - dy * sa), ty(SRC_CY + dx * sa + dy * ca)

        for i, seg in enumerate(geometry.GEAR_SECTOR):
            p0, p1, p2, p3 = (place(p) for p in seg)
            if k == 0 and i == 0:
                out.append(f"M{f(p0[0])},{f(p0[1])}")
            out.append(f"C{f(p1[0])},{f(p1[1])} {f(p2[0])},{f(p2[1])} {f(p3[0])},{f(p3[1])}")
    out.append("Z")
    return "".join(out)

# --- key --------------------------------------------------------------------------

K = 0.5522847498  # circle-to-cubic constant

def round_rect(x0, y0, x1, y1, r):
    """Axis-aligned rounded rectangle. r == half the short side gives a capsule."""
    r = min(r, (x1 - x0) / 2, (y1 - y0) / 2)
    o = r * K
    return (f"M{f(x0 + r)},{f(y0)}L{f(x1 - r)},{f(y0)}"
            f"C{f(x1 - r + o)},{f(y0)} {f(x1)},{f(y0 + r - o)} {f(x1)},{f(y0 + r)}"
            f"L{f(x1)},{f(y1 - r)}"
            f"C{f(x1)},{f(y1 - r + o)} {f(x1 - r + o)},{f(y1)} {f(x1 - r)},{f(y1)}"
            f"L{f(x0 + r)},{f(y1)}"
            f"C{f(x0 + r - o)},{f(y1)} {f(x0)},{f(y1 - r + o)} {f(x0)},{f(y1 - r)}"
            f"L{f(x0)},{f(y0 + r)}"
            f"C{f(x0)},{f(y0 + r - o)} {f(x0 + r - o)},{f(y0)} {f(x0 + r)},{f(y0)}Z")

def fillet(cx, cy, r, u, v):
    """The wedge that softens a re-entrant corner at (cx, cy).

    `u` and `v` are unit vectors along the two edges meeting there, pointing away from
    the corner. The wedge is filled in the same colour and unioned by the non-zero
    winding rule, which is cheaper than expressing the union as a single outline.
    """
    fx, fy = cx + r * (u[0] + v[0]), cy + r * (u[1] + v[1])
    t1 = (cx + r * u[0], cy + r * u[1])
    t2 = (cx + r * v[0], cy + r * v[1])
    a1 = math.atan2(t1[1] - fy, t1[0] - fx)
    a2 = math.atan2(t2[1] - fy, t2[0] - fx)
    sweep = 1 if (a2 - a1) % (2 * math.pi) <= math.pi else 0
    return (f"M{f(cx)},{f(cy)}L{f(t1[0])},{f(t1[1])}"
            f"A{f(r)},{f(r)} 0 0 {sweep} {f(t2[0])},{f(t2[1])}Z")

# Sub-pixel measurements of the source PNG, in its own 1024-unit coordinates.
SHAFT_TOP, SHAFT_BOT, SHAFT_LEFT = 474.80, 505.38, 347.32
BOW_CX, BOW_CY, BOW_HW, BOW_HH = 620.95, 490.26, 55.09, 80.80
HOLE_CX, HOLE_CY, HOLE_HW, HOLE_HH = 620.75, 490.25, 24.78, 50.72
TEETH = [(377.45, 407.92, 554.08), (439.40, 470.24, 541.20)]
TOOTH_FILLET, BOW_FILLET = 16.4, 15.3

LEFT, RIGHT, UP, DOWN = (-1.0, 0.0), (1.0, 0.0), (0.0, -1.0), (0.0, 1.0)

def key_body():
    parts = [
        # Run the shaft to the bow's centre so the two overlap rather than abut.
        round_rect(tx(SHAFT_LEFT), ty(SHAFT_TOP), tx(BOW_CX), ty(SHAFT_BOT),
                   sc((SHAFT_BOT - SHAFT_TOP) / 2)),
        round_rect(tx(BOW_CX - BOW_HW), ty(BOW_CY - BOW_HH),
                   tx(BOW_CX + BOW_HW), ty(BOW_CY + BOW_HH), sc(BOW_HW)),
    ]
    for x0, x1, bottom in TEETH:
        # Started at the shaft's mid-line: the top of each tooth is buried in the shaft,
        # so its own corner rounding never shows.
        parts.append(round_rect(tx(x0), ty((SHAFT_TOP + SHAFT_BOT) / 2),
                                tx(x1), ty(bottom), sc((x1 - x0) / 2)))
        parts.append(fillet(tx(x0), ty(SHAFT_BOT), sc(TOOTH_FILLET), LEFT, DOWN))
        parts.append(fillet(tx(x1), ty(SHAFT_BOT), sc(TOOTH_FILLET), RIGHT, DOWN))

    bow_left = BOW_CX - BOW_HW
    parts.append(fillet(tx(bow_left), ty(SHAFT_TOP), sc(BOW_FILLET), LEFT, UP))
    parts.append(fillet(tx(bow_left), ty(SHAFT_BOT), sc(BOW_FILLET), LEFT, DOWN))
    return "".join(parts)

def key_hole():
    return round_rect(tx(HOLE_CX - HOLE_HW), ty(HOLE_CY - HOLE_HH),
                      tx(HOLE_CX + HOLE_HW), ty(HOLE_CY + HOLE_HH), sc(HOLE_HW))

GEAR_COLOUR, KEY_COLOUR = "#A5DBB9", "#13A75B"

HEADER = """<?xml version="1.0" encoding="utf-8"?><!--
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
"""

def vector(body):
    return (HEADER +
            '<vector xmlns:android="http://schemas.android.com/apk/res/android"\n'
            '    android:width="108dp"\n    android:height="108dp"\n'
            '    android:viewportWidth="108"\n    android:viewportHeight="108">\n' +
            body + '</vector>\n')

if __name__ == "__main__":
    gear, body, hole = gear_path(), key_body(), key_hole()

    foreground = (
        f'    <path\n        android:fillColor="{GEAR_COLOUR}"\n        android:pathData="{gear}" />\n'
        f'    <path\n        android:fillColor="{KEY_COLOUR}"\n        android:pathData="{body}" />\n'
        # Painted in the gear colour rather than cut out with even-odd: the shaft overlaps
        # the bow, and an even-odd knockout across the whole key would punch through that
        # overlap as well as the intended hole.
        f'    <path\n        android:fillColor="{GEAR_COLOUR}"\n        android:pathData="{hole}" />\n')

    # Themed icons are a single tinted silhouette, so the gear alone is used. Knocking the
    # key out with even-odd would also knock out every place the key self-overlaps.
    monochrome = f'    <path\n        android:fillColor="#FFFFFF"\n        android:pathData="{gear}" />\n'

    open("ic_launcher_foreground.xml", "w").write(vector(foreground))
    open("ic_launcher_monochrome.xml", "w").write(vector(monochrome))
    open("ic_launcher.svg", "w").write(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 108 108" width="512" height="512">\n'
        f'  <title>SU IMD (Geto+)</title>\n'
        f'  <rect width="108" height="108" fill="#FFFFFF"/>\n'
        f'  <path fill="{GEAR_COLOUR}" d="{gear}"/>\n'
        f'  <path fill="{KEY_COLOUR}" d="{body}"/>\n'
        f'  <path fill="{GEAR_COLOUR}" d="{hole}"/>\n</svg>\n')
    print("gear:", len(gear), "chars | key:", len(body), "| hole:", len(hole))
