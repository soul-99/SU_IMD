#!/usr/bin/env python3
"""v3-r4s — the IMD+ section says EXPERIMENTAL before it says anything else.

    "also put a 'EXPERIMENTAL' description at the start of IMD+ setting section not auto hide
     toggle description, it stays above the toggle label"

His word, verbatim and alone on its line.

## ⚠ Where it goes, and where it deliberately does not

The **first child of the section's body**, above the Auto-hide settings row - so it is read on the
way in, before the label of the thing it is warning about, and it applies to the section rather
than to that one row.

⚠ **Not back into the row's subtitle.** r2b3c put EXPERIMENTAL there and r4-something took it out
again, because a subtitle's job is to say what a tap does. Putting it back would undo that
decision rather than carry out this one; the author's *"not auto hide toggle description"* is
exactly this distinction.

## The one judgement call, and it is small

Drawn in `error`, at `labelMedium`, aligned to the same 16.dp the row titles start at. The colour
is the app's existing idiom for a caution and the caps are the author's; if he wants it in the
quiet description grey the whole change is the `color` line.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCREEN = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"

STRINGS = "feature/settings/src/main/res/values/strings.xml"

TRANSLATIONS = "tools/check_translations.py"

EDITS: list[tuple[str, str, str]] = [
    (
        SCREEN,
        """        ) {
            // A split row: the label opens the page, the switch on the right turns IMD+ on
            // and off without going in. The divider between them is what stops a tap near the
            // switch being a coin toss between the two.
            SplitToggleSetting(
                title = stringResource(R.string.auto_hide),""",
        """        ) {
            // ⚠ **The section's own warning, above the first row rather than inside it.** The
            // author asked for it here and said where it must not be — "not auto hide toggle
            // description" — because a subtitle says what a tap does, and this is about the
            // whole feature. It was in that subtitle once, and was taken out on purpose.
            Text(
                modifier = Modifier.padding(
                    start = 16.dp,
                    end = 16.dp,
                    top = 12.dp,
                    bottom = 4.dp,
                ),
                text = stringResource(R.string.imd_plus_experimental),
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.error,
            )

            // A split row: the label opens the page, the switch on the right turns IMD+ on
            // and off without going in. The divider between them is what stops a tap near the
            // switch being a coin toss between the two.
            SplitToggleSetting(
                title = stringResource(R.string.auto_hide),""",
    ),
    (
        STRINGS,
        """    <string name="auto_hide_setup">""",
        """    <string name="imd_plus_experimental">EXPERIMENTAL</string>
    <string name="auto_hide_setup">""",
    ),
    (
        TRANSLATIONS,
        """    # r4s: Retry, beside Skip on the Display over other apps step.
    "retry",""",
        """    # r4s: Retry, beside Skip on the Display over other apps step.
    "retry",
    # r4s: the IMD+ section's own warning, above its first row.
    "imd_plus_experimental",""",
    ),
]

AFTER = [
    (SCREEN, "R.string.imd_plus_experimental", 1),
    # ⚠ Spelled as only the statement can be: the comment above it names the row's subtitle in
    # prose, and a bare token would have counted that too.
    (SCREEN, "title = stringResource(R.string.auto_hide),", 1),
    (STRINGS, '<string name="imd_plus_experimental">EXPERIMENTAL</string>', 1),
    (TRANSLATIONS, '"imd_plus_experimental",', 1),
]


def main() -> int:
    staged: dict[str, str] = {}

    for relative, old, new in EDITS:
        path = ROOT / relative

        if not path.is_file():
            print(f"REFUSED: missing {relative}")
            return 1

        text = staged.get(relative, path.read_text(encoding="utf-8"))

        found = text.count(old)

        if found != 1:
            head = old.strip().splitlines()[0][:70]

            print(f"REFUSED: {relative}\n  {head!r} matched {found} time(s), expected 1")
            return 1

        staged[relative] = text.replace(old, new, 1)

    for relative, token, expected in AFTER:
        found = staged[relative].count(token)

        if found != expected:
            print(
                f"REFUSED: {relative}\n  {token!r} occurs {found} time(s) after the edits, "
                f"expected {expected}",
            )
            return 1

    # Every name the new lines use was already imported for the rows around them; this is what
    # says so rather than assuming it.
    for statement in (
        "import androidx.compose.material3.Text",
        "import androidx.compose.material3.MaterialTheme",
        "import androidx.compose.foundation.layout.padding",
        "import androidx.compose.ui.res.stringResource",
        "import androidx.compose.ui.unit.dp",
    ):
        if statement not in staged[SCREEN]:
            print(f"REFUSED: {SCREEN}\n  {statement!r} is absent")
            return 1

    for relative, text in staged.items():
        (ROOT / relative).write_text(text, encoding="utf-8")

    print(f"  ok        {SCREEN}  :: EXPERIMENTAL above the IMD+ section's first row")
    print(f"  ok        {STRINGS}  :: the author's word, verbatim")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
