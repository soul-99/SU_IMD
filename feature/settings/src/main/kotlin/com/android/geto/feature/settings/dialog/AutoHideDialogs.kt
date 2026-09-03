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
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.ListItem
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import coil.compose.AsyncImage
import com.android.geto.designsystem.component.GetoCheckbox
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.domain.model.InstalledAppData
import com.android.geto.feature.settings.R
import com.android.geto.common.R as commonR

/**
 * Which apps IMD+ watches for.
 *
 * The same shape as the overlay and accessibility pickers, deliberately — three lists of the
 * same kind of thing should not look like three different features. It differs in one way that
 * matters: this one carries a search field, because it lists *every* installed package rather
 * than the handful that hold a particular permission, and scrolling a few hundred rows to find
 * one app is not a picker.
 *
 * Nothing here changes the device. The list is read the next time one of these apps is opened.
 */
/**
 * The app icon beside each row.
 *
 * The same 36 dp the accessibility and overlay pickers draw theirs at, and declared here for the
 * same reason they each declare their own: one number is cheaper duplicated than shared through a
 * file that exists only to hold it.
 */
private val PICKER_ICON = 36.dp

@Composable
internal fun AutoHideAppsDialog(
    modifier: Modifier = Modifier,
    installedApps: List<InstalledAppData>,
    selectedPackages: List<String>,
    onDismissRequest: () -> Unit,
    onUpdateAutoHidePackages: (List<String>) -> Unit,
) {
    // Keyed on the persisted selection only, so the app-list read landing a beat after the
    // dialog opens cannot reset the user's ticks.
    val selected = remember(selectedPackages) {
        mutableStateListOf<String>().apply { addAll(selectedPackages) }
    }

    var query by rememberSaveable { mutableStateOf("") }

    // Two orderings, one after the other: by name first, then ticked apps lifted to the top.
    // `sortedBy` is stable, so sorting by name and *then* by ticked leaves the alphabetical
    // order intact inside each of the two groups - which is what makes the list scannable
    // both ways at once rather than one way at the cost of the other.
    //
    // The search filters and nothing else. It used to keep every ticked app visible whatever
    // was typed, on the theory that hiding them looked like the search had cleared them; in
    // practice it meant a search for one app returned that app plus the whole selection, which
    // reads as the search being broken. The count under the list already says how many are
    // ticked, so nothing is lost by letting the search mean what it says.
    val shown = remember(installedApps, query, selected.toList()) {
        val needle = query.trim()

        val matching = if (needle.isBlank()) {
            installedApps
        } else {
            installedApps.filter {
                it.label.contains(needle, ignoreCase = true) ||
                    it.packageName.contains(needle, ignoreCase = true)
            }
        }

        matching
            .sortedBy { it.label.lowercase() }
            .sortedByDescending { it.packageName in selected }
    }

    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(10.dp),
        ) {
            Text(
                modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
                text = stringResource(R.string.auto_hide_apps),
                style = MaterialTheme.typography.titleLarge,
            )

            Text(
                modifier = Modifier.padding(horizontal = 10.dp),
                text = stringResource(R.string.auto_hide_apps_description),
                style = MaterialTheme.typography.bodySmall,
            )

            Spacer(modifier = Modifier.height(12.dp))

            OutlinedTextField(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 10.dp),
                value = query,
                onValueChange = { query = it },
                singleLine = true,
                label = { Text(text = stringResource(R.string.auto_hide_apps_search)) },
            )

            Spacer(modifier = Modifier.height(12.dp))

            if (installedApps.isEmpty()) {
                Text(
                    modifier = Modifier.padding(20.dp),
                    text = stringResource(R.string.auto_hide_apps_loading),
                    style = MaterialTheme.typography.bodyMedium,
                )
            } else {
                LazyColumn(modifier = Modifier.heightIn(max = 400.dp)) {
                    items(items = shown, key = { it.packageName }) { app ->
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
                                    text = id,
                                    style = MaterialTheme.typography.bodySmall,
                                    maxLines = 1,
                                )
                            },
                            leadingContent = {
                                // Checkbox first, then the icon, then the label - the
                                // arrangement the accessibility and overlay pickers already
                                // use. The icon rides in on InstalledAppData and was simply
                                // never drawn; see this file's own note about the three
                                // pickers being one shape.
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
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(commonR.string.cancel))
                }

                TextButton(
                    onClick = {
                        onUpdateAutoHidePackages(selected.toList())

                        onDismissRequest()
                    },
                ) {
                    Text(text = stringResource(commonR.string.update))
                }
            }
        }
    }
}

