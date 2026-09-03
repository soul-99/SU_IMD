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

import android.app.NotificationManager
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.PowerManager
import android.provider.Settings
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
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
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import androidx.core.net.toUri
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import com.android.geto.designsystem.component.GetoCheckbox
import com.android.geto.designsystem.component.GetoSwitch
import com.android.geto.designsystem.icon.GetoIcons
import com.android.geto.domain.model.AutoHideRequirements
import com.android.geto.domain.model.UserData
import com.android.geto.domain.model.autoHideBlockedByHide
import com.android.geto.domain.model.autoHideSwitchOn
import com.android.geto.feature.settings.R
import kotlinx.coroutines.delay

/**
 * Everything Auto-hide settings (IMD+) needs, on one page.
 *
 * The shape is deliberate rather than a list of controls in the order they were written. The
 * switch is first because it is what the page is for; the two explanations follow it, because
 * a feature that kills and reopens the user's apps has to be understood before it is switched
 * on; then the five requirements, each saying plainly whether it is met and what to press if it
 * is not; then the two exceptions; then the notes.
 *
 * **The switch reads the live answer, not the stored one.** [autoHideSwitchOn] is off whenever
 * a requirement is missing or a hide is outstanding, whatever the user last chose — and the
 * stored choice is kept rather than overwritten, so a requirement coming back brings IMD+ back
 * with it. A switch that stayed on while the feature could not work would be the one lie this
 * page must not tell.
 */
