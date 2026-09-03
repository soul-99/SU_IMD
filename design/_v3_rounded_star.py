#!/usr/bin/env python3
"""
v3-r10 — the rounded star, and it replaces Material's everywhere.

The author asked for the Favourites tab's star to be *"less pointy"*, *"curvy"* and — on the empty
tab — *"solid"*, then picked **S1b** off a ladder: the midpoint between the two steps he had named.
Two knobs move together to make a star less pointy and they are not the same thing:

  * how deep the notches cut  — 0.470 of the outer radius here, against Material's ~0.38. Fatter
    arms, so the shape reads as round before any corner is touched.
  * how big the arc is that replaces each corner — 1.50 at the five tips, 1.15 at the five notches,
    in viewport units on a 24 grid. Rounder tips, and the notches rounded rather less so the star
    keeps five distinct arms instead of turning into a flower.

⚠ **Every star in the app, at his instruction — *"everywhere"*.** The tab, the empty-tab backdrop
and the ★/☆ favourite toggles on app rows all take this shape. That is the whole reason the hollow
one is generated here too: half a change would leave a rounded star in the tab bar and a pointy one
on every row underneath it, which is worse than either shape on its own.

⚠ **Both are one geometry, not two drawings.** The hollow star is the same path stroked instead of
filled, so the two cannot drift: a tick and an untick are the same outline with and without ink.
The stroke is 1.6 units wide and the path is inset to R=10.2 so the outer edge lands at 0.98 rather
than off the 24-unit grid — a star that touched the viewport edge would be clipped by any caller
that draws it without padding, and `Icon` is exactly such a caller.

⚠ **Generated, and only here.** The arithmetic below is the definition; `GetoStars.kt` is output.
Re-run this script rather than editing it.

Every edit asserts its anchor matches exactly once. Nothing is written if any file fails.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

OUT = "design-system/src/main/kotlin/com/android/geto/designsystem/icon/GetoStars.kt"

ICONS = "design-system/src/main/kotlin/com/android/geto/designsystem/icon/GetoIcons.kt"

# --- the geometry -------------------------------------------------------------------------

CENTRE = 12.0

# S1b, the author's pick: the midpoint of S1 (0.44 / 1.10 / 0.90) and S2 (0.50 / 1.90 / 1.40).
NOTCH_RATIO = 0.470

TIP_ROUNDING = 1.50

NOTCH_ROUNDING = 1.15

# The filled star fills the grid; the hollow one is pulled in by half its stroke plus a hair.
FILLED_RADIUS = 11.0

HOLLOW_RADIUS = 10.2

STROKE_WIDTH = 1.6


def rounded_star(radius: float) -> str:
    """A five-point star with every corner replaced by a circular arc, as SVG path data.

    The rounding radii are given in grid units rather than as a fraction, so the hollow star -
    drawn on a slightly smaller radius - keeps corners the same absolute size as the filled one.
    Scaling them with the radius would give the two stars visibly different tips.
    """
    points = []

    for k in range(10):
        angle = math.radians(-90 + k * 36)

        r = radius if k % 2 == 0 else radius * NOTCH_RATIO

        points.append((CENTRE + r * math.cos(angle), CENTRE + r * math.sin(angle)))

    out = []

    n = len(points)

    for i, v in enumerate(points):
        p = points[(i - 1) % n]

        q = points[(i + 1) % n]

        def unit(a: tuple[float, float]) -> tuple[float, float, float]:
            dx, dy = a[0] - v[0], a[1] - v[1]

            length = math.hypot(dx, dy)

            return dx / length, dy / length, length

        u1x, u1y, l1 = unit(p)

        u2x, u2y, l2 = unit(q)

        cosine = max(-1.0, min(1.0, u1x * u2x + u1y * u2y))

        half = math.acos(cosine) / 2

        rho = TIP_ROUNDING if i % 2 == 0 else NOTCH_ROUNDING

        # How far back along both edges the arc starts, clamped so two adjacent arcs can never
        # overlap - at which point the path would fold back on itself and fill inside out.
        distance = min(rho / math.tan(half), l1 / 2, l2 / 2)

        rho = distance * math.tan(half)

        t1 = (v[0] + u1x * distance, v[1] + u1y * distance)

        t2 = (v[0] + u2x * distance, v[1] + u2y * distance)

        # Which way the arc bends. A tip turns one way and a notch the other, and the sign of the
        # cross product says which without either being special-cased.
        cross = (v[0] - p[0]) * (q[1] - v[1]) - (v[1] - p[1]) * (q[0] - v[0])

        sweep = 1 if cross > 0 else 0

        out.append(("M" if i == 0 else "L") + f"{t1[0]:.3f},{t1[1]:.3f}")

        out.append(f"A{rho:.3f},{rho:.3f} 0 0 {sweep} {t2[0]:.3f},{t2[1]:.3f}")

    out.append("Z")

    return " ".join(out)


FILLED = rounded_star(FILLED_RADIUS)

HOLLOW = rounded_star(HOLLOW_RADIUS)

# --- the file -----------------------------------------------------------------------------

TEMPLATE = '''/*
 *
 *   Copyright 2026 soul_99 (suIMD)
 *
 *   Licensed under the GNU General Public License v3.0 (the "License");
 *   you may not use this file except in compliance with the License.
 *   You may obtain a copy of the License at
 *
 *       https://www.gnu.org/licenses/gpl-3.0
 *
 *   GENERATED by design/_v3_rounded_star.py. Do not edit by hand; change the geometry there
 *   and re-run it. The header on that script is where the two knobs are explained.
 *
 */
package com.android.geto.designsystem.icon

import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.StrokeJoin
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.graphics.vector.PathParser
import androidx.compose.ui.unit.dp

/**
 * The app's star, rounded — the author's S1b.
 *
 * ⚠ **One geometry, drawn twice.** [GetoStarFilled] fills the path and [GetoStarHollow] strokes
 * a slightly smaller copy of it, so a favourite and a not-favourite are the same outline with and
 * without ink. Material's own Star/StarBorder pair is what these replace, and replacing both is
 * the point: a rounded star in the tab bar over pointy ones on every row reads as a mistake.
 *
 * ⚠ **Black, and that is not a colour decision.** `Icon` tints whatever it is handed, so the
 * colour here is only what the tint replaces. The same convention every Material icon uses.
 */
val GetoStarFilled: ImageVector by lazy {{
    ImageVector.Builder(
        name = "GetoStarFilled",
        defaultWidth = 24.dp,
        defaultHeight = 24.dp,
        viewportWidth = 24f,
        viewportHeight = 24f,
    ).addPath(
        pathData = PathParser().parsePathString(FILLED_STAR_PATH).toNodes(),
        fill = SolidColor(Color.Black),
    ).build()
}}

/**
 * The same star, hollow.
 *
 * Drawn on a smaller radius than the filled one so that half the stroke still lands inside the
 * 24-unit grid: an outline on the filled radius would have its outer edge clipped by any caller
 * that does not pad the icon, and `Icon` does not.
 */
val GetoStarHollow: ImageVector by lazy {{
    ImageVector.Builder(
        name = "GetoStarHollow",
        defaultWidth = 24.dp,
        defaultHeight = 24.dp,
        viewportWidth = 24f,
        viewportHeight = 24f,
    ).addPath(
        pathData = PathParser().parsePathString(HOLLOW_STAR_PATH).toNodes(),
        stroke = SolidColor(Color.Black),
        strokeLineWidth = {stroke}f,
        strokeLineCap = StrokeCap.Round,
        strokeLineJoin = StrokeJoin.Round,
    ).build()
}}

private const val FILLED_STAR_PATH =
    "{filled}"

private const val HOLLOW_STAR_PATH =
    "{hollow}"
'''

# --- GetoIcons ----------------------------------------------------------------------------

IMPORT_OLD = """import androidx.compose.material.icons.filled.Star
import androidx.compose.material.icons.filled.StarBorder
"""

IMPORT_NEW = ""

STAR_OLD = """    // suIMD additions
    val Star = Icons.Default.Star
    val StarBorder = Icons.Default.StarBorder
