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
import androidx.compose.foundation.layout.Box
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
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.android.geto.designsystem.component.GetoSwitch
import com.android.geto.designsystem.component.ConfigureFirstDialog
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.ShizukuForkMode
import com.android.geto.domain.model.UnhidingFramework
import com.android.geto.feature.settings.R
import com.android.geto.feature.settings.SetupNextButtons
import com.android.geto.common.R as commonR

/**
 * What "Revert to default" should leave each target set to.
 *
 * A configuration screen, not a control panel: nothing here changes the device. The switches
 * describe the state the user wants restored, which is why they stay where they are put even
 * when the device is currently the other way round.
 */
@Composable
internal fun RevertDefaultsDialog(
    modifier: Modifier = Modifier,
    states: Map<ManualRevertTarget, Boolean>,
    /**
     * Why the Display over other apps row is greyed, or null while it is usable.
     *
     * A list rather than a boolean because that row has three ways to be unusable and each is
     * fixed somewhere different. An **empty** list is the Shevery case: unsupported rather
     * than unconfigured, so there is nothing to point at. See `overlayBlockedPaths` on the
     * settings screen, which is the single place that decides.
     */
    overlayBlockedPaths: List<String>?,
    /** Whether anything at all is selected under 'Accessibility services to hide'. */
    accessibilityManageable: Boolean,
    /**
     * Whether 'Manage Shizuku' is on **and** the configuration under it is complete.
     *
     * The effective value, never the stored one - see `UserData.manageShizukuEffective`. With
     * it off IMD is not driving that service at all, so the row below greys rather than
     * offering to hide something the master switch has said no to.
     */
    manageShizukuEffective: Boolean,
    shizukuForkMode: ShizukuForkMode,
    /**
     * Non-null turns this into a step of the setup flow.
     *
     * The page is drawn flat rather than as a dialog, and its footer carries Skip at the left
     * beside Next at the right — see `SettingsPage`, which does both.
     */
    onSkip: (() -> Unit)? = null,
    /** Set by the setup flow on every step that has one behind it. */
    onBack: (() -> Unit)? = null,
    onDismissRequest: () -> Unit,
    unhidingFramework: UnhidingFramework,
    onUpdateRevertDefaults: (Map<ManualRevertTarget, Boolean>) -> Unit,
) {
    // The full map, overlay entry included, even when that row is not drawn - the same
    // reasoning as in SettingsToHideDialog: the draft is what gets saved.
    var draft by remember(states) { mutableStateOf(states) }

    // Raised when the Wireless debugging switch is turned on. The short sentence, not the
    // checkbox's two points - see WirelessPrivateWifiDialog.
    var showWirelessNotice by rememberSaveable { mutableStateOf(false) }

    // Null while nothing is blocked. ⚠ **A BlockedExplanation since r4n, not a list of
    // paths** - the Shizuku row on Shevery has nothing to point at *and* its own sentence, so
    // "empty list means the fork sentence" could no longer tell the two apart.
    var blocked by remember { mutableStateOf<BlockedExplanation?>(null) }

    val accessibilityPath = stringResource(R.string.help_path_accessibility)

    val manageShizukuPath = stringResource(R.string.help_path_manage_shizuku)

    // Hoisted because stringResource cannot be called from inside the row callbacks below.
    val configureFirst = stringResource(R.string.configure_first)

    val dooaThedjchiOnly = stringResource(R.string.dooa_thedjchi_only)

    val shizukuThedjchiOnly = stringResource(R.string.shizuku_thedjchi_only)

    // ⚠ **One expression for the Shizuku row's three states, read by `checked`, by `enabled`
    // and by the press.** `null` is exactly the answer `UserData.canHide` gives for the
    // Shizuku target - 'Manage Shizuku' on and a fork that answers intents - so the row and
    // the engine cannot disagree. The fork case comes first: on Shevery there is nothing to
    // go and switch on, so sending the reader to Manage Shizuku would be sending them
    // nowhere.
    //
    // ⚠ Spelled without its brackets on purpose: check18_missing_imports matches
    // `.canHide` followed by an open bracket against the whole file, comments included, and
    // would read this sentence as an unimported call.
    val shizukuBlocked: BlockedExplanation? = when {
        !shizukuForkMode.supportsIntents -> BlockedExplanation(message = shizukuThedjchiOnly)

        !manageShizukuEffective -> BlockedExplanation(
            message = configureFirst,
            paths = listOf(manageShizukuPath),
        )

        else -> null
    }

    blocked?.let { explanation ->
        ConfigureFirstDialog(
            message = explanation.message,
            paths = explanation.paths,
            dismissLabel = stringResource(R.string.understood),
            onDismissRequest = { blocked = null },
        )
    }

    if (showWirelessNotice) {
        WirelessPrivateWifiDialog(onDismissRequest = { showWirelessNotice = false })
    }

    // Each row sets only itself. Shizuku used to drag USB debugging with it and vice versa,
    // which meant a tap could silently undo a choice the user had made two rows up.
    val toggle = { target: ManualRevertTarget, enabled: Boolean ->
        draft = draft + (target to enabled)
    }

    SettingsPage(
        modifier = modifier,
        // Two lines under Revert to default, one under the memory function — the same
        // label as the row, at the author's instruction.
        title = if (unhidingFramework == UnhidingFramework.Memory) {
            stringResource(R.string.revert_defaults)
        } else {
            stringResource(R.string.revert_defaults_entry_both)
        },
        // ⚠ **No stepTitle parameter, unlike the other three steps.** This page already
        // computes its own title from the author's labels, and computes it *differently* under
        // the memory function — see above. A fixed heading passed in from the flow would be one
        // of those two and wrong half the time.
        flat = onSkip != null,
        onDismissRequest = onDismissRequest,
        actions = {
            // One lambda, two labels: Save and Next do the same two things in the same order,
            // and writing them once is what stops them drifting apart.
            val commit = {
                onUpdateRevertDefaults(draft)

                onDismissRequest()
            }

            if (onSkip != null) {
                TextButton(onClick = onSkip) {
                    Text(text = stringResource(commonR.string.skip))
                }

                SetupNextButtons(onBack = onBack, onNext = commit)
            } else {
                TextButton(onClick = commit) {
                    Text(text = stringResource(R.string.save))
                }
            }
        },
    ) {
        // ⚠ **What this is for, before what it does** - the author's placement. The
        // paragraph below answers "when does this run", and answers it differently under the
        // two unhiding frameworks; this answers "why would I fill this in", which has the same
        // answer either way. Its own Text rather than folded into both of those strings,
        // which would have been two copies of one sentence, free to drift apart.
        Text(
            modifier = Modifier.padding(horizontal = 10.dp),
            text = stringResource(R.string.revert_defaults_desc_recover),
            style = MaterialTheme.typography.bodyMedium,
            fontWeight = FontWeight.Bold,
        )

        Spacer(modifier = Modifier.height(8.dp))

        // Says when this runs, which the title does not: "Revert to default" is the
        // name of five different buttons, and someone arriving here from the settings
        // list has just read "Settings to hide" one row above.
        Text(
            modifier = Modifier.padding(horizontal = 10.dp),
            // Under the memory function this list is no longer what an ordinary unhide
            // reads — memory is — so it drops to being what the named `Revert to default`
            // function drives, and says so rather than claiming every unhide.
            text = stringResource(
                if (unhidingFramework == UnhidingFramework.Memory) {
                    R.string.revert_defaults_desc_memory
                } else {
                    R.string.revert_defaults_desc_revert
                },
            ),
            style = MaterialTheme.typography.bodyMedium,
        )

        Spacer(modifier = Modifier.height(4.dp))

        RevertDefaultRow(
            label = stringResource(R.string.revert_defaults_developer_settings),
            checked = draft[ManualRevertTarget.DeveloperSettings] == true,
            onCheckedChange = { toggle(ManualRevertTarget.DeveloperSettings, it) },
        )

        RevertDefaultRow(
            label = stringResource(R.string.revert_defaults_usb_debugging),
            checked = draft[ManualRevertTarget.UsbDebugging] == true,
            onCheckedChange = { toggle(ManualRevertTarget.UsbDebugging, it) },
        )

        RevertDefaultRow(
            label = stringResource(R.string.revert_defaults_wireless_debugging),
            checked = draft[ManualRevertTarget.WirelessDebugging] == true,
            onCheckedChange = { wanted ->
                toggle(ManualRevertTarget.WirelessDebugging, wanted)

                // On the way on only. This switch is the one thing in the app that can leave
                // a device listening on the network after a revert, and it says so once.
                if (wanted) showWirelessNotice = true
            },
        )

        RevertDefaultRow(
            label = stringResource(R.string.revert_defaults_accessibility_services),
            note = stringResource(R.string.revert_defaults_accessibility_note),
            // Unticked while blocked, in the drawing only - the author's rule for every
            // greyed control. The draft keeps the stored answer.
            checked = accessibilityManageable &&
                draft[ManualRevertTarget.AccessibilityServices] == true,
            // Dead with nothing selected, exactly as in Settings to hide/unhide - see the
            // matching row there for why IMD+'s own detector is not part of this question.
            enabled = accessibilityManageable,
            onBlockedClick = {
                blocked = BlockedExplanation(
                    message = configureFirst,
                    paths = listOf(accessibilityPath),
                )
            },
            onCheckedChange = { toggle(ManualRevertTarget.AccessibilityServices, it) },
        )

        // ⚠ **Drawn on every fork since r4n, greyed where it cannot work** - the author's
        // reversal, and the same treatment the row above it gets. On Shevery the service
        // still comes back only when its own ErrorProtect watchdog sees the debugging
        // transport again, which the debugging rows above decide; the row says so by being
        // greyed rather than by being absent.
        RevertDefaultRow(
            label = stringResource(R.string.revert_defaults_shizuku),
            // ⚠ **No note, at the author's instruction.** "Depending on which method Shizuku
            // uses to keep service alive, it will enable/disable USB or wireless debugging" was
            // the only one of the three he did not replace, so it goes. Its string is kept
            // rather than deleted: removing an English entry that eleven locales still carry is
            // what check_translations reports as eleven invented names.
            // Unticked and greyed while blocked, in the drawing only - spec item 9 names this
            // dialog as well as the hide one, and r4n adds the fork to the same expression.
            checked = shizukuBlocked == null &&
                draft[ManualRevertTarget.Shizuku] == true,
            enabled = shizukuBlocked == null,
            onBlockedClick = { blocked = shizukuBlocked },
            onCheckedChange = { toggle(ManualRevertTarget.Shizuku, it) },
        )

        // ⚠ **Drawn for everyone since v3**, and greyed rather than hidden when it cannot
        // work. Greying it does not abandon anything already hidden: a revert still hands
        // overlay access back to apps IMD took it from, whatever this row says - see
        // UserData.effectiveRevertDefaults.
        RevertDefaultRow(
            label = stringResource(R.string.revert_defaults_display_over_other_apps),
            // One note now - see the same row in SettingsToHideDialog.
            note = stringResource(R.string.revert_defaults_overlay_note),
            // ⚠ **Unchecked while blocked, at the author's instruction - and only in the
            // drawing.** `draft` is not touched, so the stored selection survives Manage
            // Shizuku being switched off and comes back when it is switched on again; a Save
            // taken in this state writes the same draft back rather than quietly clearing it.
            //
            // `== null` and not `isNullOrEmpty()`: an empty list is the Shevery case, blocked
            // because the fork cannot do this at all, and it is still blocked. Only no list
            // at all means allowed - the convention the line below has always used.
            checked = overlayBlockedPaths == null &&
                draft[ManualRevertTarget.DisplayOverOtherApps] == true,
            enabled = overlayBlockedPaths == null,
            onBlockedClick = {
                blocked = BlockedExplanation(
                    // The fork sentence when there is nothing to point at, his configure-first
                    // one otherwise - the same choice the old empty-list convention made, now
                    // written where it is made instead of inferred at the dialog.
                    message = if (overlayBlockedPaths.isNullOrEmpty()) {
                        dooaThedjchiOnly
                    } else {
                        configureFirst
                    },
                    paths = overlayBlockedPaths.orEmpty(),
                )
            },
            onCheckedChange = { toggle(ManualRevertTarget.DisplayOverOtherApps, it) },
        )
    }
}

