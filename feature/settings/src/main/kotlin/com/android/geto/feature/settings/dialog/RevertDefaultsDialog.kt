/*
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
package com.android.geto.feature.settings.dialog

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Switch
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
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.feature.settings.R

/**
 * What "Revert to default" should leave each target set to.
 *
 * A configuration screen, not a control panel: nothing here changes the device. The switches
 * describe the state the user wants restored, which is why they stay where they are put even
 * when the device is currently the other way round.
 */
@Composable
internal fun RevertDefaultsDialog(
    modifier: Modifier = Modifier,
    states: Map<ManualRevertTarget, Boolean>,
    onDismissRequest: () -> Unit,
    onUpdateRevertDefaults: (Map<ManualRevertTarget, Boolean>) -> Unit,
) {
    var draft by remember(states) { mutableStateOf(states) }

    // Each row sets only itself. Shizuku used to drag USB debugging with it and vice versa,
    // which meant a tap could silently undo a choice the user had made two rows up.
    val toggle = { target: ManualRevertTarget, enabled: Boolean ->
        draft = draft + (target to enabled)
    }

    DialogContainer(
        modifier = modifier,
        onDismissRequest = onDismissRequest,
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .verticalScroll(rememberScrollState())
                .padding(10.dp),
        ) {
            Text(
                modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
                text = stringResource(R.string.revert_defaults),
                style = MaterialTheme.typography.titleLarge,
            )

            // Says when this runs, which the title does not: "Revert to default" is the
            // name of five different buttons, and someone arriving here from the settings
            // list has just read "Settings to hide" one row above.
            Text(
                modifier = Modifier.padding(horizontal = 10.dp),
                text = stringResource(R.string.revert_defaults_description),
                style = MaterialTheme.typography.bodyMedium,
            )

            Spacer(modifier = Modifier.height(4.dp))

            RevertDefaultRow(
                label = stringResource(R.string.revert_defaults_developer_settings),
                checked = draft[ManualRevertTarget.DeveloperSettings] == true,
                onCheckedChange = { toggle(ManualRevertTarget.DeveloperSettings, it) },
            )

            RevertDefaultRow(
                label = stringResource(R.string.revert_defaults_usb_debugging),
                checked = draft[ManualRevertTarget.UsbDebugging] == true,
                onCheckedChange = { toggle(ManualRevertTarget.UsbDebugging, it) },
            )

            RevertDefaultRow(
                label = stringResource(R.string.revert_defaults_wireless_debugging),
                checked = draft[ManualRevertTarget.WirelessDebugging] == true,
                onCheckedChange = { toggle(ManualRevertTarget.WirelessDebugging, it) },
            )

            RevertDefaultRow(
                label = stringResource(R.string.revert_defaults_accessibility_services),
                note = stringResource(R.string.revert_defaults_accessibility_all_note),
                checked = draft[ManualRevertTarget.AccessibilityServices] == true,
                onCheckedChange = { toggle(ManualRevertTarget.AccessibilityServices, it) },
            )

            RevertDefaultRow(
                label = stringResource(R.string.revert_defaults_shizuku),
                note = stringResource(R.string.revert_defaults_shizuku_note),
                checked = draft[ManualRevertTarget.Shizuku] == true,
                onCheckedChange = { toggle(ManualRevertTarget.Shizuku, it) },
            )

            RevertDefaultRow(
                label = stringResource(R.string.revert_defaults_display_over_other_apps),
                note = stringResource(R.string.revert_defaults_overlay_note),
                checked = draft[ManualRevertTarget.DisplayOverOtherApps] == true,
                onCheckedChange = { toggle(ManualRevertTarget.DisplayOverOtherApps, it) },
            )

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(10.dp),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(
                    onClick = {
                        onUpdateRevertDefaults(draft)

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
 * One target's row.
 *
 * [note] is the small print under a label, for the two rows whose switch does something
 * narrower or broader than the label alone suggests: accessibility services, which governs
 * only the services picked elsewhere in settings rather than every service on the device,
 * and Shizuku, which brings a debugging transport up with it.
 */
@Composable
private fun RevertDefaultRow(
    modifier: Modifier = Modifier,
    label: String,
    note: String? = null,
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit,
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .clickable { onCheckedChange(!checked) }
            .padding(horizontal = 10.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(text = label, style = MaterialTheme.typography.bodyLarge)

            if (note != null) {
                Spacer(modifier = Modifier.height(4.dp))

                Text(text = note, style = MaterialTheme.typography.bodySmall)
            }
        }

        Switch(checked = checked, onCheckedChange = onCheckedChange)
    }
}
