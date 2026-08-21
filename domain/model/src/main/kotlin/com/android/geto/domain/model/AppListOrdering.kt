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
 * How the All Apps list is filtered and ordered.
 *
 * Split out of [UserData] so the expensive part — sorting every installed app — can be
 * skipped when an unrelated preference changes. Favourites live in UserData too, so
 * without this every star tap re-sorted the entire launcher list.
 */
data class AppListOrder(
    val sort: SortLauncherAppsActivityInfo,
    val order: SortOrderLauncherAppsActivityInfo,
    val showSystem: Boolean,
) {
    constructor(userData: UserData) : this(
        sort = userData.sortLauncherAppsActivityInfo,
        order = userData.sortOrderLauncherAppsActivityInfo,
        showSystem = userData.showSystem,
    )
}

object AppListOrdering {

    /**
     * Deliberately not named `apply`: a method reference to it would be ambiguous with the
     * `apply` scope function from the Kotlin standard library.
     */
    fun arrange(
        apps: List<LauncherAppsActivityInfo>,
        order: AppListOrder,
    ): List<LauncherAppsActivityInfo> {
        val comparator = when (order.sort) {
            SortLauncherAppsActivityInfo.Name -> {
                compareBy(String.CASE_INSENSITIVE_ORDER) { it.activityLabel }
            }

            SortLauncherAppsActivityInfo.UpdateTime -> {
                compareBy<LauncherAppsActivityInfo> { it.lastUpdateTime }
                    .thenBy(String.CASE_INSENSITIVE_ORDER) { it.activityLabel }
            }

            SortLauncherAppsActivityInfo.InstallTime -> {
                compareBy<LauncherAppsActivityInfo> { it.firstInstallTime }
                    .thenBy(String.CASE_INSENSITIVE_ORDER) { it.activityLabel }
            }
        }

        val visible = if (order.showSystem) apps else apps.filterNot { it.isSystem }

        return visible.sortedWith(
            if (order.order == SortOrderLauncherAppsActivityInfo.Ascending) {
                comparator
            } else {
                comparator.reversed()
            },
        )
    }

    /** Case-insensitive label search. Empty or null text means no filtering at all. */
    fun search(
        apps: List<LauncherAppsActivityInfo>,
        text: String?,
    ): List<LauncherAppsActivityInfo> = if (text.isNullOrEmpty()) {
        apps
    } else {
        apps.filter { it.activityLabel.contains(other = text, ignoreCase = true) }
    }
}
