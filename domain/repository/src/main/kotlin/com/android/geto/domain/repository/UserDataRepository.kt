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

    suspend fun updateIconStyle(iconStyle: IconStyle)

    suspend fun updateFavouriteAppsView(favouriteAppsView: FavouriteAppsView)

    suspend fun updateRestartShizuku(restartShizuku: Boolean)

    suspend fun updateShizukuForkMode(shizukuForkMode: ShizukuForkMode)

    suspend fun updateShizukuAuthKey(shizukuAuthKey: String)

    suspend fun updateShizukuPackageName(shizukuPackageName: String)

    suspend fun updateShizukuStartAction(shizukuStartAction: String)

    suspend fun updateManagedAccessibilityServices(components: List<String>)

    suspend fun updateHeldAccessibilityServices(held: Map<String, List<String>>)

    suspend fun updateManagedOverlayPackages(packages: List<String>)

    suspend fun updateHeldOverlayPackages(
        held: Map<String, List<String>>,
        identities: Map<String, String>,
    )

    /**
     * Whether a memory restore may switch wireless debugging back on. Off until ticked; see
     * [com.android.geto.domain.model.UserData.restoreWirelessDebugging].
     */
    suspend fun updateRestoreWirelessDebugging(enabled: Boolean)

    /**
     * The user's stored answer to 'Manage Shizuku'. See
     * [com.android.geto.domain.model.UserData.manageShizuku] for why this is not what the
     * switch shows.
     */
    suspend fun updateManageShizuku(enabled: Boolean)

    /** Marks the one-shot 'Manage Shizuku' migration done. */
    suspend fun updateManageShizukuMigratedV3(done: Boolean)

    suspend fun updateAutoUnhideResetV3(done: Boolean)

    suspend fun updateUpgradedToV3(upgraded: Boolean)

    /**
     * Records that the Favourites tab's view is somebody's answer rather than the default.
     *
     * The stored view is Grid until this is true, so an upgrade has to set it to keep the list
     * it was already showing.
     */
    suspend fun updateFavouriteAppsViewSet(set: Boolean)

    /**
     * Records that the Favourites tab's sort order is somebody's answer rather than the default.
     *
     * The stored order is Alphabetical until this is true, so an upgrade has to set it to keep
     * the order it was already showing.
     */
    suspend fun updateSortFavouriteAppsSet(set: Boolean)

    suspend fun updateManageOverlay(enabled: Boolean)

    /** Returns the Tasker auth key, generating and storing one the first time. */
    suspend fun ensureTaskerAuthKey(): String

    /** Replaces the Tasker auth key with a new one and returns it. */
    suspend fun refreshTaskerAuthKey(): String

    /** Turns the Tasker integration on or off; enabling also ensures a key exists. */
    suspend fun updateTaskerIntegrationEnabled(enabled: Boolean)

    suspend fun updateOverlayRestoreFailed(failed: Boolean)

    suspend fun updateAutoRevertOnReturn(enabled: Boolean)

    suspend fun updateManualRevertTargets(targets: Set<ManualRevertTarget>)

    suspend fun updateNotificationFunction(notificationFunction: NotificationFunction)

    suspend fun updateHidingFramework(hidingFramework: HidingFramework)

    suspend fun updateUnhidingFramework(unhidingFramework: UnhidingFramework)

    suspend fun updateFrameworksMigratedV3(done: Boolean)

    suspend fun updateRevertDefaults(states: Map<ManualRevertTarget, Boolean>)

    /** Which rows the settings manager draws - see `UserData.managerRows`. */
    suspend fun updateManagerRows(states: Map<ManualRevertTarget, Boolean>)

    /** The bottom-edge blur - see `UserData.progressiveBlur`. Takes the positive. */
    suspend fun updateProgressiveBlur(enabled: Boolean)

    /** Pure black backgrounds in the dark scheme - see `UserData.oledBackground`. */
    suspend fun updateOledBackground(enabled: Boolean)

    /** The three blur sliders, written together — see `UserData.blurRadiusDp`. */
    suspend fun updateBlurSettings(radiusDp: Int, tintPercent: Int, fadeDp: Int)

    /** Which app-drawer entries to publish - see `UserData.drawerShortcutManager`. */
    suspend fun updateDrawerShortcuts(manager: Boolean, hideUnhide: Boolean)

    suspend fun updateAutoHideDetectorManagedV3(done: Boolean)

    suspend fun updateSettingsToHide(states: Map<ManualRevertTarget, Boolean>)

    suspend fun updateNotificationFunctionResetV16(done: Boolean)

    suspend fun updateRevertDefaultsResetV166(done: Boolean)

    suspend fun updateSettingsToHideDefaultsV21(done: Boolean)

    /**
     * Records whether the device-wide "Settings to hide" is applied right now.
     *
     * Written by the hide itself and by every revert to default, rather than by whatever
     * triggered them, so a revert fired from a notification, an intent or a shortcut updates
     * the Quick Settings tile without knowing the tile exists.
     */
    suspend fun updateSettingsHiddenDeviceWide(hidden: Boolean)

    /** The user's own answer to Auto-hide settings (IMD+), never the live requirements. */
    suspend fun updateAutoHideEnabled(enabled: Boolean)

    suspend fun updateAutoHidePackages(packages: List<String>)

    suspend fun updateAutoHideNoKillOnLaunch(noKill: Boolean)

    /** Parks the switch's state while a hide has IMD's own accessibility service switched off. */
    suspend fun updateAutoHideEnabledBeforeHide(enabled: Boolean)

    /** Whether what is hidden right now was hidden by IMD+ rather than by a launch or the tile. */
    suspend fun updateAutoHideRunning(running: Boolean)

    /** The user's own answer to Auto unhide settings, never the live requirements. */
    suspend fun updateAutoUnhideEnabled(enabled: Boolean)

    /** All three triggers at once — see the data source for why they cannot be written apart. */
    suspend fun updateAutoUnhideTriggers(
        onSwipe: Boolean,
        onScreenLock: Boolean,
        onIdle: Boolean,
    )

    suspend fun updateAutoUnhideScreenLockMinutes(minutes: Int)

    suspend fun updateAutoUnhideIdleMinutes(minutes: Int)

    /** Both "used for" answers at once — see the data source for why they cannot be split. */
    suspend fun updateAutoUnhideUsedFor(onAppLaunch: Boolean, onTile: Boolean)

    /** Whether the diagnostic log is being recorded. Nothing runs because this is true. */
    suspend fun updateDiagnosticsEnabled(enabled: Boolean)

    /** Records the newest "what changed" notice this install has been shown. */
    suspend fun updateSettingsNoticeRevision(revision: Int)

    /** Records that IMD+ has been switched on by the user at least once. */
    suspend fun markAutoHideEverEnabled()

    suspend fun updateRevertDefaultsNoticePending(pending: Boolean)

    suspend fun updateSettingsManagerInfoShown(shown: Boolean)

    suspend fun updateShizukuStartFailed(failed: Boolean)

    suspend fun updateSetupNoticeVersion(versionCode: Int)

    suspend fun updateSettingStateBefore(states: Map<String, Map<String, String?>>)

    suspend fun updateTipShown(tipShown: Boolean)

    suspend fun updateObtainiumTipShown(obtainiumTipShown: Boolean)
}
