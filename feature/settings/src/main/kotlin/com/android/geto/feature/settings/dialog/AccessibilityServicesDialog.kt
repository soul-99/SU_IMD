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
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.ListItem
import androidx.compose.material3.LocalContentColor
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import coil.compose.AsyncImage
import com.android.geto.designsystem.component.GetoCheckbox
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.domain.model.AccessibilityServiceData
import com.android.geto.feature.settings.R
import com.android.geto.feature.settings.SetupNextButtons
import com.android.geto.common.R as commonR

/** The picker rows' app icon. Matches the 40dp slot the Shizuku package picker draws. */
private val PICKER_ICON = 36.dp

/**
 * Which accessibility services IMD is allowed to switch off.
 *
 * **IMD's own IMD+ detector is in this list and cannot be unticked**, while IMD+ is switched on.
 * It is shown rather than filtered out because hiding it would be the dishonest option — a hide
 * does switch it off, and a list claiming otherwise would leave the user unable to account for
 * a service that keeps turning itself off. It cannot be unticked because a detector left
 * listening through a hide would be the one accessibility service still watching the device
 * that the hide exists to quieten. The rule lives in DisableAutoHideServiceUseCase, which every
 * hide calls whatever this list says; this row is what says so on screen.
 *
 * The services manager's own accessibility switch deliberately does not touch it in either
 * direction - see SetManualTargetUseCase.
 */
@Composable
fun AccessibilityServicesDialog(
    modifier: Modifier = Modifier,
    accessibilityServices: List<AccessibilityServiceData>,
    selectedServices: List<String>,
    /**
     * IMD's own detector, or blank while IMD+ is off — in which case nothing here is special
     * and the row behaves like any other.
     */
    ownDetector: String,
    onDismissRequest: () -> Unit,
    /**
     * Re-read the list. Called when the app comes back to the foreground, because the button
     * below sends the user to Android's own settings to change exactly what this lists — and
     * returning to a stale list makes the trip look like it did nothing.
     */
    onRefresh: () -> Unit = {},
    /**
     * Non-null turns this into a step of the setup flow.
     *
     * ⚠ **Three things follow and nothing else does**: the container is drawn flat rather than
     * as a dialog, the actions become Skip and Next instead of Cancel and Update, and the row
     * holding them is arranged so Skip sits at the left. The body above is the same composable
     * either way, which is why this is a flag and not a second copy of the list.
     *
     * ⚠ **Not [onDismissRequest].** During setup that one is what advances the flow *after* a
     * save, so wiring Skip to it would work by accident and break the moment either meaning
     * changes.
     */
    /**
     * The heading this step wears, replacing the one this dialog carries in Settings.
     *
     * Null everywhere but the setup flow. Drawn in the theme's `primary`, which is the accent
     * the Shizuku setup page's heading and the help page's own sub-headings already use.
     */
    stepTitle: String? = null,
    onSkip: (() -> Unit)? = null,
    /** Set by the setup flow on every step that has one behind it. */
    onBack: (() -> Unit)? = null,
    onUpdateManagedAccessibilityServices: (List<String>) -> Unit,
) {
    // Registered only while this dialog is composed, so nothing observes once it closes.
    val lifecycleOwner = LocalLifecycleOwner.current

    DisposableEffect(lifecycleOwner, onRefresh) {
        val observer = LifecycleEventObserver { _, event ->
            if (event == Lifecycle.Event.ON_RESUME) onRefresh()
        }

        lifecycleOwner.lifecycle.addObserver(observer)

        onDispose { lifecycleOwner.lifecycle.removeObserver(observer) }
    }

    // Keyed on the persisted selection only. Keying on accessibilityServices as well
    // would reset the user's ticks the moment the asynchronous device refresh lands,
    // which happens a beat after the dialog opens.
    val selected = remember(selectedServices) {
        mutableStateListOf<String>().apply { addAll(selectedServices) }
    }

    DialogContainer(
        modifier = modifier,
        flat = onSkip != null,
        onDismissRequest = onDismissRequest,
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(10.dp),
        ) {
            Text(
                modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
                text = stepTitle ?: stringResource(R.string.accessibility_services),
                style = MaterialTheme.typography.titleLarge,
                color = if (stepTitle != null) {
                    MaterialTheme.colorScheme.primary
                } else {
                    LocalContentColor.current
                },
            )

            Text(
                modifier = Modifier.padding(horizontal = 10.dp),
                text = stringResource(R.string.accessibility_services_dialog_description),
                style = MaterialTheme.typography.bodySmall,
            )

            Spacer(modifier = Modifier.height(12.dp))

            SystemSettingsButton(
                text = stringResource(R.string.accessibility_system_settings),
                intent = accessibilitySettingsIntent(),
            )

            Spacer(modifier = Modifier.height(12.dp))

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

                        // IMD's own detector: always ticked, never clickable, and with its own
                        // explanation in place of the package name.
                        val own = ownDetector.isNotBlank() && id == ownDetector

                        val checked = own || id in selected

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
                            modifier = if (own) {
                                Modifier
                            } else {
                                Modifier.clickable(onClick = toggle)
                            },
                            headlineContent = {
                                Text(text = service.label, maxLines = 1)
                            },
                            supportingContent = {
                                Text(
                                    text = when {
                                        own -> stringResource(R.string.accessibility_service_own)

                                        service.enabled -> stringResource(
                                            R.string.accessibility_service_enabled,
                                            service.packageName,
                                        )

                                        else -> stringResource(
                                            R.string.accessibility_service_disabled,
                                            service.packageName,
                                        )
                                    },
                                    style = MaterialTheme.typography.bodySmall,
                                )
                            },
                            leadingContent = {
                                // Checkbox at the leading edge as in every other picker here,
                                // with the icon between it and the label — the arrangement the
                                // Shizuku package picker already uses.
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    GetoCheckbox(
                                        checked = checked,
                                        enabled = !own,
                                        onCheckedChange = { toggle() },
                                    )

                                    AsyncImage(
                                        modifier = Modifier
                                            .padding(start = 4.dp)
                                            .size(PICKER_ICON),
                                        model = service.icon,
                                        contentDescription = null,
                                    )
                                }
                            },
                        )
                    }
                }
            }

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(10.dp),
                // SpaceBetween is what puts Skip at the left - see SettingsPage, which does the
                // same for the two dialogs built on it.
                horizontalArrangement = if (onSkip != null) {
                    Arrangement.SpaceBetween
                } else {
                    Arrangement.End
                },
            ) {
                TextButton(onClick = onSkip ?: onDismissRequest) {
                    Text(
                        text = stringResource(
                            if (onSkip != null) commonR.string.skip else commonR.string.cancel,
                        ),
                    )
                }

                // ⚠ **The same button, renamed.** Next writes the draft this dialog is already
                // holding, exactly as Update does, so the two cannot drift into meaning
                // different things — which is why both branches below call the same lambda.
                val commit = {
                    onUpdateManagedAccessibilityServices(selected.toList())

                    onDismissRequest()
                }

                if (onSkip != null) {
                    SetupNextButtons(onBack = onBack, onNext = commit)
                } else {
                    TextButton(onClick = commit) {
                        Text(text = stringResource(commonR.string.update))
                    }
                }
            }
        }
    }
}
