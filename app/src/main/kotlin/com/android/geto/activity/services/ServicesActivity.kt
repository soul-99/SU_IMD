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
import com.android.geto.designsystem.theme.GetoTheme
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
            ) {
                SettingsManagerRoute(onDismissRequest = ::finish)
            }
        }
    }
}