@Composable
internal fun AutoHidePage(
    modifier: Modifier = Modifier,
    userData: UserData,
    requirements: AutoHideRequirements,
    enabling: Boolean,
    onDismissRequest: () -> Unit,
    onUpdateAutoHideEnabled: (Boolean) -> Unit,
    onSetAutoHideService: (Boolean) -> Unit,
    onRequestShizukuPermission: () -> Unit,
    onUpdateNoKillOnLaunch: (Boolean) -> Unit,
    onOpenApps: () -> Unit,
    onOpenHowItWorks: () -> Unit,
    onOpenShizukuSettings: () -> Unit,
    /**
     * Re-reads the two requirements that only Android can answer: the battery exemption and
     * whether notifications are allowed.
     *
     * Needed because neither change reaches this page on its own. Both were read once and then
     * refreshed on the activity's next resume, so granting the battery exemption from the
     * system dialog left the dot red until the user went out to the settings screen and came
     * back - the state was right and the page was simply not looking. See the poll below.
     */
    onRefreshSystemChecks: () -> Unit,
) {
    val blockedByHide = userData.autoHideBlockedByHide

    // The author's report: the switch inside this dialog moved and sprang back with nothing
    // said, while the IMD+ row on the settings list has raised this dialog for the same case
    // all along. Same dialog, same string - not a second sentence saying the same thing.
    var showSetupNotice by rememberSaveable { mutableStateOf(false) }

    if (showSetupNotice) {
        AutoHideSetupNoticeDialog(onDismissRequest = { showSetupNotice = false })
    }

    // Read once for the page rather than at the row that needs it: the notification settings
    // intent names this app's package, and this page recomposes on every requirement change.
    val context = LocalContext.current

    val packageName = remember(context) { context.packageName }

    // While this page is open, and only while it is open, ask Android again every second.
    // A resume-only refresh cannot see a permission granted by a dialog that never stopped
    // this activity, which is exactly what the battery exemption prompt is. Two cheap
    // system calls a second, for as long as somebody is looking at the dots they feed.
    LaunchedEffect(Unit) {
        while (true) {
            delay(REQUIREMENT_POLL_MILLIS)

            onRefreshSystemChecks()
        }
    }

    SettingsPage(
        modifier = modifier,
        title = stringResource(R.string.auto_hide_title),
        onDismissRequest = onDismissRequest,
    ) {
        Text(
            modifier = Modifier.padding(horizontal = 10.dp),
            text = stringResource(R.string.auto_hide_intro),
            style = MaterialTheme.typography.bodyMedium,
        )

        Spacer(modifier = Modifier.height(12.dp))

        // 1. The switch itself.
        AutoHideSwitchRow(
            title = stringResource(R.string.auto_hide_switch),
            checked = autoHideSwitchOn(userData = userData, requirements = requirements),
            // Off while a hide is outstanding, and off while the requirements are not met -
            // in both cases moving it would only write an answer that changes nothing. The
            // subtitle says which of the two it is.
            enabled = !blockedByHide,
            // ⚠ **Only for the unmet-requirements case.** `blockedByHide` keeps its own arm
            // and stays disabled: that is "not while a hide is outstanding", which its subtitle
            // already says, and answering it with a dialog about setup would be wrong rather
            // than merely missing.
            onBlocked = if (!blockedByHide && !requirements.satisfied) {
                { showSetupNotice = true }
            } else {
                null
            },
            subtitle = when {
                blockedByHide -> stringResource(R.string.auto_hide_switch_blocked)

                !requirements.satisfied -> stringResource(R.string.auto_hide_switch_incomplete)

                userData.autoHideEnabled -> stringResource(R.string.auto_hide_switch_on)

                else -> stringResource(R.string.auto_hide_switch_off)
            },
            onCheckedChange = onUpdateAutoHideEnabled,
        )

        HorizontalDivider(modifier = Modifier.padding(vertical = 8.dp))

        // 2. What it actually does, before anything else asks the user to agree to it.
        // Drawn as a link rather than as a settings row, because it opens an explanation
        // rather than changing anything.
        AutoHideHowItWorksLink(
            text = stringResource(R.string.auto_hide_how_it_works_button),
            onClick = onOpenHowItWorks,
        )

        // 3. The watched list.
        AutoHideLinkRow(
            title = stringResource(R.string.auto_hide_apps),
            subtitle = if (userData.autoHidePackages.isEmpty()) {
                stringResource(R.string.auto_hide_apps_none)
            } else {
                stringResource(R.string.auto_hide_apps_chosen, userData.autoHidePackages.size)
            },
            met = requirements.appsChosen,
            onClick = onOpenApps,
        )

        HorizontalDivider(modifier = Modifier.padding(vertical = 8.dp))

        Text(
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
            text = stringResource(R.string.auto_hide_requirements),
            style = MaterialTheme.typography.titleSmall,
            color = MaterialTheme.colorScheme.primary,
        )

        // 4. The detector. A switch rather than a link, because this is the one requirement
        // IMD can satisfy by itself - see EnableAutoHideServiceUseCase for the three steps it
        // goes through before giving up and asking the user.
        AutoHideRequirementRow(
            title = stringResource(R.string.auto_hide_req_accessibility),
            subtitle = stringResource(R.string.auto_hide_req_accessibility_note),
            met = requirements.accessibilityEnabled,
            busy = enabling,
            trailing = {
                GetoSwitch(
                    checked = requirements.accessibilityEnabled,
                    enabled = !enabling,
                    onCheckedChange = onSetAutoHideService,
                )
            },
            onClick = { if (!enabling) onSetAutoHideService(!requirements.accessibilityEnabled) },
        )

        // 5 and 6. Shizuku's two halves, and they are genuinely two: a fork can be configured
        // with no permission granted, and a permission can be granted for a fork whose fields
        // are still blank. Both are shown even when neither is needed - see below - because a
        // greyed-out pair says more than a pair that is not there.
        AutoHideRequirementRow(
            title = stringResource(R.string.auto_hide_req_shizuku_permission),
            subtitle = stringResource(R.string.auto_hide_req_shizuku_permission_note),
            met = requirements.shizukuPermission,
            optional = !requirements.shizukuNeeded,
            onClick = onRequestShizukuPermission,
        )

        AutoHideRequirementRow(
            title = stringResource(R.string.auto_hide_req_shizuku_configured),
            // Only on a fork IMD cannot drive. Nothing to go and configure, so it says so
            // rather than sending the reader to a screen that cannot help them.
            titleSuffix = if (requirements.forkSupported) {
                null
            } else {
                stringResource(R.string.auto_hide_req_shizuku_shevery)
            },
            subtitle = stringResource(R.string.auto_hide_req_shizuku_configured_note),
            met = requirements.shizukuManageable && requirements.forkSupported,
            // ⚠ **Greyed as optional only while the fork is one IMD can drive.** On Shevery
            // this requirement is not optional at any setting of the kill checkbox - see
            // AutoHideRequirements.satisfied - so greying it there would say the opposite of
            // why the switch will not move. The permission row above keeps the plain rule,
            // because a permission really is unnecessary once nothing is killed.
            optional = !requirements.shizukuNeeded && requirements.forkSupported,
            onClick = onOpenShizukuSettings,
        )

        // 7. Battery. Without this the process is frozen between runs and the detector stops
        // being delivered events, which looks exactly like IMD+ having been switched off.
        AutoHideRequirementRow(
            title = stringResource(R.string.auto_hide_req_battery),
            subtitle = stringResource(R.string.auto_hide_req_battery_note),
            met = requirements.batteryUnrestricted,
            onClick = {},
            clickable = false,
        )

        // Two ways to the same end, side by side. The first asks Android directly and is
        // answered without leaving IMD; the second opens the list, which is the way through
        // on the builds whose manufacturer ignores the direct request.
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

        // 8. Notifications, which are the only way back from a run.
        AutoHideRequirementRow(
            title = stringResource(R.string.auto_hide_req_notifications),
            subtitle = stringResource(R.string.auto_hide_req_notifications_note),
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

        HorizontalDivider(modifier = Modifier.padding(vertical = 8.dp))

        // 9. The one exception, and the whole of the Shizuku question with it: force-stopping
        // the launched app is the only thing IMD+ asks Shizuku for on its own account, so
        // ticking this makes both Shizuku rows above stop applying. See
        // AutoHideRequirements.shizukuNeeded.
        AutoHideCheckboxRow(
            label = stringResource(R.string.auto_hide_no_kill_launch),
            note = stringResource(R.string.auto_hide_no_kill_launch_note),
            checked = userData.autoHideNoKillOnLaunch,
            onCheckedChange = onUpdateNoKillOnLaunch,
        )

        Spacer(modifier = Modifier.height(8.dp))
    }
}

/**
 * "How IMD+ works", drawn as a link.
 *
 * An information mark and underlined text in the theme colour, because it is the one row on
 * this page that explains rather than configures - and a feature that closes and reopens the
 * user's apps needs its explanation to look worth opening.
 */
@Composable
internal fun AutoHideHowItWorksLink(
    modifier: Modifier = Modifier,
    text: String,
    onClick: () -> Unit,
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
            .padding(horizontal = 10.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Icon(
            modifier = Modifier.size(18.dp),
            imageVector = GetoIcons.Info,
            contentDescription = null,
            tint = MaterialTheme.colorScheme.primary,
        )

        Spacer(modifier = Modifier.width(8.dp))

        Text(
            text = text,
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.primary,
            textDecoration = TextDecoration.Underline,
        )
    }
}

/** The master switch, with its own row so the disabled case can grey the whole thing. */
@Composable
internal fun AutoHideSwitchRow(
    modifier: Modifier = Modifier,
    title: String,
    checked: Boolean,
    enabled: Boolean,
    subtitle: String,
    /**
     * Raised instead of moving the switch, when it would only spring back.
     *
     * ⚠ **The row stays [enabled] while this is set.** A disabled Switch swallows the press
     * inside its own bounds, and a master control that does nothing at all when tapped reads as
     * a broken app - the same argument the settings manager's `TargetRow` and the Shizuku
     * master switch both make.
     *
     * Null for the two callers that have nothing to explain.
     */
    onBlocked: (() -> Unit)? = null,
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
            .clickable(enabled = enabled) {
                if (onBlocked != null) onBlocked() else onCheckedChange(!checked)
            }
            .padding(horizontal = 10.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = title,
                style = MaterialTheme.typography.bodyLarge,
                color = contentColour,
            )

            Spacer(modifier = Modifier.height(4.dp))

            Text(
                text = subtitle,
                style = MaterialTheme.typography.bodySmall,
                color = contentColour,
            )
        }

        // Wrapped rather than disabled when blocked, so the press reaches the row's own
        // click above instead of dying inside the Switch.
        if (onBlocked == null) {
            GetoSwitch(checked = checked, enabled = enabled, onCheckedChange = onCheckedChange)
        } else {
            Box(modifier = Modifier.clickable(onClick = onBlocked)) {
                GetoSwitch(checked = checked, enabled = false, onCheckedChange = null)
            }
        }
    }
}

