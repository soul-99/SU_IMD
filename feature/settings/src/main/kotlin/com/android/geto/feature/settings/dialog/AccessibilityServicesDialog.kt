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
import androidx.compose.foundation.layout.heightIn
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
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.domain.model.AccessibilityServiceData
import com.android.geto.feature.settings.R
import com.android.geto.common.R as commonR

@Composable
internal fun AccessibilityServicesDialog(
    modifier: Modifier = Modifier,
    accessibilityServices: List<AccessibilityServiceData>,
    selectedServices: List<String>,
    onDismissRequest: () -> Unit,
    onUpdateManagedAccessibilityServices: (List<String>) -> Unit,
) {
    // Keyed on the persisted selection only. Keying on accessibilityServices as well
    // would reset the user's ticks the moment the asynchronous device refresh lands,
    // which happens a beat after the dialog opens.
    val selected = remember(selectedServices) {
        mutableStateListOf<String>().apply { addAll(selectedServices) }
    }

    DialogContainer(
        modifier = modifier,
        onDismissRequest = onDismissRequest,
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(10.dp),
        ) {
            Text(
                modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
                text = stringResource(R.string.accessibility_services),
                style = MaterialTheme.typography.titleLarge,
            )

            Text(
                modifier = Modifier.padding(horizontal = 10.dp),
                text = stringResource(R.string.accessibility_services_dialog_description),
                style = MaterialTheme.typography.bodySmall,
            )

            Spacer(modifier = Modifier.height(8.dp))

            if (accessibilityServices.isEmpty()) {
                Text(
                    modifier = Modifier.padding(20.dp),
                    text = stringResource(R.string.no_accessibility_services),
                    style = MaterialTheme.typography.bodyMedium,
                )
            } else {
                LazyColumn(modifier = Modifier.heightIn(max = 400.dp)) {
                    items(items = accessibilityServices, key = { it.id }) { service ->
                        // Typed explicitly so remove() can only bind to the
                        // remove-by-element overload, never the deprecated
                        // remove-by-index one.
                        val id: String = service.id

                        val checked = id in selected

                        // Reads the list rather than closing over `checked`, so two taps
                        // dispatched inside one frame cannot both take the add branch.
                        val toggle = {
                            if (id in selected) {
                                selected.remove(id)
                            } else {
                                selected.add(id)
                            }

                            Unit
                        }

                        ListItem(
                            modifier = Modifier.clickable(onClick = toggle),
                            headlineContent = {
                                Text(text = service.label, maxLines = 1)
                            },
                            supportingContent = {
                                Text(
                                    text = if (service.enabled) {
                                        stringResource(
                                            R.string.accessibility_service_enabled,
                                            service.packageName,
                                        )
                                    } else {
                                        stringResource(
                                            R.string.accessibility_service_disabled,
                                            service.packageName,
                                        )
                                    },
                                    style = MaterialTheme.typography.bodySmall,
                                )
                            },
                            leadingContent = {
                                Checkbox(
                                    checked = checked,
                                    onCheckedChange = { toggle() },
                                )
                            },
                        )
                    }
                }
            }

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(10.dp),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(commonR.string.cancel))
                }

                TextButton(
                    onClick = {
                        onUpdateManagedAccessibilityServices(selected.toList())

                        onDismissRequest()
                    },
                ) {
                    Text(text = stringResource(commonR.string.update))
                }
            }
        }
    }
}
