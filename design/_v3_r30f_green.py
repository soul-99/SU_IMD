#!/usr/bin/env python3
"""
r30f — the dark scheme's green stops being a highlighter.

The author, of the three options in `design/preview_r30_green.py`: *"use c"*.

## What C is

`primary` in `DarkGreenColorScheme` goes from **#B3E675** to **#8FAE6E**, and nothing else moves.

A highlighter pen is a yellow-green at high lightness *and* high chroma together, and #B3E675 sat
squarely in that corner — which is why six switch tracks stacked in the settings manager is where
he saw it first. #8FAE6E is the same hue, taken well down in both.

## Why exactly two literals, and why the second one

`GetoToggles` derives every switch colour from `scheme.primary`, and a filled `Button` and a
`Checkbox` take it straight from the theme, so **one token is all three places he named**.

The second edit is not a second decision. `inversePrimary` in a light scheme *is* the dark scheme's
primary — that is what the role means — so the two have to be the same literal or the light theme's
inverse surfaces start showing a green the dark theme no longer contains.

## Why C and not the light green in both

The option he first asked for was `primary = #58743E` in dark too. It fills beautifully, and it
fails the token's other job: about thirty places in this app draw a word, a link or an icon in
`colorScheme.primary` directly on a card, where #58743E measures **2.38:1**. #8FAE6E clears 4.5:1
in both directions — 5.20:1 for the dark ink drawn on it, 5.04:1 for it as ink on a dialog card —
so `onPrimary` keeps its existing dark green and no caller anywhere has to change.

⚠ **The light scheme is untouched**, deliberately. It was never the thing that read as a
highlighter, and its `#4E7819` is within a hair of the muted green he picked out of the sheet.

Computes every edit in memory, asserts every match count and every contrast ratio, writes nothing
if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

THEME = ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/theme/Theme.kt"
CHANGELOG = ROOT / "CHANGELOG.md"

WAS = "B3E675"
NOW = "8FAE6E"

failures: list[str] = []


def check(condition: bool, message: str) -> bool:
    if not condition:
        failures.append(message)

    return condition


def to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(value: str) -> float:
    r, g, b = (to_linear(int(value[i:i + 2], 16) / 255) for i in (0, 2, 4))

    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    high, low = sorted((luminance(a), luminance(b)), reverse=True)

    return round((high + 0.05) / (low + 0.05), 2)


# ⚠ Asserted, not trusted to the sheet that produced it. These are the two ratios the whole choice
# rests on, and a mistyped hex would pass every other check in this file.
for other, job, floor in (
    ("1F3800", "onPrimary drawn on it", 4.5),      # the switch thumb, the filled button's label
    ("31352B", "it drawn on a dialog card", 4.5),  # the emphasised phrases, the links, the icons
    ("1B1E16", "it drawn on the page", 4.5),
):
    ratio = contrast(NOW, other)

    check(ratio >= floor, f"contrast: {job} is {ratio}:1, below {floor}:1")

# ---------------------------------------------------------------- the theme

theme = THEME.read_text(encoding="utf-8")

check(
    theme.count(f"Color(0xFF{WAS})") == 2,
    f"theme: {theme.count(f'Color(0xFF{WAS})')} uses of {WAS}, expected 2",
)

# Both must be the roles this script believes they are, named on their own lines.
for line in (f"    inversePrimary = Color(0xFF{WAS}),", f"    primary = Color(0xFF{WAS}),"):
    check(theme.count(line) == 1, f"theme: {line.strip()!r} found {theme.count(line)}x, expected 1")

check(f"Color(0xFF{NOW})" not in theme, f"theme: {NOW} is already in the file")

theme = theme.replace(f"Color(0xFF{WAS})", f"Color(0xFF{NOW})")

check(WAS not in theme, f"theme: {WAS} survived somewhere")

check(theme.count(f"Color(0xFF{NOW})") == 2, "theme: the replacement did not land twice")

# The light scheme's own primary is not in this edit and must still be there.
check(
    "    primary = Color(0xFF4E7819),\n    onPrimary = Color(0xFFFFFFFF)," in theme,
    "theme: the light scheme's primary moved, and this round does not touch it",
)

# The comment above the dark scheme's background explains a different decision entirely; if the
# replacement had run wide it would be the first thing damaged.
check(
    "background = Color(0xFF1B1E16)," in theme,
    "theme: the dark background moved",
)

# ---------------------------------------------------------------- the changelog

changelog = CHANGELOG.read_text(encoding="utf-8")

ANCHOR = "- **Dynamic (wallpaper) colours and progressive blur are both on by default.**\n"

check(changelog.count(ANCHOR) == 1, "changelog: the dynamic-theme line is not where it was")

changelog = changelog.replace(
    ANCHOR,
    ANCHOR
    + "- **The dark theme's green is calmer** - the switches and buttons no longer read as a\n"
    "  highlighter, which was most obvious with six of them stacked in the settings manager.\n",
    1,
)

check(
    changelog.count("no longer read as a") == 1,
    "changelog: the green line did not land exactly once",
)

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

THEME.write_text(theme, encoding="utf-8")

CHANGELOG.write_text(changelog, encoding="utf-8")

print(f"dark primary  #{WAS} -> #{NOW}")

print(f"  onPrimary on it     {contrast(NOW, '1F3800')}:1")

print(f"  as ink on a card    {contrast(NOW, '31352B')}:1")

print(f"  as ink on the page  {contrast(NOW, '1B1E16')}:1")

print("wrote 2 files")

print("ok")
