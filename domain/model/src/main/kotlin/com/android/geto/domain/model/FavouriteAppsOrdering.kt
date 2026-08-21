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
package com.android.geto.domain.model

/**
 * Favourites ordering, kept pure so the custom-order and drop-uninstalled behaviour can
 * be tested without a package manager.
 */
/**
 * The only two pieces of [UserData] the favourites ordering depends on.
 *
 * Same reasoning as [AppListOrder]: everything the app stores lives in one UserData
 * object, so without this projection every unrelated preference write — including ticking
 * a box in the Re-enable dialog — re-ran the ordering.
 */
data class FavouriteAppsOrder(
    val favouriteComponentNames: List<String>,
    val sort: SortFavouriteApps,
) {
    constructor(userData: UserData) : this(
        favouriteComponentNames = userData.favouriteComponentNames,
        sort = userData.sortFavouriteApps,
    )
}

object FavouriteAppsOrdering {

    /**
     * Resolves saved component names against the installed apps.
     *
     * Walking the saved list (rather than filtering the installed list) is what makes the
     * custom order meaningful, and it drops favourites whose app has been uninstalled
     * instead of leaving a dead tile behind. Duplicates in the saved list collapse.
     */
    fun order(
        favouriteComponentNames: List<String>,
        installed: List<LauncherAppsActivityInfo>,
        sortFavouriteApps: SortFavouriteApps,
    ): List<LauncherAppsActivityInfo> {
        val byComponentName = installed.associateBy { it.componentName }

        val resolved = favouriteComponentNames.distinct().mapNotNull { byComponentName[it] }

        return when (sortFavouriteApps) {
            SortFavouriteApps.Custom -> resolved

            SortFavouriteApps.Alphabetical -> resolved.sortedWith(
                compareBy(String.CASE_INSENSITIVE_ORDER) { it.activityLabel },
            )
        }
    }

    /** Case-insensitive label search, matching the All Apps tab's behaviour. */
    fun filter(
        apps: List<LauncherAppsActivityInfo>,
        text: String?,
    ): List<LauncherAppsActivityInfo> = if (text.isNullOrEmpty()) {
        apps
    } else {
        apps.filter { it.activityLabel.contains(other = text, ignoreCase = true) }
    }

    /**
     * Appends on add so the newest favourite lands at the end of the custom order, and
     * removes on clear. Adding something already present is a no-op rather than a
     * reorder.
     */
    fun toggle(
        favouriteComponentNames: List<String>,
        componentName: String,
        favourite: Boolean,
    ): List<String> = if (favourite) {
        if (componentName in favouriteComponentNames) {
            favouriteComponentNames
        } else {
            favouriteComponentNames + componentName
        }
    } else {
        favouriteComponentNames.filterNot { it == componentName }
    }
}
