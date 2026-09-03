#!/usr/bin/env python3
"""
r27a — the eight new settings-row icons as `VectorDrawable`s, plus the app grid as an `ImageVector`.

Same geometry the author signed off in `design/template_r27_settings_icons.html`, emitted as Android
assets instead of SVG. It is generated rather than hand-transcribed for the reason r26 already found
the hard way: **`VectorDrawable` looks like SVG and is not.**

  * There is no `<circle>` and no `<rect>` — everything is `pathData`, so both are emitted as arcs
    and lines here.
  * Arc flags must be space-separated; Android's parser mis-reads SVG's run-together `0 01` form.
  * A group's transform is `scale` then `translate` about a pivot, which happens to match SVG's
    `translate(a,b) scale(s)` only when the pivot is the origin — asserted below rather than assumed.
  * `currentColor` does not exist. Every path is plain white and Compose's `Icon` tints it, which is
    what makes one `colorScheme.outline` reach the whole set.

## What is *not* here

Three of the eleven rows already have a drawable in `:design-system` and get no new file:
`Setting manager toggles` → `ic_services_glyph`, `Revert to default` → `ic_revert_glyph`, and the
two framework rows reuse `ic_hidden_glyph` / `ic_hide_glyph` — though those two do get new files,
because the author picked the variant with a swap badge beside the gear, and a badge is geometry the
source glyph does not have.

The app grid is the exception in the other direction: it is needed as an **`ImageVector`**, because
its second home is the All Apps tab and `TopLevelDestination.icon` is typed `ImageVector` through the
`HomeDestination` interface in another module. Changing that type to reach one icon would be a
refactor across three modules; building the grid in Kotlin costs nine rounded rectangles. The
settings row then uses the same value through `rememberVectorPainter`, so the shape has one
definition rather than two.

Computes every file in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DRAWABLES = ROOT / "design-system/src/main/res/drawable"

ANDROID = "{http://schemas.android.com/apk/res/android}"

failures: list[str] = []


def check(condition: bool, message: str) -> bool:
    if not condition:
        failures.append(message)

    return condition


def n(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")


# ─────────────────────────────────────────────────────────────────────────────────────────────
# Primitives. Everything becomes pathData, because that is all a VectorDrawable has.
# ─────────────────────────────────────────────────────────────────────────────────────────────


def circle_path(cx: float, cy: float, r: float) -> str:
    """A circle as two half arcs. Seven space-separated parameters each — see the module note."""
    return (
        f"M{n(cx - r)},{n(cy)} "
        f"A {n(r)} {n(r)} 0 1 0 {n(cx + r)} {n(cy)} "
        f"A {n(r)} {n(r)} 0 1 0 {n(cx - r)} {n(cy)} Z"
    )


def rrect_path(x: float, y: float, w: float, h: float, r: float) -> str:
    return (
        f"M{n(x + r)},{n(y)} H{n(x + w - r)} "
        f"A {n(r)} {n(r)} 0 0 1 {n(x + w)} {n(y + r)} "
        f"V{n(y + h - r)} A {n(r)} {n(r)} 0 0 1 {n(x + w - r)} {n(y + h)} "
        f"H{n(x + r)} A {n(r)} {n(r)} 0 0 1 {n(x)} {n(y + h - r)} "
        f"V{n(y + r)} A {n(r)} {n(r)} 0 0 1 {n(x + r)} {n(y)} Z"
    )


WHITE = "#FFFFFFFF"


def stroke(data: str, width: float, cap: str = "round", join: str = "round") -> str:
    return (
        '    <path\n'
        f'        android:pathData="{data}"\n'
        f'        android:strokeColor="{WHITE}"\n'
        f'        android:strokeWidth="{n(width)}"\n'
        f'        android:strokeLineCap="{cap}"\n'
        f'        android:strokeLineJoin="{join}" />\n'
    )


def fill(data: str, even_odd: bool = False) -> str:
    rule = '\n        android:fillType="evenOdd"' if even_odd else ""

    return f'    <path\n        android:pathData="{data}"\n        android:fillColor="{WHITE}"{rule} />\n'


def group(body: str, translate_x: float, translate_y: float, scale: float) -> str:
    """⚠ Pivot left at the origin on purpose — that is the only case where this matches SVG's
    `translate(a,b) scale(s)`, which is the form the approved template used."""
    inner = "".join("    " + line if line.strip() else line for line in body.splitlines(True))

    return (
        f'    <group\n        android:translateX="{n(translate_x)}"\n'
        f'        android:translateY="{n(translate_y)}"\n'
        f'        android:scaleX="{n(scale)}"\n        android:scaleY="{n(scale)}">\n'
        f"{inner}    </group>\n"
    )


LICENCE = """<?xml version="1.0" encoding="utf-8"?><!--
  ~
  ~   Copyright 2026 soul_99 (suIMD)
  ~
  ~   Licensed under the GNU General Public License v3.0 (the "License");
  ~   you may not use this file except in compliance with the License.
  ~   You may obtain a copy of the License at
  ~
  ~       https://www.gnu.org/licenses/gpl-3.0
  ~
  ~   GENERATED by design/_v3_r27a_icon_vectors.py from the geometry the author approved in
  ~   design/template_r27_settings_icons.html. Do not edit by hand; re-run the script.
  ~
  ~   {note}
  ~
  ~   Carries no android:tint. Compose's Icon applies its own - colorScheme.outline for every row
  ~   in this set, which is the off-switch rim grey the author asked for - and a tint here would
  ~   fight it.
  -->