/**
 * What IMD+ actually does, step by step, before anybody switches it on.
 *
 * Written as a flow rather than a paragraph because it *is* a flow, and because two of its
 * steps — the app being force-stopped, and IMD's own detector switching itself off — look like
 * faults if they are met without warning. Someone whose app closes and reopens by itself needs
 * to have read step three before it happens, not afterwards.
 */
@Composable
internal fun AutoHideHowItWorksDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {
    // The whole flow, both halves of it. The revert used to be a paragraph under the chart,
    // which read as an aside rather than as the other end of the same sequence - and the
    // sequence is the point: the steps that surprise people are the ones in the middle, and
    // they only make sense with the ones after them in view.
    val steps = listOf(
        stringResource(R.string.auto_hide_flow_1),
        stringResource(R.string.auto_hide_flow_2),
        stringResource(R.string.auto_hide_flow_3),
        stringResource(R.string.auto_hide_flow_4),
        stringResource(R.string.auto_hide_flow_5),
        stringResource(R.string.auto_hide_flow_6),
        stringResource(R.string.auto_hide_flow_7),
        stringResource(R.string.auto_hide_flow_8),
        stringResource(R.string.auto_hide_flow_9),
    )

    SettingsPage(
        modifier = modifier,
        title = stringResource(R.string.auto_hide_how_it_works),
        onDismissRequest = onDismissRequest,
    ) {
        Text(
            modifier = Modifier.padding(horizontal = 10.dp),
            text = stringResource(R.string.auto_hide_flow_intro),
            style = MaterialTheme.typography.bodyMedium,
        )

        Spacer(modifier = Modifier.height(12.dp))

        steps.forEachIndexed { index, step ->
            FlowStep(number = index + 1, text = step, last = index == steps.lastIndex)
        }

        Spacer(modifier = Modifier.height(12.dp))
    }
}

/** The width of the number gutter, so every step's text starts at the same x. */
internal val FLOW_GUTTER_WIDTH = 24.dp

/**
 * One step of the flow: its number, what happens, and an arrow down to the next one so the list
 * reads in order rather than as nine unrelated notes.
 *
 * The arrow is emitted *below* the whole step rather than under the number, and centred across
 * the full width. Tucked into the gutter it sat under the numbers, hard against the left margin,
 * which read as a bullet decoration rather than as a flow; centred, the nine of them make one
 * line down the middle of the page - and centring is also what puts every arrow on the same x
 * without anyone having to keep a measurement in step.
 */
@Composable
internal fun FlowStep(
    modifier: Modifier = Modifier,
    number: Int,
    text: String,
    last: Boolean,
) {
    Column(modifier = modifier.fillMaxWidth()) {
        Row(modifier = Modifier.padding(horizontal = 10.dp)) {
            Column(
                modifier = Modifier.width(FLOW_GUTTER_WIDTH),
                horizontalAlignment = Alignment.CenterHorizontally,
            ) {
                Text(
                    text = "$number",
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.primary,
                )
            }

            Spacer(modifier = Modifier.width(14.dp))

            Text(
                modifier = Modifier.weight(1f),
                text = text,
                style = MaterialTheme.typography.bodyMedium,
            )
        }

        if (!last) {
            Spacer(modifier = Modifier.height(6.dp))

            Text(
                modifier = Modifier.fillMaxWidth(),
                // The theme's own green, like the numbers either side of it: the arrow is part
                // of the chain rather than a rule between two unrelated notes, and the outline
                // grey it used to be read as the latter.
                text = "↓",
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.primary,
                textAlign = TextAlign.Center,
            )

            Spacer(modifier = Modifier.height(6.dp))
        }
    }
}

