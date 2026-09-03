/*
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
package com.android.geto.feature.settings.dialog

import androidx.compose.foundation.clickable
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
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.designsystem.component.GetoCheckbox
import com.android.geto.feature.settings.R

/**
 * Which of IMD's two extra entries appear in the app drawer.
 *
 * The author's r11 instruction: *"I want to give user to decide which ones to show, by default
 * only settings manager is shown on install, add a new setting under settings manager options
 * named 'App drawer shortcuts' with a dialog box on click and save button, checkboxes 'Settings
 * manager' and 'Hide/unhide Settings'"*.
 *
 * ⚠ **A draft, committed by Save, and no Cancel** — the shape [ManagerRowsDialog] and
 * `SettingsToHideDialog` already have, so the three read the same way. Ticks move local state;
 * Save writes both and closes; a tap outside or a back press discards.
 *
 * ⚠ **Nothing ticked is allowed here, unlike the manager's own dialog.** There the last tick is
 * refused because an empty manager is the one screen someone opens *because* developer options
 * are already off. Here, unticking both simply leaves IMD with the one launcher entry every app
 * has — its own — which is a reasonable thing to want and takes nothing away.
 *
 * ⚠ **What Save writes is a preference, not a component state.** `DrawerShortcuts` in `:app`
 * collects the preference and enables or disables the aliases; this dialog never touches the
 * package manager, and the two Hide/unhide aliases are one tick here because which of the pair is
 * enabled is decided by the device's state rather than by the user.
 */
@Composable
internal fun AppDrawerShortcutsDialog(
    modifier: Modifier = Modifier,
    manager: Boolean,
    hideUnhide: Boolean,
    onDismissRequest: () -> Unit,
    onUpdateDrawerShortcuts: (manager: Boolean, hideUnhide: Boolean) -> Unit,
) {
    // Keyed on the stored pair, so a re-emission of user data while the dialog is open — which a
    // write from anywhere else in the app can cause — does not wipe ticks made since it opened.
    var draftManager by remember(manager) { mutableStateOf(manager) }

    var draftHideUnhide by remember(hideUnhide) { mutableStateOf(hideUnhide) }

    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = stringResource(R.string.drawer_shortcuts_entry),
                style = MaterialTheme.typography.titleLarge,
            )

            Spacer(modifier = Modifier.height(12.dp))

            DrawerShortcutRow(
                label = stringResource(R.string.drawer_shortcut_manager),
                checked = draftManager,
                onCheckedChange = { draftManager = it },
            )

            DrawerShortcutRow(
                label = stringResource(R.string.drawer_shortcut_hide_unhide),
                checked = draftHideUnhide,
                onCheckedChange = { draftHideUnhide = it },
            )

            Spacer(modifier = Modifier.height(12.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(
                    onClick = {
                        onUpdateDrawerShortcuts(draftManager, draftHideUnhide)

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
 * One row: a checkbox and its label, the whole of it taking the press.
 *
 * The same shape `ManagerRowCheckbox` has, minus the indent — there is no nesting to draw here.
 */
@Composable
private fun DrawerShortcutRow(
    label: String,
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onCheckedChange(!checked) }
            .padding(vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        GetoCheckbox(checked = checked, onCheckedChange = onCheckedChange)

        Text(
            modifier = Modifier.padding(start = 8.dp),
            text = label,
            style = MaterialTheme.typography.bodyLarge,
        )
    }
}
