#!/usr/bin/env python3
"""
r26 (part one) — the Logics card icon, as a single coloured `VectorDrawable`.

The author, settling the two open questions from `design/template_r26_logics_icon.html`:
*"use single vector for the logics icon"* and *"no logics icon stay coloured"*. So: one file, one
set of colours in both themes, and drawn with `Image` rather than `Icon` — an `Icon` would replace
every pixel with a tint, which is exactly what "stay coloured" rules out.

## Why the geometry is generated rather than typed

Two things in the template's SVG do not survive a paste into Android:

  1. ⚠ **`VectorDrawable` has no dashed stroke.** There is no `strokeDasharray`; `trimPathStart` /
     `trimPathEnd` trim one range and cannot repeat. So the dashed circuit boundary is emitted as
     sixteen separate arc segments, computed here from the dash and gap lengths the template used
     (6 on, 7 off at r = 33) rather than eyeballed.
  2. ⚠ **Android's path parser is stricter than a browser's about arc flags.** SVG lets
     `a7 7 0 00-1.7 1` run the two flags and the following coordinate together; Android's parser
     mis-reads that shape. Every arc below is emitted with its seven parameters space-separated.

Both are the same class of problem — a format that looks like SVG and is not — and generating the
numbers is what keeps a hand-typed transcription error out of a file nobody will proofread.

## Colours

Fixed, and chosen to sit on **both** cards, because a single vector has no second chance: the ring
grey, the node teals and green, the bulb amber and the two badge colours all read against
`#FFFFFF` and against `#14160E`. The gear's hole is a real hole — an `evenOdd` fill with the inner
circle as a second subpath — rather than a circle painted in the page colour, which would have been
a light disc on a dark card.

The tick and the cross keep IMD's own meanings: green for hidden, red for restored. Those two are
not decoration and do not change with anything.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DRAWABLE = ROOT / "feature/settings/src/main/res/drawable/ic_logics.xml"

SETTINGS = ROOT / "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"

failures: list[str] = []


def check(condition: bool, message: str) -> bool:
    if not condition:
        failures.append(message)

    return condition


def replace_once(text: str, old: str, new: str, label: str) -> str:
    found = text.count(old)

    if not check(found == 1, f"{label}: found {found}x, expected 1"):
        return text

    return text.replace(old, new, 1)


def n(value: float) -> str:
    """A coordinate, short enough to read and precise enough to draw."""
    return f"{value:.2f}".rstrip("0").rstrip(".")


# ─────────────────────────────────────────────────────────────────────────────────────────────
# Geometry
# ─────────────────────────────────────────────────────────────────────────────────────────────

RING_CX, RING_CY, RING_R = 48.0, 46.0, 33.0

DASH_ON, DASH_OFF = 6.0, 7.0


def dashed_ring() -> str:
    """The circuit boundary, as discrete arcs because a dash array is not available."""
    circumference = 2 * math.pi * RING_R

    period = DASH_ON + DASH_OFF

    # Rounded to a whole number of periods so the last gap is the same as the others rather than
    # whatever is left over — a seam in a ring is the one thing the eye finds immediately.
    count = round(circumference / period)

    step = 2 * math.pi / count

    on = step * DASH_ON / period

    segments = []

    for index in range(count):
        start = index * step - math.pi / 2

        end = start + on

        x1 = RING_CX + RING_R * math.cos(start)

        y1 = RING_CY + RING_R * math.sin(start)

        x2 = RING_CX + RING_R * math.cos(end)

        y2 = RING_CY + RING_R * math.sin(end)

        # Seven space-separated arc parameters: rx ry rotation large-arc sweep x y.
        segments.append(
            f"M{n(x1)},{n(y1)} A {n(RING_R)} {n(RING_R)} 0 0 1 {n(x2)} {n(y2)}",
        )

    return " ".join(segments)


def hexagon(cx: float, cy: float, radius: float) -> str:
    """A flat-topped hex node. Straight lines only — nothing for a parser to disagree about."""
    points = []

    for index in range(6):
        angle = math.pi / 180 * (60 * index - 30)

        points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))

    head = f"M{n(points[0][0])},{n(points[0][1])}"

    tail = " ".join(f"L{n(x)},{n(y)}" for x, y in points[1:])

    return f"{head} {tail} Z"


def circle(cx: float, cy: float, radius: float, clockwise: int = 1) -> str:
    """A circle as two half-arcs. `clockwise` flips the sweep, which is how an evenOdd hole works."""
    return (
        f"M{n(cx - radius)},{n(cy)} "
        f"A {n(radius)} {n(radius)} 0 0 {clockwise} {n(cx + radius)} {n(cy)} "
        f"A {n(radius)} {n(radius)} 0 0 {clockwise} {n(cx - radius)} {n(cy)} Z"
    )


def gear(cx: float, cy: float, outer: float, inner: float, hole: float, teeth: int = 8) -> str:
    """A gear as one polygon plus a hole, filled evenOdd so the hole is genuinely empty."""
    points = []

    step = 2 * math.pi / teeth

    # Each tooth is four points: up the flank, across the tip, down, across the root.
    for index in range(teeth):
        base = index * step

        for offset, radius in (
            (-step * 0.22, inner),
            (-step * 0.13, outer),
            (step * 0.13, outer),
            (step * 0.22, inner),
        ):
            angle = base + offset

            points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))

    head = f"M{n(points[0][0])},{n(points[0][1])}"

    tail = " ".join(f"L{n(x)},{n(y)}" for x, y in points[1:])

    return f"{head} {tail} Z {circle(cx, cy, hole)}"


# ─────────────────────────────────────────────────────────────────────────────────────────────
# The drawable
# ─────────────────────────────────────────────────────────────────────────────────────────────

RING_GREY = "#FF8F9285"

NODE_TEAL_DEEP = "#FF3E9B94"

NODE_TEAL_LIGHT = "#FF7FC8C2"

NODE_GREEN = "#FF6FA22B"

BULB_LIGHT = "#FFFFCF4D"

BULB_SHADE = "#FFE0A800"

FILAMENT = "#FF7A5B00"

BASE_LIGHT = "#FF9AA08D"

BASE_DARK = "#FF75796C"

GEAR_GREY = "#FF9AA08D"

TICK_GREEN = "#FF3EC46D"

CROSS_RED = "#FFE5484D"

BADGE_INK = "#FFFFFFFF"

BULB_GLASS = (
    "M48,24 C39.4,24 32.5,30.9 32.5,39.4 C32.5,45 35.4,48.8 37.9,51.8 "
    "C39.5,53.7 40.5,55 40.8,56.5 L55.2,56.5 C55.5,55 56.5,53.7 58.1,51.8 "
    "C60.6,48.8 63.5,45 63.5,39.4 C63.5,30.9 56.6,24 48,24 Z"
)

BULB_SHADED_SIDE = (
    "M48,24 C47,24 46,24.1 45.1,24.3 C52.3,25.7 57.7,31.9 57.7,39.4 "
    "C57.7,45 54.8,48.8 52.3,51.8 C50.7,53.7 49.7,55 49.4,56.5 L55.2,56.5 "
    "C55.5,55 56.5,53.7 58.1,51.8 C60.6,48.8 63.5,45 63.5,39.4 "
    "C63.5,30.9 56.6,24 48,24 Z"
)

DRAWABLE_XML = f"""<?xml version="1.0" encoding="utf-8"?>
<!--
  ~ The Logics card's illustration - r26, at the author's request, and drawn from scratch.
  ~
  ~ NOT the Flaticon original he pointed at. That licence wants visible attribution and does not
  ~ allow the asset to be redistributed; IMD is GPL-3.0, which requires that everything in the
  ~ source can be. The two cannot both be satisfied, so this is an original in the same spirit:
  ~ a bulb wired into logic, with the two outcomes IMD actually produces on either side of it.
  ~
  ~ One file for both themes, and coloured rather than tinted, both at the author's word. Drawn
  ~ with Image() rather than Icon() for that reason - an Icon replaces every pixel with its tint.
  ~
  ~ Generated by design/_v3_r26_logics_vector.py. The ring is sixteen arcs because VectorDrawable
  ~ has no dashed stroke, and every arc spells its seven parameters out because Android's path
  ~ parser will not read SVG's run-together flag shorthand. Edit the script, not this file.
  -->
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="56dp"
    android:height="56dp"
    android:viewportWidth="96"
    android:viewportHeight="96">

    <!-- The circuit boundary. -->
    <path
        android:pathData="{dashed_ring()}"
        android:strokeColor="{RING_GREY}"
        android:strokeWidth="2.5"
        android:strokeLineCap="round" />

    <!-- Three nodes on it, in the app's own teals and green. -->
    <path
        android:pathData="{hexagon(48, 14, 8)}"
        android:fillColor="{NODE_TEAL_DEEP}" />
    <path
        android:pathData="{hexagon(15, 37, 7)}"
        android:fillColor="{NODE_TEAL_LIGHT}" />
    <path
        android:pathData="{hexagon(81, 37, 7)}"
        android:fillColor="{NODE_TEAL_LIGHT}" />
    <path
        android:pathData="{hexagon(26, 76, 6)}"
        android:fillColor="{NODE_GREEN}" />

    <!-- The bulb: the idea at the centre of it. -->
    <path
        android:pathData="{BULB_GLASS}"
        android:fillColor="{BULB_LIGHT}" />
    <path
        android:pathData="{BULB_SHADED_SIDE}"
        android:fillColor="{BULB_SHADE}" />
    <path
        android:pathData="M42,41.5 L46,33.5 L50,39 L54,31"
        android:strokeColor="{FILAMENT}"
        android:strokeWidth="2.2"
        android:strokeLineCap="round"
        android:strokeLineJoin="round" />

    <!-- Its base. -->
    <path
        android:pathData="M42.2,60 L53.8,60 A 2.2 2.2 0 0 1 53.8 64.5 L42.2,64.5 A 2.2 2.2 0 0 1 42.2 60 Z"
        android:fillColor="{BASE_LIGHT}" />
    <path
        android:pathData="M43.7,66.5 L52.3,66.5 A 2.2 2.2 0 0 1 52.3 71 L43.7,71 A 2.2 2.2 0 0 1 43.7 66.5 Z"
        android:fillColor="{BASE_LIGHT}" />
    <path
        android:pathData="M44,73.5 L52,73.5 C52,76.1 50.2,78 48,78 C45.8,78 44,76.1 44,73.5 Z"
        android:fillColor="{BASE_DARK}" />

    <!-- The gear: the mechanism. A real hole, not a disc in the page's colour. -->
    <path
        android:pathData="{gear(78, 70, 9.5, 6.4, 3.2)}"
        android:fillColor="{GEAR_GREY}"
        android:fillType="evenOdd" />

    <!-- The two outcomes. Green for hidden, red for restored - IMD's own meanings. -->
    <path
        android:pathData="{circle(76, 16, 11)}"
        android:fillColor="{TICK_GREEN}" />
    <path
        android:pathData="M71,16.2 L74.4,19.6 L80.4,13.2"
        android:strokeColor="{BADGE_INK}"
        android:strokeWidth="2.6"
        android:strokeLineCap="round"
        android:strokeLineJoin="round" />
    <path
        android:pathData="{circle(19, 63, 10)}"
        android:fillColor="{CROSS_RED}" />
    <path
        android:pathData="M15.6,59.6 L22.4,66.4 M22.4,59.6 L15.6,66.4"
        android:strokeColor="{BADGE_INK}"
        android:strokeWidth="2.6"
        android:strokeLineCap="round" />
