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
package com.android.geto.data.datastore

import androidx.datastore.core.DataStore
import com.android.geto.data.datastore.mapper.asFavouriteAppsView
import com.android.geto.data.datastore.mapper.asFavouriteAppsViewProto
import com.android.geto.data.datastore.mapper.asNotificationFunction
import com.android.geto.data.datastore.mapper.asNotificationFunctionProto
import com.android.geto.data.datastore.mapper.asShizukuForkMode
import com.android.geto.data.datastore.mapper.asShizukuForkModeProto
import com.android.geto.data.datastore.mapper.asSortFavouriteApps
import com.android.geto.data.datastore.mapper.asSortFavouriteAppsProto
import com.android.geto.data.datastore.mapper.asSortLauncherAppsActivityInfo
import com.android.geto.data.datastore.mapper.asSortLauncherAppsActivityInfoProto
import com.android.geto.data.datastore.mapper.asSortOrderLauncherAppsActivityInfo
import com.android.geto.data.datastore.mapper.asSortOrderLauncherAppsActivityInfoProto
import com.android.geto.data.datastore.mapper.asTheme
import com.android.geto.data.datastore.mapper.asThemeProto
import com.android.geto.data.datastore.proto.UserPreferences
import com.android.geto.data.datastore.proto.copy
import com.android.geto.domain.framework.ShizukuWrapper
import com.android.geto.domain.model.AccessibilityServicePlan
import com.android.geto.domain.model.FavouriteAppsOrdering
import com.android.geto.domain.model.FavouriteAppsView
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.NotificationFunction
import com.android.geto.domain.model.RevertDefaults
import com.android.geto.domain.model.SettingSnapshot
import com.android.geto.domain.model.SettingsToHide
import com.android.geto.domain.model.ShizukuForkMode
import com.android.geto.domain.model.SortFavouriteApps
import com.android.geto.domain.model.SortLauncherAppsActivityInfo
import com.android.geto.domain.model.SortOrderLauncherAppsActivityInfo
import com.android.geto.domain.model.Theme
import com.android.geto.domain.model.UserData
import kotlinx.coroutines.flow.map
import javax.inject.Inject

class UserPreferencesDataSource @Inject constructor(private val userPreferences: DataStore<UserPreferences>) {
    val userData = userPreferences.data.map {
        UserData(
            theme = it.theme.asTheme(),
            dynamicTheme = it.dynamicTheme,
            sortLauncherAppsActivityInfo = it.sortLauncherAppsActivityInfo.asSortLauncherAppsActivityInfo(),
            sortOrderLauncherAppsActivityInfo = it.sortOrderLauncherAppsActivityInfo.asSortOrderLauncherAppsActivityInfo(),
            showSystem = it.showSystem,
            favouriteComponentNames = it.favouriteComponentNamesList.toList(),
            sortFavouriteApps = it.sortFavouriteApps.asSortFavouriteApps(),
            favouriteAppsView = it.favouriteAppsView.asFavouriteAppsView(),
            // On unless the user has said otherwise. Reverting USB debugging without
            // bringing Shizuku back leaves the service down with nothing saying why, which
            // is a worse default than restarting something that was already running.
            restartShizuku = if (it.restartShizukuSet) it.restartShizuku else true,
            // An install upgraded from 1.0 has no fork stored but does have an auth key,
            // and only thedjchi's fork ever asked for one — so it is already telling us
            // which family it was set up against. Reading it that way keeps a working
            // setup working instead of resetting it to "not chosen".
            shizukuForkMode = it.shizukuForkMode.asShizukuForkMode().let { mode ->
                if (mode == ShizukuForkMode.Unset && it.shizukuAuthKey.isNotBlank()) {
                    ShizukuForkMode.Thedjchi
                } else {
                    mode
                }
            },
            shizukuAuthKey = it.shizukuAuthKey,
            // Empty proto default means "never set", so fall back to stock Shizuku
            // rather than storing the default eagerly.
            shizukuPackageName = it.shizukuPackageName.ifEmpty {
                ShizukuWrapper.DEFAULT_SHIZUKU_PACKAGE_NAME
            },
            shizukuStartAction = it.shizukuStartAction,
            managedAccessibilityServices = it.managedAccessibilityServicesList.toList(),
            heldAccessibilityServices = it.heldAccessibilityServicesMap.mapValues { entry ->
                AccessibilityServicePlan.decode(entry.value)
            },
            manualRevertTargets = ManualRevertTarget.decode(it.manualRevertTargetsList),
            notificationFunction = it.notificationFunction.asNotificationFunction(),
            revertDefaults = RevertDefaults.decode(it.revertDefaultsList),
            settingsToHide = SettingsToHide.decode(it.settingsToHideList),
            notificationFunctionResetV16 = it.notificationFunctionResetV16,
            revertDefaultsResetV166 = it.revertDefaultsResetV166,
            revertDefaultsNoticePending = it.revertDefaultsNoticePending,
            settingsManagerInfoShown = it.settingsManagerInfoShown,
            shizukuStartFailed = it.shizukuStartFailed,
            settingStateBefore = it.settingStateBeforeMap.mapValues { entry ->
                SettingSnapshot.decode(entry.value)
            },
            tipShown = it.tipShown,
            obtainiumTipShown = it.obtainiumTipShown,
            setupNoticeVersion = it.setupNoticeVersion,
        )
    }

