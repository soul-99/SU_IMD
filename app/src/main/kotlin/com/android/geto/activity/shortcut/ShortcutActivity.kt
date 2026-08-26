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
import androidx.annotation.StringRes
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import com.android.geto.broadcastreceiver.postAppliedSettingsNotification
import com.android.geto.common.AppLocale
import com.android.geto.designsystem.theme.GetoTheme
import com.android.geto.domain.framework.ShortcutManagerCompatWrapper
import com.android.geto.domain.model.AppSettingsResult
import com.android.geto.domain.model.Theme
import com.android.geto.domain.usecase.OverlayStart
import com.android.geto.feature.apps.dialog.OverlayFailureDialog
import com.android.geto.feature.apps.dialog.ShizukuStartingDialog
import com.android.geto.framework.launcherapps.AndroidLauncherAppsWrapper
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.launch
import javax.inject.Inject
import com.android.geto.feature.apps.R as appsR
import com.android.geto.feature.appsettings.R as appSettingsR

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

    private enum class TerminalScreen { None, NotConfigured, OverlayFailure }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val componentName =
            intent.getStringExtra(ShortcutManagerCompatWrapper.SHORTCUT_EXTRA_COMPONENT_NAME)
                ?: return

        viewModel.applyAppSettings(componentName = componentName)

        setContent {
            val userData by viewModel.userData.collectAsStateWithLifecycle()

            val overlayStart by viewModel.overlayStart.collectAsStateWithLifecycle()

            GetoTheme(
                theme = userData?.theme ?: Theme.FOLLOW_SYSTEM,
                dynamicTheme = userData?.dynamicTheme ?: false,
            ) {
                when (terminalScreen) {
                    TerminalScreen.NotConfigured -> NotConfiguredDialog(onDismissRequest = ::finish)

                    TerminalScreen.OverlayFailure -> OverlayFailureDialog(onDismissRequest = ::finish)

                    // Nothing settled yet. The window stays transparent unless overlay access
                    // is being hidden, in which case the same spinner the app shows sits over
                    // it for the Shizuku wait - so the ten seconds reads as work rather than a
                    // dead tap. Only the hide direction: a shortcut applies, it never reverts.
                    TerminalScreen.None ->
                        if (overlayStart == OverlayStart.Hide) {
                            ShizukuStartingDialog(reason = OverlayStart.Hide)
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

                    // The launch is abandoned and this window is transparent, so without a
                    // dialog the shortcut is a tap that does nothing at all. That was the
                    // whole complaint: in-app launches at least got a snackbar.
                    if (result == AppSettingsResult.OverlayFailure) {
                        terminalScreen = TerminalScreen.OverlayFailure

                        return@collect
                    }

                    // One notification for every other outcome, differing only in its text.
                    // This was six near-identical blocks; the shape was easy to get subtly
                    // wrong and the difference between them was one string each.
                    postAppliedSettingsNotification(
                        context = this@ShortcutActivity,
                        notificationManager = androidNotificationManagerWrapper,
                        notificationFunction = shortcutActivityUiState.notificationFunction,
                        componentName = componentName,
                        icon = shortcutActivityUiState.applicationIcon,
                        contentTitle = getString(appSettingsR.string.geto_settings),
                        contentText = getString(contentTextFor(result)),
                    )

                    if (result == AppSettingsResult.Success) {
                        androidLauncherAppsWrapper.startMainActivity(componentName = componentName)
                    }

                    finish()
                }
            }
        }
    }

    @StringRes
    private fun contentTextFor(result: AppSettingsResult): Int = when (result) {
        AppSettingsResult.Success -> appSettingsR.string.apply_success
        AppSettingsResult.Failure -> appSettingsR.string.apply_failure
        AppSettingsResult.OverlayFailure -> appsR.string.overlay_failure_title
        AppSettingsResult.NoPermission -> appSettingsR.string.no_permission
        AppSettingsResult.InvalidValues -> appSettingsR.string.settings_has_invalid_values
        AppSettingsResult.EmptyAppSettings -> appSettingsR.string.empty_app_settings_list
        AppSettingsResult.DisabledAppSettings -> appSettingsR.string.app_settings_disabled
    }
}
