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

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.viewModels
import androidx.compose.material3.Surface
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.navigation.compose.rememberNavController
import com.android.geto.designsystem.theme.GetoTheme
import com.android.geto.domain.framework.ShizukuWrapper
import com.android.geto.framework.launcherapps.AndroidLauncherAppsWrapper
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper
import com.android.geto.navigation.GetoNavHost
import com.android.geto.onboarding.SetupScreen
import com.android.geto.onboarding.TipDialog
import com.android.geto.onboarding.rememberSetupState
import com.android.geto.ui.local.LocalLauncherApps
import com.android.geto.ui.local.LocalNotificationManager
import dagger.hilt.android.AndroidEntryPoint
import javax.inject.Inject

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
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

    override fun onCreate(savedInstanceState: Bundle?) {
        installSplashScreen()

        enableEdgeToEdge()

        super.onCreate(savedInstanceState)

        setContent {
            CompositionLocalProvider(
                LocalLauncherApps provides androidLauncherAppsWrapper,
                LocalNotificationManager provides androidNotificationManagerWrapper,
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
                                var showSetup by remember {
                                    mutableStateOf(!setupState.isComplete)
                                }

                                if (showSetup || !setupState.isComplete) {
                                    SetupScreen(
                                        setupState = setupState,
                                        grantViaShizuku = {
                                            shizukuWrapper.grantWriteSecureSettings(
                                                packageName = packageName,
                                            )
                                        },
                                        onContinue = { showSetup = false },
                                    )
                                } else {
                                    GetoNavHost(navController = navController)

                                    // Gated on a stored flag rather than on "has setup
                                    // just finished", so it also reaches anyone upgrading
                                    // into this version — they were set up long ago and
                                    // would otherwise never see it.
                                    if (!uiState.userData.tipShown) {
                                        TipDialog(onDismissRequest = viewModel::markTipShown)
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