    suspend fun updateDynamicColor(dynamicTheme: Boolean) {
        userPreferences.updateData {
            it.copy { this.dynamicTheme = dynamicTheme }
        }
    }

    suspend fun updateTheme(theme: Theme) {
        userPreferences.updateData {
            it.copy {
                this.theme = theme.asThemeProto()
            }
        }
    }

    suspend fun updateSortLauncherAppsActivityInfo(sortLauncherAppsActivityInfo: SortLauncherAppsActivityInfo) {
        userPreferences.updateData {
            it.copy {
                this.sortLauncherAppsActivityInfo =
                    sortLauncherAppsActivityInfo.asSortLauncherAppsActivityInfoProto()
            }
        }
    }

    suspend fun updateSortOrderLauncherAppsActivityInfo(sortOrderLauncherAppsActivityInfo: SortOrderLauncherAppsActivityInfo) {
        userPreferences.updateData {
            it.copy {
                this.sortOrderLauncherAppsActivityInfo =
                    sortOrderLauncherAppsActivityInfo.asSortOrderLauncherAppsActivityInfoProto()
            }
        }
    }

    suspend fun updateShowSystem(showSystem: Boolean) {
        userPreferences.updateData {
            it.copy {
                this.showSystem = showSystem
            }
        }
    }

    suspend fun updateFavourite(componentName: String, favourite: Boolean) {
        userPreferences.updateData { preferences ->
            val updated = FavouriteAppsOrdering.toggle(
                favouriteComponentNames = preferences.favouriteComponentNamesList,
                componentName = componentName,
                favourite = favourite,
            )

            preferences.copy {
                favouriteComponentNames.clear()
                favouriteComponentNames.addAll(updated)
            }
        }
    }

    suspend fun updateFavouriteComponentNames(componentNames: List<String>) {
        userPreferences.updateData {
            it.copy {
                favouriteComponentNames.clear()
                favouriteComponentNames.addAll(componentNames.distinct())
            }
        }
    }

    suspend fun updateSortFavouriteApps(sortFavouriteApps: SortFavouriteApps) {
        userPreferences.updateData {
            it.copy {
                this.sortFavouriteApps = sortFavouriteApps.asSortFavouriteAppsProto()
            }
        }
    }

    suspend fun updateFavouriteAppsView(favouriteAppsView: FavouriteAppsView) {
        userPreferences.updateData {
            it.copy {
                this.favouriteAppsView = favouriteAppsView.asFavouriteAppsViewProto()
            }
        }
    }

    suspend fun updateRestartShizuku(restartShizuku: Boolean) {
        userPreferences.updateData {
            it.copy {
                this.restartShizuku = restartShizuku
                // Recorded alongside, so the value above is read as a decision from now on
                // rather than falling back to the default on every read.
                this.restartShizukuSet = true
            }
        }
    }

