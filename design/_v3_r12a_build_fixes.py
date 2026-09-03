#!/usr/bin/env python3
"""
r12a — the three build defects r12 shipped, and the deprecation warning beside them.

⚠ **All of them are mine, from the r12 header rewrite**, and all three are the same class of
mistake: an import written from memory rather than from the symbol's actual package.

  1. `androidx.compose.foundation.layout.WindowInsets` imported **twice**. r11's floating-header
     script added it; my r12 `adds` list added it again without checking. Kotlin reports that as
     `Conflicting import: imported name 'WindowInsets' is ambiguous` on *both* lines.

  2. `androidx.compose.ui.util.lerp` has `Float`/`Int`/`Long` overloads only. The two header lerps
     interpolate **`Dp`**, whose overload lives in `androidx.compose.ui.unit`.

  3. The obvious fix — import both — is a coin flip I am not taking in a round that has already
     failed to build twice. Kotlin does form an overload set across two callable imports of the
     same name, but this file also carries a *classifier* import from each of those packages, and
     the diagnostic in (1) is exactly what an ambiguity here would look like. So the single `Float`
     lerp is written out arithmetically instead and only the `unit` import remains. `lerp(a, b, t)`
     *is* `a + (b - a) * t`; there is nothing lost.

  4. `Icons.Rounded.OpenInNew` is deprecated in favour of `Icons.AutoMirrored.Rounded.OpenInNew`
     — a warning, not an error, but r12 was the round that moved all 23 icons to Rounded and this
     is the one that did not land on its final name.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HOME = ROOT / "feature/home/src/main/kotlin/com/android/geto/feature/home/HomeScreen.kt"

ICONS = ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/icon/GetoIcons.kt"

WINDOW_INSETS = "import androidx.compose.foundation.layout.WindowInsets\n"

failures: list[str] = []

pending: list[tuple[Path, str]] = []


def check(condition: bool, message: str) -> bool:
    if not condition:
        failures.append(message)

    return condition


# ---------------------------------------------------------------- HomeScreen.kt

home = HOME.read_text(encoding="utf-8")

# 1 — the duplicate import. Counted on whole lines, so `consumeWindowInsets` and
#     `windowInsetsPadding` cannot be mistaken for it.
lines = home.splitlines(keepends=True)

insets_at = [i for i, line in enumerate(lines) if line == WINDOW_INSETS]

if check(len(insets_at) == 2, f"WindowInsets import appears {len(insets_at)}x, expected 2"):
    # Drop the second: the first sits in r11's alphabetical run, mine was appended after
    # `consumeWindowInsets` and is the one out of place.
    del lines[insets_at[1]]

    home = "".join(lines)

# 2 — the lerp import, swapped rather than added.
OLD_IMPORT = "import androidx.compose.ui.util.lerp\n"

NEW_IMPORT = "import androidx.compose.ui.unit.lerp\n"

if check(home.count(OLD_IMPORT) == 1, "ui.util.lerp import not found exactly once"):
    home = home.replace(OLD_IMPORT, "", 1)

    # Placed after `unit.dp`, where ASCII ordering puts it (uppercase, then lowercase).
    DP_IMPORT = "import androidx.compose.ui.unit.dp\n"

    if check(home.count(DP_IMPORT) == 1, "ui.unit.dp import not found exactly once"):
        home = home.replace(DP_IMPORT, DP_IMPORT + NEW_IMPORT, 1)

check(home.count("import androidx.compose.ui.unit.lerp") == 1, "unit.lerp import not placed once")

check("import androidx.compose.ui.util.lerp" not in home, "util.lerp import survived")

# 3 — the Float lerp, written out.
OLD_SCALE = "    val scale = lerp(1f, COLLAPSED_TITLE_SCALE, collapsedFraction)\n"

NEW_SCALE = (
    "    // ⚠ **Not `lerp`.** The two lines below interpolate `Dp` and need\n"
    "    // `androidx.compose.ui.unit.lerp`; this one is a `Float` and would need\n"
    "    // `androidx.compose.ui.util.lerp`. One file, one name, two packages — so this one is\n"
    "    // spelled out and the import stays unambiguous. `lerp(a, b, t)` is `a + (b - a) * t`.\n"
    "    val scale = 1f + (COLLAPSED_TITLE_SCALE - 1f) * collapsedFraction\n"
)

if check(home.count(OLD_SCALE) == 1, "the Float lerp line was not found exactly once"):
    home = home.replace(OLD_SCALE, NEW_SCALE, 1)

# Only the two Dp lerps may remain as calls.
call_lines = [
    line for line in home.splitlines()
    if "lerp(" in line and not line.lstrip().startswith(("//", "*", "/*", "import "))
]

check(len(call_lines) == 2, f"{len(call_lines)} lerp call(s) left, expected 2 (both Dp)")

check(
    all("GetoLargeTopBarHeight" in line for line in call_lines),
    "a surviving lerp call is not one of the two Dp ones",
)

pending.append((HOME, home))

# ---------------------------------------------------------------- GetoIcons.kt

icons = ICONS.read_text(encoding="utf-8")

OLD_ICON_IMPORT = "import androidx.compose.material.icons.rounded.OpenInNew\n"

NEW_ICON_IMPORT = "import androidx.compose.material.icons.automirrored.rounded.OpenInNew\n"

if check(icons.count(OLD_ICON_IMPORT) == 1, "rounded.OpenInNew import not found exactly once"):
    icons = icons.replace(OLD_ICON_IMPORT, NEW_ICON_IMPORT, 1)

OLD_ICON = "    val OpenInNew = Icons.Rounded.OpenInNew\n"

NEW_ICON = "    val OpenInNew = Icons.AutoMirrored.Rounded.OpenInNew\n"

if check(icons.count(OLD_ICON) == 1, "the OpenInNew value line was not found exactly once"):
    icons = icons.replace(OLD_ICON, NEW_ICON, 1)

check("Icons.Rounded.OpenInNew" not in icons, "the deprecated spelling survived")

pending.append((ICONS, icons))

# ---------------------------------------------------------------- commit

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

for path, text in pending:
    path.write_text(text, encoding="utf-8")

    print(f"wrote {path.relative_to(ROOT).as_posix()}")

print("ok")