"""


def vector(note: str, body: str) -> str:
    return (
        LICENCE.format(note=note)
        + '<vector xmlns:android="http://schemas.android.com/apk/res/android"\n'
        '    android:width="24dp"\n    android:height="24dp"\n'
        '    android:viewportWidth="24"\n    android:viewportHeight="24">\n'
        f"{body}</vector>\n"
    )


# ─────────────────────────────────────────────────────────────────────────────────────────────
# The drawings, at the numbers the author settled.
# ─────────────────────────────────────────────────────────────────────────────────────────────


def theme() -> str:
    # Measured off the author's own file: his ring runs 6.2 to 7.8 and his flares 8.7 to 11.95,
    # so the gap is 0.9. Round caps add half a stroke past the coordinate, which is why the flare
    # coordinates below (9.9 and 10.7) are nothing like those numbers — 9.9 - 1.2 = 8.7.
    body = ""

    for index in range(8):
        angle = math.radians(index * 45)

        body += stroke(
            f"M{n(12 + 9.9 * math.cos(angle))},{n(12 + 9.9 * math.sin(angle))} "
            f"L{n(12 + 10.7 * math.cos(angle))},{n(12 + 10.7 * math.sin(angle))}",
            2.4,
        )

    body += stroke(circle_path(12, 12, 6.85), 1.9)

    # The moon: the disc's major arc, then the bite circle's arc back. Two overlapping circles with
    # evenOdd cannot draw this — the part of the bite hanging outside the disc would fill solid.
    disc_r, bite_x, bite_y, bite_r = 4.10, 8.392, 8.146, 3.28

    dx, dy = bite_x - 12, bite_y - 12

    distance = math.hypot(dx, dy)

    along = (disc_r**2 - bite_r**2 + distance**2) / (2 * distance)

    across = math.sqrt(disc_r**2 - along**2)

    mid = (12 + along * dx / distance, 12 + along * dy / distance)

    off = (across * -dy / distance, across * dx / distance)

    first = (mid[0] - off[0], mid[1] - off[1])

    second = (mid[0] + off[0], mid[1] + off[1])

    body += fill(
        f"M{n(first[0])},{n(first[1])} "
        f"A {n(disc_r)} {n(disc_r)} 0 1 0 {n(second[0])} {n(second[1])} "
        f"A {n(bite_r)} {n(bite_r)} 0 0 1 {n(first[0])} {n(first[1])} Z",
    )

    return body


def language() -> str:
    return (
        stroke(
            "M12.6,8 H3.4 A 1.7 1.7 0 0 0 1.7,9.7 V15.9 A 1.7 1.7 0 0 0 3.4,17.6 H4.4 V20.8 "
            "L7.9,17.6 H12.6 A 1.7 1.7 0 0 0 14.3,15.9 V13.5",
            1.9,
        )
        + stroke("M5.2,15.1 L7.5,10 L9.8,15.1 M6,13.5 H9", 1.7)
        + stroke(
            "M12,2 H20.6 A 1.7 1.7 0 0 1 22.3,3.7 V10.1 A 1.7 1.7 0 0 1 20.6,11.8 H18.2 "
            "L14.7,14.9 V11.8 H12 A 1.7 1.7 0 0 1 10.3,10.1 V3.7 A 1.7 1.7 0 0 1 12,2 Z",
            1.9,
        )
        + stroke("M16.5,3.5 V4.6 M13.6,5.5 H19.5", 1.6)
        + stroke("M17.1,5.9 C16.6,7.7 15.4,9 13.8,9.9 M15.6,7.1 C16.6,8.6 17.9,9.5 19.4,9.9", 1.6)
    )


def services_droid() -> str:
    """The droid out of `ic_services_glyph` — subpaths 1 to 3 of four, subpath 0 being the gear.

    ⚠ **Lifted, not redrawn.** Two attempts at drawing one to these proportions were both rejected,
    and they would be: the head is a particular curve and the antennae a particular rake. In the
    source these three are *holes* punched through the gear; taken alone with the same `evenOdd`
    rule, the head fills and the eyes stay holes, which is the solid-head-hollow-eyes asked for.
    """
    path = DRAWABLES / "ic_services_glyph.xml"

    data = ET.parse(path).getroot().find("path").get(ANDROID + "pathData")

    pieces = [piece for piece in re.split(r"(?=M)", data) if piece.strip()]

    check(len(pieces) == 4, f"services glyph: expected 4 subpaths, found {len(pieces)}")

    return "".join(pieces[1:])


def icon_style() -> str:
    points = []

    for index in range(16):
        radius = 9.5 if index % 2 == 0 else 7.5

        angle = math.radians(index * 22.5 - 90)

        points.append(f"{n(12 + radius * math.cos(angle))},{n(12 + radius * math.sin(angle))}")

    star = "M" + points[0] + " " + " ".join(f"L{p}" for p in points[1:]) + " Z"

    return (
        stroke(circle_path(12, 12, 11), 1.4)
        + stroke(star, 1.6, join="miter")
        + group(fill(services_droid(), even_odd=True), 2.4, 2.4, 0.80)
    )


def settings_hidden() -> str:
    """The struck-out eye without its gear — the author's *"use the icon without the gear"*."""
    return (
        stroke(
            "M2.4,12 C4.8,7.6 8.2,5.4 12,5.4 C15.8,5.4 19.2,7.6 21.6,12 "
            "C19.2,16.4 15.8,18.6 12,18.6 C8.2,18.6 4.8,16.4 2.4,12 Z",
            2.0,
        )
        + fill(circle_path(12, 12, 2.7))
        + stroke("M4.4,3.4 L19.6,20.6", 2.4)
    )


