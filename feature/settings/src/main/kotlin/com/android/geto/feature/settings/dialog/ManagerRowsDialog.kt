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
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.mutableStateMapOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.android.geto.designsystem.component.GetoCheckbox
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.domain.model.ManagerRows
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.ShizukuForkMode
import com.android.geto.feature.settings.R
import com.android.geto.feature.settings.SetupNextButtons
import com.android.geto.common.R as commonR

/**
 * Which rows the settings manager draws.
 *
 * The author's "Settings manager options": *"Only selected options are showed in the IMD's
 * Settings manager"*. A checkbox per target, and nothing else — this dialog changes what is on a
 * card, never what the app does to the device. See `ManagerRows` for why that is worth saying
 * twice.
 *
 * ⚠ **The order and the indentation are the manager's own**, at the author's pick from the r9
 * template: the list is a picture of the card it configures, so the row someone is looking for
 * here is in the place they last saw it there. [managerRowOrder] is this file's copy of that
 * arrangement rather than a reader of it — the manager lives in `:feature:apps`, which this module
 * cannot see, and the two are kept honest by tools/check_manager_row_order.py.
 *
 * ⚠ **A draft, committed by Save, and no Cancel** — the shape `SettingsToHideDialog` already has.
 * Ticks move a local copy; Save writes it and closes; a tap outside or a back press discards it.
 * The author asked for a Save button and declined a Cancel beside it.
 *
 * ⚠ **Save is refused with nothing ticked**, his instruction. A manager with no rows is not merely
 * empty: it is the screen someone opens *because* developer options are already off, with nothing
 * on it to switch them back on.
 */
@Composable
internal fun ManagerRowsDialog(
    modifier: Modifier = Modifier,
    states: Map<ManualRevertTarget, Boolean>,
    /**
     * Which fork is configured, which renames one row and nothing else.
     *
     * The same rename the manager itself makes — with Shevery selected that row is that service,
     * and calling it Shizuku would name an app the user has not chosen.
     */
    shizukuForkMode: ShizukuForkMode,
    /** Set by the setup flow, which draws this page flat and offers Skip beside Next. */
    onSkip: (() -> Unit)? = null,
    /** Set by the setup flow on every step that has one behind it. */
    onBack: (() -> Unit)? = null,
    stepTitle: String? = null,
    onDismissRequest: () -> Unit,
    onUpdateManagerRows: (Map<ManualRevertTarget, Boolean>) -> Unit,
) {
    // Keyed on the stored map, so a re-emission of user data while the dialog is open — which a
    // write from anywhere else in the app can cause — does not wipe ticks made since it opened.
    val draft = remember(states) {
        mutableStateMapOf<ManualRevertTarget, Boolean>().apply {
            ManualRevertTarget.entries.forEach { target ->
                put(target, states[target] ?: true)
            }
        }
    }

    val savable = ManagerRows.isSavable(draft)

    DialogContainer(
        modifier = modifier,
        // A setup page reaches its own edges; a dialog over the settings list does not.
        flat = onSkip != null,
        onDismissRequest = onDismissRequest,
    ) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = stepTitle ?: stringResource(R.string.manager_rows_title),
                style = MaterialTheme.typography.titleLarge,
            )

            Spacer(modifier = Modifier.height(12.dp))

            // ⚠ **Two sentences, the author's own.** The first says what the list is, the
            // second says what the thing it configures is *for* — which the old one line
            // ("Only selected options are showed in…") never did, and which is the question
            // somebody opening this dialog for the first time actually has.
            Text(
                text = stringResource(R.string.manager_rows_description),
                style = MaterialTheme.typography.bodyMedium,
            )

            Spacer(modifier = Modifier.height(6.dp))

            Text(
                text = stringResource(R.string.manager_rows_description_two),
                style = MaterialTheme.typography.bodyMedium,
            )

            Spacer(modifier = Modifier.height(10.dp))

            // ⚠ **Dimmed, and it is a caption rather than a sentence** — the author's *"show
            // faded 'only selected ones' just like settings manager under Accessb. and dooa"*.
            // Those two rows carry a small dimmed line under their title saying what the list
            // beneath amounts to; this is the same line doing the same job for this list.
            Text(
                text = stringResource(R.string.manager_rows_only_selected),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurface.copy(alpha = MANAGER_ROWS_CAPTION_ALPHA),
            )

            Spacer(modifier = Modifier.height(8.dp))

            managerRowOrder(shizukuForkMode.isShevery).forEach { (target, level) ->
                val checked = draft[target] == true

                // ⚠ **The last tick cannot be taken out.** Refusing the press is a plainer
                // answer than a Save button that greys itself a moment later and leaves the
                // reader working out which of six boxes did it.
                val lastOne = checked && draft.count { it.value } == 1

                ManagerRowCheckbox(
                    label = target.managerRowLabel(shizukuForkMode),
                    level = level,
                    checked = checked,
                    enabled = !lastOne,
                    onCheckedChange = { draft[target] = it },
                )
            }

            Spacer(modifier = Modifier.height(12.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                // Skip on the left and Next on the right in the flow; Save alone on the right
                // in Settings. The same arrangement the four steps before this one use.
                horizontalArrangement = if (onSkip != null) {
                    Arrangement.SpaceBetween
                } else {
                    Arrangement.End
                },
            ) {
                // ⚠ **`savable` gates both branches.** The last tick cannot be taken out, and
                // a Next that committed an empty list would be a different rule from the Save
                // beside it.
                val commit = {
                    onUpdateManagerRows(draft.toMap())

                    onDismissRequest()
                }

                if (onSkip != null) {
                    TextButton(onClick = onSkip) {
                        Text(text = stringResource(commonR.string.skip))
                    }

                    SetupNextButtons(onBack = onBack, onNext = commit, enabled = savable)
                } else {
                    TextButton(enabled = savable, onClick = commit) {
                        Text(text = stringResource(R.string.save))
                    }
                }
            }
        }
    }
}

