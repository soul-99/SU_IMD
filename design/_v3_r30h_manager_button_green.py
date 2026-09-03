#!/usr/bin/env python3
"""
r30h — the two manager buttons and the Favourites manager button join the rest of the app's green.

The author: *"all other buttons green is good, but in settings manager hide button and rev to def
button use diff green fix that, also make the settings manager button in fav/all apps tab use same
green/theme colour"*.

## Three different greens, and why

Every filled `Button` in the app draws itself in `primary` — that is the green he is happy with.
The three he is not happy with never went through `Button` at all:

| | drew itself in | which in dark mode is |
| --- | --- | --- |
| **Hide settings**, **Revert to default** | `primaryContainer` / `onPrimaryContainer` | `#375F05`, a dark bottle green |
| the **Settings manager** button in Favourites | `secondaryContainer` / `onSecondaryContainer` | `#41512C`, a muted olive |
| every other filled button | `primary` / `onPrimary` | `#8FAE6E` |

So there were three greens on screen at once, and after r30f moved `primary` they diverged further
still. All three now take `primary` / `onPrimary`.

## The two comments this overturns, and why it is safe

⚠ **r23 raised the manager pair from `secondaryContainer` to `primaryContainer`** because *"against
a translucent frosted card it stopped reading as a button at all"*. That reasoning is not being
reversed — it is being carried further. `primary` is a **stronger** fill than `primaryContainer`,
not a weaker one, so the pair reads as a button at least as well as it did. Both comments are
rewritten rather than deleted, so the frosted-card constraint stays recorded for whoever looks next.

⚠ **The Favourites pair still reads as one prominent action with a way in beside it** — that came
from size and position, which do not change: the manager button is still the small FAB on the left,
the unhide one still the large FAB on the right.

⚠ **The red pending state is untouched** in both files. It is not competing with these greens; it
replaces one of them, and `GetoRed` with white on it is fixed in both themes on purpose.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MANAGER = ROOT / "feature/apps/src/main/kotlin/com/android/geto/feature/apps/dialog/AndroidSettingsManagerDialog.kt"
FLOATING = ROOT / "feature/apps/src/main/kotlin/com/android/geto/feature/apps/AppsFloatingActions.kt"

failures: list[str] = []

writes: dict[Path, str] = {}


def check(condition: bool, message: str) -> bool:
    if not condition:
        failures.append(message)

    return condition


def replace_once(text: str, old: str, new: str, label: str) -> str:
    found = text.count(old)

    if not check(found == 1, f"{label}: found {found}x, expected 1"):
        return text

    return text.replace(old, new, 1)


# ---------------------------------------------------------------- the manager's two buttons

manager = MANAGER.read_text(encoding="utf-8")

manager = replace_once(
    manager,
    """    // ⚠ **`primaryContainer`, up from `secondaryContainer` — r23, from the author's annotated
    // screenshot.** The secondary container is a muted olive in the dark scheme, and against a
    // translucent frosted card it stopped reading as a button at all. These two are what the
    // dialog is *for*, so they take the strongest container the scheme has and the ink that goes
    // with it. The red pending state is untouched: it is not competing with these, it replaces
    // one of them.
    val container = if (pending) {
        GetoRed
    } else {
        MaterialTheme.colorScheme.primaryContainer
    }

    val content = if (pending) {
        Color.White
    } else {
        MaterialTheme.colorScheme.onPrimaryContainer
    }""",
    """    // ⚠ **`primary`, up from `primaryContainer` — r30h, at the author's word: the manager's two
    // buttons were "a diff green" from every other button in the app.** They were, and there were
    // three: a filled `Button` anywhere else is `primary`, these were `primaryContainer`, and the
    // Favourites manager button was `secondaryContainer`.
    //
    // ⚠ **This carries r23's reason further rather than reversing it.** r23 raised this pair off
    // `secondaryContainer` because against a translucent frosted card a muted olive stopped
    // reading as a button at all. `primary` is a *stronger* fill than `primaryContainer`, so the
    // constraint that produced that change is better served, not worse. These two are what the
    // dialog is *for*.
    //
    // The red pending state is untouched: it is not competing with these, it replaces one of them.
    val container = if (pending) {
        GetoRed
    } else {
        MaterialTheme.colorScheme.primary
    }

    val content = if (pending) {
        Color.White
    } else {
        MaterialTheme.colorScheme.onPrimary
    }""",
    "manager: the two action buttons",
)

check(
    manager.count("MaterialTheme.colorScheme.primaryContainer") == 0,
    "manager: a primaryContainer survived",
)

check(
    manager.count("MaterialTheme.colorScheme.onPrimaryContainer") == 0,
    "manager: an onPrimaryContainer survived",
)

check(manager.count("GetoRed") == 2, "manager: the red pending state moved")

writes[MANAGER] = manager

# ---------------------------------------------------------------- the Favourites button

floating = FLOATING.read_text(encoding="utf-8")

floating = replace_once(
    floating,
    """        // Left of the primary one, and smaller. A tonal container rather than the primary one, so
        // the pair reads as one prominent action with a way in to the detail beside it.
        SmallFloatingActionButton(
            onClick = { showManagerDialog = true },
            containerColor = MaterialTheme.colorScheme.secondaryContainer,
            contentColor = MaterialTheme.colorScheme.onSecondaryContainer,
        ) {""",
    """        // Left of the primary one, and smaller.
        //
        // ⚠ **`primary`, up from `secondaryContainer` — r30h, at the author's word.** It opens the
        // settings manager, whose own two buttons are `primary` as of the same round, and a third
        // green for the button that opens them was the thing he was looking at. What makes the
        // pair read as one prominent action with a way in beside it is size and position, and
        // neither of those changes: this is still the small one on the left.
        SmallFloatingActionButton(
            onClick = { showManagerDialog = true },
            containerColor = MaterialTheme.colorScheme.primary,
            contentColor = MaterialTheme.colorScheme.onPrimary,
        ) {""",
    "favourites: the manager button",
)

# ⚠ **`colorScheme.` is not decoration here.** The bare word also occurs in the comment written
# just above, which names the role being left behind — so a check for the word alone reports a
# failure about the very sentence explaining the fix.
check(
    floating.count("colorScheme.secondaryContainer") == 0
    and floating.count("colorScheme.onSecondaryContainer") == 0,
    "favourites: a secondaryContainer draw survived",
)

# The large one beside it is not in this round: grey when nothing is owed, GetoRed when something
# is, and both are deliberate.
check(
    "containerColor = if (anythingHidden) {\n                GetoRed" in floating,
    "favourites: the unhide button's colours moved, and this round does not touch them",
)

check(
    "MaterialTheme.colorScheme.surfaceContainerHighest" in floating,
    "favourites: the unhide button's idle colour moved",
)

writes[FLOATING] = floating

# ---------------------------------------------------------------- one green, asserted

# The point of the round: after it, nothing in these two files paints itself a green that is not
# `primary`. `GetoRed` and the neutral idle state are the two deliberate exceptions.
for path, text in writes.items():
    for role in ("primaryContainer", "secondaryContainer", "onPrimaryContainer", "onSecondaryContainer"):
        check(
            f"colorScheme.{role}" not in text,
            f"{path.name}: still paints with {role}",
        )

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

for path, text in writes.items():
    path.write_text(text, encoding="utf-8")

print("Hide settings / Revert to default   primaryContainer   -> primary")

print("Settings manager (Favourites tab)   secondaryContainer -> primary")

print(f"wrote {len(writes)} files")

print("ok")
