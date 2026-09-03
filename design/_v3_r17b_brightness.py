#!/usr/bin/env python3
"""
r17b — brightness, at the author's *"increase the colour contrast of toggles / sections / settings
labels / checkboxes / selected tab bg in tab switcher, it is barely visible sometimes … i mean
brightness mostly"*.

Every change is **one rung up the same ladder**, not a new colour. r14 put the sections on Material
3's tonal container roles, which is the right structure and landed a step too quiet in a scheme
this dark; the fix is to start higher up the ladder, not to leave it.

  * **Sections** — collapsed card `surfaceContainerLow` → `surfaceContainerHigh`, open body
    `surfaceContainer` → `surfaceContainerHighest`, open heading `surfaceContainerHigh` →
    `secondaryContainer`. The ordering the sections depend on still holds, and the heading strip
    now carries a real tonal colour instead of a fourth shade of grey.
  * **The switch, off** — track `surfaceVariant` → `surfaceContainerHighest`, thumb `outline` →
    `onSurfaceVariant`. An off switch was two greys a shade apart on a grey card.
  * **The checkbox, off** — outline `onSurfaceVariant` → `onSurface`.
  * **The selected tab** — `primaryContainer` → `primary`, with `onPrimary` on top. In this scheme
    `primaryContainer` is a dark olive that all but disappears into the bar; `primary` is the light
    green the app already uses for its links and buttons, so a selected tab now reads at a glance.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SETTINGS = ROOT / "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"

TOGGLES = ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/component/GetoToggles.kt"

NAV = ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/component/GetoFloatingNavigation.kt"

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


# ------------------------------------------------------------ 1. the sections

settings = SETTINGS.read_text(encoding="utf-8")

settings = swap(
    settings,
    """    val bodyTint = MaterialTheme.colorScheme.surfaceContainer

    val headingTint = MaterialTheme.colorScheme.surfaceContainerHigh

    val collapsedTint = MaterialTheme.colorScheme.surfaceContainerLow""",
    """    // ⚠ **One rung higher than r14 put them — r17b.** The roles were right and the starting
    // point was too quiet: on a page this dark, `surfaceContainerLow` against `surface` is a
    // couple of points, and the author could barely see the cards. Same ladder, same ordering,
    // three steps further up — and the open heading takes a real tonal colour rather than a
    // fourth shade of grey, because that strip is the thing that says *this section is open*.
    val bodyTint = MaterialTheme.colorScheme.surfaceContainerHighest

    val headingTint = MaterialTheme.colorScheme.secondaryContainer

    val collapsedTint = MaterialTheme.colorScheme.surfaceContainerHigh""",
    "settings: section tints",
)

pending.append((SETTINGS, settings))

# ------------------------------------------------------------ 2. the switch and the checkbox

toggles = TOGGLES.read_text(encoding="utf-8")

toggles = swap(
    toggles,
    """        error -> scheme.errorContainer
        enabled -> scheme.surfaceVariant
        else -> scheme.surfaceVariant.copy(alpha = 0.45f)""",
    """        error -> scheme.errorContainer
        // ⚠ **The brightest container, not `surfaceVariant` — r17b.** An off switch sitting on a
        // settings card was two greys a shade apart, which the author reported as barely visible.
        enabled -> scheme.surfaceContainerHighest
        else -> scheme.surfaceContainerHighest.copy(alpha = 0.45f)""",
    "toggles: switch track",
)

toggles = swap(
    toggles,
    """        error -> scheme.error
        enabled -> scheme.outline
        else -> scheme.outline.copy(alpha = 0.45f)""",
    """        error -> scheme.error
        // The thumb has to clear the track it sits in, so it moves up with it.
        enabled -> scheme.onSurfaceVariant
        else -> scheme.onSurfaceVariant.copy(alpha = 0.45f)""",
    "toggles: switch thumb",
)

toggles = swap(
    toggles,
    """    val outline = when {
        enabled -> scheme.onSurfaceVariant
        else -> scheme.onSurface.copy(alpha = 0.38f)
    }""",
    """    val outline = when {
        // ⚠ **Full ink — r17b.** An unticked box is nothing but its outline, so a dimmed one is
        // the whole control being hard to see.
        enabled -> scheme.onSurface
        else -> scheme.onSurface.copy(alpha = 0.38f)
    }""",
    "toggles: checkbox outline",
)

pending.append((TOGGLES, toggles))

# ------------------------------------------------------------ 3. the selected tab

nav = NAV.read_text(encoding="utf-8")

nav = swap(
    nav,
    "            MaterialTheme.colorScheme.primaryContainer\n",
    "            MaterialTheme.colorScheme.primary\n",
    "nav: selected container",
    count=2,
)

nav = swap(
    nav,
    "            MaterialTheme.colorScheme.onPrimaryContainer\n",
    "            MaterialTheme.colorScheme.onPrimary\n",
    "nav: selected content",
    count=2,
)

check(
    "primaryContainer" not in nav,
    "a primaryContainer reference survived in the navigation bar",
)

pending.append((NAV, nav))

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
