/*
 *
 *   Copyright 2023 Einstein Blanco
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
package com.android.geto.activity.shortcut

import android.content.Context
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.res.stringResource
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import com.android.geto.broadcastreceiver.postAppliedSettingsNotification
import com.android.geto.common.AppLocale
import com.android.geto.common.PriorHideRestore
import com.android.geto.common.showHiddenToast
import com.android.geto.designsystem.theme.GetoTheme
import com.android.geto.designsystem.theme.GetoBlurSettings
import com.android.geto.domain.model.DEFAULT_FADE_DP
import com.android.geto.domain.model.DEFAULT_RADIUS_DP
import com.android.geto.domain.model.DEFAULT_TINT_PERCENT
import com.android.geto.domain.framework.ShortcutManagerCompatWrapper
import com.android.geto.domain.model.AppSettingsResult
import com.android.geto.domain.model.HidingFramework
import com.android.geto.domain.model.Theme
import com.android.geto.domain.usecase.OverlayStart
import com.android.geto.feature.apps.NothingToHideDialog
import com.android.geto.feature.apps.PermissionsLostDialog
import com.android.geto.designsystem.component.PriorHideDialog
import com.android.geto.designsystem.component.WaitingDialog
import com.android.geto.feature.apps.dialog.AutoHideConflictDialog
import com.android.geto.feature.apps.dialog.OverlayFailureDialog
import com.android.geto.feature.apps.dialog.ShizukuStartingDialog
import com.android.geto.framework.launcherapps.AndroidLauncherAppsWrapper
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.launch
import javax.inject.Inject
import com.android.geto.common.R as commonR

/**
 * Which terminal dialog, if any, the transparent shortcut window is currently showing.
 *
 * File-level rather than nested in the activity: an enum a `when` has to cover exhaustively is
 * easier to read - and to check - where nothing is indenting it.
 */
private enum class TerminalScreen {
    None,
    NotConfigured,
    NothingToHide,
    OverlayFailure,
    AutoHideConflict,
    PermissionsLost,

    /** Settings are down from a run of IMD that is no longer alive. */
    PriorHide,
}

@AndroidEntryPoint
class ShortcutActivity : ComponentActivity() {
    // The chosen language, applied before anything reads a string. A no-op on Android 13
    // and up, where the platform has already applied it to this context.
    override fun attachBaseContext(newBase: Context) {
        super.attachBaseContext(AppLocale.wrap(newBase))
    }

    @Inject
    lateinit var androidNotificationManagerWrapper: AndroidNotificationManagerWrapper

    @Inject
    lateinit var androidLauncherAppsWrapper: AndroidLauncherAppsWrapper

    private val viewModel: ShortcutActivityViewModel by viewModels()

    /**
     * Which terminal dialog, if any, this transparent window is currently showing.
     *
     * Held as snapshot state rather than swapped in with a second [setContent] call, because
     * the window now draws two different things at two different times - the Shizuku spinner
     * while the launch is applying, then a terminal dialog if it fails - and one composition
     * that reads this is simpler to reason about than two that race.
     */
    private var terminalScreen by mutableStateOf(TerminalScreen.None)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val componentName =
            intent.getStringExtra(ShortcutManagerCompatWrapper.SHORTCUT_EXTRA_COMPONENT_NAME)
                ?: return

        viewModel.applyAppSettings(componentName = componentName)

        setContent {
            val userData by viewModel.userData.collectAsStateWithLifecycle()

            val overlayStart by viewModel.overlayStart.collectAsStateWithLifecycle()

            val priorHideRestoring by PriorHideRestore.running.collectAsStateWithLifecycle()

            GetoTheme(
                theme = userData?.theme ?: Theme.FOLLOW_SYSTEM,
                dynamicTheme = userData?.dynamicTheme ?: false,
                oledBackground = userData?.oledBackground ?: false,
                blurSettings = GetoBlurSettings(
                    enabled = userData?.progressiveBlur ?: false,
                    radiusDp = userData?.blurRadiusDp ?: DEFAULT_RADIUS_DP,
                    tintPercent = userData?.blurTintPercent ?: DEFAULT_TINT_PERCENT,
                    fadeDp = userData?.blurFadeDp ?: DEFAULT_FADE_DP,
                ),
            ) {
                when (terminalScreen) {
                    TerminalScreen.NotConfigured -> NotConfiguredDialog(onDismissRequest = ::finish)

                    TerminalScreen.NothingToHide -> NothingToHideDialog(onDismissRequest = ::finish)

                    TerminalScreen.OverlayFailure -> OverlayFailureDialog(onDismissRequest = ::finish)

                    TerminalScreen.AutoHideConflict -> AutoHideConflictDialog(onDismissRequest = ::finish)

                    TerminalScreen.PermissionsLost -> PermissionsLostDialog(onDismissRequest = ::finish)

                    // Both answers end in this shortcut doing what it was tapped to do, so
                    // neither closes the window: the apply runs again and the collector below
                    // picks up where it left off. The transparent window stays, which is what
                    // lets the Shizuku spinner show through for a restore that has to wait.
                    TerminalScreen.PriorHide -> PriorHideDialog(
                        title = stringResource(commonR.string.prior_hide_title),
                        restoreLabel = stringResource(commonR.string.prior_hide_restore),
                        ignoreLabel = stringResource(commonR.string.prior_hide_ignore),
                        onRestore = {
                            terminalScreen = TerminalScreen.None

                            viewModel.restoreThenApply(componentName = componentName)
                        },
                        onIgnore = {
                            terminalScreen = TerminalScreen.None

                            viewModel.discardThenApply(componentName = componentName)
                        },
                    )

                    // Nothing settled yet. The window stays transparent unless overlay access
                    // is being hidden, in which case the same spinner the app shows sits over
                    // it for the Shizuku wait - so the ten seconds reads as work rather than a
                    // dead tap. Only the hide direction: a shortcut applies, it never reverts.
                    TerminalScreen.None ->
                        if (overlayStart == OverlayStart.Hide) {
                            ShizukuStartingDialog(reason = OverlayStart.Hide)
                        } else if (priorHideRestoring) {
                            // After the Shizuku branch, because that one names what is being
                            // waited for and this one only says that something is.
                            WaitingDialog(
                                text = stringResource(commonR.string.prior_hide_restoring),
                            )
                        }
                }
            }
        }

