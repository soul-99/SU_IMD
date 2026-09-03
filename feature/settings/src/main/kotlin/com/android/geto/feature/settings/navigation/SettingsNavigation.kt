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
package com.android.geto.feature.settings.navigation

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.ui.Modifier
import androidx.navigation.NavController
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.NavGraphBuilder
import androidx.navigation.compose.composable
import com.android.geto.designsystem.component.blockTouchesWhileAnimating
import com.android.geto.feature.settings.SettingsRoute

fun NavController.navigateToSettings() {
    navigate(SettingsRouteData) {
        popUpTo(graph.findStartDestination().id) {
            saveState = true
        }
        launchSingleTop = true
        restoreState = true
    }
}

fun NavGraphBuilder.settingsScreen() {
    composable<SettingsRouteData> {
        // Full size around a full-size destination, so this changes no layout - it only gives
        // the transition somewhere to hang its touch blocker. See blockTouchesWhileAnimating.
        Box(modifier = Modifier.fillMaxSize().blockTouchesWhileAnimating(this)) {
            SettingsRoute()
        }
    }
}
