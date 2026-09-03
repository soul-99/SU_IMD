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
import com.android.geto.domain.model.HidingFramework
import com.android.geto.domain.model.IconStyle
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.NotificationFunction
import com.android.geto.domain.model.ShizukuForkMode
import com.android.geto.domain.model.SortFavouriteApps
import com.android.geto.domain.model.SortLauncherAppsActivityInfo
import com.android.geto.domain.model.SortOrderLauncherAppsActivityInfo
import com.android.geto.domain.model.Theme
import com.android.geto.domain.model.UnhidingFramework
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

    override suspend fun updateIconStyle(iconStyle: IconStyle) {
        userPreferencesDataSource.updateIconStyle(iconStyle = iconStyle)
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

    override suspend fun updateAutoRevertOnReturn(enabled: Boolean) {
        userPreferencesDataSource.updateAutoRevertOnReturn(enabled = enabled)
    }

    override suspend fun updateRestoreWirelessDebugging(enabled: Boolean) {
        userPreferencesDataSource.updateRestoreWirelessDebugging(enabled = enabled)
    }

    override suspend fun updateManageShizuku(enabled: Boolean) {
        userPreferencesDataSource.updateManageShizuku(enabled = enabled)
    }

    override suspend fun updateManageShizukuMigratedV3(done: Boolean) {
        userPreferencesDataSource.updateManageShizukuMigratedV3(done = done)
    }

    override suspend fun updateAutoUnhideResetV3(done: Boolean) {
        userPreferencesDataSource.updateAutoUnhideResetV3(done = done)
    }

    override suspend fun updateUpgradedToV3(upgraded: Boolean) {
        userPreferencesDataSource.updateUpgradedToV3(upgraded = upgraded)
    }

    override suspend fun updateFavouriteAppsViewSet(set: Boolean) {
        userPreferencesDataSource.updateFavouriteAppsViewSet(set = set)
    }

    override suspend fun updateSortFavouriteAppsSet(set: Boolean) {
        userPreferencesDataSource.updateSortFavouriteAppsSet(set = set)
    }

    override suspend fun updateManageOverlay(enabled: Boolean) {
        userPreferencesDataSource.updateManageOverlay(enabled = enabled)
    }

    override suspend fun ensureTaskerAuthKey(): String =
        userPreferencesDataSource.ensureTaskerAuthKey()

    override suspend fun refreshTaskerAuthKey(): String =
        userPreferencesDataSource.refreshTaskerAuthKey()

    override suspend fun updateTaskerIntegrationEnabled(enabled: Boolean) {
        userPreferencesDataSource.updateTaskerIntegrationEnabled(enabled = enabled)
    }

    override suspend fun updateOverlayRestoreFailed(failed: Boolean) {
        userPreferencesDataSource.updateOverlayRestoreFailed(failed = failed)
    }

    override suspend fun updateManagedOverlayPackages(packages: List<String>) {
        userPreferencesDataSource.updateManagedOverlayPackages(packages = packages)
    }

    override suspend fun updateHeldOverlayPackages(
        held: Map<String, List<String>>,
        identities: Map<String, String>,
    ) {
        userPreferencesDataSource.updateHeldOverlayPackages(
            held = held,
            identities = identities,
        )
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

    override suspend fun updateHidingFramework(hidingFramework: HidingFramework) {
        userPreferencesDataSource.updateHidingFramework(hidingFramework = hidingFramework)
    }

    override suspend fun updateUnhidingFramework(unhidingFramework: UnhidingFramework) {
        userPreferencesDataSource.updateUnhidingFramework(unhidingFramework = unhidingFramework)
    }

    override suspend fun updateFrameworksMigratedV3(done: Boolean) {
        userPreferencesDataSource.updateFrameworksMigratedV3(done = done)
    }

    override suspend fun updateManagerRows(states: Map<ManualRevertTarget, Boolean>) {
        userPreferencesDataSource.updateManagerRows(states = states)
    }

    override suspend fun updateProgressiveBlur(enabled: Boolean) {
        userPreferencesDataSource.updateProgressiveBlur(enabled = enabled)
    }

    override suspend fun updateBlurSettings(radiusDp: Int, tintPercent: Int, fadeDp: Int) {
        userPreferencesDataSource.updateBlurSettings(
            radiusDp = radiusDp,
            tintPercent = tintPercent,
            fadeDp = fadeDp,
        )
    }

    override suspend fun updateOledBackground(enabled: Boolean) {
        userPreferencesDataSource.updateOledBackground(enabled = enabled)
    }

    override suspend fun updateDrawerShortcuts(manager: Boolean, hideUnhide: Boolean) {
        userPreferencesDataSource.updateDrawerShortcuts(manager = manager, hideUnhide = hideUnhide)
    }

    override suspend fun updateAutoHideDetectorManagedV3(done: Boolean) {
        userPreferencesDataSource.updateAutoHideDetectorManagedV3(done = done)
    }

    override suspend fun updateRevertDefaults(states: Map<ManualRevertTarget, Boolean>) {
        userPreferencesDataSource.updateRevertDefaults(states = states)
    }

    override suspend fun updateSettingsToHide(states: Map<ManualRevertTarget, Boolean>) {
        userPreferencesDataSource.updateSettingsToHide(states = states)
    }

    override suspend fun updateSettingsToHideDefaultsV21(done: Boolean) {
        userPreferencesDataSource.updateSettingsToHideDefaultsV21(done = done)
    }

    override suspend fun updateSettingsHiddenDeviceWide(hidden: Boolean) {
        userPreferencesDataSource.updateSettingsHiddenDeviceWide(hidden = hidden)
    }

    override suspend fun updateAutoHideEnabled(enabled: Boolean) {
        userPreferencesDataSource.updateAutoHideEnabled(enabled = enabled)
    }

    override suspend fun updateAutoHidePackages(packages: List<String>) {
        userPreferencesDataSource.updateAutoHidePackages(packages = packages)
    }

    override suspend fun updateAutoHideNoKillOnLaunch(noKill: Boolean) {
        userPreferencesDataSource.updateAutoHideNoKillOnLaunch(noKill = noKill)
    }

    override suspend fun updateAutoHideEnabledBeforeHide(enabled: Boolean) {
        userPreferencesDataSource.updateAutoHideEnabledBeforeHide(enabled = enabled)
    }

    override suspend fun updateAutoHideRunning(running: Boolean) {
        userPreferencesDataSource.updateAutoHideRunning(running = running)
    }

    override suspend fun updateAutoUnhideEnabled(enabled: Boolean) {
        userPreferencesDataSource.updateAutoUnhideEnabled(enabled = enabled)
    }

    override suspend fun updateAutoUnhideTriggers(
        onSwipe: Boolean,
        onScreenLock: Boolean,
        onIdle: Boolean,
    ) {
        userPreferencesDataSource.updateAutoUnhideTriggers(
            onSwipe = onSwipe,
            onScreenLock = onScreenLock,
            onIdle = onIdle,
        )
    }

    override suspend fun updateAutoUnhideScreenLockMinutes(minutes: Int) {
        userPreferencesDataSource.updateAutoUnhideScreenLockMinutes(minutes = minutes)
    }

    override suspend fun updateAutoUnhideIdleMinutes(minutes: Int) {
        userPreferencesDataSource.updateAutoUnhideIdleMinutes(minutes = minutes)
    }

    override suspend fun updateSettingsNoticeRevision(revision: Int) {
        userPreferencesDataSource.updateSettingsNoticeRevision(revision = revision)
    }

    override suspend fun markAutoHideEverEnabled() {
        userPreferencesDataSource.markAutoHideEverEnabled()
    }

    override suspend fun updateDiagnosticsEnabled(enabled: Boolean) {
        userPreferencesDataSource.updateDiagnosticsEnabled(enabled = enabled)
    }

    override suspend fun updateAutoUnhideUsedFor(onAppLaunch: Boolean, onTile: Boolean) {
        userPreferencesDataSource.updateAutoUnhideUsedFor(
            onAppLaunch = onAppLaunch,
            onTile = onTile,
        )
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
