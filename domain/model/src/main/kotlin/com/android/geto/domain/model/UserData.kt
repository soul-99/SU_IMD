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

data class UserData(
    val theme: Theme,
    val dynamicTheme: Boolean,
    val sortLauncherAppsActivityInfo: SortLauncherAppsActivityInfo,
    val sortOrderLauncherAppsActivityInfo: SortOrderLauncherAppsActivityInfo,
    val showSystem: Boolean,
    val favouriteComponentNames: List<String>,
    val sortFavouriteApps: SortFavouriteApps,
    val favouriteAppsView: FavouriteAppsView,
    val restartShizuku: Boolean,
    val shizukuForkMode: ShizukuForkMode,
    val shizukuAuthKey: String,
    val shizukuPackageName: String,
    val shizukuStartAction: String,
    val managedAccessibilityServices: List<String>,
    val heldAccessibilityServices: Map<String, List<String>>,
    val managedOverlayPackages: List<String>,
    val heldOverlayPackages: Map<String, List<String>>,
    val heldOverlayIdentities: Map<String, String>,
    val manageOverlay: Boolean,
    val taskerAuthKey: String,
    val taskerIntegrationEnabled: Boolean,
    val overlayRestoreFailed: Boolean,
    val autoRevertOnReturn: Boolean,
    val manualRevertTargets: Set<ManualRevertTarget>,
    val notificationFunction: NotificationFunction,
    val revertDefaults: Map<ManualRevertTarget, Boolean>,
    val settingsToHide: Map<ManualRevertTarget, Boolean>,
    val notificationFunctionResetV16: Boolean,
    val revertDefaultsResetV166: Boolean,
    val revertDefaultsNoticePending: Boolean,
    val settingsManagerInfoShown: Boolean,
    val shizukuStartFailed: Boolean,
    val settingStateBefore: Map<String, Map<String, String?>>,
    val tipShown: Boolean,
    val obtainiumTipShown: Boolean,
    val setupNoticeVersion: Int,
)
