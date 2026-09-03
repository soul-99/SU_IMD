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

import android.content.Intent
import android.provider.Settings
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.android.geto.designsystem.component.GetoCheckbox
import com.android.geto.domain.model.AutoUnhideRequirements
import com.android.geto.domain.model.UserData
import com.android.geto.domain.model.autoUnhideSwitchOn
import com.android.geto.feature.settings.R
import kotlinx.coroutines.delay
import com.android.geto.common.R as commonR

/**
 * Everything Auto unhide settings needs, on one page.
 *
 * The same shape as [AutoHidePage] and built from the same rows on purpose — the two sit next
 * to each other in the IMD+ section, and a user who has set one up should recognise the other
 * immediately rather than having to read it as something new.
 *
 * **One structural difference, and it is the interesting one.** On the IMD+ page a single
 * checkbox decided the whole Shizuku question. Here each *trigger* brings its own requirement
 * and drops it again when unticked, so the requirement rows grey out and come back as the
 * triggers above them are ticked. A page with only the screen-lock trigger on needs no
 * permission beyond the two every trigger shares.
 *
 * **The switch reads the live answer, not the stored one**, exactly as the IMD+ one does. The
 * stored choice is kept rather than overwritten, so a permission coming back brings the feature
 * back with it.
 */
@Composable
fun AutoUnhidePage(
    modifier: Modifier = Modifier,
    userData: UserData,
    requirements: AutoUnhideRequirements,
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
    stepTitle: String? = null,
    onDismissRequest: () -> Unit,
    onUpdateAutoUnhideEnabled: (Boolean) -> Unit,
    onUpdateTriggers: (onSwipe: Boolean, onScreenLock: Boolean, onIdle: Boolean) -> Unit,
    onUpdateUsedFor: (onAppLaunch: Boolean, onTile: Boolean) -> Unit,
    onOpenScreenLockMinutes: () -> Unit,
    onOpenIdleMinutes: () -> Unit,
    onGrantDumpPermission: () -> Unit,
    onShowAdbCommand: () -> Unit,
    onGrantUsageAccess: () -> Unit,
    onOpenUsageSettings: () -> Unit,
    onOpenHowItWorks: () -> Unit,
    /** See [AutoHidePage]'s parameter of the same name — the battery prompt never stops us. */
    onRefreshSystemChecks: () -> Unit,
) {
    val context = LocalContext.current

    // Raised by the master switch when it would only spring back. Its own dialog rather than
    // IMD+'s: that one's sentence is about a different feature, and this one already knows how
    // to tell a missing permission from an unticked trigger.
    var showBlocked by rememberSaveable { mutableStateOf(false) }

    if (showBlocked) {
        AutoUnhideBlockedDialog(
            // ⚠ Read as it is drawn, not as it was raised: the page behind polls every second,
            // so a permission granted while this is up must not leave it naming that permission.
            permissionsMissing = !requirements.permissionsSatisfied,
            onDismissRequest = { showBlocked = false },
        )
    }

    val packageName = remember(context) { context.packageName }

    LaunchedEffect(Unit) {
        while (true) {
            delay(REQUIREMENT_POLL_MILLIS)

            onRefreshSystemChecks()
        }
    }

    SettingsPage(
        modifier = modifier,
        title = stepTitle ?: stringResource(R.string.auto_unhide_title),
        flat = onSkip != null,
        onDismissRequest = onDismissRequest,
        actions = {
            // ⚠ **Skip switches auto unhide off here, and that is the author's decision.**
            // This page holds no draft - every control on it writes as it is moved, and its
            // permission grants cannot be taken back by a button - so a Skip that only advanced
            // would have been a second Next. Turning the feature off is the one thing "I do not
            // want this" can honestly mean.
            //
            // Only the master switch. A permission granted or a trigger ticked on the way
            // through is not auto unhide being *on*, and is left exactly as it was.
            if (onSkip != null) {
                TextButton(
                    onClick = {
                        onUpdateAutoUnhideEnabled(false)

                        onSkip()
                    },
                ) {
                    Text(text = stringResource(commonR.string.skip))
                }

                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(commonR.string.next))
                }
            }
        },
    ) {
        Text(
            modifier = Modifier.padding(horizontal = 10.dp),
            text = stringResource(R.string.auto_unhide_intro),
            style = MaterialTheme.typography.bodyMedium,
        )

        // A third line, in the theme's own green, and its own Text rather than a span inside
        // the one above: the author's two lines are verbatim and stay a single untouched
        // string, so nothing here can accidentally re-word them.
        //
        // colorScheme.primary rather than a fixed hex, unlike the About screen's shell block.
        // That block is decorative and had to be the same yellow in both themes; this is a
        // sentence the reader has to be able to read, so it takes the colour the theme has
        // already guaranteed is legible on this surface.
        Text(
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
            text = stringResource(R.string.auto_unhide_intro_battery),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.primary,
        )

        Spacer(modifier = Modifier.height(12.dp))

        // No "blocked while settings are hidden" arm, unlike IMD+. A hide being outstanding is
        // not a reason this cannot work — it is the only time it has anything to do.
        AutoHideSwitchRow(
            title = stringResource(R.string.auto_unhide_switch),
            checked = autoUnhideSwitchOn(userData = userData, requirements = requirements),
            enabled = true,
            // ⚠ **The same silence the IMD+ switch had until r4q**, reported and fixed there,
            // left here until the author asked for it too. With the requirements unmet this row
            // was live: the press stored `autoUnhideEnabled = true` and the switch sprang back,
            // because autoUnhideSwitchOn reads the requirements as well as the stored answer.
            onBlocked = if (!requirements.satisfied) {
                { showBlocked = true }
            } else {
                null
            },
            subtitle = when {
                !requirements.satisfied -> stringResource(R.string.auto_hide_switch_incomplete)

                userData.autoUnhideEnabled -> stringResource(R.string.auto_unhide_switch_on)

                else -> stringResource(R.string.auto_unhide_switch_off)
            },
            onCheckedChange = onUpdateAutoUnhideEnabled,
        )

        HorizontalDivider(modifier = Modifier.padding(vertical = 8.dp))

        AutoHideHowItWorksLink(
            text = stringResource(R.string.auto_hide_how_it_works_button),
            onClick = onOpenHowItWorks,
        )

        SectionHeading(text = stringResource(R.string.auto_unhide_used_for))

        AutoUnhideTriggerRow(
            title = stringResource(R.string.auto_unhide_used_for_launch),
            note = stringResource(R.string.auto_unhide_used_for_launch_note),
            checked = userData.autoUnhideOnAppLaunch,
            onCheckedChange = { checked ->
                onUpdateUsedFor(checked, userData.autoUnhideOnTile)
            },
        )

        AutoUnhideTriggerRow(
            title = stringResource(R.string.auto_unhide_used_for_tile),
            note = stringResource(R.string.auto_unhide_used_for_tile_note),
            checked = userData.autoUnhideOnTile,
            onCheckedChange = { checked ->
                onUpdateUsedFor(userData.autoUnhideOnAppLaunch, checked)
            },
        )

        SectionHeading(text = stringResource(R.string.auto_unhide_triggers))

        // Swipe first because it is the precise one: it says the user actually finished with
        // the app, where the two below infer it from time passing.
        AutoUnhideTriggerRow(
            title = stringResource(R.string.auto_unhide_trigger_swipe),
            note = stringResource(R.string.auto_unhide_trigger_swipe_note),
            checked = requirements.swipeChosen,
            // Not "unticked" — unavailable. The stored answer is left as the user set it so
            // that the same install on a newer Android brings the trigger back rather than
            // having quietly forgotten it.
            enabled = requirements.exitReasonsSupported,
            onCheckedChange = { checked ->
                onUpdateTriggers(checked, requirements.onScreenLock, requirements.onIdle)
            },
        )

        if (!requirements.exitReasonsSupported) {
            Text(
                modifier = Modifier.padding(start = 10.dp, end = 10.dp, bottom = 8.dp),
                text = stringResource(R.string.auto_unhide_trigger_swipe_unsupported),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.error,
            )
        }

        AutoUnhideTriggerRow(
            title = stringResource(R.string.auto_unhide_trigger_lock),
            note = stringResource(R.string.auto_unhide_trigger_lock_note),
            checked = requirements.onScreenLock,
            minutes = userData.autoUnhideScreenLockMinutes,
            onMinutesClick = onOpenScreenLockMinutes,
            onCheckedChange = { checked ->
                onUpdateTriggers(requirements.onSwipe, checked, requirements.onIdle)
            },
        )

        AutoUnhideTriggerRow(
            title = stringResource(R.string.auto_unhide_trigger_idle),
            note = stringResource(R.string.auto_unhide_trigger_idle_note),
            checked = requirements.onIdle,
            minutes = userData.autoUnhideIdleMinutes,
            onMinutesClick = onOpenIdleMinutes,
            onCheckedChange = { checked ->
                onUpdateTriggers(requirements.onSwipe, requirements.onScreenLock, checked)
            },
        )

        HorizontalDivider(modifier = Modifier.padding(vertical = 8.dp))

        SectionHeading(text = stringResource(R.string.auto_hide_requirements))

        // Greyed when no ticked trigger needs it, rather than removed - the same treatment the
        // IMD+ page gives its two Shizuku rows, and for the same reason: a requirement that
        // vanishes when it stops mattering leaves nobody able to find out why it was there.
        AutoHideRequirementRow(
            title = stringResource(R.string.auto_unhide_req_dump),
            subtitle = stringResource(R.string.auto_unhide_req_dump_note),
            met = requirements.dumpPermission,
            optional = !requirements.dumpNeeded,
            onClick = onGrantDumpPermission,
        )

        // Two routes to one grant. Shizuku is the one that needs no computer, and it only has
        // to work once - after this the detection never asks Shizuku for anything again.
        TwoButtons(
            first = {
                GrantButton(
                    modifier = it,
                    granted = requirements.dumpPermission,
                    text = stringResource(R.string.auto_unhide_dump_grant),
                    onClick = onGrantDumpPermission,
                )
            },
            second = {
                SystemSettingsTextButton(
                    modifier = it,
                    text = stringResource(R.string.auto_unhide_dump_adb),
                    onClick = onShowAdbCommand,
                )
            },
        )

        AutoHideRequirementRow(
            title = stringResource(R.string.auto_unhide_req_usage),
            subtitle = stringResource(R.string.auto_unhide_req_usage_note),
            met = requirements.usageAccess,
            optional = !requirements.usageNeeded,
            onClick = onOpenUsageSettings,
        )

        TwoButtons(
            first = {
                GrantButton(
                    modifier = it,
                    granted = requirements.usageAccess,
                    text = stringResource(R.string.auto_unhide_usage_grant),
                    onClick = onGrantUsageAccess,
                )
            },
            second = {
                SystemSettingsTextButton(
                    modifier = it,
                    text = stringResource(R.string.auto_unhide_usage_settings),
                    onClick = onOpenUsageSettings,
                )
            },
        )

        // Shared with IMD+ verbatim: same requirement, same words, same buttons.
        AutoHideRequirementRow(
            title = stringResource(R.string.auto_hide_req_battery),
            subtitle = stringResource(R.string.auto_hide_req_battery_note),
            met = requirements.batteryUnrestricted,
            onClick = {},
            clickable = false,
        )

        Row(
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            BatteryOptimisationButton(
                modifier = Modifier.weight(1f),
                unrestricted = requirements.batteryUnrestricted,
                packageName = packageName,
            )

            SystemSettingsButton(
                modifier = Modifier.weight(1f),
                text = stringResource(R.string.auto_hide_battery_settings),
                intent = batterySettingsIntent(),
                showIcon = false,
            )
        }

        // The note differs from the IMD+ one and that is not a slip: there the permission
        // carries the revert notification, here it is what a foreground service is allowed to
        // run on. Without it the watcher cannot stay alive to notice anything.
        AutoHideRequirementRow(
            title = stringResource(R.string.auto_hide_req_notifications),
            subtitle = stringResource(R.string.auto_unhide_req_notifications_note),
            met = requirements.notificationsAllowed,
            onClick = {},
            clickable = false,
        )

        Row(
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            NotificationPermissionButton(
                modifier = Modifier.weight(1f),
                allowed = requirements.notificationsAllowed,
                onRefreshSystemChecks = onRefreshSystemChecks,
            )

            SystemSettingsButton(
                modifier = Modifier.weight(1f),
                text = stringResource(R.string.auto_hide_notification_settings),
                intent = appNotificationSettingsIntent(packageName = packageName),
                showIcon = false,
            )
        }

        Spacer(modifier = Modifier.height(8.dp))
    }
}

