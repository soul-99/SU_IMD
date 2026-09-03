#!/usr/bin/env python3
"""
v3-r8 — take "Only selected ones" a step further back.

The author: *"for both 'only selected ones' make the font less visible (less contrast)"*, and 75%
from the r8 template, checked in both themes before it shipped.

⚠ **An alpha on the token, not a different token.** The note is already a step below the row label
it hangs under — `onSurfaceVariant` against the label's `onSurface` — and reaching for a fourth
colour would be a value this scheme does not have. Fading the one it already uses keeps it in step
with the ⓘ and the open-link arrows through every theme, dynamic ones included, and there is only
one number to move if it turns out too faint on a real screen.

⚠ **The countdown is not touched, and shares the same text style.** `managerNoteStyle()` is the
size; the colour is chosen at each call site, and the countdown's is `primary`. Both of the
author's "both" are this one string in this one row.

Alpha reads differently in the two themes and that is why it was drawn in both: in dark it fades a
light note *towards* the card, in light it fades a dark note towards a light card, which is the
larger perceived step. 75% holds in both.

Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DIALOG = (
    "feature/apps/src/main/kotlin/com/android/geto/feature/apps/dialog/"
    "AndroidSettingsManagerDialog.kt"
)

CONST_OLD = '''private val MANAGER_ROW_INDENT = 16.dp
'''

CONST_NEW = '''private val MANAGER_ROW_INDENT = 16.dp

/**
 * How strongly the scope note under a row is drawn.
 *
 * ⚠ **An alpha on [ManagerSize.rowStyle]'s neighbour token, not a fourth colour.** The note is
 * already a step below its row label — `onSurfaceVariant` against `onSurface` — and the author
 * asked for one more: *"make the font less visible (less contrast)"*. Fading the token it already
 * shares with the ⓘ and the open-link arrows keeps all three in step through every theme, dynamic
 * ones included, where a hand-picked colour would drift out of one.
 *
 * 0.75 is his pick, drawn in both themes before it landed. Alpha is not symmetrical between them —
 * in dark it fades a light note *towards* the card, in light it fades a dark note towards a light
 * card, which is the larger perceived step — and 75 holds in both.
 */
private const val MANAGER_NOTE_ALPHA = 0.75f
'''

NOTE_OLD = '''                Text(
                    text = stringResource(R.string.settings_manager_only_selected),
                    style = managerNoteStyle(),
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
'''

NOTE_NEW = '''                Text(
                    text = stringResource(R.string.settings_manager_only_selected),
                    style = managerNoteStyle(),
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                        .copy(alpha = MANAGER_NOTE_ALPHA),
                )
'''

CHECKS = [
    ("MANAGER_NOTE_ALPHA", 2, "declared once, used once"),
    ("copy(alpha = MANAGER_NOTE_ALPHA)", 1, "one line is faded"),
    # The countdown keeps `primary` and is not this note. If this ever reads 0 the wrong Text
    # was edited.
    ("color = MaterialTheme.colorScheme.primary,", 2, "the countdown and the busy note are intact"),
]


def main() -> int:
    path = ROOT / DIALOG

    original = path.read_text(encoding="utf-8")

    text = original

    for old, new in ((CONST_OLD, CONST_NEW), (NOTE_OLD, NOTE_NEW)):
        if text.count(old) != 1:
            print(f"REFUSED: anchor {old.strip()[:60]!r} matched {text.count(old)} time(s)")
            return 1

        if new in original:
            print("REFUSED: already applied")
            return 1

        text = text.replace(old, new, 1)

    for token, want, why in CHECKS:
        got = text.count(token)

        if got != want:
            print(f"REFUSED: {why} — {token!r} appears {got} time(s), expected {want}")
            return 1

        print(f"  checked  x{got:<3} {token[:50]!r}")

    over = lambda s: {ln for ln in s.split("\n")
                      if len(ln) > 120 and not ln.lstrip().startswith("import ")}

    if over(text) - over(original):
        print("REFUSED: would gain lines over 120 chars")
        return 1

    path.write_text(text, encoding="utf-8")

    print("\n  ok  the scope note is drawn at 75%")

    return 0


if __name__ == "__main__":
    sys.exit(main())