</vector>
"""

# ── the geometry has to be sane before it is written ─────────────────────────────────────────
ring = dashed_ring()

check(ring.count("M") == 16, f"ring: expected 16 dashes, got {ring.count('M')}")

check(ring.count("A") == 16, "ring: every dash should be one arc")

check("A  " not in ring and ",A" not in ring, "ring: an arc lost its spacing")

# ⚠ The parser trap this file exists to avoid: a flag pair run into the next coordinate.
for path in (ring, gear(78, 70, 9.5, 6.4, 3.2), circle(76, 16, 11)):
    for bad in ("0 00", "0 01", "0 10", "0 11"):
        check(bad not in path, f"path: run-together arc flags ({bad}) — Android will misread it")

check(gear(78, 70, 9.5, 6.4, 3.2).count("L") == 31, "gear: expected 8 teeth of 4 points")

# One ring, four nodes, three for the bulb, three for its base, one gear, and two badges of two.
check(DRAWABLE_XML.count("<path") == 16, "drawable: unexpected path count")

check("android:fillType=\"evenOdd\"" in DRAWABLE_XML, "drawable: the gear's hole would be filled")

# ─────────────────────────────────────────────────────────────────────────────────────────────
# Wiring it into the About card
# ─────────────────────────────────────────────────────────────────────────────────────────────

settings = SETTINGS.read_text(encoding="utf-8")

OLD = """                    // A Column so the second line starts where the first one does, under the
                    // "I" of IMD rather than under the chain icon.
                    Column {
                        Text(
                            text = logicsText,
                            style = MaterialTheme.typography.bodyLarge,
                            color = MaterialTheme.colorScheme.primary,
                            textDecoration = TextDecoration.Underline,
                        )

                        Text(
                            text = stringResource(R.string.about_logics_how),
                            style = MaterialTheme.typography.bodyLarge,
                            color = MaterialTheme.colorScheme.primary,
                            textDecoration = TextDecoration.Underline,
                        )
                    }
                }"""

NEW = """                    // A Column so the second line starts where the first one does, under the
                    // "I" of IMD rather than under the chain icon.
                    //
                    // ⚠ **Weighted since r26**, because there is something to its right now. Two
                    // underlined lines would otherwise measure to their own width and leave the
                    // illustration wherever that happened to end.
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = logicsText,
                            style = MaterialTheme.typography.bodyLarge,
                            color = MaterialTheme.colorScheme.primary,
                            textDecoration = TextDecoration.Underline,
                        )

                        Text(
                            text = stringResource(R.string.about_logics_how),
                            style = MaterialTheme.typography.bodyLarge,
                            color = MaterialTheme.colorScheme.primary,
                            textDecoration = TextDecoration.Underline,
                        )
                    }

                    Spacer(modifier = Modifier.width(10.dp))

                    // ⚠ **`Image`, not `Icon`, and that is the author's *"no logics icon stay
                    // coloured"*.** `Icon` replaces every non-transparent pixel with a tint, which
                    // would flatten this to a grey silhouette — the same treatment the settings
                    // rows are getting, and precisely what he ruled out for this one.
                    //
                    // No contentDescription: the two underlined lines beside it already name the
                    // link, and a reader hearing the destination twice learns nothing the second
                    // time.
                    Image(
                        modifier = Modifier.size(LOGICS_ICON_SIZE),
                        painter = painterResource(R.drawable.ic_logics),
                        contentDescription = null,
                    )
                }"""

settings = replace_once(settings, OLD, NEW, "settings: logics illustration")

settings = replace_once(
    settings,
    """/**
 * Where a surface stops being light and starts being dark.""",
    """/** The Logics card's illustration. Big enough to read its parts, short enough for two lines. */
private val LOGICS_ICON_SIZE = 56.dp

/**
 * Where a surface stops being light and starts being dark.""",
    "settings: LOGICS_ICON_SIZE",
)

if "import androidx.compose.foundation.Image\n" not in settings:
    failures.append("settings: Image is not imported and this script expected it to be")

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

DRAWABLE.parent.mkdir(parents=True, exist_ok=True)

DRAWABLE.write_text(DRAWABLE_XML, encoding="utf-8")

SETTINGS.write_text(settings, encoding="utf-8")

for path in (DRAWABLE, SETTINGS):
    print(f"wrote {path.relative_to(ROOT).as_posix()}")

print("ok")