"""

STAR_NEW = """    // suIMD additions

    /**
     * The app's star, rounded — r10, and it is deliberately not Material's.
     *
     * The author asked for a star that is *"less pointy"* and *"curvy"*, and asked for it
     * *"everywhere"* rather than in the Favourites tab alone. Both members of the pair moved
     * together for that reason: the tab, the empty tab's backdrop and the ★/☆ on every app row
     * are one shape now. See design/_v3_rounded_star.py for the geometry.
     */
    val Star = GetoStarFilled
    val StarBorder = GetoStarHollow
"""


def main() -> int:
    written: dict[Path, str] = {}

    # 1. the generated file ---------------------------------------------------------------
    out = ROOT / OUT

    body = TEMPLATE.format(filled=FILLED, hollow=HOLLOW, stroke=STROKE_WIDTH)

    for token, want, why in (
        ("val GetoStarFilled", 1, "the filled star is declared once"),
        ("val GetoStarHollow", 1, "and the hollow one once"),
        ("PathParser()", 2, "each parses its own path"),
        ("A", None, ""),
    ):
        if want is None:
            continue

        got = body.count(token)

        if got != want:
            print(f"REFUSED: {why} — {token!r} x{got}, expected {want}")
            return 1

    # Ten corners, ten arcs, in both stars. A path that lost one would still parse and would
    # still look like a star, which is exactly why this is asserted rather than eyeballed.
    for name, data in (("filled", FILLED), ("hollow", HOLLOW)):
        arcs = data.count("A")

        if arcs != 10:
            print(f"REFUSED: the {name} star has {arcs} arcs, expected 10")
            return 1

        if not data.endswith("Z"):
            print(f"REFUSED: the {name} star does not close")
            return 1

    written[out] = body

    # 2. GetoIcons ------------------------------------------------------------------------
    icons = ROOT / ICONS

    if not icons.is_file():
        print(f"REFUSED: missing {ICONS}")
        return 1

    original = icons.read_text(encoding="utf-8")

    text = original

    for old, new in ((IMPORT_OLD, IMPORT_NEW), (STAR_OLD, STAR_NEW)):
        found = text.count(old)

        if found != 1:
            print(
                f"REFUSED: GetoIcons.kt anchor {old.strip().splitlines()[0][:60]!r}\n"
                f"  matched {found} time(s), expected exactly 1",
            )
            return 1

        text = text.replace(old, new, 1)

    for token, want, why in (
        ("Icons.Default.Star", 0, "no Material star survives"),
        ("Icons.Default.StarBorder", 0, "nor the outline"),
        ("val Star = GetoStarFilled", 1, "Star points at the generated one"),
        ("val StarBorder = GetoStarHollow", 1, "and StarBorder at its hollow twin"),
        ("import androidx.compose.material.icons.filled.Star", 0, "the imports are gone with it"),
    ):
        got = text.count(token)

        if got != want:
            print(f"REFUSED: {why} — {token!r} x{got}, expected {want}")
            return 1

    written[icons] = text

    # ⚠ Long lines are the one thing a generated path can produce by accident: the two path
    # constants are one string each and would run to ~700 characters if written inline.
    def over(source: str) -> set[str]:
        return {
            line
            for line in source.split("\n")
            if len(line) > 120
            and not line.lstrip().startswith("import ")
            and not line.lstrip().startswith('"M')
        }

    if over(text) - over(original):
        print("REFUSED: GetoIcons.kt would gain lines over 120 chars")
        return 1

    out.parent.mkdir(parents=True, exist_ok=True)

    for path, content in written.items():
        path.write_text(content, encoding="utf-8")

    print(f"  ok  {OUT}")
    print(f"  ok  {ICONS}  Star and StarBorder rewired")
    print(f"      filled {len(FILLED)} chars, hollow {len(HOLLOW)} chars, 10 arcs each")

    return 0


if __name__ == "__main__":
    sys.exit(main())
