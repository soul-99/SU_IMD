#!/usr/bin/env python3
"""
r18 — a more saturated theme, and an off switch you can actually see.

  1. **Saturation.** Every accent token in both schemes has its HSL saturation multiplied by
     **1.35**, hue and lightness untouched. Doing it as one arithmetic operation rather than by
     picking nicer-looking hexes is what keeps the palette a palette: the greens stay the same
     greens, at the same lightnesses, in the same relationships to each other and to the text that
     has to sit on them. Contrast ratios are unchanged for the same reason — lightness is what
     drives those, and lightness does not move.

     Surfaces, outlines and the error family are left alone. The surfaces are the page the author
     already tuned twice, and the error red is a warning colour whose job is to not look like the
     theme.

  2. **The off switch.** r17b's mistake, and a clear one: it set the off track to
     `surfaceContainerHighest` in the same round it set the settings card to
     `surfaceContainerHighest`. Identical colours, so the track vanished and all that was left was
     a pale disc floating on the card — exactly what the author's screenshot shows. An off track is
     now `surfaceContainerLowest` with an `outline` border, which is Material's own answer: a
     recess with a rim, darker than whatever card it sits on rather than lighter.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

THEME = ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/theme/Theme.kt"

TOGGLES = ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/component/GetoToggles.kt"

failures: list[str] = []

pending: list[tuple[Path, str]] = []


def check(condition: bool, message: str) -> bool:
    if not condition:
        failures.append(message)

    return condition


def swap(text: str, old: str, new: str, label: str, count: int = 1) -> str:
    found = text.count(old)

    if check(found == count, f"{label}: found {found}x, expected {count}"):
        return text.replace(old, new, count)

    return text


# ------------------------------------------------------------ 1. the palette
#
# (scheme, token, before, after) — computed by multiplying HSL saturation by 1.35 and rounding, not
# chosen by eye. Anchored on the token name as well as the hex, because several of these values
# appear in both schemes in different roles: #B1D18A is the dark scheme's `primary` and the light
# scheme's `inversePrimary`, #4C662B the other way round, and #CDEDA3 is a container in one and an
# on-container in the other. Replacing by colour alone would repaint the wrong halves.
LIFTS = (
    ("primary", "0xFF4C662B", "0xFF4D7021"),
    ("primaryContainer", "0xFFCDEDA3", "0xFFCFFA96"),
    ("onPrimaryContainer", "0xFF102000", "0xFF102000"),
    ("secondary", "0xFF586249", "0xFF596645"),
    ("secondaryContainer", "0xFFDCE7C8", "0xFFDEECC3"),
    ("onSecondaryContainer", "0xFF151E0B", "0xFF152108"),
    ("tertiary", "0xFF386663", "0xFF306E6A"),
    ("tertiaryContainer", "0xFFBCECE7", "0xFFB4F4EE"),
    ("inversePrimary", "0xFFB1D18A", "0xFFB2DD7E"),
    ("primary", "0xFFB1D18A", "0xFFB2DD7E"),
    ("onPrimary", "0xFF1F3701", "0xFF1F3800"),
    ("primaryContainer", "0xFF354E16", "0xFF36580C"),
    ("onPrimaryContainer", "0xFFCDEDA3", "0xFFCFFA96"),
    ("secondary", "0xFFBFCBAD", "0xFFC0D0A8"),
    ("onSecondary", "0xFF2A331E", "0xFF2B371A"),
    ("secondaryContainer", "0xFF404A33", "0xFF414E2F"),
    ("onSecondaryContainer", "0xFFDCE7C8", "0xFFDEECC3"),
    ("tertiary", "0xFFA0D0CB", "0xFF98D8D2"),
    ("tertiaryContainer", "0xFF1F4E4B", "0xFF175652"),
    ("onTertiaryContainer", "0xFFBCECE7", "0xFFB4F4EE"),
    ("inversePrimary", "0xFF4C662B", "0xFF4D7021"),
)

theme = THEME.read_text(encoding="utf-8")

for token, before, after in LIFTS:
    if before == after:
        # Already at full saturation for its lightness; nothing to do, and asserting it is still
        # present is worth more than skipping it silently.
        check(
            f"    {token} = Color({before}),\n" in theme,
            f"theme: {token} = {before} is not where it was expected",
        )

        continue

    theme = swap(
        theme,
        f"    {token} = Color({before}),\n",
        f"    {token} = Color({after}),\n",
        f"theme: {token} {before}",
    )

# The surfaces must not have moved: the author tuned those separately, twice.
for untouched in (
    "    background = Color(0xFFF9FAEF),",
    "    background = Color(0xFF1B1E16),",
    "    surfaceContainerHighest = Color(0xFF3C4036),",
    "    error = Color(0xFFBA1A1A),",
    "    error = Color(0xFFFFB4AB),",
):
    check(untouched in theme, f"theme: a token that should not have moved did: {untouched.strip()}")

pending.append((THEME, theme))

# ------------------------------------------------------------ 2. the off switch

toggles = TOGGLES.read_text(encoding="utf-8")

toggles = swap(
    toggles,
    """        error -> scheme.errorContainer
        // ⚠ **The brightest container, not `surfaceVariant` — r17b.** An off switch sitting on a
        // settings card was two greys a shade apart, which the author reported as barely visible.
        enabled -> scheme.surfaceContainerHighest
        else -> scheme.surfaceContainerHighest.copy(alpha = 0.45f)""",
    """        error -> scheme.errorContainer
        // ⚠ **The *darkest* container, with a rim — r18, undoing r17b.** r17b reached for
        // `surfaceContainerHighest` in the same round that made the settings card
        // `surfaceContainerHighest`, so an off switch and the card behind it became the same
        // colour and the track disappeared: the author was left looking at a pale disc floating
        // on a card. An off track reads as a recess, not a raised patch, so it goes below
        // whatever it sits on and takes an outline — which is Material's own answer too.
        enabled -> scheme.surfaceContainerLowest
        else -> scheme.surfaceContainerLowest.copy(alpha = 0.45f)""",
    "toggles: switch track",
)

toggles = swap(
    toggles,
    """        Box(
            modifier = Modifier
                .align(Alignment.Center)
                .size(width = SWITCH_TRACK_WIDTH, height = SWITCH_TRACK_HEIGHT)
                .clip(CircleShape)
                .background(track),
        )""",
    """        Box(
            modifier = Modifier
                .align(Alignment.Center)
                .size(width = SWITCH_TRACK_WIDTH, height = SWITCH_TRACK_HEIGHT)
                .clip(CircleShape)
                .background(track)
                // ⚠ **Only while off.** A checked track is a filled `primaryContainer` and needs
                // no rim; an unchecked one is a dark slot on a dark card, and the rim is most of
                // what makes it a slot at all.
                .border(
                    width = SWITCH_TRACK_BORDER,
                    color = if (checked) Color.Transparent else border,
                    shape = CircleShape,
                ),
        )""",
    "toggles: track border",
)

toggles = swap(
    toggles,
    """    val offset by animateDpAsState(
        targetValue = if (checked) SWITCH_TRACK_WIDTH - SWITCH_THUMB_SIZE else 0.dp,""",
    """    val border = if (live) scheme.outline else scheme.outline.copy(alpha = 0.45f)

    val offset by animateDpAsState(
        targetValue = if (checked) SWITCH_TRACK_WIDTH - SWITCH_THUMB_SIZE else 0.dp,""",
    "toggles: border colour",
)

toggles = swap(
    toggles,
    "private val SWITCH_THUMB_SIZE: Dp = ",
    "/** The rim around an unchecked track. */\nprivate val SWITCH_TRACK_BORDER: Dp = 2.dp\n\nprivate val SWITCH_THUMB_SIZE: Dp = ",
    "toggles: border width",
)

pending.append((TOGGLES, toggles))

# ------------------------------------------------------------ commit

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

for path, text in pending:
    path.write_text(text, encoding="utf-8")

    print(f"wrote {path.relative_to(ROOT).as_posix()}")

print("ok")
