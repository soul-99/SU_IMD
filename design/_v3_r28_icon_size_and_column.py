#!/usr/bin/env python3
"""
r28 — the settings-row icons get bigger, and land on the switches' centre line.

The author, from a screenshot: *"increase the new icons size and center them above the center point
of switches"*.

## Why they were off-centre, which is the part worth writing down

Both the icon and the switch are the last thing in a row that ends with `padding(horizontal = 16.dp)`,
so both are flush to the same right edge — and *that* is the problem. A Material switch is **52 dp**
wide, so its centre sits 16 + 26 = **42 dp** from the row's right edge. A 24 dp icon flush to the
same edge has its centre at 16 + 12 = **28 dp**. The two columns were always going to be 14 dp apart;
nothing about the icons was wrong, they were simply a different width.

⚠ **So the fix is not a nudge.** Padding the icon by 14 dp would line the two up *at these two
sizes* and drift the moment either changed — including in the same breath the author asked for,
since he also wants the icons bigger. The icon now sits in a box exactly as wide as a switch and is
centred in it, so the two centre lines coincide by construction and stay that way whatever size the
glyph is drawn at.

`SETTINGS_TRAILING_WIDTH` is 52 dp because that is Material's switch track width — the settings
manager already writes the same number down for the same reason (`SWITCH_TRACK_WIDTH`, so its row
titles share a centre line). Different file, different module, same fact about the same component.

## The size

24 dp to 30 dp. The ceiling is the box: a glyph wider than 52 dp would push the column back out. 30
gives the busiest of them — the octagram with the droid inside it — noticeably more room, and it
cannot change any row's height, because the two lines of text beside it already measure about 45 dp.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

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


def code(text: str) -> str:
    return "\n".join(
        line for line in text.splitlines() if not line.strip().startswith(("//", "*", "/*", "/**"))
    )


settings = SETTINGS.read_text(encoding="utf-8")

settings = replace_once(
    settings,
    """        icon?.let {
            Spacer(modifier = Modifier.width(12.dp))

            Icon(
                modifier = Modifier.size(SETTINGS_ICON_SIZE),
                painter = it,
                contentDescription = null,
                // The off-switch rim, at the author's word. Dimmed with the row, because a row
                // that greys its words and keeps a full-strength mark reads as half disabled.
                tint = if (enabled) {
                    MaterialTheme.colorScheme.outline
                } else {
                    MaterialTheme.colorScheme.outline.copy(alpha = 0.38f)
                },
            )
        }""",
    """        icon?.let {
            Spacer(modifier = Modifier.width(12.dp))

            // ⚠ **A switch-width box, not a nudge — r28.** Both the icon and a switch are flush to
            // the row's trailing padding, which is exactly why they did not line up: a switch is
            // 52 dp wide so its centre lands 42 dp from the edge, and a 24 dp icon's landed at 28.
            // The 14 dp between them was never about the drawings.
            //
            // Padding the difference away would have fixed it at one pair of sizes and broken it
            // again the moment either changed - which is the same breath the author asked in,
            // since the icons got bigger too. Centred inside a box the width of a switch, the two
            // centre lines coincide by construction at any glyph size.
            Box(
                modifier = Modifier.width(SETTINGS_TRAILING_WIDTH),
                contentAlignment = Alignment.Center,
            ) {
                Icon(
                    modifier = Modifier.size(SETTINGS_ICON_SIZE),
                    painter = it,
                    contentDescription = null,
                    // The off-switch rim, at the author's word. Dimmed with the row, because a row
                    // that greys its words and keeps a full-strength mark reads as half disabled.
                    tint = if (enabled) {
                        MaterialTheme.colorScheme.outline
                    } else {
                        MaterialTheme.colorScheme.outline.copy(alpha = 0.38f)
                    },
                )
            }
        }""",
    "settings: icon box",
)

settings = replace_once(
    settings,
    """/**
 * Every settings-row mark, at one size.
 *
 * 24 dp: the same box the drawables are drawn in, and near enough a switch's height that the two
 * kinds of row do not look like different lists.
 */
private val SETTINGS_ICON_SIZE = 24.dp""",
    """/**
 * Every settings-row mark, at one size.
 *
 * ⚠ **30 dp, up from 24 — r28, the author's *"increase the new icons size"*.** The ceiling is
 * [SETTINGS_TRAILING_WIDTH]: a glyph wider than the box that centres it would push the column back
 * out of line with the switches. It cannot change a row's height either way, because the two lines
 * of text beside it already measure about 45 dp.
 */
private val SETTINGS_ICON_SIZE = 30.dp

/**
 * How wide the trailing slot is, so a mark and a switch share one centre line.
 *
 * 52 dp because that is Material's switch track width. The settings manager writes the same number
 * down for the same reason - see `SWITCH_TRACK_WIDTH` there, which keeps *its* row titles on a
 * centre line. Different file, different module, one fact about one component.
 */
private val SETTINGS_TRAILING_WIDTH = 52.dp""",
    "settings: sizes",
)

body = code(settings)

check(body.count("SETTINGS_TRAILING_WIDTH") == 2, "settings: expected the declaration and one use")

check(body.count("SETTINGS_ICON_SIZE") == 2, "settings: expected the declaration and one use")

check("private val SETTINGS_ICON_SIZE = 30.dp" in body, "settings: the icon size did not change")

# The box needs both of these, and `SettingsColumn` sits in a file that uses them constantly — so
# this is a check that they are already imported rather than an insertion.
for needed in (
    "import androidx.compose.foundation.layout.Box\n",
    "import androidx.compose.foundation.layout.width\n",
    "import androidx.compose.ui.Alignment\n",
):
    check(needed in settings, f"settings: {needed.rsplit('.', 1)[1].strip()} is not imported")

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

SETTINGS.write_text(settings, encoding="utf-8")

print(f"wrote {SETTINGS.relative_to(ROOT).as_posix()}")

print("ok")
