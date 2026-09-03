#!/usr/bin/env python3
"""v3-r4v — the Icon style row, its dialog, and the repository method behind them.

The companion to `_v3_r4v_icon_style.py`, which stopped at the interface. This adds the override
that satisfies it, the row under **User interface**, and the pop-up.

His three labels go in verbatim: `Icon style`, `Smart adaptive icons`, `System icons`. The one
line under each option is mine, not his — a radio with no explanation would make the choice a
guess — and each is one string to change.

## ⚠ Built on `ThemeDialog`, not on a new shape

The Theme pop-up in this same section is already *"radio group, Cancel, a Save-shaped button"*,
which is what the author asked for. The icon-style dialog mirrors it row for row, so the two
controls two rows apart in the same section behave identically.

⚠ **The draft is held in the dialog and written on Save**, exactly as Theme's is: the pop-up has a
Save button, so nothing may be written by tapping a radio. Cancel leaves the stored value alone.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REPO_IMPL = "data/repository/src/main/kotlin/com/android/geto/data/repository/DefaultUserDataRepository.kt"

DIALOG = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/IconStyleDialog.kt"

SCREEN = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"

VIEW_MODEL = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsViewModel.kt"

STRINGS = "feature/settings/src/main/res/values/strings.xml"

TRANSLATIONS = "tools/check_translations.py"

LICENCE = """/*
 *
 *   Copyright 2026 soul_99 (suIMD)
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
"""

DIALOG_SOURCE = LICENCE + """package com.android.geto.feature.settings.dialog

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.selectableGroup
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.unit.dp
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.domain.model.IconStyle
import com.android.geto.feature.settings.R

/**
 * How app icons are drawn — the author's *"Icon style"*.
 *
 * ⚠ **Built as `ThemeDialog` is, two rows above it in the same section**: a radio group, then
 * Cancel beside the committing button. Two controls in one section that behave differently is a
 * worse outcome than either shape on its own.
 *
 * ⚠ **The choice is a draft until Save.** The author asked for a Save button, and a radio that
 * wrote as it was tapped would make that button decorative — and Cancel a lie.
 */
@Composable
internal fun IconStyleDialog(
    modifier: Modifier = Modifier,
    selected: IconStyle,
    onSave: (IconStyle) -> Unit,
    onDismissRequest: () -> Unit,
) {
    var draft by rememberSaveable(selected) { mutableStateOf(selected) }

    DialogContainer(
        modifier = modifier.verticalScroll(rememberScrollState()),
        onDismissRequest = onDismissRequest,
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(10.dp),
        ) {
            Text(
                modifier = Modifier.padding(10.dp),
                text = stringResource(R.string.icon_style),
                style = MaterialTheme.typography.titleLarge,
            )

            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .selectableGroup(),
            ) {
                IconStyleOption(
                    label = stringResource(R.string.icon_style_smart),
                    note = stringResource(R.string.icon_style_smart_note),
                    selected = draft == IconStyle.SmartAdaptive,
                    onSelect = { draft = IconStyle.SmartAdaptive },
                )

                IconStyleOption(
                    label = stringResource(R.string.icon_style_system),
                    note = stringResource(R.string.icon_style_system_note),
                    selected = draft == IconStyle.System,
                    onSelect = { draft = IconStyle.System },
                )
            }

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(top = 8.dp),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(R.string.cancel))
                }

                TextButton(
                    onClick = {
                        onSave(draft)

                        onDismissRequest()
                    },
                ) {
                    Text(text = stringResource(R.string.save))
                }
            }
        }
    }
}

/**
 * One option, with the line that says what it does.
 *
 * The whole row is the target rather than the button alone — the note is the part most people
 * read, and a row whose explanation is not tappable invites a miss.
 */
