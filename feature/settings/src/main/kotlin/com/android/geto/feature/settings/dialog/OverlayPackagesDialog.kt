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
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.CircularProgressIndicator
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
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import coil.compose.AsyncImage
import com.android.geto.designsystem.component.GetoCheckbox
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.domain.model.OverlayPackageData
import com.android.geto.feature.settings.R
import com.android.geto.feature.settings.SetupNextButtons
import com.android.geto.common.R as commonR

/** The picker rows' app icon. Matches the 40dp slot the Shizuku package picker draws. */
private val PICKER_ICON = 36.dp

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
fun OverlayPackagesDialog(
    modifier: Modifier = Modifier,
    overlayPackages: List<OverlayPackageData>,
    selectedPackages: List<String>,
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
    onUpdateManagedOverlayPackages: (List<String>) -> Unit,
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

    // Keyed on the persisted selection only, so the asynchronous device refresh landing a
    // beat after the dialog opens cannot reset the user's ticks.
    val selected = remember(selectedPackages) {
        mutableStateListOf<String>().apply { addAll(selectedPackages) }
    }

    val context = LocalContext.current

    // The same shape as the accessibility picker, deliberately: the two ask the same question
    // about the same kind of list, and one opening as a full page while the other opened as a
    // small dialog made them look like different features. A capped LazyColumn rather than a
    // weighted one, because this is no longer inside a full-height page to take a share of.
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
                text = stepTitle ?: stringResource(R.string.overlay_packages),
                style = MaterialTheme.typography.titleLarge,
                color = if (stepTitle != null) {
                    MaterialTheme.colorScheme.primary
                } else {
                    LocalContentColor.current
                },
            )

            // Point 1 is red on its own, as the author asked, because it is the only one that
            // describes a cost rather than a fact — hiding overlay access adds a wait to every
            // hide. Points 2 and 3 are the ordinary colour. Two Texts rather than one coloured
            // span, matching how SettingsToHideDialog already draws its red info line.
            Text(
                modifier = Modifier.padding(horizontal = 10.dp),
                text = stringResource(R.string.overlay_packages_dialog_delay),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.error,
            )

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
                LazyColumn(modifier = Modifier.heightIn(max = 400.dp)) {
                    items(items = overlayPackages, key = { it.packageName }) { app ->
                        // Typed explicitly so remove() can only bind to the remove-by-element
                        // overload, never the deprecated remove-by-index one.
                        val id: String = app.packageName

                        // Reads the list rather than closing over a captured boolean, so two
                        // taps dispatched inside one frame cannot both take the add branch.
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
                                // The same arrangement as the accessibility picker beside it.
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    GetoCheckbox(
                                        checked = id in selected,
                                        onCheckedChange = { toggle() },
                                    )

                                    AsyncImage(
                                        modifier = Modifier
                                            .padding(start = 4.dp)
                                            .size(PICKER_ICON),
                                        model = app.icon,
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
                    onUpdateManagedOverlayPackages(selected.toList())

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

/**
 * Shown while the overlay list is being read.
 *
 * Not dismissable, and deliberately: it stands in for a picker the user has already asked
 * for, and it resolves itself within a couple of seconds either into that picker or into the
 * notice below. A cancel here would only produce a third outcome nobody asked about.
 */
@Composable
internal fun OverlayLoadingDialog(modifier: Modifier = Modifier) {
    DialogContainer(modifier = modifier, onDismissRequest = {}) {
        Row(
            modifier = Modifier.padding(horizontal = 20.dp, vertical = 24.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            CircularProgressIndicator(modifier = Modifier.size(24.dp))

            Text(
                modifier = Modifier.padding(start = 16.dp),
                text = stringResource(R.string.overlay_loading_list),
                style = MaterialTheme.typography.bodyMedium,
            )
        }
    }
}

/**
 * The Display over other apps *step* while its list has not arrived — spinner first, then a way
 * out of it.
 *
 * ⚠ **Separate from [OverlayLoadingDialog], which stays exactly as it was.** That one stands in
 * for a picker the user has just asked for from Settings and resolves in a second or two; this one
 * is a page of the setup flow that has to survive the list never arriving at all, which is the
 * case the author hit. Giving the dialog a failure state would have put a Skip button on a dialog
 * that has nothing to skip.
 *
 * [failed] is the eight-second wait having elapsed with no list, not the read having returned an
 * error — see `OverlayStep`, which owns the timing.
 */
@Composable
internal fun OverlayStepWaiting(
    modifier: Modifier = Modifier,
    stepTitle: String,
    failed: Boolean,
    onSkip: () -> Unit,
    onRetry: () -> Unit,
) {
    SettingsPage(
        modifier = modifier,
        title = stepTitle,
        flat = true,
        // Nothing to dismiss to during setup; the footer is the only way past this page.
        onDismissRequest = onSkip,
        actions = {
            // ⚠ **No buttons at all while the spinner is up.** A Skip offered in the first
            // second is an invitation to leave before the page has had a chance to work, and a
            // Retry before the first attempt has finished would start a second one on top of it.
            if (failed) {
                TextButton(onClick = onSkip) {
                    Text(text = stringResource(commonR.string.skip))
                }

                TextButton(onClick = onRetry) {
                    Text(text = stringResource(commonR.string.retry))
                }
            }
        },
    ) {
        if (failed) {
            Text(
                modifier = Modifier.padding(vertical = 12.dp),
                text = stringResource(R.string.overlay_load_failed),
                style = MaterialTheme.typography.bodyMedium,
            )
        } else {
            Row(
                modifier = Modifier.padding(vertical = 24.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                CircularProgressIndicator(modifier = Modifier.size(24.dp))

                Text(
                    modifier = Modifier.padding(start = 16.dp),
                    text = stringResource(R.string.overlay_loading_list),
                    style = MaterialTheme.typography.bodyMedium,
                )
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
                text = stringResource(R.string.overlay_load_failed),
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
