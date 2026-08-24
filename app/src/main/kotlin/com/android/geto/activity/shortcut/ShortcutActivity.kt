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
import com.android.geto.framework.launcherapps.AndroidLauncherAppsWrapper
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.launch
import javax.inject.Inject
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

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val componentName =
            intent.getStringExtra(ShortcutManagerCompatWrapper.SHORTCUT_EXTRA_COMPONENT_NAME)
                ?: return

        viewModel.applyAppSettings(componentName = componentName)

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
                        showNotConfigured()

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

    /**
     * Replaces this activity's empty window with the explanation, rather than finishing.
     *
     * The window is transparent and normally never draws anything, which is what makes a
     * shortcut feel like it launches the app directly. Here it has to say something, and
     * dismissing is what finishes it.
     */
    private fun showNotConfigured() {
        setContent {
            val userData by viewModel.userData.collectAsStateWithLifecycle()

            GetoTheme(
                theme = userData?.theme ?: Theme.FOLLOW_SYSTEM,
                dynamicTheme = userData?.dynamicTheme ?: false,
            ) {
                NotConfiguredDialog(onDismissRequest = ::finish)
            }
        }
    }

    @StringRes
    private fun contentTextFor(result: AppSettingsResult): Int = when (result) {
        AppSettingsResult.Success -> appSettingsR.string.apply_success
        AppSettingsResult.Failure -> appSettingsR.string.apply_failure
        AppSettingsResult.NoPermission -> appSettingsR.string.no_permission
        AppSettingsResult.InvalidValues -> appSettingsR.string.settings_has_invalid_values
        AppSettingsResult.EmptyAppSettings -> appSettingsR.string.empty_app_settings_list
        AppSettingsResult.DisabledAppSettings -> appSettingsR.string.app_settings_disabled
    }
}
