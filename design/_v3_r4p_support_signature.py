#!/usr/bin/env python3
"""v3-r4p — the Support dialog is signed.

    "in the support this project add this to bottom right of dialog '- soul_99[from next line]
     (Dr. Utkarsh Rajput)' but start s of soul_99 where D of Dr. starts"
    "make s aligned with ("

Template `design/out/support_signature.png`, approved.

## ⚠ The alignment is what decides the layout

The two readings differ by one glyph, and the author settled it: the **s** of *soul_99* sits over
the **(** of *(Dr.* - so the two lines' first characters share a left edge and the dash hangs
outside it.

That is a `Row` whose dash is its own `Text` and whose two lines are a `Column` beside it: the
column has one left edge, both lines start at it, and the dash sits to its left. Nothing about
either string is padded or measured, so it holds at any text size and in any font the reader has
set - which a hand-computed offset would not.

## ⚠ Three resources, all translatable="false"

A name is a name. Marking them untranslatable keeps them out of the eleven locale files and out
of `tools/check_translations.py`'s "every name in the English file is present" - so this adds
nothing to the translation pass, which is the author's to run.

⚠ **The dash carries no trailing space**, and that is deliberate: aapt strips trailing whitespace
from an unquoted string resource, so a space typed there never reaches the screen. The gap is a
`Spacer`, which is the same fix `shizukuRikkaRecommendation` already documents for the same trap.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DIALOG = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/SupportDialog.kt"

STRINGS = "feature/settings/src/main/res/values/strings.xml"

EDITS: list[tuple[str, str, str]] = [
    (
        STRINGS,
        """    <string name="support_share_message">""",
        """    <!--
      The author's signature at the foot of the dialog. Names, so untranslatable - and the dash
      carries no trailing space, because aapt would strip it; the gap is a Spacer.
    -->
    <string name="support_signature_dash" translatable="false">-</string>
    <string name="support_signature_name" translatable="false">soul_99</string>
    <string name="support_signature_real_name" translatable="false">(Dr. Utkarsh Rajput)</string>
    <string name="support_share_message">""",
    ),
    (
        DIALOG,
        """            SupportPoint(number = 5, text = stringResource(R.string.support_point_contribute))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(R.string.close))
                }
            }""",
        """            SupportPoint(number = 5, text = stringResource(R.string.support_point_contribute))

            Spacer(modifier = Modifier.height(16.dp))

            Signature()

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(R.string.close))
                }
            }""",
    ),
    (
        DIALOG,
        """/** One paragraph of the note, with a little air under it so the four read as separate. */""",
        """/**
 * The author's signature, at the foot of his own note.
 *
 * ⚠ **The dash hangs outside the block.** The author's rule is that the **s** of *soul_99* starts
 * where the **(** of *(Dr.* starts, so the two lines share a left edge and the dash sits to the
 * left of it - which is a `Row` of the dash beside a `Column` of the two lines, not two lines
 * with an offset computed from a glyph width. Nothing here measures text, so it holds at any
 * font scale.
 *
 * Right-aligned as a block, so the whole thing sits at the foot of the dialog on the same side
 * as **Close**.
 */
@Composable
private fun Signature() {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(bottom = 4.dp),
        horizontalArrangement = Arrangement.End,
    ) {
        Text(
            text = stringResource(R.string.support_signature_dash),
            style = MaterialTheme.typography.bodyMedium,
        )

        // The gap the dash's own resource cannot carry - see the comment beside it.
        Spacer(modifier = Modifier.width(4.dp))

        Column {
            Text(
                text = stringResource(R.string.support_signature_name),
                style = MaterialTheme.typography.bodyMedium,
            )

            Text(
                text = stringResource(R.string.support_signature_real_name),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

/** One paragraph of the note, with a little air under it so the four read as separate. */""",
    ),
]

AFTER = [
    (STRINGS, 'name="support_signature_dash" translatable="false"', 1),
    (STRINGS, 'name="support_signature_name" translatable="false"', 1),
    (STRINGS, 'name="support_signature_real_name" translatable="false"', 1),
    (STRINGS, "support_share_message", 1),
    (DIALOG, "private fun Signature()", 1),
    (DIALOG, "Signature()", 2),
    (DIALOG, "R.string.support_signature_dash", 1),
    (DIALOG, "R.string.support_signature_name", 1),
    (DIALOG, "R.string.support_signature_real_name", 1),
    # Close is still the last thing in the dialog, exactly once.
    (DIALOG, "R.string.close", 1),
]

# Everything the new composable reaches for. The module does not compile here, so each is
# checked against the file's own import block rather than assumed.
NEEDED = [
    "import androidx.compose.foundation.layout.Arrangement",
    "import androidx.compose.foundation.layout.Column",
    "import androidx.compose.foundation.layout.Row",
    "import androidx.compose.foundation.layout.Spacer",
    "import androidx.compose.foundation.layout.fillMaxWidth",
    "import androidx.compose.foundation.layout.height",
    "import androidx.compose.foundation.layout.padding",
    "import androidx.compose.foundation.layout.width",
    "import androidx.compose.material3.MaterialTheme",
    "import androidx.compose.material3.Text",
    "import androidx.compose.runtime.Composable",
    "import androidx.compose.ui.Modifier",
    "import androidx.compose.ui.res.stringResource",
    "import androidx.compose.ui.unit.dp",
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

    for statement in NEEDED:
        if statement not in staged[DIALOG]:
            print(f"REFUSED: {DIALOG}\n  the signature needs {statement!r}, which is absent")
            return 1

    for relative, text in staged.items():
        (ROOT / relative).write_text(text, encoding="utf-8")

    print(f"  ok        {STRINGS}  :: three untranslatable signature resources")
    print(f"  ok        {DIALOG}  :: signed, dash hanging, s over (")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
