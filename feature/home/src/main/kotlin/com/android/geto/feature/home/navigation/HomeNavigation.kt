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
package com.android.geto.feature.home.navigation

import androidx.compose.foundation.layout.BoxScope
import androidx.compose.material3.SnackbarHostState
import androidx.compose.runtime.Composable
import androidx.navigation.NavGraphBuilder
import androidx.navigation.NavHostController
import androidx.navigation.compose.composable
import com.android.geto.feature.home.HomeRoute
import kotlin.reflect.KClass

fun NavGraphBuilder.homeScreen(
    snackbarHostState: SnackbarHostState,
    topLevelDestinations: List<HomeDestination>,
    startDestination: KClass<*>,
    onClickHomeDestination: (NavHostController, HomeDestination) -> Unit,
    onSettingsTabRequest: (NavHostController) -> Unit,
    /**
     * Buttons that float over the tabs rather than inside one.
     *
     * ⚠ **Outside the tab host on purpose**, at the author's *"do not move them when swiping away
     * from one tab to another"*. Anything drawn inside a destination travels with that
     * destination's slide; this slot is drawn by the home scaffold, so it stays put while the tabs
     * move underneath it. It is handed the tab that is showing so the caller can decide which tabs
     * get it - `:feature:home` has no idea what any of them are.
     */
    floatingActions: @Composable BoxScope.(HomeDestination?) -> Unit = {},
    builder: NavGraphBuilder.() -> Unit,
) {
    composable<HomeRouteData> {
        HomeRoute(
            snackbarHostState = snackbarHostState,
            topLevelDestinations = topLevelDestinations,
            startDestination = startDestination,
            onClickHomeDestination = onClickHomeDestination,
            floatingActions = floatingActions,
            onSettingsTabRequest = onSettingsTabRequest,
            builder = builder,
        )
    }
}