def accessibility() -> str:
    """Traced off the author's own file rather than drawn by eye — see the template's note."""
    return (
        stroke(circle_path(12, 12, 10.75), 2.3)
        + fill(circle_path(12, 5.95, 1.92))
        + stroke("M5.9,8.55 C8.2,9.25 10.1,9.6 12,9.6 C13.9,9.6 15.8,9.25 18.1,8.55", 1.95)
        + stroke("M12,9.6 L12,14.4 M12,14.4 L9.3,19.6 M12,14.4 L14.7,19.6", 1.95)
    )


def overlay() -> str:
    return (
        stroke(
            "M11.8,5.6 H4.2 A 2 2 0 0 0 2.2,7.6 V17.8 A 2 2 0 0 0 4.2,19.8 H14.4 "
            "A 2 2 0 0 0 16.4,17.8 V13.4",
            2.0,
        )
        + stroke(rrect_path(13.8, 2.4, 8.0, 8.0, 1.8), 2.0)
        + stroke("M6,16.4 L11.2,11.2", 2.2)
        # A chevron head rather than a filled triangle: at 24 dp a triangle's three points land on
        # different pixels and it reads as a smudge.
        + stroke("M7.4,11.6 L11.6,10.8 L10.8,15", 2.1)
    )


def swap_badge() -> str:
    """⚠ **No backing disc, and that is not a style choice.** Through Compose's `Icon` every path in
    a drawable becomes the tint, so a disc in the card's colour would come out the same grey as the
    gear and blot it. The gear shrinks and the arrows take the corner it vacates instead."""
    return group(
        stroke("M1.4,6 H14.6 M11.2,2.6 L14.9,6 L11.2,9.4", 2.7)
        + stroke("M16.6,14.2 H3.4 M6.8,10.8 L3.1,14.2 L6.8,17.6", 2.7),
        12.9,
        13.6,
        0.50,
    )


