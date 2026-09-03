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
package com.android.geto.feature.apps.navigation

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.SnackbarHostState
import androidx.compose.ui.Modifier
import androidx.navigation.NavController
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.NavGraphBuilder
import androidx.navigation.compose.composable
import com.android.geto.designsystem.component.blockTouchesWhileAnimating
import com.android.geto.feature.apps.AppsRoute

fun NavController.navigateToApps() {
    navigate(AppsRouteData) {
        popUpTo(graph.findStartDestination().id) {
            saveState = true
        }
        launchSingleTop = true
        restoreState = true
    }
}

fun NavGraphBuilder.appsScreen(
    snackbarHostState: SnackbarHostState,
    onClickApp: (
        componentName: String,
        activityLabel: String,
    ) -> Unit,
) {
    composable<AppsRouteData> {
        // See settingsScreen - a full-size wrapper for the touch blocker, no layout change.
        Box(modifier = Modifier.fillMaxSize().blockTouchesWhileAnimating(this)) {
            AppsRoute(snackbarHostState = snackbarHostState, onClickApp = onClickApp)
        }
    }
}
