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
package com.android.geto.feature.apps.dialog

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Checkbox
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.designsystem.icon.GetoIcons
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.feature.apps.R

/**
 * The way out when the ongoing notification is gone.
 *
 * Once developer options are switched off there is no system screen left to switch them
 * back on from, so this has to work with nothing else in place. Every row does the same
 * thing two ways: the tick joins it to the batch under the Re-enable button, and the small
 * button on the right does that one row immediately and on its own — useful for retrying
 * a single thing without disturbing a selection you want to keep.
 */
@Composable
internal fun RevertSettingsDialog(
    modifier: Modifier = Modifier,
    selected: Set<ManualRevertTarget>,
    busy: Boolean,
    onDismissRequest: () -> Unit,
    onToggle: (ManualRevertTarget) -> Unit,
    onRevertOne: (ManualRevertTarget) -> Unit,
    onRevert: () -> Unit,
) {
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
                text = stringResource(R.string.revert_settings),
                style = MaterialTheme.typography.titleLarge,
            )

            Spacer(modifier = Modifier.height(4.dp))

            ManualRevertTarget.entries.forEach { target ->
                RevertTargetRow(
                    target = target,
                    checked = target in selected,
                    busy = busy,
                    onToggle = { onToggle(target) },
                    onRevertOne = { onRevertOne(target) },
                )
            }

            Spacer(modifier = Modifier.height(4.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(R.string.cancel))
                }

                Spacer(modifier = Modifier.size(8.dp))

                Button(
                    onClick = onRevert,
                    enabled = !busy && selected.isNotEmpty(),
                ) {
                    Text(text = stringResource(R.string.re_enable))
                }
            }
        }
    }
}

@Composable
private fun RevertTargetRow(
    modifier: Modifier = Modifier,
    target: ManualRevertTarget,
    checked: Boolean,
    busy: Boolean,
    onToggle: () -> Unit,
    onRevertOne: () -> Unit,
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .clickable(enabled = !busy, onClick = onToggle)
            .padding(vertical = 2.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Checkbox(checked = checked, enabled = !busy, onCheckedChange = { onToggle() })

        Text(
            modifier = Modifier
                .weight(1f)
                .padding(start = 4.dp),
            text = target.getTitle(),
            style = MaterialTheme.typography.bodyLarge,
        )

        // Understated on purpose: the primary action is the Re-enable button below, and
        // these are the escape hatch for one stubborn row.
        IconButton(onClick = onRevertOne, enabled = !busy) {
            Icon(
                modifier = Modifier.size(18.dp),
                imageVector = GetoIcons.Restore,
                contentDescription = stringResource(
                    R.string.revert_one,
                    target.getTitle(),
                ),
                tint = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
internal fun ManualRevertTarget.getTitle(): String = when (this) {
    ManualRevertTarget.DeveloperSettings -> stringResource(R.string.revert_developer_settings)
    ManualRevertTarget.UsbDebugging -> stringResource(R.string.revert_usb_debugging)
    ManualRevertTarget.WirelessDebugging -> stringResource(R.string.revert_wireless_debugging)
    ManualRevertTarget.AccessibilityServices -> stringResource(R.string.revert_accessibility)
    ManualRevertTarget.Shizuku -> stringResource(R.string.revert_shizuku)
}