/**
 * A grant button that stops offering once the permission is held.
 *
 * The same shape as [BatteryOptimisationButton], and for the same reason it has: a button
 * still reading "Grant dump permission" after the grant has landed invites a second trip to
 * something with nothing left to do. Saying so and going quiet is more useful.
 */
@Composable
private fun GrantButton(
    modifier: Modifier = Modifier,
    granted: Boolean,
    text: String,
    onClick: () -> Unit,
) {
    Button(
        modifier = modifier.fillMaxWidth(),
        enabled = !granted,
        onClick = onClick,
    ) {
        Text(
            text = if (granted) {
                stringResource(R.string.auto_hide_permission_granted)
            } else {
                text
            },
        )
    }
}

/** The second half of a pair, for the routes that are an action here rather than an intent. */
@Composable
private fun SystemSettingsTextButton(
    modifier: Modifier = Modifier,
    text: String,
    onClick: () -> Unit,
) {
    Button(modifier = modifier.fillMaxWidth(), onClick = onClick) {
        Text(text = text)
    }
}

/**
 * Android's own usage-access list, which is where this permission is granted by hand.
 *
 * A list of every installed app rather than a prompt for this one — Android offers no direct
 * request for usage access, which is why the Shizuku route beside it is worth having.
 */
internal fun usageAccessSettingsIntent(): Intent =
    Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS)

