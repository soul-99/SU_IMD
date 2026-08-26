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
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.unit.dp
import com.android.geto.designsystem.component.emphasised
import com.android.geto.designsystem.icon.GetoIcons
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
    shizukuConfigured: Boolean,
    manageOverlay: Boolean,
    onDismissRequest: () -> Unit,
    onUpdateSettingsToHide: (Map<ManualRevertTarget, Boolean>) -> Unit,
) {
    // The full map, overlay entry included, even when that row is not drawn. The draft is
    // what gets saved, so dropping the entry while the feature is switched off would quietly
    // clear a choice made while it was on and hand it back unticked later.
    var draft by remember(states) { mutableStateOf(states) }

    val toggle = { target: ManualRevertTarget, enabled: Boolean ->
        draft = draft + (target to enabled)
    }

    SettingsPage(
        modifier = modifier,
        title = stringResource(R.string.settings_to_hide_title),
        onDismissRequest = onDismissRequest,
        actions = {
            TextButton(
                onClick = {
                    onUpdateSettingsToHide(draft)

                    onDismissRequest()
                },
            ) {
                Text(text = stringResource(R.string.save))
            }
        },
    ) {
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
            // A different string from the revert dialog's, unlike the label. Hiding is about
            // which services this app is allowed to touch; reverting is about which ones come
            // back. They were one string while they said the same thing, and stopped being
            // able to be the moment either side gained a detail the other did not have.
            label = stringResource(R.string.revert_defaults_accessibility_services),
            note = stringResource(R.string.settings_to_hide_accessibility_note),
            checked = draft[ManualRevertTarget.AccessibilityServices] == true,
            onCheckedChange = { toggle(ManualRevertTarget.AccessibilityServices, it) },
        )

        // Only once overlay management has been switched on in Advanced. Off is the
        // default, and on a device with no working Shizuku it is the only honest state -
        // a row that can only ever fail is worse than no row, and greying it out here
        // would say "configure Shizuku" to someone who has decided not to use the feature
        // at all.
        if (manageOverlay) {
            SettingToHideRow(
                label = stringResource(R.string.revert_defaults_display_over_other_apps),
                note = if (shizukuConfigured) {
                    stringResource(R.string.settings_to_hide_overlay_note)
                } else {
                    stringResource(R.string.overlay_needs_shizuku_configured)
                },
                checked = draft[ManualRevertTarget.DisplayOverOtherApps] == true &&
                    shizukuConfigured,
                // Overlay AppOps can only be written through Shizuku. Letting this be
                // ticked with no Shizuku configured buys the user a launch that fails ten
                // seconds later for a reason the dialog already knew about.
                enabled = shizukuConfigured,
                onCheckedChange = { toggle(ManualRevertTarget.DisplayOverOtherApps, it) },
            )
        }

        Spacer(modifier = Modifier.height(8.dp))

        // First, and in the error colour, because it is the one note here that means
        // "you may be in the wrong place entirely". Everything else in this dialog is
        // device-wide by design; someone who wanted per-app settings will otherwise
        // tick these boxes and wonder why every app gets the same treatment.
        InfoLine(
            text = AnnotatedString(stringResource(R.string.settings_to_hide_info_per_app)),
            color = MaterialTheme.colorScheme.error,
        )

        InfoLine(text = AnnotatedString(stringResource(R.string.settings_to_hide_info_all)))

        // Third, and red, because it is the one line here that describes a way the
        // hiding can be undone without anybody touching the device. Shizuku's watchdog
        // restarts the service on its own, and starting the service turns ADB back on -
        // so the settings this dialog just hid come back mid-session, which is exactly
        // the state a locked-down app is looking for.
        InfoLine(
            text = emphasised(
                text = stringResource(R.string.settings_to_hide_info_watchdog),
                names = listOf(
                    stringResource(R.string.settings_to_hide_name_shizuku_watchdog),
                ),
            ),
            color = MaterialTheme.colorScheme.error,
        )

        InfoLine(
            text = emphasised(
                text = stringResource(R.string.settings_to_hide_info_shizuku),
                names = listOf(stringResource(R.string.settings_to_hide_name_shizuku_hide)),
            ),
        )
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
    enabled: Boolean = true,
    onCheckedChange: (Boolean) -> Unit,
) {
    // Greyed rather than hidden. A row that vanishes when Shizuku is unconfigured leaves
    // the user with no way to find out the feature exists, let alone what to configure.
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

        Checkbox(checked = checked, enabled = enabled, onCheckedChange = onCheckedChange)
    }
}

/**
 * A note that is about the list as a whole rather than about one row.
 *
 * Marked with an information icon rather than indented or italicised, so it cannot be read
 * as another item to tick — one of these is specifically warning against ticking only one
 * of them.
 *
 * [color] tints the icon and the text together. Anything other than the default reads as a
 * warning, so it should stay rare, and the two that exist sit at opposite ends of the list:
 * coloured lines next to each other stop being a warning and become a colour scheme.
 */
@Composable
private fun InfoLine(
    modifier: Modifier = Modifier,
    text: AnnotatedString,
    color: Color = MaterialTheme.colorScheme.onSurfaceVariant,
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
            tint = color,
        )

        Spacer(modifier = Modifier.width(8.dp))

        Text(
            text = text,
            style = MaterialTheme.typography.bodySmall,
            color = color,
        )
    }
}
