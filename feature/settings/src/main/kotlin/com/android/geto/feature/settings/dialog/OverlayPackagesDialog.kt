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
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Checkbox
import androidx.compose.material3.ListItem
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.domain.model.OverlayPackageData
import com.android.geto.feature.settings.R
import com.android.geto.common.R as commonR

/**
 * Which apps' overlay permission IMD is allowed to take away.
 *
 * The counterpart of [AccessibilityServicesDialog], down to the shape of the rows: nothing
 * here changes the device, the ticks are read the next time an app is launched, and only what
 * is ticked is ever touched.
 *
 * Reached only when the list could actually be read. Overlay AppOps need a running Shizuku
 * service, and a picker that opened empty on a device where IMD simply cannot see would be
 * telling the user they have nothing to choose from - so the caller shows an error instead.
 */
@Composable
internal fun OverlayPackagesDialog(
    modifier: Modifier = Modifier,
    overlayPackages: List<OverlayPackageData>,
    selectedPackages: List<String>,
    onDismissRequest: () -> Unit,
    onUpdateManagedOverlayPackages: (List<String>) -> Unit,
) {
    // Keyed on the persisted selection only, so the asynchronous device refresh landing a
    // beat after the dialog opens cannot reset the user's ticks.
    val selected = remember(selectedPackages) {
        mutableStateListOf<String>().apply { addAll(selectedPackages) }
    }

    val context = LocalContext.current

    SettingsPage(
        modifier = modifier,
        title = stringResource(R.string.overlay_packages),
        scrollableBody = false,
        onDismissRequest = onDismissRequest,
        actions = {
            TextButton(onClick = onDismissRequest) {
                Text(text = stringResource(commonR.string.cancel))
            }

            TextButton(
                onClick = {
                    onUpdateManagedOverlayPackages(selected.toList())

                    onDismissRequest()
                },
            ) {
                Text(text = stringResource(commonR.string.update))
            }
        },
    ) {
        Text(
            modifier = Modifier.padding(horizontal = 10.dp),
            text = stringResource(R.string.overlay_packages_dialog_description),
            style = MaterialTheme.typography.bodySmall,
        )

        Spacer(modifier = Modifier.height(12.dp))

        SystemSettingsButton(
            text = stringResource(R.string.overlay_system_settings),
            intent = overlaySettingsIntent(context),
        )

        Spacer(modifier = Modifier.height(12.dp))

        if (overlayPackages.isEmpty()) {
            Text(
                modifier = Modifier.padding(20.dp),
                text = stringResource(R.string.no_overlay_packages),
                style = MaterialTheme.typography.bodyMedium,
            )
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f),
            ) {
                items(items = overlayPackages, key = { it.packageName }) { app ->
                    // Typed explicitly so remove() can only bind to the remove-by-element
                    // overload, never the deprecated remove-by-index one.
                    val id: String = app.packageName

                    // Reads the list rather than closing over a captured boolean, so two taps
                    // dispatched inside one frame cannot both take the add branch.
                    val toggle = {
                        if (id in selected) selected.remove(id) else selected.add(id)

                        Unit
                    }

                    ListItem(
                        modifier = Modifier.clickable(onClick = toggle),
                        headlineContent = { Text(text = app.label, maxLines = 1) },
                        supportingContent = {
                            Text(
                                text = if (app.allowed) {
                                    stringResource(R.string.overlay_package_allowed, id)
                                } else {
                                    stringResource(R.string.overlay_package_held, id)
                                },
                                style = MaterialTheme.typography.bodySmall,
                            )
                        },
                        leadingContent = {
                            Checkbox(checked = id in selected, onCheckedChange = { toggle() })
                        },
                    )
                }
            }
        }
    }
}

/** Why the picker would not open: the list can only be read through a running Shizuku. */
@Composable
internal fun OverlayUnreadableDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = stringResource(R.string.overlay_needs_shizuku_running),
                style = MaterialTheme.typography.bodyMedium,
            )

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(R.string.understood))
                }
            }
        }
    }
}