/** A section heading, in the theme colour, matching the IMD+ page's "Requirements". */
@Composable
private fun SectionHeading(
    modifier: Modifier = Modifier,
    text: String,
) {
    Text(
        modifier = modifier.padding(horizontal = 10.dp, vertical = 4.dp),
        text = text,
        style = MaterialTheme.typography.titleSmall,
        color = MaterialTheme.colorScheme.primary,
    )
}

/**
 * One trigger: tick it, and — for the two timed ones — set how long it waits.
 *
 * The interval sits on the row rather than in a settings sub-page because it is meaningless
 * apart from the trigger it belongs to. Tapping the row toggles; tapping the interval opens
 * the picker, and the two do not fight because the interval swallows its own tap.
 */
@Composable
private fun AutoUnhideTriggerRow(
    modifier: Modifier = Modifier,
    title: String,
    note: String,
    checked: Boolean,
    enabled: Boolean = true,
    minutes: Int? = null,
    onMinutesClick: (() -> Unit)? = null,
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
            .clickable(enabled = enabled) { onCheckedChange(!checked) }
            .padding(horizontal = 10.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        GetoCheckbox(checked = checked, enabled = enabled, onCheckedChange = onCheckedChange)

        Spacer(modifier = Modifier.width(4.dp))

        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = title,
                style = MaterialTheme.typography.bodyLarge,
                color = contentColour,
            )

            Spacer(modifier = Modifier.height(4.dp))

            Text(
                text = note,
                style = MaterialTheme.typography.bodySmall,
                color = contentColour,
            )
        }

        if (minutes != null && onMinutesClick != null) {
            Spacer(modifier = Modifier.width(8.dp))

            Surface(
                shape = RoundedCornerShape(12.dp),
                color = MaterialTheme.colorScheme.secondaryContainer,
                onClick = onMinutesClick,
                enabled = enabled && checked,
            ) {
                Text(
                    modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
                    text = stringResource(R.string.auto_unhide_minutes, minutes),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSecondaryContainer,
                )
            }
        }
    }
}

/** The paired-buttons row the requirement rows use, so the two always share the width evenly. */
@Composable
private fun TwoButtons(
    modifier: Modifier = Modifier,
    first: @Composable (Modifier) -> Unit,
    second: @Composable (Modifier) -> Unit,
) {
    Row(
        modifier = modifier.padding(horizontal = 10.dp, vertical = 4.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        first(Modifier.weight(1f))

        second(Modifier.weight(1f))
    }
}