        lifecycleScope.launch {
            lifecycle.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.shortcutActivityUiState.collect { shortcutActivityUiState ->
                    if (shortcutActivityUiState !is ShortcutActivityUiState.Success) return@collect

                    val result = shortcutActivityUiState.appSettingsResult ?: return@collect

                    // Nothing was applied and nothing will be reverted, so a notification
                    // with a Revert button would be offering to undo nothing. The shortcut
                    // was made for an app that was never configured, and saying where to
                    // configure it is the only useful thing left to do.
                    if (result == AppSettingsResult.EmptyAppSettings) {
                        terminalScreen = TerminalScreen.NotConfigured

                        return@collect
                    }

                    // Nothing is ticked device-wide, so this shortcut would open the app
                    // with everything it objects to still switched on - which is the one
                    // outcome that makes the app look broken rather than unconfigured. Said
                    // here rather than in a notification, because a shortcut tapped from the
                    // home screen has no other surface to say it on.
                    if (result == AppSettingsResult.NothingToHide) {
                        terminalScreen = TerminalScreen.NothingToHide

                        return@collect
                    }

                    // ⚠ **Said here, where nothing said it before.** A lost
                    // WRITE_SECURE_SETTINGS grant used to fall past every branch in this
                    // chain and reach the plain finish() at the bottom, so a shortcut on a
                    // device whose grant had gone was a home-screen icon that did nothing
                    // whatsoever - no app, no message, no notification. The author's rule
                    // is that this one is said the same way on every route.
                    if (result == AppSettingsResult.NoPermission) {
                        terminalScreen = TerminalScreen.PermissionsLost

                        return@collect
                    }

                    // Nothing was written and the app is not opening. A shortcut has no other
                    // surface to say this on, and saying nothing is how the home-screen icon
                    // becomes a tap that silently hides over somebody else's hide.
                    if (result == AppSettingsResult.HiddenFromPreviousUse) {
                        terminalScreen = TerminalScreen.PriorHide

                        return@collect
                    }

                    // The launch is abandoned and this window is transparent, so without a
                    // dialog the shortcut is a tap that does nothing at all. That was the
                    // whole complaint: in-app launches at least got a snackbar.
                    if (result == AppSettingsResult.OverlayFailure) {
                        terminalScreen = TerminalScreen.OverlayFailure

                        return@collect
                    }

                    // Auto-hide settings (IMD+) is holding the device down with a list this
                    // profile does not fit inside. The same dialog the in-app launch shows,
                    // for the same reason: the app is not opening, and the way forward is to
                    // revert IMD+ first.
                    if (result == AppSettingsResult.AutoHideConflict) {
                        terminalScreen = TerminalScreen.AutoHideConflict

                        return@collect
                    }

                    // Everything this shortcut would have hidden is hidden already. The app
                    // opens and nothing else happens - no notification, because this launch
                    // created no debt and the button on one would offer to undo IMD+'s run.
                    if (result == AppSettingsResult.AlreadyHidden) {
                        androidLauncherAppsWrapper.startMainActivity(componentName = componentName)

                        finish()

                        return@collect
                    }

                    // Only where the device may actually have changed. The notification
                    // now says one fixed thing - "settings hidden, tap to revert" - so
                    // posting it after an outcome that wrote nothing would be a plain
                    // untruth, and an offer to undo something that never happened. A
                    // partial failure still counts: some of it may have been written.
                    if (result == AppSettingsResult.Success || result == AppSettingsResult.Failure) {
                        postAppliedSettingsNotification(
                            context = this@ShortcutActivity,
                            notificationManager = androidNotificationManagerWrapper,
                        )
                    }

                    // The author's completion toast, on the same test as the notification
                    // above. Named for the app only under Per app configuration, for the same
                    // reason the in-app launch is: under IMD defaults the shortcut hid the
                    // device-wide list, which is not this app's own.
                    if (result == AppSettingsResult.Success || result == AppSettingsResult.Failure) {
                        showHiddenToast(
                            appName = shortcutActivityUiState.appName?.takeIf {
                                shortcutActivityUiState.hidingFramework == HidingFramework.PerApp
                            },
                        )
                    }

                    if (result == AppSettingsResult.Success) {
                        androidLauncherAppsWrapper.startMainActivity(componentName = componentName)
                    }

                    finish()
                }
            }
        }
    }

}
