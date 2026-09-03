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
package com.android.geto.feature.apps

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.android.geto.broadcastreceiver.postAppliedSettingsNotification
import com.android.geto.common.AutoRevertPending
import com.android.geto.common.showHiddenToast
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.domain.model.AppSettingsResult
import com.android.geto.domain.model.HidingFramework
import com.android.geto.ui.local.LocalLauncherApps
import com.android.geto.ui.local.LocalNotificationManager
import com.android.geto.common.R as commonR

/**
 * Shared by both tabs, because a tap now launches an app from either of them.
 *
 * It lived in the Favourites screen when Favourites was the only place that could launch.
 * Copying it into the All apps screen would have meant two places deciding what a launch
 * result means, which is exactly the sort of thing that drifts once one of them gains a
 * case the other does not.
 */
/**
 * Applies the app's settings, posts the ongoing revert notification, then opens the app — the same three steps a pinned shortcut performs, so a favourite behaves
 * identically however it is launched.
 *
 * An app with nothing configured is simply opened; there is no point refusing to launch it
 * or nagging about a configuration the user never made.
 */
@Composable
internal fun ApplyThenLaunchEffect(
    appLaunch: FavouriteAppLaunch?,
    snackbarHostState: SnackbarHostState,
    onNotConfigured: (componentName: String) -> Unit,
    onNothingToHide: () -> Unit,
    onOverlayFailure: () -> Unit,
    onAutoHideConflict: () -> Unit,
    onPermissionsLost: () -> Unit,
    onPriorHide: (componentName: String) -> Unit,
    onConsumed: () -> Unit,
) {
    val context = LocalContext.current

    val launcherApps = LocalLauncherApps.current

    val notificationManager = LocalNotificationManager.current

    val failureText = stringResource(R.string.applied_settings_failure)

    val invalidText = stringResource(R.string.applied_settings_invalid)

    LaunchedEffect(appLaunch) {
        val launch = appLaunch ?: return@LaunchedEffect

        // showSnackbar suspends until the snackbar is dismissed. Switching tabs in that
        // window cancels this effect, and without the finally the launch would never be
        // consumed — coming back would replay the snackbar.
        try {
            when (launch.result) {
                AppSettingsResult.Success -> {
                    postAppliedSettingsNotification(
                        context = context,
                        notificationManager = notificationManager,
                    )

                    // The author's completion toast. Named for the app only under Per app
                    // configuration, because that is the framework where the hide really was
                    // this app's own — under IMD defaults the same list would have been
                    // hidden whichever app was tapped, and saying "for X" would claim
                    // otherwise.
                    context.showHiddenToast(
                        appName = launch.appName
                            ?.takeIf { launch.hidingFramework == HidingFramework.PerApp },
                    )

                    // Armed only here: this is the one branch where settings were actually
                    // applied and a launch left the app. DisabledAppSettings below opens the
                    // app having changed nothing, so there is nothing to come back and undo,
                    // and a shortcut launch never reaches this file at all - which is what
                    // makes "only apps launched from within IMD" true rather than a promise.
                    AutoRevertPending.arm(componentName = launch.componentName)

                    launcherApps.startMainActivity(componentName = launch.componentName)
                }

                // Nothing has ever been configured for this app, so launching it would do
                // exactly what tapping its own icon does — which is how someone ends up
                // believing a profile is applied when none exists. DisabledAppSettings is
                // not the same case and still launches: those settings were configured and
                // then deliberately switched off.
                AppSettingsResult.EmptyAppSettings -> onNotConfigured(launch.componentName)

                // The same case one scope up: nothing is configured device-wide, so the
                // launch would hide nothing and the app would meet every setting it objects
                // to. A dialog for the same reason - this is a step not taken yet, not a
                // failure - and the app is deliberately not opened, because opening it is
                // what would make this app look broken.
                AppSettingsResult.NothingToHide -> onNothingToHide()

                AppSettingsResult.DisabledAppSettings -> {
                    launcherApps.startMainActivity(componentName = launch.componentName)
                }

                // Everything this profile would have hidden is hidden already - normally
                // because Auto-hide settings (IMD+) is holding the device down. The app opens
                // and nothing else happens: no notification, because this launch created no
                // debt and the button on one would offer to undo somebody else's work; and no
                // auto-revert marker, for the same reason.
                AppSettingsResult.AlreadyHidden -> {
                    launcherApps.startMainActivity(componentName = launch.componentName)
                }

                // The profile wants something IMD+ is not already hiding, and satisfying it
                // would leave a device that neither revert puts back. A dialog rather than a
                // snackbar: the app is not opening, and the way forward is to revert IMD+
                // first, which is a sentence rather than a word.
                AppSettingsResult.AutoHideConflict -> onAutoHideConflict()

                AppSettingsResult.Failure -> snackbarHostState.showSnackbar(message = failureText)

                // A dialog rather than the snackbar the other failures get. This one has a
                // cause the user can act on and a fix that is two steps long, and the app
                // they asked for is not opening either way.
                AppSettingsResult.OverlayFailure -> onOverlayFailure()

                AppSettingsResult.InvalidValues -> snackbarHostState.showSnackbar(message = invalidText)

                // ⚠ **A dialog now, where it used to be a snackbar.** The author's rule is
                // that a lost WRITE_SECURE_SETTINGS grant is said the same way everywhere,
                // and a snackbar is the one surface here that scrolls itself away after a
                // few seconds — for the one failure that stops every route in the app until
                // somebody goes and fixes it. Nothing was hidden and the app is not opening.
                AppSettingsResult.NoPermission -> onPermissionsLost()

                // Nothing was written and the app is not opening: the settings that are down
                // belong to a run of IMD that is no longer alive, and the user has not been
                // told. The component name rides along because both answers end in launching
                // this same app.
                AppSettingsResult.HiddenFromPreviousUse -> onPriorHide(launch.componentName)
            }
        } finally {
            onConsumed()
        }
    }
}

