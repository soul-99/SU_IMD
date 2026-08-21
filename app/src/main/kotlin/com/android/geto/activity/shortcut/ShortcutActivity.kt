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

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import com.android.geto.broadcastreceiver.buildAppliedSettingsNotification
import com.android.geto.domain.framework.ShortcutManagerCompatWrapper
import com.android.geto.domain.model.AppSettingsResult
import com.android.geto.framework.launcherapps.AndroidLauncherAppsWrapper
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.launch
import javax.inject.Inject

@AndroidEntryPoint
class ShortcutActivity : ComponentActivity() {
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

        val notificationId = componentName.hashCode()

        viewModel.applyAppSettings(componentName = componentName)

        lifecycleScope.launch {
            lifecycle.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.shortcutActivityUiState.collect { shortcutActivityUiState ->
                    if (shortcutActivityUiState is ShortcutActivityUiState.Success) {
                        when (shortcutActivityUiState.appSettingsResult) {
                            AppSettingsResult.Success -> {
                                androidNotificationManagerWrapper.notify(
                                    id = notificationId,
                                    notification = buildAppliedSettingsNotification(
                                        context = this@ShortcutActivity,
                                        notificationId = notificationId,
                                        componentName = componentName,
                                        icon = shortcutActivityUiState.applicationIcon,
                                        contentTitle = getString(com.android.geto.feature.appsettings.R.string.geto_settings),
                                        contentText = getString(com.android.geto.feature.appsettings.R.string.apply_success),
                                    ),
                                )

                                androidLauncherAppsWrapper.startMainActivity(componentName = componentName)

                                finish()
                            }

                            AppSettingsResult.Failure -> {
                                androidNotificationManagerWrapper.notify(
                                    id = notificationId,
                                    notification = buildAppliedSettingsNotification(
                                        context = this@ShortcutActivity,
                                        notificationId = notificationId,
                                        componentName = componentName,
                                        icon = shortcutActivityUiState.applicationIcon,
                                        contentTitle = getString(com.android.geto.feature.appsettings.R.string.geto_settings),
                                        contentText = getString(com.android.geto.feature.appsettings.R.string.apply_failure),
                                    ),
                                )

                                finish()
                            }

                            AppSettingsResult.NoPermission -> {
                                androidNotificationManagerWrapper.notify(
                                    id = notificationId,
                                    notification = buildAppliedSettingsNotification(
                                        context = this@ShortcutActivity,
                                        notificationId = notificationId,
                                        componentName = componentName,
                                        icon = shortcutActivityUiState.applicationIcon,
                                        contentTitle = getString(com.android.geto.feature.appsettings.R.string.geto_settings),
                                        contentText = getString(com.android.geto.feature.appsettings.R.string.no_permission),
                                    ),
                                )

                                finish()
                            }

                            AppSettingsResult.InvalidValues -> {
                                androidNotificationManagerWrapper.notify(
                                    id = notificationId,
                                    notification = buildAppliedSettingsNotification(
                                        context = this@ShortcutActivity,
                                        notificationId = notificationId,
                                        componentName = componentName,
                                        icon = shortcutActivityUiState.applicationIcon,
                                        contentTitle = getString(com.android.geto.feature.appsettings.R.string.geto_settings),
                                        contentText = getString(com.android.geto.feature.appsettings.R.string.settings_has_invalid_values),
                                    ),
                                )

                                finish()
                            }

                            AppSettingsResult.EmptyAppSettings -> {
                                androidNotificationManagerWrapper.notify(
                                    id = notificationId,
                                    notification = buildAppliedSettingsNotification(
                                        context = this@ShortcutActivity,
                                        notificationId = notificationId,
                                        componentName = componentName,
                                        icon = shortcutActivityUiState.applicationIcon,
                                        contentTitle = getString(com.android.geto.feature.appsettings.R.string.geto_settings),
                                        contentText = getString(com.android.geto.feature.appsettings.R.string.empty_app_settings_list),
                                    ),
                                )

                                finish()
                            }

                            AppSettingsResult.DisabledAppSettings -> {
                                androidNotificationManagerWrapper.notify(
                                    id = notificationId,
                                    notification = buildAppliedSettingsNotification(
                                        context = this@ShortcutActivity,
                                        notificationId = notificationId,
                                        componentName = componentName,
                                        icon = shortcutActivityUiState.applicationIcon,
                                        contentTitle = getString(com.android.geto.feature.appsettings.R.string.geto_settings),
                                        contentText = getString(com.android.geto.feature.appsettings.R.string.app_settings_disabled),
                                    ),
                                )

                                finish()
                            }

                            null -> Unit
                        }
                    }
                }
            }
        }
    }
}