@Composable
private fun IconStyleOption(
    label: String,
    note: String,
    selected: Boolean,
    onSelect: () -> Unit,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .selectable(selected = selected, role = Role.RadioButton, onClick = onSelect)
            .padding(horizontal = 16.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        // Null, so TalkBack announces one control for the row rather than two.
        RadioButton(selected = selected, onClick = null)

        Column(modifier = Modifier.padding(start = 10.dp)) {
            Text(text = label, style = MaterialTheme.typography.bodyLarge)

            Text(
                text = note,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}
"""

EDITS: list[tuple[str, str, str]] = [
    (
        REPO_IMPL,
        "    override suspend fun updateFavouriteAppsView(favouriteAppsView: FavouriteAppsView) {",
        """    override suspend fun updateIconStyle(iconStyle: IconStyle) {
        userPreferencesDataSource.updateIconStyle(iconStyle = iconStyle)
    }

    override suspend fun updateFavouriteAppsView(favouriteAppsView: FavouriteAppsView) {""",
    ),
    (
        VIEW_MODEL,
        "    fun updateShizukuForkMode(shizukuForkMode: ShizukuForkMode) {",
        """    fun updateIconStyle(iconStyle: IconStyle) {
        viewModelScope.launch {
            userDataRepository.updateIconStyle(iconStyle = iconStyle)
        }
    }

    fun updateShizukuForkMode(shizukuForkMode: ShizukuForkMode) {""",
    ),
    # ---------------- The row, under Language ----------------
    (
        SCREEN,
        """            SettingsColumn(
                title = stringResource(R.string.language),
                subtitle = languageLabel(languageTag),
                onClick = { showLanguageDialog = true },
            )
        }""",
        """            SettingsColumn(
                title = stringResource(R.string.language),
                subtitle = languageLabel(languageTag),
                onClick = { showLanguageDialog = true },
            )

            SettingsRowDivider()

            // The subtitle is the chosen option's own label, as Theme's is: the row says what
            // it is set to, so the pop-up is for changing it rather than for finding out.
            SettingsColumn(
                title = stringResource(R.string.icon_style),
                subtitle = stringResource(
                    if (userData.iconStyle == IconStyle.SmartAdaptive) {
                        R.string.icon_style_smart
                    } else {
                        R.string.icon_style_system
                    },
                ),
                onClick = { showIconStyleDialog = true },
            )
        }""",
    ),
    # The callback, threaded exactly as onUpdateTheme is: route -> screen -> inner screen.
    (
        SCREEN,
        "        onUpdateTheme = viewModel::updateTheme,",
        "        onUpdateIconStyle = viewModel::updateIconStyle,\n"
        "        onUpdateTheme = viewModel::updateTheme,",
    ),
    (
        SCREEN,
        "    onUpdateTheme: (Theme) -> Unit,\n    onUpdateDynamicTheme",
        "    onUpdateIconStyle: (IconStyle) -> Unit,\n"
        "    onUpdateTheme: (Theme) -> Unit,\n    onUpdateDynamicTheme",
    ),
    (
        SCREEN,
        "    onUpdateDynamicTheme: (Boolean) -> Unit,\n    onUpdateTheme: (Theme) -> Unit,",
        "    onUpdateDynamicTheme: (Boolean) -> Unit,\n"
        "    onUpdateIconStyle: (IconStyle) -> Unit,\n    onUpdateTheme: (Theme) -> Unit,",
    ),
    (
        SCREEN,
        "                    onUpdateTheme = onUpdateTheme,",
        "                    onUpdateIconStyle = onUpdateIconStyle,\n"
        "                    onUpdateTheme = onUpdateTheme,",
    ),
    (
        SCREEN,
        "    if (showThemeDialog) {",
        """    if (showIconStyleDialog) {
        IconStyleDialog(
            selected = userData.iconStyle,
            onSave = onUpdateIconStyle,
            onDismissRequest = { showIconStyleDialog = false },
        )
    }

    if (showThemeDialog) {""",
    ),
    (
        TRANSLATIONS,
        """    # r4v: the other spelling of the two rows whose label follows the unhiding framework.
    "help_path_hide_defaults",
    "help_path_unhide_both",""",
        """    # r4v: the other spelling of the two rows whose label follows the unhiding framework.
    "help_path_hide_defaults",
    "help_path_unhide_both",
    # r4v: Icon style and its two options.
    "icon_style",
    "icon_style_smart",
    "icon_style_smart_note",
    "icon_style_system",
    "icon_style_system_note",""",
    ),
    (
        STRINGS,
        '<string name="section_ui">User interface</string>',
        '<string name="section_ui">User interface</string>\n'
        '    <string name="icon_style">Icon style</string>\n'
        '    <string name="icon_style_smart">Smart adaptive icons</string>\n'
        '    <string name="icon_style_smart_note">Older icons are trimmed and given your device\\\'s own icon shape, so every icon matches.</string>\n'
        '    <string name="icon_style_system">System icons</string>\n'
        '    <string name="icon_style_system_note">Icons are drawn exactly as Android hands them over.</string>',
    ),
]

AFTER = [
    (REPO_IMPL, "override suspend fun updateIconStyle(", 1),
    (VIEW_MODEL, "fun updateIconStyle(", 1),
    # Four: the declaration, the row's onClick, the `if`, and the dismiss. A first draft said
    # three and was refused — the dismiss is easy to forget when counting from the edits alone.
    (SCREEN, "showIconStyleDialog", 4),
    # Six: passed by the route, declared and passed on by the outer screen, declared by the
    # inner one, and handed to the dialog.
    (SCREEN, "onUpdateIconStyle", 6),
    (SCREEN, "R.string.icon_style_smart", 1),
    (SCREEN, "R.string.icon_style_system", 1),
    (STRINGS, 'name="icon_style"', 1),
    (STRINGS, 'name="icon_style_smart_note"', 1),
    (TRANSLATIONS, '"icon_style_smart_note",', 1),
]

# The state and the callback the row and the dialog need, added by hand below because both have
# to land inside a specific function rather than at a file scope an anchor could name.
STATE_ANCHOR = "    var showThemeDialog by rememberSaveable { mutableStateOf(false) }"

STATE_NEW = """    var showThemeDialog by rememberSaveable { mutableStateOf(false) }

    var showIconStyleDialog by rememberSaveable { mutableStateOf(false) }"""

IMPORTS = [
    (REPO_IMPL, "import com.android.geto.domain.model.IconStyle"),
    (VIEW_MODEL, "import com.android.geto.domain.model.IconStyle"),
    (SCREEN, "import com.android.geto.domain.model.IconStyle"),
    (SCREEN, "import com.android.geto.feature.settings.dialog.IconStyleDialog"),
]


def add_import(text: str, statement: str) -> str:
    if statement in text:
        return text

    lines = text.splitlines(keepends=True)

    indices = [i for i, line in enumerate(lines) if line.startswith("import com.android.geto.")]

    if not indices:
        raise SystemExit(f"REFUSED: nowhere to put {statement!r}")

    target = next((i for i in indices if lines[i] > statement + "\n"), indices[-1] + 1)

    lines.insert(target, statement + "\n")

    return "".join(lines)


def main() -> int:
    if (ROOT / DIALOG).exists():
        print(f"REFUSED: {DIALOG} already exists")
        return 1

    staged: dict[str, str] = {}

    for relative, old, new in EDITS:
        path = ROOT / relative

        if not path.is_file():
            print(f"REFUSED: missing {relative}")
            return 1

        text = staged.get(relative, path.read_text(encoding="utf-8"))

        found = text.count(old)

        if found != 1:
            print(f"REFUSED: {relative}\n  {old.strip().splitlines()[0][:70]!r} matched {found} time(s)")
            return 1

        staged[relative] = text.replace(old, new, 1)

    if staged[SCREEN].count(STATE_ANCHOR) != 1:
        print(f"REFUSED: {SCREEN}\n  the dialog-visibility block was not found exactly once")
        return 1

    staged[SCREEN] = staged[SCREEN].replace(STATE_ANCHOR, STATE_NEW, 1)

    for relative, statement in IMPORTS:
        staged[relative] = add_import(staged[relative], statement)

    for relative, token, expected in AFTER:
        found = staged[relative].count(token)

        if found != expected:
            print(f"REFUSED: {relative}\n  {token!r} occurs {found} time(s), expected {expected}")
            return 1

    # ⚠ The row is wired to a callback the screen must already receive. Asserted rather than
    # assumed: a missing parameter here is a build error on the author's machine, not here.
    if "onUpdateIconStyle" not in staged[SCREEN]:
        print(f"REFUSED: {SCREEN}\n  onUpdateIconStyle is not referenced")
        return 1

    # And the two strings the dialog reuses from elsewhere in this module.
    labels = staged[STRINGS]

    for name in ('name="save"', 'name="cancel"'):
        if name not in labels:
            print(f"REFUSED: {STRINGS}\n  {name} is absent; the dialog's buttons need it")
            return 1

    (ROOT / DIALOG).write_text(DIALOG_SOURCE, encoding="utf-8")

    for relative, text in staged.items():
        (ROOT / relative).write_text(text, encoding="utf-8")

    print(f"  ok        {DIALOG}  :: radio group, Cancel and Save, drafted until Save")
    print(f"  ok        {SCREEN}  :: Icon style under Language")
    print(f"\nwrote {1 + len(staged)} file(s), {len(EDITS) + 1} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
