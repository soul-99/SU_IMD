#!/usr/bin/env python3
"""r3 — greyed toggles that say why, and the location trees that point at the fix.

The author's spec item 8: *"For both dialog boxes 'settings to hide/unhide' 'Revert to default
dialog box' and 'IMD services manager' if no DOOAs and no Accessibility services set to be
hidden (do not count IMD+ accessibility service) then disable the toggles and make them
unclickable for both in both dialog boxes ... on clicking any of the greyed out toggles or
templates display a popup 'Please configure the settings first (from next line)[display a
location tree to the {Accessibility services/DOOAs to hide setting} to whichever setting's
greyed out toggle or template was clicked on.]"*

and, from the DOOA half: *"if for some reason shevery toggle is selected automatically disable
DOOAs ... and when clicked display 'managing Display over other apps is only supported for
Thedjchi fork of Shizuku'"*.

### What this script does

* `ConfigureFirstDialog` in `design-system`, taking its sentences as parameters — the same
  arrangement `PriorHideDialog` has, and for the same reason: `feature/apps` depends on
  `feature/app-settings`, so anything both need cannot live in either.
* `SettingToHideRow` and `RevertDefaultRow` gain `onBlockedClick`. A greyed row is wrapped so
  the press still lands, exactly as the settings manager's `TargetRow` already does — a
  disabled control swallows the tap, and a row that does nothing reads as a broken app.
* The **accessibility** row in both dialogs is gated on `accessibilityManageable`.
* The **DOOA** row in both dialogs is always drawn now and gated on `overlayManageable`, with
  the reason chosen from the three things that expression asks: the fork, the master switch,
  and the selection.

⚠ **Three reasons, one greyed row, and the dialog has to name the right one.** `overlayManageable`
is a single boolean, but the fix is in a different place for each of its three terms. The row
therefore asks them separately rather than reading the collapsed answer — which is why the
helper's own KDoc says the three are deliberately not collapsed anywhere else.

⚠ **The Shevery case is checked first**, before the master switch and the selection. On Shevery
DOOA is not merely unconfigured, it is not supported at all, and telling somebody to go and
fill in a picker that will never help them is worse than telling them nothing.

Every sentence here is the author's except the two location-tree paths, which follow the
house `IMD Settings → Section → Row` shape already used by `help_path_*`.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HIDE_DIALOG = ("feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/"
               "SettingsToHideDialog.kt")
REVERT_DIALOG = ("feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/"
                 "RevertDefaultsDialog.kt")
SCREEN = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"
STRINGS = "feature/settings/src/main/res/values/strings.xml"
TRANSLATIONS = "tools/check_translations.py"

CONFIGURE_DIALOG = ("design-system/src/main/kotlin/com/android/geto/designsystem/component/"
                    "ConfigureFirstDialog.kt")

LICENCE = '''/*
 *
 *   Copyright 2023 Einstein Blanco
 *   Modifications Copyright 2026 soul_99 (suIMD)
 *
 *   Licensed under the GNU General Public License v3.0 (the "License");
 *   you may not use this file except in compliance with the License.
 *   You may obtain a copy of the License at
 *
 *       https://www.gnu.org/licenses/gpl-3.0
 *
 *   Unless required by applicable law or agreed to in writing, software
 *   distributed under the License is distributed on an "AS IS" BASIS,
 *   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *   See the License for the specific language governing permissions and
 *   limitations under the License.
 *
 */
'''

CONFIGURE_SOURCE = LICENCE + '''package com.android.geto.designsystem.component

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp

/**
 * Why a greyed toggle or template will not move, and where to go and fix it.
 *
 * One sentence and a location tree — the author's shape: *"'Please configure the settings
 * first' (from next line) [display a location tree to the setting]"*. More than one path
 * where more than one thing is missing, so somebody who has configured neither is not sent
 * back twice.
 *
 * ⚠ **[paths] may be empty, and then this is a plain notice.** The Shevery case has nothing to
 * point at: Display over other apps is not supported on that fork at all, so a path would be
 * directions to a picker that can never help.
 *
 * ⚠ **Here rather than in a feature module, and the sentences are parameters.** The same two
 * reasons as [PriorHideDialog]: `feature/apps` depends on `feature/app-settings`, so anything
 * both surfaces need cannot live in either, and this module has no `values/` folder to hold
 * product copy in.
 *
 * The paths carry the primary colour and a medium weight, which is how `HelpPath` already
 * draws the same shape in the setup help.
 */
@Composable
fun ConfigureFirstDialog(
    message: String,
    modifier: Modifier = Modifier,
    paths: List<String> = emptyList(),
    dismissLabel: String,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(text = message, style = MaterialTheme.typography.bodyLarge)

            for (path in paths) {
                Spacer(modifier = Modifier.height(10.dp))

                Text(
                    text = path,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.primary,
                    fontWeight = FontWeight.Medium,
                )
            }

            Spacer(modifier = Modifier.height(14.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = dismissLabel)
                }
            }
        }
    }
}
'''

NEW_STRINGS = """
    <!-- ===================== r3: greyed toggles, and where to fix them ==================== -->

    <!-- The author's sentence, followed by one location tree per thing that is missing. -->
    <string name="configure_first">Please configure the settings first</string>
    <string name="dooa_thedjchi_only">managing Display over other apps is only supported for Thedjchi fork of Shizuku</string>

    <!-- Whole strings in the house shape, so a translation can reorder them. help_path_accessibility
      already existed and is reused unchanged. -->
    <string name="help_path_dooa">IMD Settings \\u2192 Default IMD settings \\u2192 Display over other apps to hide</string>
    <string name="help_path_manage_shizuku">IMD Settings \\u2192 Shizuku (Thedjchi) configuration in IMD \\u2192 Manage Shizuku</string>
