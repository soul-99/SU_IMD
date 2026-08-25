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
package com.android.geto.data.repository

import com.android.geto.data.datastore.UserPreferencesDataSource
import com.android.geto.domain.model.FavouriteAppsView
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.NotificationFunction
import com.android.geto.domain.model.ShizukuForkMode
import com.android.geto.domain.model.SortFavouriteApps
import com.android.geto.domain.model.SortLauncherAppsActivityInfo
import com.android.geto.domain.model.SortOrderLauncherAppsActivityInfo
import com.android.geto.domain.model.Theme
import com.android.geto.domain.model.UserData
import com.android.geto.domain.repository.UserDataRepository
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject

class DefaultUserDataRepository @Inject constructor(
    private val userPreferencesDataSource: UserPreferencesDataSource,
) : UserDataRepository {
    override val userData: Flow<UserData> = userPreferencesDataSource.userData

    override suspend fun updateTheme(theme: Theme) {
        userPreferencesDataSource.updateTheme(theme = theme)
    }

    override suspend fun updateDynamicTheme(dynamicTheme: Boolean) {
        userPreferencesDataSource.updateDynamicColor(dynamicTheme = dynamicTheme)
    }

    override suspend fun updateSortLauncherAppsActivityInfo(sortLauncherAppsActivityInfo: SortLauncherAppsActivityInfo) {
        userPreferencesDataSource.updateSortLauncherAppsActivityInfo(sortLauncherAppsActivityInfo = sortLauncherAppsActivityInfo)
    }

    override suspend fun updateSortOrderLauncherAppsActivityInfo(sortOrderLauncherAppsActivityInfo: SortOrderLauncherAppsActivityInfo) {
        userPreferencesDataSource.updateSortOrderLauncherAppsActivityInfo(
            sortOrderLauncherAppsActivityInfo = sortOrderLauncherAppsActivityInfo,
        )
    }

    override suspend fun updateShowSystem(showSystem: Boolean) {
        userPreferencesDataSource.updateShowSystem(showSystem = showSystem)
    }

    override suspend fun updateFavourite(componentName: String, favourite: Boolean) {
        userPreferencesDataSource.updateFavourite(
            componentName = componentName,
            favourite = favourite,
        )
    }

    override suspend fun updateFavouriteComponentNames(componentNames: List<String>) {
        userPreferencesDataSource.updateFavouriteComponentNames(componentNames = componentNames)
    }

    override suspend fun updateSortFavouriteApps(sortFavouriteApps: SortFavouriteApps) {
        userPreferencesDataSource.updateSortFavouriteApps(sortFavouriteApps = sortFavouriteApps)
    }

    override suspend fun updateFavouriteAppsView(favouriteAppsView: FavouriteAppsView) {
        userPreferencesDataSource.updateFavouriteAppsView(favouriteAppsView = favouriteAppsView)
    }

    override suspend fun updateRestartShizuku(restartShizuku: Boolean) {
        userPreferencesDataSource.updateRestartShizuku(restartShizuku = restartShizuku)
    }

    override suspend fun updateShizukuForkMode(shizukuForkMode: ShizukuForkMode) {
        userPreferencesDataSource.updateShizukuForkMode(shizukuForkMode = shizukuForkMode)
    }

    override suspend fun updateShizukuAuthKey(shizukuAuthKey: String) {
        userPreferencesDataSource.updateShizukuAuthKey(shizukuAuthKey = shizukuAuthKey)
    }

    override suspend fun updateShizukuPackageName(shizukuPackageName: String) {
        userPreferencesDataSource.updateShizukuPackageName(shizukuPackageName = shizukuPackageName)
    }

    override suspend fun updateShizukuStartAction(shizukuStartAction: String) {
        userPreferencesDataSource.updateShizukuStartAction(shizukuStartAction = shizukuStartAction)
    }

    override suspend fun updateObtainiumTipShown(obtainiumTipShown: Boolean) {
        userPreferencesDataSource.updateObtainiumTipShown(obtainiumTipShown = obtainiumTipShown)
    }

    override suspend fun updateManagedAccessibilityServices(components: List<String>) {
        userPreferencesDataSource.updateManagedAccessibilityServices(components = components)
    }

    override suspend fun updateHeldAccessibilityServices(held: Map<String, List<String>>) {
        userPreferencesDataSource.updateHeldAccessibilityServices(held = held)
    }

    override suspend fun updateHeldOverlayPackages(packages: Map<String, String>) {
        userPreferencesDataSource.updateHeldOverlayPackages(packages = packages)
    }

    override suspend fun updateManualRevertTargets(targets: Set<ManualRevertTarget>) {
        userPreferencesDataSource.updateManualRevertTargets(targets = targets)
    }

    override suspend fun updateSettingStateBefore(states: Map<String, Map<String, String?>>) {
        userPreferencesDataSource.updateSettingStateBefore(states = states)
    }

    override suspend fun updateTipShown(tipShown: Boolean) {
        userPreferencesDataSource.updateTipShown(tipShown = tipShown)
    }

    override suspend fun updateNotificationFunction(notificationFunction: NotificationFunction) {
        userPreferencesDataSource.updateNotificationFunction(notificationFunction = notificationFunction)
    }

    override suspend fun updateRevertDefaults(states: Map<ManualRevertTarget, Boolean>) {
        userPreferencesDataSource.updateRevertDefaults(states = states)
    }

    override suspend fun updateSettingsToHide(states: Map<ManualRevertTarget, Boolean>) {
        userPreferencesDataSource.updateSettingsToHide(states = states)
    }

    override suspend fun updateRevertDefaultsResetV166(done: Boolean) {
        userPreferencesDataSource.updateRevertDefaultsResetV166(done = done)
    }

    override suspend fun updateRevertDefaultsNoticePending(pending: Boolean) {
        userPreferencesDataSource.updateRevertDefaultsNoticePending(pending = pending)
    }

    override suspend fun updateSettingsManagerInfoShown(shown: Boolean) {
        userPreferencesDataSource.updateSettingsManagerInfoShown(shown = shown)
    }

    override suspend fun updateNotificationFunctionResetV16(done: Boolean) {
        userPreferencesDataSource.updateNotificationFunctionResetV16(done = done)
    }

    override suspend fun updateShizukuStartFailed(failed: Boolean) {
        userPreferencesDataSource.updateShizukuStartFailed(failed = failed)
    }

    override suspend fun updateSetupNoticeVersion(versionCode: Int) {
        userPreferencesDataSource.updateSetupNoticeVersion(versionCode = versionCode)
    }
}
