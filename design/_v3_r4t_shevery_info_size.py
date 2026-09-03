#!/usr/bin/env python3
"""v3-r4t — the Shevery ⓘ is the same size as the Thedjchi ⓘ.

    "inscrease shizuku page shevery toggle i button size to match that of thedjchi i button size"

## ⚠ They were sized in two different units, which is why they could not match

The Thedjchi ⓘ is drawn *inside* its label through an `InlineTextContent` whose `Placeholder` is
**1.2 em** — one and a fifth of the label's own type size, so it grows with the text and with the
user's font-scale setting. The Shevery ⓘ sits beside its label as a separate control and was a
flat **13.dp**, which at the default scale is about a quarter smaller and at a large font-scale
setting is much smaller still.

So this is not "make 13 into 17". Both are now derived from **one constant** and the **same type
style** the label uses: `FORK_INFO_EM` × `bodyMedium.fontSize`, converted to dp for the one that
needs a dp. They are the same size at every font scale, and they cannot drift apart later,
because there is only one number.

⚠ **The Placeholder keeps its `em` and the icon takes a `dp`, and that asymmetry is required**:
a `Placeholder` measures in text units by definition, and `Modifier.size` takes a `Dp`. Converting
through `LocalDensity` is what makes the second follow the first rather than approximate it.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCREEN = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"

EDITS: list[tuple[str, str]] = [
    # 1. One constant for both.
    (
        """@Composable
private fun SheveryCaution(""",
        """/**
 * How large a fork row's ⓘ is, as a multiple of the label's own type size.
 *
 * ⚠ **One number for both rows, at the author's instruction** — *"match that of thedjchi i button
 * size"*. The Thedjchi ⓘ is an inline placeholder inside its label and measures in `em`; the
 * Shevery one is a separate control beside its label and measures in `Dp`. Deriving both from
 * this and from `bodyMedium` is what makes them the same size at every font scale, rather than
 * the same size on one device.
 */
private const val FORK_INFO_EM = 1.2f

@Composable
private fun SheveryCaution(""",
    ),
    # 2. The separate control follows it.
    (
        """    Row(
        // A small gap after the option's name - close enough to read as a continuation of it
        // rather than as a separate control at the end of the row.
        modifier = modifier
            .padding(start = 6.dp)
            .clickable(onClick = onClick)
            .padding(vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Icon(
            modifier = Modifier.size(13.dp),""",
        """    // The Thedjchi row's ⓘ in dp: the same multiple of the same type style, resolved through
    // the current density so the two stay identical when the user changes their font size.
    val infoSize = with(LocalDensity.current) {
        (MaterialTheme.typography.bodyMedium.fontSize * FORK_INFO_EM).toDp()
    }

    Row(
        // A small gap after the option's name - close enough to read as a continuation of it
        // rather than as a separate control at the end of the row.
        modifier = modifier
            .padding(start = 6.dp)
            .clickable(onClick = onClick)
            .padding(vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Icon(
            modifier = Modifier.size(infoSize),""",
    ),
    # 3. And so does the inline one.
    (
        """            placeholder = Placeholder(
                width = 1.2.em,
                height = 1.2.em,""",
        """            placeholder = Placeholder(
                width = FORK_INFO_EM.em,
                height = FORK_INFO_EM.em,""",
    ),
]

IMPORTS = ["import androidx.compose.ui.platform.LocalDensity"]

AFTER = [
    ("private const val FORK_INFO_EM = 1.2f", 1),
    ("Modifier.size(infoSize)", 1),
    ("FORK_INFO_EM.em", 2),
    # The old literals are gone from both.
    ("Modifier.size(13.dp)", 0),
    ("1.2.em", 0),
]


def add_import(text: str, statement: str) -> str:
    if statement in text:
        return text

    lines = text.splitlines(keepends=True)

    indices = [i for i, line in enumerate(lines) if line.startswith("import androidx.")]

    target = next((i for i in indices if lines[i] > statement + "\n"), indices[-1] + 1)

    lines.insert(target, statement + "\n")

    return "".join(lines)


def main() -> int:
    path = ROOT / SCREEN

    if not path.is_file():
        print(f"REFUSED: missing {SCREEN}")
        return 1

    text = path.read_text(encoding="utf-8")

    for old, new in EDITS:
        found = text.count(old)

        if found != 1:
            print(f"REFUSED: {SCREEN}\n  {old.strip().splitlines()[0][:60]!r} matched {found} time(s)")
            return 1

        text = text.replace(old, new, 1)

    text = add_import(text, IMPORTS[0])

    for token, expected in AFTER:
        found = text.count(token)

        if found != expected:
            print(f"REFUSED: {SCREEN}\n  {token!r} occurs {found} time(s), expected {expected}")
            return 1

    for statement in ("import androidx.compose.ui.unit.em", "import androidx.compose.foundation.layout.size"):
        if statement not in text:
            print(f"REFUSED: {SCREEN}\n  {statement!r} is absent")
            return 1

    path.write_text(text, encoding="utf-8")

    print(f"  ok        {SCREEN}  :: both fork ⓘ icons are 1.2em of bodyMedium")
    print(f"\nwrote 1 file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
