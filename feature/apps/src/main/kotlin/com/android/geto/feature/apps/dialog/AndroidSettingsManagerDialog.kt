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
package com.android.geto.feature.apps.dialog

import androidx.annotation.StringRes
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.Image
import androidx.compose.foundation.clickable
import androidx.compose.foundation.combinedClickable
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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.designsystem.icon.GetoIcons
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.ManualTargetStates
import com.android.geto.feature.apps.R
import com.android.geto.designsystem.R as designR

/** Enough failed attempts to conclude the user is not going to succeed by trying again. */
private const val SHIZUKU_ATTEMPTS_BEFORE_HELP = 2

/**
 * Which rows this dialog draws.
 *
 * Every target, minus overlay access when the master switch in Advanced is off - the same
 * rule the three rows in Settings follow, so the feature is either present everywhere or
 * nowhere rather than hidden in one place and live in another.
 *
 * Removing it costs the red row that a failed restore used to turn on, so the two ways back
 * are worth naming here because this function is what takes the third one away:
 *
 *  1. The revert failure notification. It is ongoing and `setAutoCancel(false)`, so the tap
 *     that opens this dialog does not clear it: Shizuku can be started from the row below,
 *     or from its arrow out to the Shizuku app, and the notification is still in the shade
 *     afterwards with **Try again** on it. That retry restores from the persisted debt and
 *     does not go through this dialog at all.
 *  2. **Revert to default**, at the bottom of this dialog. A debt taken while the switch was
 *     on is still owed after it is switched off, so the revert still hands overlay access
 *     back - see UserData.effectiveRevertDefaults. This is the way back if the notification
 *     has been swiped away, which the user can do from Android 14 even on an ongoing one.
 */
private fun rows(manageOverlay: Boolean): List<ManualRevertTarget> =
    if (manageOverlay) {
        ManualRevertTarget.entries
    } else {
        ManualRevertTarget.entries.filter {
            it != ManualRevertTarget.DisplayOverOtherApps
        }
    }

/**
 * Manage the settings this app switches off, from one place.
 *
 * It began as a rescue hatch — once developer options are off there is no system screen
 * left to switch them back on from, and the ongoing notification can be swiped away. It is
 * now simply a control panel: every row shows what that setting is really set to and
 * switches it either way, with an arrow out to the system screen or app that owns it.
 *
 * The batch selection it used to carry is gone. Ticking boxes and then pressing a second
 * button was two steps to do what one switch now does directly, and the switches have to
 * exist anyway to show the live state.
 */