/**
 * One row: a checkbox, indented by its depth.
 *
 * The whole row takes the press, as every list row in this app does — a checkbox on its own is a
 * small target beside a long label.
 */
@Composable
private fun ManagerRowCheckbox(
    modifier: Modifier = Modifier,
    label: String,
    level: Int,
    checked: Boolean,
    enabled: Boolean,
    onCheckedChange: (Boolean) -> Unit,
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .clickable(enabled = enabled) { onCheckedChange(!checked) }
            .padding(start = MANAGER_ROWS_INDENT * level, top = 2.dp, bottom = 2.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        GetoCheckbox(
            checked = checked,
            enabled = enabled,
            onCheckedChange = onCheckedChange,
        )

        Text(
            modifier = Modifier.padding(start = 8.dp),
            text = label,
            style = MaterialTheme.typography.bodyMedium,
        )
    }
}

/**
 * The label the manager gives this row, in this module's own copy of the strings.
 *
 * ⚠ **Not called `label`, and `check_symbol_imports` is why.** That checker collects top-level
 * declarations by name, so a top-level `label` here made every unrelated `label` in the tree — a
 * property, a parameter, a local — look like a reference to this one with a missing import: 23 of
 * them, from a baseline of zero. A name this reused does not belong at top level whoever declares
 * it, and `private` does not change that.
 */
@Composable
private fun ManualRevertTarget.managerRowLabel(shizukuForkMode: ShizukuForkMode): String =
    when (this) {
    ManualRevertTarget.DeveloperSettings ->
        stringResource(R.string.revert_defaults_developer_settings)

    ManualRevertTarget.UsbDebugging -> stringResource(R.string.revert_defaults_usb_debugging)

    ManualRevertTarget.WirelessDebugging ->
        stringResource(R.string.revert_defaults_wireless_debugging)

    ManualRevertTarget.AccessibilityServices ->
        stringResource(R.string.revert_defaults_accessibility_services)

    ManualRevertTarget.Shizuku -> stringResource(
        if (shizukuForkMode.isShevery) {
            R.string.revert_defaults_shevery
        } else {
            R.string.revert_defaults_shizuku
        },
    )

    ManualRevertTarget.DisplayOverOtherApps ->
        stringResource(R.string.revert_defaults_display_over_other_apps)
}

/**
 * The manager's own order and nesting, as target-and-depth pairs — one list per configured
 * service, because since r11 the manager draws two.
 *
 * ⚠ **A copy, and deliberately not a reader.** The arrangement lives on `rowPosition` and
 * `nestingLevel` in `AndroidSettingsManagerDialog`, which is `:feature:apps` — a module this one
 * cannot see and should not start depending on for a dozen integers. What keeps the copy honest is
 * `tools/check_manager_row_order.py`, which reads both files and compares both orders — so a
 * change made in one and not the other is caught rather than quietly leaving this list describing
 * a card that no longer looks like it. That checker was claimed here from r9 and only actually
 * written in r11; it now exists.
 *
 * ⚠ **The author's two orders**, and the r11 instruction that produced them: *"remove nesting from
 * settings manager only nest display over other apps under shevery if shevery is the toggle
 * selected"*. Under Shizuku the list is flat; under Shevery the two debugging rows swap, the
 * service moves down beside Accessibility, and overlay access hangs off it.
 */
private fun managerRowOrder(isShevery: Boolean): List<Pair<ManualRevertTarget, Int>> = if (
    isShevery
) {
    listOf(
        ManualRevertTarget.DeveloperSettings to 0,
        ManualRevertTarget.WirelessDebugging to 0,
        ManualRevertTarget.UsbDebugging to 0,
        ManualRevertTarget.AccessibilityServices to 0,
        ManualRevertTarget.Shizuku to 0,
        ManualRevertTarget.DisplayOverOtherApps to 1,
    )
} else {
    listOf(
        ManualRevertTarget.DeveloperSettings to 0,
        ManualRevertTarget.UsbDebugging to 0,
        ManualRevertTarget.WirelessDebugging to 0,
        ManualRevertTarget.Shizuku to 0,
        ManualRevertTarget.AccessibilityServices to 0,
        ManualRevertTarget.DisplayOverOtherApps to 0,
    )
}

/** The same 16 dp a level the manager indents by. */
/** The same dimming the Accessibility and Display over other apps rows use for their line. */
private const val MANAGER_ROWS_CAPTION_ALPHA = 0.7f

private val MANAGER_ROWS_INDENT = 16.dp
