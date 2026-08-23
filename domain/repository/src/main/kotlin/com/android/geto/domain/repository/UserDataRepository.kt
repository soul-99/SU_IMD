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
package com.android.geto.domain.repository

import com.android.geto.domain.model.FavouriteAppsView
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.NotificationFunction
import com.android.geto.domain.model.ShizukuForkMode
import com.android.geto.domain.model.SortFavouriteApps
import com.android.geto.domain.model.SortLauncherAppsActivityInfo
import com.android.geto.domain.model.SortOrderLauncherAppsActivityInfo
import com.android.geto.domain.model.Theme
import com.android.geto.domain.model.UserData
import kotlinx.coroutines.flow.Flow

interface UserDataRepository {

    val userData: Flow<UserData>

    suspend fun updateTheme(theme: Theme)

    suspend fun updateDynamicTheme(dynamicTheme: Boolean)

    suspend fun updateSortLauncherAppsActivityInfo(sortLauncherAppsActivityInfo: SortLauncherAppsActivityInfo)

    suspend fun updateSortOrderLauncherAppsActivityInfo(sortOrderLauncherAppsActivityInfo: SortOrderLauncherAppsActivityInfo)

    suspend fun updateShowSystem(showSystem: Boolean)

    suspend fun updateFavourite(componentName: String, favourite: Boolean)

    suspend fun updateFavouriteComponentNames(componentNames: List<String>)

    suspend fun updateSortFavouriteApps(sortFavouriteApps: SortFavouriteApps)

    suspend fun updateFavouriteAppsView(favouriteAppsView: FavouriteAppsView)

    suspend fun updateRestartShizuku(restartShizuku: Boolean)

    suspend fun updateShizukuForkMode(shizukuForkMode: ShizukuForkMode)

    suspend fun updateShizukuAuthKey(shizukuAuthKey: String)

    suspend fun updateShizukuPackageName(shizukuPackageName: String)

    suspend fun updateShizukuStartAction(shizukuStartAction: String)

    suspend fun updateManagedAccessibilityServices(components: List<String>)

    suspend fun updateHeldAccessibilityServices(held: Map<String, List<String>>)

    suspend fun updateManualRevertTargets(targets: Set<ManualRevertTarget>)

    suspend fun updateNotificationFunction(notificationFunction: NotificationFunction)

    suspend fun updateRevertDefaults(states: Map<ManualRevertTarget, Boolean>)

    suspend fun updateSettingsToHide(states: Map<ManualRevertTarget, Boolean>)

    suspend fun updateNotificationFunctionResetV16(done: Boolean)

    suspend fun updateShizukuStartFailed(failed: Boolean)

    suspend fun updateSetupNoticeVersion(versionCode: Int)

    suspend fun updateSettingStateBefore(states: Map<String, Map<String, String?>>)

    suspend fun updateTipShown(tipShown: Boolean)

    suspend fun updateObtainiumTipShown(obtainiumTipShown: Boolean)
}