/** A row that opens something else. [met] paints the dot when the row stands for a requirement. */
@Composable
internal fun AutoHideLinkRow(
    modifier: Modifier = Modifier,
    title: String,
    subtitle: String,
    met: Boolean? = null,
    onClick: () -> Unit,
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
            .padding(horizontal = 10.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        if (met != null) {
            StatusDot(met = met)

            Spacer(modifier = Modifier.width(12.dp))
        }

        Column(modifier = Modifier.weight(1f)) {
            Text(text = title, style = MaterialTheme.typography.bodyLarge)

            Spacer(modifier = Modifier.height(4.dp))

            Text(text = subtitle, style = MaterialTheme.typography.bodySmall)
        }
    }
}

/**
 * One requirement: a dot saying whether it is met, what it is, and what to do about it.
 *
 * [optional] is for the two Shizuku rows when both kill steps are switched off. They are shown
 * greyed rather than removed, because a requirement that disappears when it stops mattering
 * leaves the user with no way to discover why it was there — and it comes back the moment
 * either checkbox is unticked.
 */
@Composable
internal fun AutoHideRequirementRow(
    modifier: Modifier = Modifier,
    title: String,
    /**
     * Appended to [title] after a space, in the error colour.
     *
     * ⚠ **Two resources for one sentence, on purpose.** The author asked for the suffix alone
     * to be red, and a single string cannot carry two colours. `title + " " + suffix` is
     * asserted in `design/_v3_r4n_imd_plus_gate.py` to be his sentence exactly, so the split
     * cannot drift from what he wrote. The space is added here because aapt strips leading
     * whitespace from an unquoted string resource.
     */
    titleSuffix: String? = null,
    subtitle: String,
    met: Boolean,
    optional: Boolean = false,
    busy: Boolean = false,
    clickable: Boolean = true,
    trailing: (@Composable () -> Unit)? = null,
    onClick: () -> Unit,
) {
    val contentColour = if (optional) {
        MaterialTheme.colorScheme.onSurface.copy(alpha = 0.38f)
    } else {
        MaterialTheme.colorScheme.onSurface
    }

    Row(
        modifier = modifier
            .fillMaxWidth()
            .clickable(enabled = clickable && !busy, onClick = onClick)
            .padding(horizontal = 10.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        if (busy) {
            CircularProgressIndicator(modifier = Modifier.size(12.dp), strokeWidth = 2.dp)
        } else {
            StatusDot(met = met, optional = optional)
        }

        Spacer(modifier = Modifier.width(12.dp))

        Column(modifier = Modifier.weight(1f)) {
            Text(
                // One paragraph rather than two Texts, so the suffix wraps with the title
                // instead of being pushed onto a line of its own on a narrow screen.
                text = buildAnnotatedString {
                    append(title)

                    if (titleSuffix != null) {
                        append(" ")

                        withStyle(SpanStyle(color = MaterialTheme.colorScheme.error)) {
                            append(titleSuffix)
                        }
                    }
                },
                style = MaterialTheme.typography.bodyLarge,
                color = contentColour,
            )

            Spacer(modifier = Modifier.height(4.dp))

            Text(
                text = subtitle,
                style = MaterialTheme.typography.bodySmall,
                color = contentColour,
            )
        }

        trailing?.let {
            Spacer(modifier = Modifier.width(12.dp))

            it()
        }
    }
}

/**
 * The green-or-red mark beside a requirement.
 *
 * A dot rather than a tick and a cross, because five ticks in a column read as a checklist the
 * user is meant to be filling in by hand — which is the opposite of the truth for the two IMD
 * satisfies for itself.
 */
@Composable
internal fun StatusDot(
    modifier: Modifier = Modifier,
    met: Boolean,
    optional: Boolean = false,
) {
    val colour: Color = when {
        optional -> MaterialTheme.colorScheme.outlineVariant

        met -> MaterialTheme.colorScheme.primary

        else -> MaterialTheme.colorScheme.error
    }

    Box(
        modifier = modifier
            .size(12.dp)
            .background(color = colour, shape = CircleShape),
    )
}

/** One of the two "do not kill" exceptions. */
@Composable
internal fun AutoHideCheckboxRow(
    modifier: Modifier = Modifier,
    label: String,
    note: String,
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit,
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .clickable { onCheckedChange(!checked) }
            .padding(horizontal = 10.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(text = label, style = MaterialTheme.typography.bodyLarge)

            Spacer(modifier = Modifier.height(4.dp))

            Text(text = note, style = MaterialTheme.typography.bodySmall)
        }

        GetoCheckbox(checked = checked, onCheckedChange = onCheckedChange)
    }
}

