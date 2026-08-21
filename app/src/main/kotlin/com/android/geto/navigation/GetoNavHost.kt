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
package com.android.geto.navigation

import androidx.compose.material3.SnackbarHostState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import com.android.geto.feature.apps.navigation.FavouriteAppsRouteData
import com.android.geto.feature.apps.navigation.appsScreen
import com.android.geto.feature.apps.navigation.favouriteAppsScreen
import com.android.geto.feature.apps.navigation.navigateToApps
import com.android.geto.feature.apps.navigation.navigateToFavouriteApps
import com.android.geto.feature.appsettings.navigation.appSettingsScreen
import com.android.geto.feature.appsettings.navigation.navigateToAppSettings
import com.android.geto.feature.home.navigation.HomeRouteData
import com.android.geto.feature.home.navigation.homeScreen
import com.android.geto.feature.settings.navigation.navigateToSettings
import com.android.geto.feature.settings.navigation.settingsScreen
import com.android.geto.navigation.TopLevelDestination.ALL_APPS
import com.android.geto.navigation.TopLevelDestination.FAVOURITE_APPS
import com.android.geto.navigation.TopLevelDestination.SETTINGS

@Composable
fun GetoNavHost(navController: NavHostController) {
    val snackbarHostState = remember { SnackbarHostState() }

    NavHost(
        navController = navController,
        startDestination = HomeRouteData::class,
    ) {
        homeScreen(
            snackbarHostState = snackbarHostState,
            topLevelDestinations = TopLevelDestination.entries,
            startDestination = FavouriteAppsRouteData::class,
            onClickHomeDestination = { homeNavHostController, homeDestination ->
                // HomeDestination is an interface, so this when is not checked for
                // exhaustiveness. The else branch keeps a forgotten tab from crashing.
                when (homeDestination) {
                    FAVOURITE_APPS -> homeNavHostController.navigateToFavouriteApps()
                    ALL_APPS -> homeNavHostController.navigateToApps()
                    SETTINGS -> homeNavHostController.navigateToSettings()
                    else -> Unit
                }
            },
            builder = {
                favouriteAppsScreen(
                    snackbarHostState = snackbarHostState,
                    onClickApp = navController::navigateToAppSettings,
                )

                appsScreen(onClickApp = navController::navigateToAppSettings)

                settingsScreen()
            },
        )

        appSettingsScreen(onNavigationIconClick = navController::navigateUp)
    }
}