    suspend fun updateShizukuAuthKey(shizukuAuthKey: String) {
        userPreferences.updateData {
            it.copy {
                this.shizukuAuthKey = shizukuAuthKey.trim()
            }
        }
    }

    suspend fun updateShizukuPackageName(shizukuPackageName: String) {
        userPreferences.updateData {
            it.copy {
                this.shizukuPackageName = shizukuPackageName.trim()
            }
        }
    }

    suspend fun updateShizukuForkMode(shizukuForkMode: ShizukuForkMode) {
        userPreferences.updateData {
            it.copy {
                this.shizukuForkMode = shizukuForkMode.asShizukuForkModeProto()
            }
        }
    }

    suspend fun updateShizukuStartAction(shizukuStartAction: String) {
        userPreferences.updateData {
            it.copy {
                this.shizukuStartAction = shizukuStartAction.trim()
            }
        }
    }

    suspend fun updateObtainiumTipShown(obtainiumTipShown: Boolean) {
        userPreferences.updateData {
            it.copy {
                this.obtainiumTipShown = obtainiumTipShown
            }
        }
    }

    suspend fun updateManagedAccessibilityServices(components: List<String>) {
        userPreferences.updateData {
            it.copy {
                managedAccessibilityServices.clear()
                managedAccessibilityServices.addAll(components.distinct())
            }
        }
    }

    suspend fun updateHeldAccessibilityServices(held: Map<String, List<String>>) {
        userPreferences.updateData {
            it.copy {
                heldAccessibilityServices.clear()
                heldAccessibilityServices.putAll(
                    held.mapValues { entry -> AccessibilityServicePlan.encode(entry.value) },
                )
            }
        }
    }

    suspend fun updateSettingStateBefore(states: Map<String, Map<String, String?>>) {
        userPreferences.updateData {
            it.copy {
                settingStateBefore.clear()
                settingStateBefore.putAll(states.mapValues { entry -> SettingSnapshot.encode(entry.value) })
            }
        }
    }

    suspend fun updateTipShown(tipShown: Boolean) {
        userPreferences.updateData {
            it.copy { this.tipShown = tipShown }
        }
    }

    suspend fun updateManualRevertTargets(targets: Set<ManualRevertTarget>) {
        userPreferences.updateData {
            it.copy {
                manualRevertTargets.clear()
                manualRevertTargets.addAll(ManualRevertTarget.encode(targets))
            }
        }
    }

    suspend fun updateNotificationFunction(notificationFunction: NotificationFunction) {
        userPreferences.updateData {
            it.copy {
                this.notificationFunction = notificationFunction.asNotificationFunctionProto()
            }
        }
    }

    suspend fun updateSetupNoticeVersion(versionCode: Int) {
        userPreferences.updateData {
            it.copy { this.setupNoticeVersion = versionCode }
        }
    }

    suspend fun updateShizukuStartFailed(failed: Boolean) {
        userPreferences.updateData {
            it.copy { this.shizukuStartFailed = failed }
        }
    }

    suspend fun updateRevertDefaults(states: Map<ManualRevertTarget, Boolean>) {
        userPreferences.updateData {
            it.copy {
                revertDefaults.clear()
                revertDefaults.addAll(RevertDefaults.encode(states))
            }
        }
    }

    suspend fun updateRevertDefaultsResetV166(done: Boolean) {
        userPreferences.updateData {
            it.copy { this.revertDefaultsResetV166 = done }
        }
    }

    suspend fun updateRevertDefaultsNoticePending(pending: Boolean) {
        userPreferences.updateData {
            it.copy { this.revertDefaultsNoticePending = pending }
        }
    }

    suspend fun updateSettingsManagerInfoShown(shown: Boolean) {
        userPreferences.updateData {
            it.copy { this.settingsManagerInfoShown = shown }
        }
    }

    suspend fun updateNotificationFunctionResetV16(done: Boolean) {
        userPreferences.updateData {
            it.copy { this.notificationFunctionResetV16 = done }
        }
    }

    suspend fun updateSettingsToHide(states: Map<ManualRevertTarget, Boolean>) {
        userPreferences.updateData {
            it.copy {
                settingsToHide.clear()
                settingsToHide.addAll(SettingsToHide.encode(states))
            }
        }
    }
}