/**
 * Whether the two requirements Android answers directly are met right now, re-read every time
 * the page comes back to the front.
 *
 * The same arrangement the first-run setup screen uses, and for the same reason: both of these
 * are switched on from a system screen the user has to leave IMD to reach, and the page has to
 * have caught up by the time they come back rather than waiting to be tapped.
 */
@Composable
internal fun rememberAutoHideSystemChecks(): AutoHideSystemChecks {
    val context = LocalContext.current

    val checks = remember(context) { AutoHideSystemChecks(context) }

    val lifecycleOwner = LocalLifecycleOwner.current

    DisposableEffect(lifecycleOwner, checks) {
        val observer = LifecycleEventObserver { _, event ->
            if (event == Lifecycle.Event.ON_RESUME) checks.refresh()
        }

        lifecycleOwner.lifecycle.addObserver(observer)

        onDispose { lifecycleOwner.lifecycle.removeObserver(observer) }
    }

    return checks
}

/**
 * Asks Android to lift the battery restriction, and stops offering once it is lifted.
 *
 * The same shape as [NotificationPermissionButton] beside it, and for the same reason: a button
 * that still says "Disable battery optimisations" after they are already disabled invites a
 * second trip to a prompt that has nothing left to ask. Greyed out and reporting the state is
 * the more useful thing for it to be.
 *
 * Unlike notifications there is no result to wait for - the prompt is a separate activity and
 * answers nothing back - so this reads the live requirement instead, which the page's own poll
 * keeps current within a second.
 */
