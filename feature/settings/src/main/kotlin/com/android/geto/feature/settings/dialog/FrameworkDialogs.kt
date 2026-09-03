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

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.selectableGroup
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.RadioButton
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
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.unit.dp
import com.android.geto.designsystem.component.emphasised
import com.android.geto.domain.model.HidingFramework
import com.android.geto.domain.model.UnhidingFramework
import com.android.geto.feature.settings.R

/**
 * Which settings a launch hides.
 *
 * Half of what the old "Hiding-unhiding mechanism" picker asked. The two are separate dialogs
 * rather than two sections of one, because they are separate decisions with separate
 * consequences and a single Save over both would make a user who wanted to change one think
 * about the other.
 *
 * **Confirmed rather than applied on tap**, like the picker it replaces: the two frameworks
 * behave differently enough that changing one by a mis-tap and finding out later — when a
 * launch hides the wrong list — is worth one extra press to avoid. The button is disabled
 * until the choice differs from what is stored, so re-launching the work for no change is not
 * something a stray tap can do.
 *
 * ⚠ **No re-launch.** The picker this replaces restarted the app, because several screens read
 * the mechanism as they compose and a change underneath a running one left parts of it
 * describing the old mechanism. Every one of those now reads a `Flow` off the same repository
 * and recomposes on its own, so the restart bought nothing but a jarring blink. What has *not*
 * changed is the sweep: pending reverts are still settled before the preference moves, because
 * a debt carried across the change can end up with nothing left that clears it.
 */
@Composable
internal fun HidingFrameworkDialog(
    modifier: Modifier = Modifier,
    selected: HidingFramework,
    onDismissRequest: () -> Unit,
    onSave: (HidingFramework) -> Unit,
) {
    var choice by remember(selected) { mutableStateOf(selected) }

    SettingsPage(
        modifier = modifier,
        title = stringResource(R.string.hiding_framework),
        onDismissRequest = onDismissRequest,
        actions = {
            TextButton(
                enabled = choice != selected,
                // Not dismissed here. The sweep that may follow belongs to the screen behind
                // this dialog, and closing this one first would show the settings list for a
                // frame before its notice appears.
                onClick = { onSave(choice) },
            ) {
                Text(text = stringResource(R.string.save))
            }
        },
    ) {
        Spacer(modifier = Modifier.height(4.dp))

        Column(modifier = Modifier.selectableGroup()) {
            FrameworkOption(
                title = stringResource(R.string.hiding_framework_defaults),
                // ⚠ **The same resource the memory function uses**, at the author's *"just like
                // we do for memory function"* — so the two dialogs cannot drift into two spellings
                // of one word. Its name still says `unhiding_` because that is where it was first
                // needed; renaming it would mean touching eight translation files, which is not
                // something this project does.
                recommended = stringResource(R.string.unhiding_framework_recommended),
                summary = stringResource(R.string.hiding_framework_defaults_summary),
                selected = choice == HidingFramework.ImdDefaults,
                onSelect = { choice = HidingFramework.ImdDefaults },
            )

            FrameworkOption(
                title = stringResource(R.string.hiding_framework_per_app),
                summary = stringResource(R.string.hiding_framework_per_app_summary),
                selected = choice == HidingFramework.PerApp,
                onSelect = { choice = HidingFramework.PerApp },
                extra = {
                    // What this option buys, in the author's words. Green rather than the
                    // error colour the old picker used here: under the split this is no
                    // longer a warning about what you lose, it is what the option is for.
                    Text(
                        text = stringResource(R.string.hiding_framework_per_app_extra),
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.primary,
                    )
                },
            )
        }
    }
}

/**
 * How a hide is undone.
 *
 * **The memory function is first and carries the recommendation**, which reverses the order
 * the old picker used. The author's reason is the stronger one: a revert to configured
 * defaults can switch *on* a setting the user never had on before the hide, and the app should
 * not be turning things on that it did not turn off.
 *
 * The v1.6 objection to the memory function — that its notification is the only way back, and
 * a notification can be swiped away, culled by a launcher or lost to a battery optimiser — is
 * answered rather than ignored: the Hide settings QS toggle settles every pending revert at
 * once without a notification, and so does the `Unhide settings and services` intent.
 */
@Composable
internal fun UnhidingFrameworkDialog(
    modifier: Modifier = Modifier,
    selected: UnhidingFramework,
    onDismissRequest: () -> Unit,
    onSave: (UnhidingFramework) -> Unit,
) {
    var choice by remember(selected) { mutableStateOf(selected) }

    SettingsPage(
        modifier = modifier,
        title = stringResource(R.string.unhiding_framework),
        onDismissRequest = onDismissRequest,
        actions = {
            TextButton(
                enabled = choice != selected,
                onClick = { onSave(choice) },
            ) {
                Text(text = stringResource(R.string.save))
            }
        },
    ) {
        Spacer(modifier = Modifier.height(4.dp))

        Column(modifier = Modifier.selectableGroup()) {
            FrameworkOption(
                title = stringResource(R.string.unhiding_framework_memory),
                recommended = stringResource(R.string.unhiding_framework_recommended),
                summary = stringResource(R.string.unhiding_framework_memory_summary),
                selected = choice == UnhidingFramework.Memory,
                onSelect = { choice = UnhidingFramework.Memory },
            )

            FrameworkOption(
                title = stringResource(R.string.unhiding_framework_revert),
                summaryText = emphasised(
                    text = stringResource(R.string.unhiding_framework_revert_summary),
                    // The same resource the settings list uses for that row, so the sentence
                    // cannot end up naming something the list does not. Asserted verbatim in
                    // every locale by check_translations — see the EMPHASIS table.
                    names = listOf(stringResource(R.string.revert_defaults)),
                ),
                selected = choice == UnhidingFramework.RevertToDefault,
                onSelect = { choice = UnhidingFramework.RevertToDefault },
            )
        }
    }
}

/**
 * One option in either picker.
 *
 * The whole row is the target, not just the radio button: [Role.RadioButton] on the row with a
 * null handler on the button is what stops a screen reader announcing the same choice twice,
 * and what makes a tap anywhere on the description select the option.
 *
 * [recommended] sits on its own line **below** the title rather than inside it, at the
 * author's instruction. A title that already carries a parenthesis — "Memory function (Revert
 * to what was actually hidden)" — cannot take a second one without reading as a list of
 * asides.
 */
@Composable
private fun FrameworkOption(
    modifier: Modifier = Modifier,
    title: String,
    summary: String? = null,
    summaryText: AnnotatedString? = null,
    recommended: String? = null,
    selected: Boolean,
    onSelect: () -> Unit,
    extra: (@Composable () -> Unit)? = null,
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .selectable(selected = selected, role = Role.RadioButton, onClick = onSelect)
            .padding(horizontal = 10.dp, vertical = 10.dp),
        verticalAlignment = Alignment.Top,
    ) {
        RadioButton(selected = selected, onClick = null)

        Column(modifier = Modifier.padding(start = 12.dp)) {
            Text(text = title, style = MaterialTheme.typography.bodyLarge)

            if (recommended != null) {
                Text(
                    text = recommended,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.primary,
                )
            }

            Spacer(modifier = Modifier.height(4.dp))

            if (summaryText != null) {
                Text(text = summaryText, style = MaterialTheme.typography.bodyMedium)
            } else if (summary != null) {
                Text(text = summary, style = MaterialTheme.typography.bodyMedium)
            }

            if (extra != null) {
                Spacer(modifier = Modifier.height(6.dp))

                extra()
            }
        }
    }
}
