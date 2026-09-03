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

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.material3.Icon
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
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.unit.dp
import com.android.geto.designsystem.component.GetoCheckbox
import com.android.geto.designsystem.component.ConfigureFirstDialog
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.designsystem.component.emphasised
import com.android.geto.designsystem.icon.GetoIcons
import com.android.geto.domain.model.HidingFramework
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.ShizukuForkMode
import com.android.geto.domain.model.UnhidingFramework
import com.android.geto.feature.settings.R
import com.android.geto.feature.settings.SetupNextButtons
import com.android.geto.common.R as commonR

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
fun SettingsToHideDialog(
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
    /**
     * The heading this step wears, replacing the one this dialog carries in Settings.
     *
     * Null everywhere but the setup flow. Drawn in the theme's `primary`, which is the accent
     * the Shizuku setup page's heading and the help page's own sub-headings already use.
     */
    /**
     * Non-null turns this into a step of the setup flow.
     *
     * The page is drawn flat rather than as a dialog, and its footer carries Skip at the left
     * beside Next at the right - see `SettingsPage`, which does both.
     */
    onSkip: (() -> Unit)? = null,
    /** Set by the setup flow on every step that has one behind it. */
    onBack: (() -> Unit)? = null,
    stepTitle: String? = null,
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
    hidingFramework: HidingFramework,
    unhidingFramework: UnhidingFramework,
    /**
     * Whether a memory restore may switch wireless debugging back on.
     *
     * Drawn as a nested checkbox under the Wireless debugging row, and only under
     * [UnhidingFramework.Memory] — see the file's own note on why the other framework asks
     * its question somewhere else.
     */
    restoreWirelessDebugging: Boolean,
    onDismissRequest: () -> Unit,
    onUpdateSettingsToHide: (Map<ManualRevertTarget, Boolean>) -> Unit,
    onUpdateRestoreWirelessDebugging: (Boolean) -> Unit,
) {
    // The full map, overlay entry included, even when that row is not drawn. The draft is
    // what gets saved, so dropping the entry while the feature is switched off would quietly
    // clear a choice made while it was on and hand it back unticked later.
    var draft by remember(states) { mutableStateOf(states) }

    // Drafted like the map above rather than written on the tick, so Save commits every
    // answer in this dialog and a Back press abandons all of them together.
    var restoreWirelessDraft by remember(restoreWirelessDebugging) {
        mutableStateOf(restoreWirelessDebugging)
    }

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

    // Raised when the nested restore checkbox is ticked. The author's two points, and not the
    // one-liner the Revert to default dialog uses - see RestoreWirelessNoticeDialog.
    var showRestoreWirelessNotice by rememberSaveable { mutableStateOf(false) }

    val toggle = { target: ManualRevertTarget, enabled: Boolean ->
        draft = draft + (target to enabled)
    }

    blocked?.let { explanation ->
        ConfigureFirstDialog(
            message = explanation.message,
            paths = explanation.paths,
            dismissLabel = stringResource(R.string.understood),
            onDismissRequest = { blocked = null },
        )
    }

    if (showRestoreWirelessNotice) {
        RestoreWirelessNoticeDialog(
            onDismissRequest = { showRestoreWirelessNotice = false },
        )
    }

    SettingsPage(
        modifier = modifier,
        // The same label the row that opened this carries, so the two cannot describe
        // the list differently. Driven by the unhiding framework — see the row for why that
        // is the half that decides it.
        title = stepTitle ?: if (unhidingFramework == UnhidingFramework.Memory) {
            stringResource(R.string.settings_to_hide_both_label)
        } else {
            stringResource(R.string.settings_to_hide_defaults_label)
        },
        flat = onSkip != null,
        onDismissRequest = onDismissRequest,
        actions = {
            // ⚠ **One lambda, two labels.** Save and Next do the same three things in the same
            // order, and writing them once is what stops "Next" from quietly becoming a
            // different button from "Save".
            val commit = {
                onUpdateSettingsToHide(draft)

                onUpdateRestoreWirelessDebugging(restoreWirelessDraft)

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
        // ⚠ **Four sentences, because the answer needs both frameworks.** Which routes read
        // this list is the hiding framework's question — under Per app configuration a launch
        // reads the app's profile instead, leaving only the tile and the intents — and
        // whether the list is also the *unhide* list is the unhiding framework's. Neither
        // half can say it alone, which is why this is a table rather than two conditions.
        Text(
            modifier = Modifier.padding(horizontal = 10.dp),
            text = stringResource(
                when {
                    hidingFramework == HidingFramework.ImdDefaults &&
                        unhidingFramework == UnhidingFramework.Memory ->
                        R.string.settings_to_hide_desc_defaults_memory

                    hidingFramework == HidingFramework.ImdDefaults ->
                        R.string.settings_to_hide_desc_defaults_revert

                    unhidingFramework == UnhidingFramework.Memory ->
                        R.string.settings_to_hide_desc_per_app_memory

                    else -> R.string.settings_to_hide_desc_per_app_revert
                },
            ),
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

        // Only under the memory function. Under Revert to default the same question is asked
        // by that dialog's own Wireless debugging switch, which is the destination a revert
        // actually drives to there.
        if (unhidingFramework == UnhidingFramework.Memory) {
            NestedRestoreRow(
                label = stringResource(R.string.restore_wireless_also),
                checked = restoreWirelessDraft,
                onCheckedChange = { wanted ->
                    restoreWirelessDraft = wanted

                    // On the way on only. Switching it back off is returning to the safe
                    // default and needs no warning.
                    if (wanted) showRestoreWirelessNotice = true
                },
            )
        }

        SettingToHideRow(
            // A different string from the revert dialog's, unlike the label. Hiding is about
            // which services this app is allowed to touch; reverting is about which ones come
            // back. They were one string while they said the same thing, and stopped being
            // able to be the moment either side gained a detail the other did not have.
            label = stringResource(R.string.revert_defaults_accessibility_services),
            note = stringResource(R.string.settings_to_hide_accessibility_note),
            // Unticked while blocked, in the drawing only. See the Shizuku row below.
            checked = accessibilityManageable &&
                draft[ManualRevertTarget.AccessibilityServices] == true,
            // ⚠ **Dead with nothing selected**, on the author's instruction. IMD+'s own
            // detector is not in that selection and never was - it is held under
            // AUTO_HIDE_HOLD - which is what makes his "do not count IMD+ accessibility
            // service" true by construction, and why it is still hidden before every launch
            // whatever this row says.
            enabled = accessibilityManageable,
            onBlockedClick = {
                blocked = BlockedExplanation(
                    message = configureFirst,
                    paths = listOf(accessibilityPath),
                )
            },
            onCheckedChange = { toggle(ManualRevertTarget.AccessibilityServices, it) },
        )

        // ⚠ **Drawn on every fork since r4n, greyed where it cannot work.** It used to be
        // wrapped in `if (shizukuForkMode.supportsIntents)`, so on Shevery the row was not
        // there at all - the author reversed that: *"greyed, unchecked (memory-preserving)
        // Shizuku service checkboxes on Shevery ... just like for DOOA"*. Greying does not
        // change the engine: `effectiveSettingsToHide` already folds a refused target to
        // false, and `withoutShizukuWhenNoIntents` still keeps the entry out of a revert.
        SettingToHideRow(
            label = stringResource(R.string.revert_defaults_shizuku),
            note = stringResource(R.string.settings_to_hide_shizuku_note),
            // ⚠ **Unticked while blocked, and only in the drawing** - the same rule the two
            // rows around it follow. `draft` is untouched, so the stored answer survives both
            // 'Manage Shizuku' being switched off and the fork being Shevery, and comes back
            // when either changes; a Save in this state writes the same draft back.
            checked = shizukuBlocked == null &&
                draft[ManualRevertTarget.Shizuku] == true,
            // ⚠ **Spec item 9 plus the fork, in one expression** - see `shizukuBlocked`. This
            // row was once drawn live with the master switch off, offering to stop a service
            // IMD is not managing, which the engine had already refused.
            enabled = shizukuBlocked == null,
            onBlockedClick = { blocked = shizukuBlocked },
            // ⚠ **No pop-up on the way on any more, at the author's instruction.** It used
            // to raise a notice about each fork's own app settings every time this was
            // ticked. The same two sentences are still reachable from the fork setup dialogs
            // in Shizuku configuration, which is where a fork is chosen and where they
            // belong; here they interrupted a checkbox.
            onCheckedChange = { toggle(ManualRevertTarget.Shizuku, it) },
        )

        // ⚠ **Drawn for everyone since v3.** It used to appear only with the Manage DOOAs
        // switch on; the author removed that switch and asked for these toggles to be shown
        // to everybody and greyed when they cannot work. A press says which of the three
        // things `overlayManageable` asks about is missing, and where to go and fix it.
        SettingToHideRow(
            label = stringResource(R.string.revert_defaults_display_over_other_apps),
            // ⚠ **One note now, not two.** It used to swap for "Shizuku must be
            // configured properly in IMD settings before this can be used" - the author's
            // replacement says what the row is for rather than what is wrong with it, and the
            // row is still greyed with a BlockedExplanation naming the path when Shizuku is
            // not configured, which is where that sentence belonged all along.
            note = stringResource(R.string.settings_to_hide_overlay_note),
            // The stored answer, not the stored answer masked by whether it can run. The row
            // used to draw itself unticked with Shizuku unconfigured, which disagreed with
            // the map underneath it - greyed and honest is what every other unusable control
            // in the app does.
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

        Spacer(modifier = Modifier.height(8.dp))

        // ⚠ **Two of the four survive, and the watchdog one is not among them.** The
        // per-app note is gone because the description at the top now says which routes read
        // this list, in whichever sense the two frameworks mean it — it said the same thing
        // and would have said it twice. The Shizuku watchdog note went at the author's
        // instruction. Both of these are red now, where only one used to be.
        InfoLine(
            text = AnnotatedString(stringResource(R.string.settings_to_hide_info_all)),
            color = MaterialTheme.colorScheme.error,
        )

        InfoLine(
            text = emphasised(
                text = stringResource(R.string.settings_to_hide_info_shizuku),
                names = listOf(stringResource(R.string.settings_to_hide_name_shizuku_hide)),
            ),
            color = MaterialTheme.colorScheme.error,
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

        // ⚠ **Wrapped, because a disabled Checkbox swallows the press inside its own bounds**
        // and the row's clickable above never sees it. Half a greyed row explaining itself and
        // the other half doing nothing is worse than neither.
        Box(
            modifier = Modifier.clickable(enabled = !enabled && onBlockedClick != null) {
                onBlockedClick?.invoke()
            },
        ) {
            GetoCheckbox(
                checked = checked,
                enabled = enabled,
                onCheckedChange = if (enabled) onCheckedChange else null,
            )
        }
    }
}

/**
 * A checkbox that belongs to the row above it.
 *
 * The elbow is drawn rather than implied by indentation alone, at the author's choice from
 * the two templates. It matters more here than it would in a plain list: this row is the only
 * one in the dialog that is not itself a setting to hide, so an indent on its own would read
 * as a seventh, oddly-placed target.
 *
 * ⚠ **No `enabled` parameter, deliberately.** Every other row in this dialog can grey out;
 * this one never does, even when the Wireless debugging box above it is unticked, because the
 * settings manager's `All on` reads the same stored answer under both frameworks and whatever
 * the parent says. A control that another screen obeys must not be unreachable here.
 */
@Composable
private fun NestedRestoreRow(
    modifier: Modifier = Modifier,
    label: String,
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit,
) {
    val elbow = MaterialTheme.colorScheme.outlineVariant

    Row(
        modifier = modifier
            .fillMaxWidth()
            .clickable { onCheckedChange(!checked) }
            .padding(start = 10.dp, end = 10.dp, top = 2.dp, bottom = 6.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        // Down from the parent row, then across to the label. Drawn from the top of this row
        // rather than from the parent's baseline, because the two are siblings in a Column and
        // neither can reach into the other's bounds.
        Canvas(modifier = Modifier.size(width = 18.dp, height = 40.dp)) {
            val x = 3.dp.toPx()
            val mid = size.height / 2f
            val stroke = 1.5.dp.toPx()

            drawLine(
                color = elbow,
                start = Offset(x = x, y = 0f),
                end = Offset(x = x, y = mid),
                strokeWidth = stroke,
            )

            drawLine(
                color = elbow,
                start = Offset(x = x, y = mid),
                end = Offset(x = size.width, y = mid),
                strokeWidth = stroke,
            )
        }

        Spacer(modifier = Modifier.width(8.dp))

        Text(
            modifier = Modifier.weight(1f),
            text = label,
            style = MaterialTheme.typography.bodyMedium,
        )

        GetoCheckbox(checked = checked, onCheckedChange = onCheckedChange)
    }
}

/**
 * Why restoring wireless debugging is off by default.
 *
 * ⚠ **Two points, and not the sentence the Revert to default dialog shows.** Point 1 here
 * says IMD does not restore wireless debugging on unhiding, which is true of the memory
 * function this checkbox governs and false of the Revert to default configuration, where a
 * switch exists that does exactly that. Two dialogs rather than one shared sentence, on the
 * author's confirmation.
 *
 * The numbers are inside the strings because that is how the author wrote them. Composing
 * them from `shizuku_help_bullet`, as the numbered lists elsewhere in the app do, would mean
 * stripping his numbering to avoid printing it twice.
 */
@Composable
private fun RestoreWirelessNoticeDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = stringResource(R.string.restore_wireless_notice_1),
                style = MaterialTheme.typography.bodyMedium,
            )

            Spacer(modifier = Modifier.height(10.dp))

            Text(
                text = stringResource(R.string.restore_wireless_notice_2),
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