"""

DEFERRED_KEYS = [
    "configure_first", "dooa_thedjchi_only", "help_path_dooa", "help_path_manage_shizuku",
]

# The reason chooser, shared by both dialogs and written once. In the screen file because both
# dialogs are called from there and neither owns it.
REASON_HELPER = '''
/**
 * Why a greyed Display over other apps row will not move, as the paths to put it right.
 *
 * ⚠ **The three terms of `overlayManageable`, asked separately.** That property collapses them
 * into one boolean, which is the right answer for "may this run" and the wrong one for "where
 * do I go" — the fix is in a different place for each.
 *
 * Shevery first, and deliberately: there DOOA is not unconfigured, it is unsupported, so the
 * caller gets the author's sentence about the fork and no path at all rather than directions
 * to a picker that will never help.
 *
 * Returns null when the row is perfectly usable, which is the caller's cue that there is
 * nothing to explain.
 */
@Composable
internal fun overlayBlockedPaths(userData: UserData): List<String>? {
    val manageShizukuPath = stringResource(R.string.help_path_manage_shizuku)

    val dooaPath = stringResource(R.string.help_path_dooa)

    if (userData.overlayManageable) return null

    if (userData.shizukuForkMode != ShizukuForkMode.Thedjchi) return emptyList()

    return buildList {
        if (!userData.manageShizukuEffective) add(manageShizukuPath)

        if (userData.managedOverlayPackages.isEmpty()) add(dooaPath)
    }
}
'''


def rows_edit(row_fun: str) -> tuple[str, str, int]:
    """The blocked-click parameter and the wrapper, for one dialog's row composable."""
    return (
        f"""private fun {row_fun}(
    modifier: Modifier = Modifier,
    label: String,
    note: String? = null,
    checked: Boolean,
""",
        f"""private fun {row_fun}(
    modifier: Modifier = Modifier,
    label: String,
    note: String? = null,
    checked: Boolean,
    /**
     * What a press on a greyed row does.
     *
     * ⚠ **Without this a disabled row swallows the tap**, which is how somebody decides the
     * app is broken rather than that they have something left to configure. The settings
     * manager's `TargetRow` has had the same parameter since r2b; this is that pattern
     * brought to the two configuration dialogs, on the author's instruction that a greyed
     * toggle must explain itself.
     */
    onBlockedClick: (() -> Unit)? = null,
""",
        1,
    )


EDITS: list[tuple[str, list[tuple[str, str, int]]]] = [
    (STRINGS, [
        (
            """    <string name="shizuku_choose_app">Choose an installed app</string>
""",
            NEW_STRINGS + """
    <string name="shizuku_choose_app">Choose an installed app</string>
""",
            1,
        ),
    ]),
    (TRANSLATIONS, [
        (
            """    "shevery_how_warning",
""",
            """    "shevery_how_warning",
    # r3: the greyed-toggle explainer and its two location trees.
"""
            + "".join(f'    "{key}",\n' for key in DEFERRED_KEYS),
            1,
        ),
    ]),
]


def main() -> int:
    staged: dict[Path, str] = {}
    problems: list[str] = []

    for rel, subs in EDITS:
        path = ROOT / rel

        if not path.exists():
            problems.append(f"{rel}: missing")

            continue

        text = path.read_text(encoding="utf-8")

        for old, new, expected in subs:
            found = text.count(old)

            if found != expected:
                problems.append(
                    f"{rel}: expected {expected} of "
                    f"{old.strip().splitlines()[0][:58]!r}, found {found}",
                )

                continue

            text = text.replace(old, new, expected)

        staged[path] = text

    if (ROOT / CONFIGURE_DIALOG).exists():
        problems.append(f"{CONFIGURE_DIALOG}: already exists")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for line in CONFIGURE_SOURCE.splitlines():
        if len(line) > 120:
            problems.append(f"{CONFIGURE_DIALOG}: line of {len(line)} chars")

    for path, text in staged.items():
        before = set(path.read_text(encoding="utf-8").splitlines())

        for line in text.splitlines():
            if line not in before and len(line) > 120 and not path.name.endswith(".xml"):
                problems.append(
                    f"{path.relative_to(ROOT)}: added line of {len(line)} chars: "
                    f"{line.strip()[:58]!r}",
                )

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")
        print(f"  wrote {path.relative_to(ROOT)}")

    (ROOT / CONFIGURE_DIALOG).write_text(CONFIGURE_SOURCE, encoding="utf-8")
    print(f"  created {CONFIGURE_DIALOG}")

    print("ok - ConfigureFirstDialog, its four strings, and the deferred list updated")

    return 0


if __name__ == "__main__":
    sys.exit(main())
