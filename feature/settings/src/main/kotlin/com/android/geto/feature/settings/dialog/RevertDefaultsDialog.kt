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
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
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
    shizukuConfigured: Boolean,
    manageOverlay: Boolean,
    onDismissRequest: () -> Unit,
    onUpdateRevertDefaults: (Map<ManualRevertTarget, Boolean>) -> Unit,
) {
    // The full map, overlay entry included, even when that row is not drawn - the same
    // reasoning as in SettingsToHideDialog: the draft is what gets saved.
    var draft by remember(states) { mutableStateOf(states) }

    // Each row sets only itself. Shizuku used to drag USB debugging with it and vice versa,
    // which meant a tap could silently undo a choice the user had made two rows up.
    val toggle = { target: ManualRevertTarget, enabled: Boolean ->
        draft = draft + (target to enabled)
    }

    SettingsPage(
        modifier = modifier,
        title = stringResource(R.string.revert_defaults),
        onDismissRequest = onDismissRequest,
        actions = {
            TextButton(
                onClick = {
                    onUpdateRevertDefaults(draft)

                    onDismissRequest()
                },
            ) {
                Text(text = stringResource(R.string.save))
            }
        },
    ) {
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
            note = stringResource(R.string.revert_defaults_accessibility_note),
            checked = draft[ManualRevertTarget.AccessibilityServices] == true,
            onCheckedChange = { toggle(ManualRevertTarget.AccessibilityServices, it) },
        )

        RevertDefaultRow(
            label = stringResource(R.string.revert_defaults_shizuku),
            note = stringResource(R.string.revert_defaults_shizuku_note),
            checked = draft[ManualRevertTarget.Shizuku] == true,
            onCheckedChange = { toggle(ManualRevertTarget.Shizuku, it) },
        )

        // Shown only once overlay management has been switched on in Advanced. Hiding the
        // row does not abandon anything already hidden: a revert still hands overlay access
        // back to apps IMD took it from, whatever this switch says - see
        // UserData.effectiveRevertDefaults.
        if (manageOverlay) {
            RevertDefaultRow(
                label = stringResource(R.string.revert_defaults_display_over_other_apps),
                note = if (shizukuConfigured) {
                    stringResource(R.string.revert_defaults_overlay_note)
                } else {
                    stringResource(R.string.overlay_needs_shizuku_configured)
                },
                checked = draft[ManualRevertTarget.DisplayOverOtherApps] == true &&
                    shizukuConfigured,
                enabled = shizukuConfigured,
                onCheckedChange = { toggle(ManualRevertTarget.DisplayOverOtherApps, it) },
            )
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
    enabled: Boolean = true,
    onCheckedChange: (Boolean) -> Unit,
) {
    val contentColour = if (enabled) {
        MaterialTheme.colorScheme.onSurface
    } else {
        MaterialTheme.colorScheme.onSurface.copy(alpha = 0.38f)
    }

    Row(
        modifier = modifier
            .fillMaxWidth()
            .clickable(enabled = enabled) { onCheckedChange(!checked) }
            .padding(horizontal = 10.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = label,
                style = MaterialTheme.typography.bodyLarge,
                color = contentColour,
            )

            if (note != null) {
                Spacer(modifier = Modifier.height(4.dp))

                Text(
                    text = note,
                    style = MaterialTheme.typography.bodySmall,
                    color = contentColour,
                )
            }
        }

        Switch(checked = checked, enabled = enabled, onCheckedChange = onCheckedChange)
    }
}
