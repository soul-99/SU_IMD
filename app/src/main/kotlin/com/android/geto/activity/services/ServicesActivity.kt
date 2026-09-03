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
package com.android.geto.activity.services

import android.content.Context
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.runtime.getValue
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.android.geto.common.AppLocale
import com.android.geto.common.openImdApp
import com.android.geto.designsystem.theme.GetoTheme
import com.android.geto.designsystem.theme.GetoBlurSettings
import com.android.geto.domain.model.DEFAULT_FADE_DP
import com.android.geto.domain.model.DEFAULT_RADIUS_DP
import com.android.geto.domain.model.DEFAULT_TINT_PERCENT
import com.android.geto.domain.model.Theme
import com.android.geto.feature.apps.manager.SettingsManagerRoute
import dagger.hilt.android.AndroidEntryPoint

/**
 * The settings manager on its own, with no app behind it.
 *
 * This is what the Quick Settings tile and the long-press shortcut open. It is a
 * transparent activity showing nothing but the dialog, so switching developer options back
 * on does not mean navigating into the app, finding the Favourites tab and pressing a
 * button — which is a lot of steps for something people reach for when a banking app has
 * just refused to start.
 *
 * Finishing when the dialog is dismissed is the whole lifecycle; there is no other content
 * for it to return to.
 */
@AndroidEntryPoint
class ServicesActivity : ComponentActivity() {
    // The chosen language, applied before anything reads a string. A no-op on Android 13
    // and up, where the platform has already applied it to this context.
    override fun attachBaseContext(newBase: Context) {
        super.attachBaseContext(AppLocale.wrap(newBase))
    }

    private val viewModel: ServicesActivityViewModel by viewModels()

    /**
     * The app icon on the manager's title line: bring IMD up, then get out of the way.
     *
     * ⚠ **Started before finished, and the order is the fix — r5.** This activity is translucent,
     * `excludeFromRecents`, and carries an empty `taskAffinity`, so it is a window in a task of
     * its own and IMD's window is in another. Finishing first asks the window manager to remove
     * this task and raise that one at the same moment, and which of the two the transition
     * settles on is a race: the author saw IMD arrive *behind* the manager on his razr, and saw
     * the transition into it drawn out of a window with nothing solid in it. Starting while this
     * window is still up leaves one ordinary open transition, with this one removed from behind
     * it afterwards.
     */
    private fun openImdAppAndFinish() {
        openImdApp()

        finish()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        setContent {
            val userData by viewModel.userData.collectAsStateWithLifecycle()

            // Themed from the user's own preference rather than left on the system
            // default, so the dialog does not arrive in the wrong colours over their
            // launcher.
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
                SettingsManagerRoute(
                    onDismissRequest = ::finish,
                    onOpenImdApp = ::openImdAppAndFinish,
                )
            }
        }
    }
}