/**
 * What turning the Wireless debugging switch on means for a device on a public network.
 *
 * ⚠ **One sentence, not the two-point notice** the nested checkbox in Settings to hide/unhide
 * raises. That one opens by saying IMD does not restore wireless debugging on unhiding, which
 * is exactly what this switch makes untrue — so the shared half is all this dialog says.
 */
@Composable
private fun WirelessPrivateWifiDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = stringResource(R.string.wireless_private_wifi_notice),
                style = MaterialTheme.typography.bodyLarge,
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
 * One target's row.
 *
 * [note] is the small print under a label, for the two rows whose switch does something
 * narrower or broader than the label alone suggests: accessibility services, which governs
 * only the services picked elsewhere in settings rather than every service on the device,
 * and Shizuku, which brings a debugging transport up with it.
 */
@Composable
private fun RevertDefaultRow(
    modifier: Modifier = Modifier,
    label: String,
    note: String? = null,
    checked: Boolean,
    enabled: Boolean = true,
    /**
     * What a press on a greyed row does.
     *
     * ⚠ **Without this a disabled control swallows the tap**, inside its own bounds, so the
     * row's own `clickable` never sees it - and a row that does nothing at all is how somebody
     * decides the app is broken rather than that they have something left to configure. The
     * settings manager's `TargetRow` has had this since r2b; the author asked for the same of
     * every greyed toggle in v3.
     */
    onBlockedClick: (() -> Unit)? = null,
    onCheckedChange: (Boolean) -> Unit,
) {
    val contentColour = if (enabled) {
        MaterialTheme.colorScheme.onSurface
    } else {
        MaterialTheme.colorScheme.onSurface.copy(alpha = 0.38f)
    }

    Row(
        modifier = modifier
            .fillMaxWidth()
            .clickable(enabled = enabled || onBlockedClick != null) {
                if (enabled) onCheckedChange(!checked) else onBlockedClick?.invoke()
            }
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

        // Wrapped for the same reason the checkbox in Settings to hide/unhide is: a disabled
        // Switch swallows the press inside its own bounds.
        Box(
            modifier = Modifier.clickable(enabled = !enabled && onBlockedClick != null) {
                onBlockedClick?.invoke()
            },
        ) {
            GetoSwitch(
                checked = checked,
                enabled = enabled,
                onCheckedChange = if (enabled) onCheckedChange else null,
            )
        }
    }
}
