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

import androidx.compose.ui.graphics.vector.ImageVector
import com.android.geto.R
import com.android.geto.designsystem.icon.GetoIcons
import com.android.geto.feature.apps.navigation.AppsRouteData
import com.android.geto.feature.apps.navigation.FavouriteAppsRouteData
import com.android.geto.feature.home.navigation.HomeDestination
import com.android.geto.feature.settings.navigation.SettingsRouteData
import kotlin.reflect.KClass

enum class TopLevelDestination(
    override val label: Int,
    override val icon: ImageVector,
    override val contentDescription: Int,
    override val route: KClass<*>,
) : HomeDestination {
    FAVOURITE_APPS(
        label = R.string.favourite_apps,
        icon = GetoIcons.Star,
        contentDescription = R.string.favourite_apps,
        route = FavouriteAppsRouteData::class,
    ),
    ALL_APPS(
        label = R.string.all_apps,
        // r27: the author's own nine-square grid, replacing Material's dotted one. The same
        // drawing carries the App drawer shortcuts row — see GetoIcons.AppGrid for why it is an
        // ImageVector rather than a drawable.
        icon = GetoIcons.AppGrid,
        contentDescription = R.string.all_apps,
        route = AppsRouteData::class,
    ),
    SETTINGS(
        label = R.string.settings,
        icon = GetoIcons.Settings,
        contentDescription = R.string.settings,
        route = SettingsRouteData::class,
    ),
}