/**
 * The last resort, when neither route to switching the detector on worked.
 *
 * IMD tries the secure setting first and the Shizuku restricted-settings AppOp second, without
 * asking, because between them they cover almost every device. This appears only when both have
 * come to nothing, and it names the two things left that a person can do — so it is a list of
 * two actions rather than an apology.
 */
@Composable
internal fun AutoHideAccessibilityBlockedDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = stringResource(R.string.auto_hide_blocked_title),
                style = MaterialTheme.typography.titleMedium,
            )

            Spacer(modifier = Modifier.height(10.dp))

            Text(
                text = stringResource(R.string.auto_hide_blocked_1),
                style = MaterialTheme.typography.bodyMedium,
            )

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = stringResource(R.string.auto_hide_blocked_2),
                style = MaterialTheme.typography.bodyMedium,
            )

            Spacer(modifier = Modifier.height(10.dp))

            Text(
                text = stringResource(R.string.auto_hide_blocked_retry),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
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

/**
 * Why the IMD+ row does nothing while a revert is outstanding.
 *
 * The row is disabled for a real reason - IMD+ is deliberately deaf for as long as anything is
 * hidden, so both switching it on and opening its page would only write an answer the next
 * revert has to undo. A control that is merely inert teaches nobody that, which is why both
 * halves of the row still take the tap and land here.
 */
@Composable
internal fun AutoHidePendingRevertsDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = stringResource(R.string.auto_hide_blocked_reverts),
                style = MaterialTheme.typography.bodyMedium,
            )

            Spacer(modifier = Modifier.height(12.dp))

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

/**
 * Why a watched app just opened and IMD+ did nothing.
 *
 * Raised over the app itself, by the IMD+ window, at the one moment a run decides not to happen:
 * the device-wide "Settings to hide" configuration has nothing ticked, so there is nothing for
 * IMD+ to hide and no reason to close the app and open it again.
 *
 * **Public rather than internal, unlike its neighbours.** It is shown from `AutoHideActivity` in
 * the `app` module rather than from the settings screen, because that window is where the run
 * happens and where the user is standing when this becomes true.
 *
 * It exists because doing nothing quietly is indistinguishable from being broken. A run that
 * hides something ends with the app arriving on screen and a notification behind it, and needs
 * no dialog; this one ends with the app arriving on screen and nothing else at all — which from
 * the user's side is IMD+ switched on, an app in its watch list, and no sign it ever ran. The
 * previous behaviour was worse than quiet: it killed the app, hid nothing, opened it again, and
 * detected its own relaunch, so the app opened and closed for as long as the user let it.
 */
@Composable
fun AutoHideNothingToHideDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = stringResource(R.string.auto_hide_nothing_to_hide),
                style = MaterialTheme.typography.bodyMedium,
            )

            Spacer(modifier = Modifier.height(12.dp))

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

/**
 * The memory function's version of [AutoHideNothingToHideDialog].
 *
 * Same moment, same reason, different place to go. Under "Revert to default" IMD+ reads one
 * device-wide list and an empty one is fixed in IMD's own settings; under the memory function it
 * reads the watched app's own page, so an app with nothing configured is fixed by long-pressing
 * that app rather than by opening settings at all. Sending the reader to the wrong one of those
 * is worse than saying nothing, which is why this is a second dialog rather than a second
 * sentence in the first.
 *
 * Public for the same reason its neighbour is: it is shown from `AutoHideActivity` in the `app`
 * module, because that window is where the run happens and where the user is standing.
 */
@Composable
fun AutoHideNoProfileDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = stringResource(R.string.auto_hide_no_profile),
                style = MaterialTheme.typography.bodyMedium,
            )

            Spacer(modifier = Modifier.height(12.dp))

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

/**
 * What the IMD+ switch says when it will not go on.
 *
 * The same treatment auto unhide gives its own blocked switch, and for the same reason: a
 * control that moves and springs back tells the user nothing about why.
 *
 * Not raised for the one case IMD can fix by itself — a missing detector on an install that
 * has had IMD+ on before switches it back on instead, which is what the row decides before it
 * ever reaches this.
 */
@Composable
internal fun AutoHideSetupNoticeDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = stringResource(R.string.auto_hide_setup_first),
                style = MaterialTheme.typography.bodyMedium,
            )

            Spacer(modifier = Modifier.height(12.dp))

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
