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
package com.android.geto.feature.home

import androidx.compose.foundation.layout.consumeWindowInsets
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.LargeTopAppBar
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBarDefaults.exitUntilCollapsedScrollBehavior
import androidx.compose.material3.adaptive.navigationsuite.NavigationSuiteScaffold
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.ExperimentalComposeUiApi
import androidx.compose.ui.Modifier
import androidx.compose.ui.input.nestedscroll.nestedScroll
import androidx.compose.ui.res.stringResource
import androidx.navigation.NavDestination
import androidx.navigation.NavDestination.Companion.hasRoute
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.NavGraphBuilder
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.android.geto.designsystem.component.LocalRevertConfigurationRequest
import com.android.geto.feature.home.navigation.HomeDestination
import kotlin.reflect.KClass

@Composable
internal fun HomeRoute(
    modifier: Modifier = Modifier,
    snackbarHostState: SnackbarHostState,
    topLevelDestinations: List<HomeDestination>,
    startDestination: KClass<*>,
    onClickHomeDestination: (NavHostController, HomeDestination) -> Unit,
    onRevertConfigurationRequest: (NavHostController) -> Unit,
    builder: NavGraphBuilder.() -> Unit,
) {
    HomeScreen(
        modifier = modifier,
        snackbarHostState = snackbarHostState,
        topLevelDestinations = topLevelDestinations,
        startDestination = startDestination,
        onClickHomeDestination = onClickHomeDestination,
        onRevertConfigurationRequest = onRevertConfigurationRequest,
        builder = builder,
    )
}

@OptIn(ExperimentalMaterial3Api::class, ExperimentalComposeUiApi::class)
@Composable
internal fun HomeScreen(
    modifier: Modifier = Modifier,
    snackbarHostState: SnackbarHostState,
    topLevelDestinations: List<HomeDestination>,
    startDestination: KClass<*>,
    onClickHomeDestination: (NavHostController, HomeDestination) -> Unit,
    onRevertConfigurationRequest: (NavHostController) -> Unit,
    builder: NavGraphBuilder.() -> Unit,
) {
    val navController = rememberNavController()

    // Something outside the graph has asked for a particular tab. The nav controller is
    // created here and not exposed, so the request comes in as a value and the navigating
    // is done here rather than by the caller reaching in.
    val revertConfigurationRequest = LocalRevertConfigurationRequest.current

    LaunchedEffect(revertConfigurationRequest) {
        if (revertConfigurationRequest > 0) onRevertConfigurationRequest(navController)
    }

    // exitUntilCollapsed, not enterAlways. enterAlways re-expands the bar on *any* upward
    // drag, so every change of direction shifts the whole page by the bar's collapse
    // distance on top of the finger movement -- and on a LargeTopAppBar that distance is
    // most of a title. On the two lazy lists it is lost in a long list; the settings tab is
    // a plain column barely taller than the screen, so the same shift is a large fraction
    // of its whole scroll range and reads as the page moving faster than the finger.
    //
    // enterAlways is meant for the small top app bar. A large one is paired with this.
    val topAppBarScrollBehavior = exitUntilCollapsedScrollBehavior()

    val currentDestination = navController.currentBackStackEntryAsState().value?.destination

    val topBarTitleStringResource = topLevelDestinations.find { destination ->
        currentDestination.isTopLevelDestinationInHierarchy(destination.route)
    }?.label ?: topLevelDestinations.first().label

    NavigationSuiteScaffold(
        navigationSuiteItems = {
            topLevelDestinations.forEach { destination ->
                item(
                    icon = {
                        Icon(
                            imageVector = destination.icon,
                            contentDescription = stringResource(id = destination.contentDescription),
                        )
                    },
                    label = { Text(stringResource(id = destination.label)) },
                    selected = currentDestination.isTopLevelDestinationInHierarchy(destination.route),
                    onClick = {
                        onClickHomeDestination(navController, destination)
                    },
                )
            }
        },
    ) {
        Scaffold(
            topBar = {
                LargeTopAppBar(
                    title = {
                        Text(
                            text = stringResource(id = topBarTitleStringResource),
                        )
                    },
                    scrollBehavior = topAppBarScrollBehavior,
                )
            },
            snackbarHost = {
                SnackbarHost(hostState = snackbarHostState)
            },
        ) { paddingValues ->
            NavHost(
                modifier = modifier
                    .nestedScroll(topAppBarScrollBehavior.nestedScrollConnection)
                    .padding(paddingValues)
                    .consumeWindowInsets(paddingValues),
                navController = navController,
                startDestination = startDestination,
                builder = builder,
            )
        }
    }
}

private fun NavDestination?.isTopLevelDestinationInHierarchy(route: KClass<*>) = this?.hierarchy?.any {
    it.hasRoute(route)
} ?: false
