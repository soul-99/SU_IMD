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
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Checkbox
import androidx.compose.material3.Icon
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
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.unit.dp
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.designsystem.icon.GetoIcons
import com.android.geto.designsystem.component.emphasised
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.feature.settings.R

/**
 * What gets switched off on the way into any app.
 *
 * Checkboxes rather than the switches the revert dialog uses, and the difference is not
 * decorative: this is one list being selected from, where every box means the same kind of
 * thing, while the revert dialog's rows each describe a state — on *or* off — that a target
 * should be left in. A switch reads as "this will be turned on", which is the opposite of
 * what a ticked box means here.
 *
 * Nothing here changes the device. It is read the next time an app is launched.
 */
@Composable
internal fun SettingsToHideDialog(
    modifier: Modifier = Modifier,
    states: Map<ManualRevertTarget, Boolean>,
    onDismissRequest: () -> Unit,
    onUpdateSettingsToHide: (Map<ManualRevertTarget, Boolean>) -> Unit,
) {
    var draft by remember(states) { mutableStateOf(states) }

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
                text = stringResource(R.string.settings_to_hide_title),
                style = MaterialTheme.typography.titleLarge,
            )

            Text(
                modifier = Modifier.padding(horizontal = 10.dp),
                text = stringResource(R.string.settings_to_hide_description),
                style = MaterialTheme.typography.bodyMedium,
            )

            Spacer(modifier = Modifier.height(8.dp))

            SettingToHideRow(
                label = stringResource(R.string.revert_defaults_developer_settings),
                checked = draft[ManualRevertTarget.DeveloperSettings] == true,
                onCheckedChange = { toggle(ManualRevertTarget.DeveloperSettings, it) },
            )

            SettingToHideRow(
                label = stringResource(R.string.revert_defaults_usb_debugging),
                note = stringResource(R.string.settings_to_hide_usb_note),
                checked = draft[ManualRevertTarget.UsbDebugging] == true,
                onCheckedChange = { toggle(ManualRevertTarget.UsbDebugging, it) },
            )

            SettingToHideRow(
                label = stringResource(R.string.revert_defaults_wireless_debugging),
                checked = draft[ManualRevertTarget.WirelessDebugging] == true,
                onCheckedChange = { toggle(ManualRevertTarget.WirelessDebugging, it) },
            )

            SettingToHideRow(
                // Deliberately the same string the revert dialog uses for this note: the
                // caveat is about which services this app manages at all, so it is the
                // same fact in both places and must not be able to drift.
                label = stringResource(R.string.revert_defaults_accessibility_services),
                note = stringResource(R.string.revert_defaults_accessibility_note),
                checked = draft[ManualRevertTarget.AccessibilityServices] == true,
                onCheckedChange = { toggle(ManualRevertTarget.AccessibilityServices, it) },
            )

            Spacer(modifier = Modifier.height(8.dp))

            InfoLine(text = AnnotatedString(stringResource(R.string.settings_to_hide_info_all)))

            InfoLine(
                text = emphasised(
                    text = stringResource(R.string.settings_to_hide_info_shizuku),
                    names = listOf(stringResource(R.string.settings_to_hide_name_shizuku_hide)),
                ),
            )

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(10.dp),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(
                    onClick = {
                        onUpdateSettingsToHide(draft)

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
 * One target's row. [note] carries the small print for the two whose effect reaches past
 * what the label says: USB debugging, which takes the Shizuku service down with it, and
 * accessibility services, which touches only the services picked elsewhere in settings.
 */
@Composable
private fun SettingToHideRow(
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

        Checkbox(checked = checked, onCheckedChange = onCheckedChange)
    }
}

/**
 * A note that is about the list as a whole rather than about one row.
 *
 * Marked with an information icon rather than indented or italicised, so it cannot be read
 * as another item to tick — the first of these is specifically warning against ticking
 * only one of them.
 */
@Composable
private fun InfoLine(
    modifier: Modifier = Modifier,
    text: AnnotatedString,
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .padding(horizontal = 10.dp, vertical = 6.dp),
    ) {
        Icon(
            modifier = Modifier.size(16.dp),
            imageVector = GetoIcons.Info,
            contentDescription = null,
            tint = MaterialTheme.colorScheme.onSurfaceVariant,
        )

        Spacer(modifier = Modifier.width(8.dp))

        Text(
            text = text,
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}
