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
package com.android.geto.activity.main

import android.content.Context
import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.viewModels
import androidx.compose.material3.Surface
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.core.content.pm.PackageInfoCompat
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.navigation.compose.rememberNavController
import com.android.geto.common.AppLocale
import com.android.geto.common.EXTRA_OPEN_REVERT_CONFIGURATION
import com.android.geto.designsystem.component.LocalRevertConfigurationRequest
import com.android.geto.designsystem.theme.GetoTheme
import com.android.geto.domain.framework.ShizukuWrapper
import com.android.geto.feature.settings.dialog.RevertDefaultsNoticeDialog
import com.android.geto.framework.launcherapps.AndroidLauncherAppsWrapper
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper
import com.android.geto.navigation.GetoNavHost
import com.android.geto.onboarding.LanguageSetupScreen
import com.android.geto.onboarding.ObtainiumDialog
import com.android.geto.onboarding.SetupScreen
import com.android.geto.onboarding.TipDialog
import com.android.geto.onboarding.rememberSetupState
import com.android.geto.ui.local.LocalLauncherApps
import com.android.geto.ui.local.LocalNotificationManager
import dagger.hilt.android.AndroidEntryPoint
import javax.inject.Inject

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    // The chosen language, applied before anything reads a string. A no-op on Android 13
    // and up, where the platform has already applied it to this context.
    override fun attachBaseContext(newBase: Context) {
        super.attachBaseContext(AppLocale.wrap(newBase))
    }

    @Inject
    lateinit var androidLauncherAppsWrapper: AndroidLauncherAppsWrapper

    @Inject
    lateinit var androidNotificationManagerWrapper: AndroidNotificationManagerWrapper

    // Injected here rather than behind a ViewModel: the setup screen is shown before the
    // nav graph exists, so it has no Hilt navigation entry point of its own, and this is
    // the one thing on it that needs a dependency.
    @Inject
    lateinit var shizukuWrapper: ShizukuWrapper

    private val viewModel: MainActivityViewModel by viewModels()

    /**
     * How many times the manager dialog has asked for the revert configuration.
     *
     * Counted rather than flagged. A boolean set true on the first request stays true, so
     * the second request changes nothing, nothing recomposes and the configuration never
     * opens again until the app is killed — which is precisely what a flag did here.
     */
    private var revertConfigurationRequest by mutableIntStateOf(0)

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)

        setIntent(intent)

        consumeRevertConfigurationRequest(intent)
    }

    /**
     * Reads the request off an intent, and takes it off again.
     *
     * Removing it matters: the same intent is handed back on every configuration change, so
     * an extra left in place would reopen the configuration on each rotation, long after the
     * press that asked for it.
     */
    private fun consumeRevertConfigurationRequest(intent: Intent) {
        if (!intent.getBooleanExtra(EXTRA_OPEN_REVERT_CONFIGURATION, false)) return

        intent.removeExtra(EXTRA_OPEN_REVERT_CONFIGURATION)

        revertConfigurationRequest += 1
    }

    /**
     * The version code of the APK actually installed.
     *
     * Read from the package manager rather than from `BuildConfig`, matching what the
     * settings screen does with the version name: every module generates its own
     * `BuildConfig`, and the one visible here is not necessarily the app's.
     *
     * Zero when the lookup fails, which matches the stored default and so simply means the
     * reminders page is shown — the harmless direction to fail in.
     */
    private val installedVersionCode: Int by lazy {
        runCatching {
            PackageInfoCompat.getLongVersionCode(
                packageManager.getPackageInfo(packageName, 0),
            ).toInt()
        }.getOrDefault(0)
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        installSplashScreen()

        enableEdgeToEdge()

        super.onCreate(savedInstanceState)

        consumeRevertConfigurationRequest(intent)

        setContent {
            CompositionLocalProvider(
                LocalLauncherApps provides androidLauncherAppsWrapper,
                LocalNotificationManager provides androidNotificationManagerWrapper,
                LocalRevertConfigurationRequest provides revertConfigurationRequest,
            ) {
                val navController = rememberNavController()

                val mainActivityUiState by viewModel.uiState.collectAsStateWithLifecycle()

                when (val uiState = mainActivityUiState) {
                    MainActivityUiState.Loading -> Unit

                    is MainActivityUiState.Success -> {
                        GetoTheme(
                            theme = uiState.userData.theme,
                            dynamicTheme = uiState.userData.dynamicTheme,
                        ) {
                            Surface {
                                val setupState = rememberSetupState()

                                // Plain remember, not rememberSaveable: this only needs
                                // to survive recomposition. Saving it would mean a user
                                // who has since granted everything still gets the setup
                                // screen after process death.
                                //
                                // A user who already has both permissions never sees the
                                // screen; a user missing one stays on it until they tap
                                // Continue, and Continue only enables once both are
                                // actually granted.
                                // Notifications are required to get *through* setup and
                                // not afterwards. Without them the Revert action on the
                                // notification is lost, but the tile, the shortcut and the
                                // in-app button all still work — so switching them off
                                // later is a choice about one route back, not a broken
                                // app, and locking the whole app behind a setup screen
                                // over it would be a punishment rather than a fix.
                                //
                                // WRITE_SECURE_SETTINGS stays mandatory forever: without
                                // it every settings write silently fails and nothing the
                                // app does works at all.
                                val setupEverCompleted = uiState.userData.setupNoticeVersion != 0

                                val permissionsMissing = if (setupEverCompleted) {
                                    !setupState.hasSecureSettings
                                } else {
                                    !setupState.isComplete
                                }

                                var showSetup by remember {
                                    mutableStateOf(permissionsMissing)
                                }

                                // The reminders page is about configuration that changes
                                // between releases, so it is gated on the version that last
                                // showed it rather than on a "seen it" flag. Someone who
                                // finished setup two versions ago has never read the
                                // current ones, and is exactly who they are written for.
                                val remindersDue = uiState.userData.setupNoticeVersion !=
                                    installedVersionCode

                                // Ahead of everything else on a new install: every screen
                                // after this one is instructions, and instructions in a
                                // language the reader does not have are worse than none.
                                // Not gated on setup being unfinished, so an install that
                                // predates this version gets the choice once as well.
                                var chooseLanguage by remember {
                                    mutableStateOf(!AppLocale.prompted(this@MainActivity))
                                }

                                if (chooseLanguage) {
                                    LanguageSetupScreen(
                                        initialTag = AppLocale.stored(this@MainActivity),
                                        onContinue = { tag ->
                                            val changed =
                                                tag != AppLocale.stored(this@MainActivity)

                                            AppLocale.markPrompted(this@MainActivity)

                                            chooseLanguage = false

                                            // Below Android 13 the screens already composed
                                            // are still in the old language, so the activity
                                            // has to come back. From 13 up the platform does
                                            // that itself when it applies the locale.
                                            if (changed &&
                                                AppLocale.set(this@MainActivity, tag)
                                            ) {
                                                recreate()
                                            }
                                        },
                                    )
                                } else if (showSetup || permissionsMissing || remindersDue) {
                                    SetupScreen(
                                        setupState = setupState,
                                        // Straight to the reminders when the only reason for
                                        // being here is an update: the permissions step is
                                        // already satisfied and asking again would read as
                                        // the app having forgotten.
                                        remindersOnly = !permissionsMissing && remindersDue,
                                        grantViaShizuku = {
                                            shizukuWrapper.grantWriteSecureSettings(
                                                packageName = packageName,
                                            )
                                        },
                                        onContinue = {
                                            viewModel.markSetupNoticeSeen(
                                                versionCode = installedVersionCode,
                                            )

                                            showSetup = false
                                        },
                                    )
                                } else {
                                    GetoNavHost(navController = navController)

                                    // Gated on a stored flag rather than on "has setup
                                    // just finished", so it also reaches anyone upgrading
                                    // into this version — they were set up long ago and
                                    // would otherwise never see it.
                                    // One at a time, in order. Two modal dialogs stacked
                                    // on a fresh install is how the second one gets
                                    // dismissed without being read.
                                    // Ahead of the two tips, because this one reports a
                                    // change the app made to their device rather than
                                    // offering advice, and because it is the only one of
                                    // the three that is ever shown to an existing install.
                                    if (uiState.userData.revertDefaultsNoticePending) {
                                        RevertDefaultsNoticeDialog(
                                            onDismissRequest =
                                                viewModel::acknowledgeRevertDefaultsNotice,
                                        )
                                    } else if (!uiState.userData.tipShown) {
                                        TipDialog(onDismissRequest = viewModel::markTipShown)
                                    } else if (!uiState.userData.obtainiumTipShown) {
                                        ObtainiumDialog(
                                            onDismissRequest = viewModel::markObtainiumTipShown,
                                        )
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