@Composable
internal fun BatteryOptimisationButton(
    modifier: Modifier = Modifier,
    unrestricted: Boolean,
    packageName: String,
) {
    if (unrestricted) {
        Button(
            modifier = modifier.fillMaxWidth(),
            enabled = false,
            onClick = {},
        ) {
            Text(text = stringResource(R.string.auto_hide_permission_granted))
        }

        return
    }

    SystemSettingsButton(
        modifier = modifier,
        text = stringResource(R.string.auto_hide_battery_disable),
        intent = batteryOptimisationRequestIntent(packageName = packageName),
        showIcon = false,
    )
}

/**
 * Asks Android for the notification permission, and says where the answer got to.
 *
 * Three states rather than one label, because "nothing happened" is the outcome a permission
 * button most needs to explain. Android shows its prompt once; every later request is refused
 * silently, and a button that still read "Grant notification permission" after that would look
 * broken rather than blocked. Denied says so, and the button beside it is then the way through.
 *
 * Below Android 13 there is no runtime permission to ask for — notifications are on unless they
 * were switched off for the app — so the button only reports, and the settings button beside it
 * is the only thing that can change the answer.
 */
@Composable
internal fun NotificationPermissionButton(
    modifier: Modifier = Modifier,
    allowed: Boolean,
    onRefreshSystemChecks: () -> Unit,
) {
    var denied by rememberSaveable { mutableStateOf(false) }

    val launcher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission(),
    ) { granted ->
        denied = !granted

        // The dots above this button are fed by the same read, and waiting for the next poll
        // to catch up would leave the answer on screen disagreeing with the one just given.
        onRefreshSystemChecks()
    }

    val askable = Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU && !allowed

    Button(
        modifier = modifier.fillMaxWidth(),
        enabled = askable,
        onClick = { launcher.launch(POST_NOTIFICATIONS) },
    ) {
        Text(
            text = when {
                allowed -> stringResource(R.string.auto_hide_permission_granted)

                // Denied covers both ways of ending up here: the prompt was answered
                // no, or there is no prompt to raise and notifications are off anyway.
                // Saying "Grant notification permission" on a button that cannot be
                // pressed would be the worse of the two mistakes.
                denied || !askable -> stringResource(R.string.auto_hide_notification_denied)

                else -> stringResource(R.string.auto_hide_notification_grant)
            },
        )
    }
}