@OptIn(ExperimentalFoundationApi::class)
@Composable
internal fun AndroidSettingsManagerDialog(
    modifier: Modifier = Modifier,
    states: ManualTargetStates,
    busy: Boolean,
    shizukuStarting: Boolean,
    shizukuStartFailed: Boolean,
    overlayRestoreFailed: Boolean,
    overlayWriteInFlight: Boolean,
    /**
     * The master switch in Advanced settings. With it off the overlay row is not drawn,
     * matching the three rows it already removes from Settings; the revert failure
     * notification carries the restore instead - see [rows].
     */
    manageOverlay: Boolean = true,
    /** Null while the stored answer is still being read; see the ViewModel. */
    infoShown: Boolean? = true,
    onInfoShown: () -> Unit = {},
    onDismissRequest: () -> Unit,
    onSetEnabled: (ManualRevertTarget, Boolean) -> Unit,
    onOpen: (ManualRevertTarget) -> Unit,
    onRevertToDefault: () -> Unit,
    onOpenRevertConfiguration: () -> Unit,
) {
    var showShizukuHelp by remember { mutableStateOf(false) }

    var showInfo by remember { mutableStateOf(false) }

    // Opened for the first time, so say what this dialog is before the user reads the
    // switches as the configuration. Recorded as shown at the moment it appears rather than
    // when it is dismissed: the requirement is that it is shown once, and a dismissal that
    // never reaches the store would show it again on the next open.
    LaunchedEffect(infoShown) {
        if (infoShown == false) {
            showInfo = true

            onInfoShown()
        }
    }

    // Counts attempts to switch Shizuku on that have not taken effect yet. Shizuku can be
    // slow to come up, so the first couple of presses are simply impatience; past that it
    // is not going to work and the user needs telling why rather than a switch that keeps
    // springing back.
    var shizukuAttempts by remember { mutableIntStateOf(0) }

    val shizukuRunning = states.isEnabled(ManualRevertTarget.Shizuku)

    LaunchedEffect(shizukuRunning) {
        if (shizukuRunning) shizukuAttempts = 0
    }

    DialogContainer(
        modifier = modifier.verticalScroll(rememberScrollState()),
        onDismissRequest = onDismissRequest,
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(10.dp),
        ) {
            // The app's own icon, as the launcher draws it. This dialog is usually opened
            // from a tile or a shortcut, over somebody else's app, with nothing else on
            // screen to say which app just put a dialog in front of them.
            Row(
                modifier = Modifier.padding(10.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Image(
                    modifier = Modifier.size(32.dp),
                    painter = painterResource(designR.drawable.ic_imd_app),
                    contentDescription = null,
                )

                Spacer(modifier = Modifier.width(12.dp))

                Text(
                    text = stringResource(R.string.settings_manager_title),
                    style = MaterialTheme.typography.titleLarge,
                )

                Spacer(modifier = Modifier.width(4.dp))

                IconButton(onClick = { showInfo = true }) {
                    Icon(
                        modifier = Modifier.size(18.dp),
                        imageVector = GetoIcons.Info,
                        contentDescription = stringResource(R.string.settings_manager_info),
                        tint = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }

            Spacer(modifier = Modifier.height(4.dp))

            rows(manageOverlay = manageOverlay).forEach { target ->
                val isShizuku = target == ManualRevertTarget.Shizuku

                val isOverlay = target == ManualRevertTarget.DisplayOverOtherApps

                // Starting a Shizuku fork switches the debugging transport on by itself, so
                // while an overlay write is running these rows are about to move without the user
                // touching them. Locked rather than left live, because a press in that window
                // races the write that puts them back.
                val disturbedByOverlayWrite = overlayWriteInFlight &&
                    (isShizuku || target.usesDebuggingTransport)

                TargetRow(
                    target = target,
                    // Shizuku is the one target the app can ask for but not make happen, so
                    // it reports back. Overlay is the one whose restore can fail long after
                    // anybody was looking, so it does too.
                    starting = (isShizuku && shizukuStarting) ||
                        (isOverlay && overlayWriteInFlight),
                    failed = (isShizuku && shizukuStartFailed && !shizukuStarting) ||
                        (isOverlay && overlayRestoreFailed && !overlayWriteInFlight),
                    failureMessage = if (isOverlay) {
                        R.string.settings_manager_overlay_restore_failed
                    } else {
                        R.string.settings_manager_shizuku_failed
                    },
                    failureOpen = if (isOverlay) {
                        R.string.settings_manager_overlay_restore_failed_open
                    } else {
                        R.string.settings_manager_shizuku_failed_open
                    },
                    // Absent means the first poll has not landed yet. Off is the safer of
                    // the two to show for a beat: it invites a press that helps, where a
                    // wrong "on" invites the user to walk away from a device still locked
                    // down.
                    enabled = states.isEnabled(target),
                    // Shizuku is the only row that can be switched off in the sense of
                    // "there is nothing here to control".
                    // Locked while an attempt is in flight. The switch already reads on and
                    // the outcome is a few seconds away; letting it be pressed again would
                    // queue a second attempt against a service that is still deciding.
                    usable = !busy && !disturbedByOverlayWrite &&
                        (!isOverlay || !overlayWriteInFlight) &&
                        (!isShizuku || (states.shizukuAvailable && !shizukuStarting)),
                    onClickWhenUnusable = when {
                        isShizuku -> {
                            { showShizukuHelp = true }
                        }

                        else -> null
                    },
                    onSetEnabled = { wanted ->
                        if (isShizuku && wanted) {
                            shizukuAttempts += 1

                            if (shizukuAttempts > SHIZUKU_ATTEMPTS_BEFORE_HELP) {
                                showShizukuHelp = true

                                shizukuAttempts = 0
                            }
                        }

                        onSetEnabled(target, wanted)
                    },
                    onOpen = { onOpen(target) },
                )
            }

            Spacer(modifier = Modifier.height(4.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                // Filled, unlike Close, because it does something to the device while the
                // other one only shuts the dialog. The rows above are switches; without the
                // weight difference this would read as a third way to close.
                // Deliberately does not dismiss. The rows below are polled live, so staying
                // open is what shows the revert happening — closing would hide the one piece
                // of feedback the action has.
                // A Surface rather than a Button, only because Button has no long press and
                // this one needs one: holding it opens the configuration that decides what
                // the short press will do. Everything else here is Button's own shape,
                // colours and content padding, so it still reads as the filled button it
                // was.
                Surface(
                    modifier = Modifier.combinedClickable(
                        onClick = onRevertToDefault,
                        onLongClick = onOpenRevertConfiguration,
                        onLongClickLabel = stringResource(
                            R.string.settings_manager_configure_revert,
                        ),
                    ),
                    shape = ButtonDefaults.shape,
                    color = MaterialTheme.colorScheme.secondaryContainer,
                    contentColor = MaterialTheme.colorScheme.onSecondaryContainer,
                ) {
                    Row(
                        modifier = Modifier.padding(ButtonDefaults.ContentPadding),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Icon(
                            modifier = Modifier.size(18.dp),
                            painter = painterResource(designR.drawable.ic_revert_glyph),
                            contentDescription = null,
                        )

                        Spacer(modifier = Modifier.width(8.dp))

                        Text(text = stringResource(R.string.revert_to_default))
                    }
                }

                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(R.string.close))
                }
            }
        }
    }

    if (showInfo) {
        SettingsManagerInfoDialog(onDismissRequest = { showInfo = false })
    }

    if (showShizukuHelp) {
        ShizukuHelpDialog(onDismissRequest = { showShizukuHelp = false })
    }
}

@Composable
private fun TargetRow(
    modifier: Modifier = Modifier,
    target: ManualRevertTarget,
    enabled: Boolean,
    usable: Boolean,
    starting: Boolean = false,
    failed: Boolean = false,
    @StringRes failureMessage: Int = R.string.settings_manager_shizuku_failed,
    @StringRes failureOpen: Int = R.string.settings_manager_shizuku_failed_open,
    onClickWhenUnusable: (() -> Unit)?,
    onSetEnabled: (Boolean) -> Unit,
    onOpen: () -> Unit,
) {
    var showFailureHelp by remember { mutableStateOf(false) }

    Row(
        modifier = modifier
            .fillMaxWidth()
            .padding(start = 4.dp, top = 2.dp, bottom = 2.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                // Weighted, so it is measured after the spinner and the icon rather than
                // before them. Unweighted, a long title - "Display over other apps" is the
                // longest here - eats the whole row and leaves the icon a few pixels to
                // draw 18.dp into, which Modifier.size honours by shrinking it. That is why
                // the overlay row's red icon came out smaller than the Shizuku row's when
                // both asked for exactly the same size. fill = false so a short title still
                // sits beside its icon instead of being pushed away from it.
                Text(
                    modifier = Modifier.weight(1f, fill = false),
                    text = target.getTitle(),
                    style = MaterialTheme.typography.bodyLarge,
                )

                if (starting) {
                    Spacer(modifier = Modifier.width(8.dp))

                    // The only moving thing on the row, and the only honest answer while the
                    // app is waiting: it has asked Shizuku to start and cannot know yet.
                    CircularProgressIndicator(
                        modifier = Modifier.size(14.dp),
                        strokeWidth = 2.dp,
                    )
                }

                if (failed) {
                    Spacer(modifier = Modifier.width(6.dp))

                    Icon(
                        modifier = Modifier
                            .size(18.dp)
                            .clickable { showFailureHelp = true },
                        imageVector = GetoIcons.Info,
                        contentDescription = stringResource(failureOpen),
                        tint = MaterialTheme.colorScheme.error,
                    )
                }
            }

            // These two rows are scoped to a chosen subset rather than the whole system
            // feature, and that difference is worth saying out loud - otherwise an "off"
            // here reads as "no accessibility service is running" or "no app can draw over
            // others", which is not what either of them means.
            val scopeNote = when (target) {
                ManualRevertTarget.AccessibilityServices ->
                    R.string.settings_manager_accessibility_note

                ManualRevertTarget.DisplayOverOtherApps ->
                    R.string.settings_manager_overlay_note

                else -> null
            }

            if (scopeNote != null) {
                Text(
                    text = stringResource(scopeNote),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }

        if (target.opensSomewhere) {
            IconButton(onClick = onOpen) {
                Icon(
                    modifier = Modifier.size(18.dp),
                    imageVector = GetoIcons.OpenInNew,
                    contentDescription = stringResource(
                        R.string.settings_manager_open,
                        target.getTitle(),
                    ),
                    tint = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }

        // Red only while the failure is being reported. Material's default colours are
        // reused otherwise rather than restated, so a theme change cannot leave this row
        // looking subtly different from its neighbours.
        val switchColors = if (failed) {
            SwitchDefaults.colors(
                uncheckedThumbColor = MaterialTheme.colorScheme.error,
                uncheckedBorderColor = MaterialTheme.colorScheme.error,
                uncheckedTrackColor = MaterialTheme.colorScheme.errorContainer,
            )
        } else {
            SwitchDefaults.colors()
        }

        if (usable) {
            Switch(checked = enabled, colors = switchColors, onCheckedChange = onSetEnabled)
        } else {
            // A disabled Switch swallows taps, so an unusable row would look simply
            // broken. Wrapping it in a clickable box and handing the Switch a null
            // onCheckedChange leaves the switch with no input modifier of its own, so the
            // press falls through to the box and explains itself.
            Box(
                modifier = Modifier.clickable(enabled = onClickWhenUnusable != null) {
                    onClickWhenUnusable?.invoke()
                },
            ) {
                Switch(
                    checked = enabled,
                    enabled = false,
                    colors = switchColors,
                    onCheckedChange = null,
                )
            }
        }
    }

    if (showFailureHelp) {
        RowFailureDialog(
            message = failureMessage,
            onDismissRequest = { showFailureHelp = false },
        )
    }
}

/** What a red switch means. One dialog, because both red switches mean "read this line". */
@Composable
private fun RowFailureDialog(
    modifier: Modifier = Modifier,
    @StringRes message: Int,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(
        modifier = modifier,
        onDismissRequest = onDismissRequest,
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(20.dp),
        ) {
            Text(
                text = stringResource(message),
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

/**
 * What to do when the Shizuku switch will not move.
 *
 * Three points because there are three different things people get wrong here, and the
 * second is the one nobody guesses: this app asks Shizuku for one permission, once, and
 * has no privileged channel to Shizuku afterwards. Everything else it does with Shizuku is
 * a broadcast that Shizuku is free to ignore.
 */
@Composable
private fun ShizukuHelpDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = stringResource(R.string.shizuku_help_title),
                style = MaterialTheme.typography.titleLarge,
            )

            Spacer(modifier = Modifier.height(12.dp))

            listOf(
                R.string.shizuku_help_point_setup,
                R.string.shizuku_help_point_permission,
                R.string.shizuku_help_point_restart,
            ).forEachIndexed { index, point ->
                if (index > 0) Spacer(modifier = Modifier.height(8.dp))

                Row {
                    Text(
                        text = stringResource(R.string.shizuku_help_bullet, index + 1),
                        style = MaterialTheme.typography.bodyMedium,
                    )

                    Text(
                        modifier = Modifier.padding(start = 6.dp),
                        text = stringResource(point),
                        style = MaterialTheme.typography.bodyMedium,
                    )
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(R.string.ok))
                }
            }
        }
    }
}

/**
 * The rows a Shizuku start moves on its own.
 *
 * A fork brings the debugging transport up with it using its own WRITE_SECURE_SETTINGS, so
 * these three change without the app writing them and without the user pressing anything.
 */
private val ManualRevertTarget.usesDebuggingTransport: Boolean
    get() = this == ManualRevertTarget.DeveloperSettings ||
        this == ManualRevertTarget.UsbDebugging ||
        this == ManualRevertTarget.WirelessDebugging

/** The three rows that have a system screen or an app behind them. */
private val ManualRevertTarget.opensSomewhere: Boolean
    get() = this == ManualRevertTarget.DeveloperSettings ||
        this == ManualRevertTarget.AccessibilityServices ||
        this == ManualRevertTarget.DisplayOverOtherApps ||
        this == ManualRevertTarget.Shizuku

@Composable
internal fun ManualRevertTarget.getTitle(): String = when (this) {
    ManualRevertTarget.DeveloperSettings -> stringResource(R.string.revert_developer_settings)
    ManualRevertTarget.UsbDebugging -> stringResource(R.string.revert_usb_debugging)
    ManualRevertTarget.WirelessDebugging -> stringResource(R.string.revert_wireless_debugging)
    ManualRevertTarget.AccessibilityServices -> stringResource(R.string.revert_accessibility)
    ManualRevertTarget.Shizuku -> stringResource(R.string.revert_shizuku)
    ManualRevertTarget.DisplayOverOtherApps -> stringResource(R.string.revert_display_over_other_apps)
}