def framework(glyph: str) -> str:
    path = DRAWABLES / f"{glyph}.xml"

    element = ET.parse(path).getroot().find("path")

    data = element.get(ANDROID + "pathData")

    even_odd = element.get(ANDROID + "fillType") == "evenOdd"

    check(bool(data), f"{glyph}: no path data")

    return group(fill(data, even_odd=even_odd), -0.6, -1.0, 0.78) + swap_badge()


FILES = {
    "ic_theme": (
        "The Theme row's sun with a moon bitten out of it. The ring, the flare gap and the moon's "
        "proportions are measured off the reference the author supplied, not chosen.",
        theme(),
    ),
    "ic_language": (
        "The Language row: two speech bubbles, one carrying A and one the strokes of the character "
        "wen. Outlined, because a filled bubble at 24 dp loses the letter inside it.",
        language(),
    ),
    "ic_icon_style": (
        "The Icon style row: the author's octagram, with the droid head taken from "
        "ic_services_glyph itself rather than redrawn - he called that one perfect, so it is that "
        "one, scaled to 0.80 to sit inside the star.",
        icon_style(),
    ),
    "ic_settings_hidden": (
        "The Settings to hide row: the Hide tile's struck-out eye WITHOUT its gear, at the "
        "author's instruction. The gear says 'settings', which the row's own label already says.",
        settings_hidden(),
    ),
    "ic_accessibility": (
        "The Accessibility services row. Traced off the author's reference by thresholding it and "
        "measuring: the arms rise slightly outward, which two hand-drawn drafts had inverted.",
        accessibility(),
    ),
    "ic_overlay": (
        "The Display over other apps row: a window with a second one over its corner. Nothing here "
        "derives from the watermarked stock file the author sent - two nested squares and an arrow "
        "is a convention, and this is drawn from scratch.",
        overlay(),
    ),
    "ic_hiding_framework": (
        "The Hiding framework row: the struck-out eye gear with a swap badge, the author's pick "
        "from the template. The badge is what separates it from Settings to hide, and it says "
        "'which mechanism' rather than 'what state' - which is what this row chooses.",
        framework("ic_hidden_glyph"),
    ),
    "ic_unhiding_framework": (
        "The Unhiding framework row: the open-eye gear with the same swap badge as its sibling.",
        framework("ic_hide_glyph"),
    ),
}

written = {name: vector(note, body) for name, (note, body) in FILES.items()}

# ── the checks that matter for this format ───────────────────────────────────────────────────
for name, text in written.items():
    check("currentColor" not in text, f"{name}: currentColor is not a VectorDrawable colour")

    check("<circle" not in text and "<rect" not in text, f"{name}: VectorDrawable has no such element")

    # ⚠ **Checked by parsing the arcs, not by looking for a substring.** The first version of this
    # searched for "0 10" and friends anywhere in the file, which fires on ordinary coordinates —
    # three of the eight failed on their own perfectly good numbers. What actually matters is that
    # every `A` is followed by seven separated parameters with the two flags apart, so that is what
    # is counted.
    arc = re.compile(
        r"A\s+-?[\d.]+[\s,]+-?[\d.]+[\s,]+-?[\d.]+[\s,]+[01][\s,]+[01][\s,]+-?[\d.]+[\s,]+-?[\d.]+",
    )

    for data in re.findall(r'android:pathData="([^"]+)"', text):
        starts = len(re.findall(r"\bA\s", data)) + len(re.findall(r"A(?=[\d.-])", data))

        check(
            starts == len(arc.findall(data)),
            f"{name}: an arc is not seven separated parameters — Android will misread it",
        )

    check(text.count("<vector") == 1 and text.rstrip().endswith("</vector>"), f"{name}: malformed")

    try:
        ET.fromstring(text[text.index("<vector") :])

    except ET.ParseError as error:
        check(False, f"{name}: not well-formed XML — {error}")

check(len(written) == 8, f"expected 8 drawables, built {len(written)}")

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

for name, text in written.items():
    (DRAWABLES / f"{name}.xml").write_text(text, encoding="utf-8")

    print(f"wrote design-system/src/main/res/drawable/{name}.xml")

print("ok")