/**
 * Named rather than referenced through Manifest.permission, which does not exist below the API
 * level that introduced it.
 */
private const val POST_NOTIFICATIONS = "android.permission.POST_NOTIFICATIONS"

/** How often the page re-asks Android about the requirements only it can answer. */
internal const val REQUIREMENT_POLL_MILLIS = 1_000L

/** Battery exemption and notification permission, both read straight from Android. */
internal class AutoHideSystemChecks(private val context: Context) {
    var batteryUnrestricted by mutableStateOf(context.isBatteryUnrestricted())
        private set

    var notificationsAllowed by mutableStateOf(context.areNotificationsAllowed())
        private set

    fun refresh() {
        batteryUnrestricted = context.isBatteryUnrestricted()

        notificationsAllowed = context.areNotificationsAllowed()
    }
}

/**
 * Broader than the POST_NOTIFICATIONS runtime permission on purpose: notifications can also be
 * switched off for the app in system settings, which loses the IMD+ revert just as thoroughly
 * while the permission still reads as granted.
 *
 * The platform's own answer rather than the AndroidX wrapper's, which needs a dependency this
 * module does not otherwise have. `areNotificationsEnabled` has been on NotificationManager
 * since API 24, and this app's minimum is 24.
 */
private fun Context.areNotificationsAllowed(): Boolean = runCatching {
    (getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager)
        .areNotificationsEnabled()
}.getOrDefault(false)

/**
 * Whether IMD is exempt from battery optimisation.
 *
 * Not a nicety. A frozen process stops being delivered accessibility events, so a restricted
 * IMD+ misses exactly the launches it was switched on for — and it does so silently, which
 * reads as the feature not working rather than as the battery optimiser doing its job.
 */
private fun Context.isBatteryUnrestricted(): Boolean = runCatching {
    (getSystemService(Context.POWER_SERVICE) as PowerManager)
        .isIgnoringBatteryOptimizations(packageName)
}.getOrDefault(false)

internal fun batterySettingsIntent(): Intent =
    Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS)

/**
 * Asks Android to exempt IMD directly, which is the "Let app run in the background?" prompt
 * rather than a list to find this app in.
 *
 * Needs REQUEST_IGNORE_BATTERY_OPTIMIZATIONS in the manifest - without it the screen refuses to
 * open at all. The permission only permits the asking; the user still answers the prompt.
 */
internal fun batteryOptimisationRequestIntent(packageName: String): Intent =
    Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS)
        .setData("package:$packageName".toUri())

internal fun appNotificationSettingsIntent(packageName: String): Intent =
    Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS)
        .putExtra(Settings.EXTRA_APP_PACKAGE, packageName)
