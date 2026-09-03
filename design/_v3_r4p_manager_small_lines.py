#!/usr/bin/env python3
"""v3-r4p — the settings manager gets one small line under two rows, and the countdown joins it.

    "in settings manager display description under accessib. and DOOA toggle in very small font
     but still legible to read 'Only selected ones'"
    "2 but also make shizuku/shevery countdown lines to this small size"

Template `design/out/manager_only_selected.png`, with the author's answer of **10sp** rather than
the 11sp drawn.

## ⚠ 10sp is not a Material type step, so it is a copy of one

`labelSmall` is 11sp and is the smallest style the scheme has. Rather than inventing a style or
reaching past the theme, both lines take `labelSmall.copy(fontSize = ..., lineHeight = ...)` from
one shared `managerNoteStyle()`, so the two cannot drift apart and there is exactly one place to
change if 10sp turns out to be too small on a device.

⚠ **The line height has to move with the size.** `labelSmall` carries a 16sp line height; left
alone, a 10sp line would sit in a 16sp box and the "very small" would come back as a gap rather
than as small type.

## ⚠ What stays removed

    // The two scope descriptions that used to sit here — "only services selected in
    // the IMD app settings are managed" and its overlay twin — are gone at the
    // author's instruction.

Those two sentences are not coming back; this is a four-word line, which is why it can sit under
the row without becoming the row. Their strings stay in the tree, untouched and still reachable
from the ⓘ dialog, exactly as that comment says.

## The new string

`settings_manager_only_selected`, added to `DEFERRED` in `tools/check_translations.py` under the
author's standing rule that translation happens in one pass when everything is built - not copied
into eleven locales.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DIALOG = "feature/apps/src/main/kotlin/com/android/geto/feature/apps/dialog/AndroidSettingsManagerDialog.kt"

STRINGS = "feature/apps/src/main/res/values/strings.xml"

TRANSLATIONS = "tools/check_translations.py"

EDITS: list[tuple[str, str, str]] = [
    # 1. The string.
    (
        STRINGS,
        # ⚠ The whole opening tag, not a prefix of it: "settings_manager_open" is also a
        # prefix of "settings_manager_open_settings" eleven lines above, and the first draft
        # matched both.
        """    <string name="settings_manager_open">""",
        """    <!-- Under the two rows that read a selection list. Deliberately four words. -->
    <string name="settings_manager_only_selected">Only selected ones</string>
    <string name="settings_manager_open">""",
    ),
    # 2. The line itself, replacing the comment that records why the long ones went.
    (
        DIALOG,
        """            // The two scope descriptions that used to sit here — "only services selected in
            // the IMD app settings are managed" and its overlay twin — are gone at the
            // author's instruction. Their strings are kept: the ⓘ dialog covers the same
            // ground, and a removed line is cheaper to put back than to re-translate.
        }""",
        """            // The two scope descriptions that used to sit here — "only services selected in
            // the IMD app settings are managed" and its overlay twin — are gone at the
            // author's instruction. Their strings are kept: the ⓘ dialog covers the same
            // ground, and a removed line is cheaper to put back than to re-translate.
            //
            // ⚠ **What is here instead is four words, and that is the difference.** The
            // sentences that were removed explained the scope; this only names it, at a size
            // that reads as a footnote to the row rather than as a second line of the row.
            // Only the two targets that actually read a selection list carry it.
            if (target.readsASelection) {
                Text(
                    text = stringResource(R.string.settings_manager_only_selected),
                    style = managerNoteStyle(),
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }""",
    ),
    # 3. The countdown takes the same size.
    (
        DIALOG,
        """                            sheveryWait,
                        ),
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.primary,
                    )""",
        """                            sheveryWait,
                        ),
                        // The author's "make shizuku/shevery countdown lines to this small
                        // size" - the same style as the note above, so the two small lines in
                        // this dialog cannot end up at two different sizes.
                        style = managerNoteStyle(),
                        color = MaterialTheme.colorScheme.primary,
                    )""",
    ),
    # 4. The style, and the predicate, declared beside the row they serve.
    (
        DIALOG,
        """@Composable
private fun TargetRow(""",
        """/**
 * The size of the two small lines in this dialog: the scope note under a row, and the fork
 * start countdown.
 *
 * ⚠ **10sp is not one of Material's steps**, so this is `labelSmall` - the smallest that is, at
 * 11sp - copied down rather than a style invented beside the scheme. One function for both, so
 * "very small" cannot come to mean two different things in one dialog.
 *
 * ⚠ **The line height moves with it.** `labelSmall` carries 16sp; a 10sp line left in a 16sp box
 * reads as a gap rather than as small type.
 */
@Composable
private fun managerNoteStyle() = MaterialTheme.typography.labelSmall.copy(
    fontSize = 10.sp,
    lineHeight = 13.sp,
)

/**
 * Whether this target manages a list the user chose rather than the whole of something.
 *
 * The two that do are the ones the author asked to carry *Only selected ones*: accessibility
 * services and display-over-other-apps are both driven by a selection made in IMD's settings,
 * where Shizuku and the debugging toggles are all-or-nothing.
 */
private val ManualRevertTarget.readsASelection: Boolean
    get() = this == ManualRevertTarget.AccessibilityServices ||
        this == ManualRevertTarget.DisplayOverOtherApps

@Composable
private fun TargetRow(""",
    ),
    # 5. `sp` is new to this file - the row's sizes are all dp.
    (
        DIALOG,
        """import androidx.compose.ui.unit.dp""",
        """import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp""",
    ),
    # 6. The deferral, under the author's standing rule.
    (
        TRANSLATIONS,
        """    # r3: the greyed-toggle explainer and its two location trees.""",
        """    # r4p: the settings manager's four-word scope note.
    "settings_manager_only_selected",
    # r3: the greyed-toggle explainer and its two location trees.""",
    ),
]

AFTER = [
    (STRINGS, 'name="settings_manager_only_selected"', 1),
    (DIALOG, "managerNoteStyle()", 3),
    (DIALOG, "readsASelection", 2),
    (DIALOG, "R.string.settings_manager_only_selected", 1),
    # ⚠ Six others in this file still use bodyMedium and are none of this script's business.
    # The first draft asserted zero on the belief that the countdown was the only one, and its
    # own assertion said otherwise - which is what the assertion is for. What has to be gone is
    # the countdown's use of it, checked below against its own surrounding lines rather than by
    # a file-wide count.
    (DIALOG, "typography.bodyMedium,", 6),
    (
        DIALOG,
        "sheveryWait,\n                        ),\n"
        "                        style = MaterialTheme.typography.bodyMedium,",
        0,
    ),
    (DIALOG, "sheveryWait,\n                        ),\n                        //", 1),
    (TRANSLATIONS, '"settings_manager_only_selected"', 1),
]

NEEDED = [
    "import androidx.compose.ui.unit.sp",
    "import androidx.compose.material3.Text",
    "import androidx.compose.material3.MaterialTheme",
    "import androidx.compose.ui.res.stringResource",
    "import com.android.geto.domain.model.ManualRevertTarget",
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
            print(f"REFUSED: {DIALOG}\n  {statement!r} is absent")
            return 1

    for relative, text in staged.items():
        (ROOT / relative).write_text(text, encoding="utf-8")

    print(f"  ok        {STRINGS}  :: settings_manager_only_selected")
    print(f"  ok        {DIALOG}  :: the note and the countdown share one 10sp style")
    print(f"  ok        {TRANSLATIONS}  :: deferred, not copied into eleven locales")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
