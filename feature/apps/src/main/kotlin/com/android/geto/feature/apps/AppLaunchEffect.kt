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
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.domain.model.AppSettingsResult
import com.android.geto.ui.local.LocalLauncherApps
import com.android.geto.ui.local.LocalNotificationManager

/**
 * Shared by both tabs, because a tap now launches an app from either of them.
 *
 * It lived in the Favourites screen when Favourites was the only place that could launch.
 * Copying it into the All apps screen would have meant two places deciding what a launch
 * result means, which is exactly the sort of thing that drifts once one of them gains a
 * case the other does not.
 */
/**
 * Applies the app's settings, posts the ongoing notification with the Revert action, then
 * opens the app — the same three steps a pinned shortcut performs, so a favourite behaves
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
    onOverlayFailure: () -> Unit,
    onConsumed: () -> Unit,
) {
    val context = LocalContext.current

    val launcherApps = LocalLauncherApps.current

    val notificationManager = LocalNotificationManager.current

    val title = stringResource(R.string.applied_settings_title)

    val successText = stringResource(R.string.applied_settings_success)

    val failureText = stringResource(R.string.applied_settings_failure)

    val invalidText = stringResource(R.string.applied_settings_invalid)

    val noPermissionText = stringResource(R.string.applied_settings_no_permission)

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
                        notificationFunction = launch.notificationFunction,
                        componentName = launch.componentName,
                        icon = launch.icon,
                        contentTitle = title,
                        contentText = successText,
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

                AppSettingsResult.DisabledAppSettings -> {
                    launcherApps.startMainActivity(componentName = launch.componentName)
                }

                AppSettingsResult.Failure -> snackbarHostState.showSnackbar(message = failureText)

                // A dialog rather than the snackbar the other failures get. This one has a
                // cause the user can act on and a fix that is two steps long, and the app
                // they asked for is not opening either way.
                AppSettingsResult.OverlayFailure -> onOverlayFailure()

                AppSettingsResult.InvalidValues -> snackbarHostState.showSnackbar(message = invalidText)

                AppSettingsResult.NoPermission -> snackbarHostState.showSnackbar(message = noPermissionText)
            }
        } finally {
            onConsumed()
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