/**
 * Why the app did not open: nothing is ticked in the device-wide "Settings to hide".
 *
 * Since v2.1 that is where every fresh install starts - nothing is hidden until somebody says
 * what - so this is the first thing a new install meets if it taps an app before reading the
 * setup page. Launching anyway would open the app with every setting it objects to still on,
 * which looks exactly like this app doing nothing, so the launch is refused and the screen to
 * go to is named instead.
 *
 * Public rather than internal, unlike everything else in this file, because a pinned shortcut
 * has to be able to say the same thing from the app module - and a shortcut is the launch with
 * no screen of its own to fall back on.
 */
@Composable
fun NothingToHideDialog(
    modifier: Modifier = Modifier,
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
                text = stringResource(R.string.nothing_to_hide_message),
                style = MaterialTheme.typography.titleMedium,
            )

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(R.string.got_it))
                }
            }
        }
    }
}

/**
 * Why nothing happened: `WRITE_SECURE_SETTINGS` is no longer granted to IMD.
 *
 * The grant is made once from outside — over adb, or through Shizuku — and it does not survive
 * everything: a reinstall drops it, some ROM permission managers revoke it, and Android's own
 * automatic revocation takes it from an app nobody has opened for a few months. Without it not
 * one setting in this app can be written, and the failure is invisible from the outside: every
 * switch still moves and nothing on the device changes.
 *
 * **The same sentence on every route, on the author's instruction**, which is why the text lives
 * in `common` rather than here — the tile, a pinned shortcut, IMD+ and an automation intent all
 * have to say it, and half of them cannot see this module's strings.
 *
 * A dialog rather than the snackbar this used to be. Every other launch failure is one launch
 * going wrong; this one stops every route in the app until somebody goes and fixes it, and a
 * message that slides away by itself after four seconds is the wrong shape for that.
 *
 * Public rather than internal, like [NothingToHideDialog] above and for the same reason: the
 * activities behind the tile and the pinned shortcuts live in the `app` module and have to be
 * able to say the same thing.
 */
@Composable
fun PermissionsLostDialog(
    modifier: Modifier = Modifier,
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
                text = stringResource(commonR.string.permissions_lost),
                style = MaterialTheme.typography.titleMedium,
            )

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(R.string.got_it))
                }
            }
        }
    }
}

/**
 * Shown when a favourite is tapped that has no settings configured.
 *
 * A dialog rather than a snackbar: a snackbar here would be read as "something went wrong
 * with the launch", and this is not a failure — it is the app pointing out that there is
 * nothing set up yet, and saying where to set it up.
 */
@Composable
internal fun NotConfiguredDialog(
    modifier: Modifier = Modifier,
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
                text = stringResource(R.string.not_configured_title),
                style = MaterialTheme.typography.titleMedium,
            )

            Spacer(modifier = Modifier.height(10.dp))

            Text(
                text = stringResource(R.string.not_configured_message),
                style = MaterialTheme.typography.bodyMedium,
            )

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(R.string.got_it))
                }
            }
        }
    }
}
