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
import com.android.geto.data.datastore.mapper.asHidingFramework
import com.android.geto.data.datastore.mapper.asHidingFrameworkProto
import com.android.geto.data.datastore.mapper.asIconStyle
import com.android.geto.data.datastore.mapper.asIconStyleProto
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
import com.android.geto.data.datastore.mapper.asUnhidingFramework
import com.android.geto.data.datastore.mapper.asUnhidingFrameworkProto
import com.android.geto.data.datastore.proto.UserPreferences
import com.android.geto.data.datastore.proto.copy
import com.android.geto.domain.framework.ShizukuWrapper
import com.android.geto.domain.model.AccessibilityServicePlan
import com.android.geto.domain.model.FavouriteAppsOrdering
import com.android.geto.domain.model.FavouriteAppsView
import com.android.geto.domain.model.HidingFramework
import com.android.geto.domain.model.IconStyle
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.NotificationFunction
import com.android.geto.domain.model.ManagerRows
import com.android.geto.domain.model.RevertDefaults
import com.android.geto.domain.model.SettingSnapshot
import com.android.geto.domain.model.SettingsToHide
import com.android.geto.domain.model.ShizukuForkMode
import com.android.geto.domain.model.SortFavouriteApps
import com.android.geto.domain.model.SortLauncherAppsActivityInfo
import com.android.geto.domain.model.SortOrderLauncherAppsActivityInfo
import com.android.geto.domain.model.Theme
import com.android.geto.domain.model.UnhidingFramework
import com.android.geto.domain.model.BLUR_FADE_RANGE
import com.android.geto.domain.model.BLUR_RADIUS_RANGE
import com.android.geto.domain.model.BLUR_TINT_RANGE
import com.android.geto.domain.model.DEFAULT_FADE_DP
import com.android.geto.domain.model.DEFAULT_RADIUS_DP
import com.android.geto.domain.model.DEFAULT_TINT_PERCENT
import com.android.geto.domain.model.UserData
import kotlinx.coroutines.flow.map
import java.security.SecureRandom
import javax.inject.Inject

class UserPreferencesDataSource @Inject constructor(private val userPreferences: DataStore<UserPreferences>) {
    val userData = userPreferences.data.map {
        UserData(
            theme = it.theme.asTheme(),
            // ⚠ **On until told otherwise — r29.** See dynamicThemeSet in the proto: the
            // companion bool is what lets the default change without discarding the choices
            // already stored against dynamicTheme. Same shape as progressiveBlur, below.
            dynamicTheme = if (it.dynamicThemeSet) it.dynamicTheme else true,
            sortLauncherAppsActivityInfo = it.sortLauncherAppsActivityInfo.asSortLauncherAppsActivityInfo(),
            sortOrderLauncherAppsActivityInfo = it.sortOrderLauncherAppsActivityInfo.asSortOrderLauncherAppsActivityInfo(),
            showSystem = it.showSystem,
            favouriteComponentNames = it.favouriteComponentNamesList.toList(),
            // A-Z until something chooses, at the author's instruction. Saving a custom
            // order is itself a choice - the reorder dialog writes Custom - so nobody ends up
            // sorted alphabetically over an order they dragged.
            sortFavouriteApps = if (it.sortFavouriteAppsSet) {
                it.sortFavouriteApps.asSortFavouriteApps()
            } else {
                SortFavouriteApps.Alphabetical
            },
            // Grid until something chooses, at the author's instruction. The marker is
            // what separates "never chosen" from "chose List": both store 0 in field 8.
            iconStyle = it.iconStyle.asIconStyle(),
            favouriteAppsView = if (it.favouriteAppsViewSet) {
                it.favouriteAppsView.asFavouriteAppsView()
            } else {
                FavouriteAppsView.Grid
            },
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
            managedOverlayPackages = it.managedOverlayPackagesList.toList(),
            heldOverlayPackages = it.heldOverlayPackagesByHolderMap.mapValues { entry ->
                AccessibilityServicePlan.decode(entry.value)
            },
            heldOverlayIdentities = it.heldOverlayIdentitiesMap.toMap(),
            manageOverlay = it.manageOverlay,
            taskerAuthKey = it.taskerAuthKey,
            taskerIntegrationEnabled = it.taskerIntegrationEnabled,
            overlayRestoreFailed = it.overlayRestoreFailed,
            autoRevertOnReturn = it.autoRevertOnReturn,
            manualRevertTargets = ManualRevertTarget.decode(it.manualRevertTargetsList),
            notificationFunction = it.notificationFunction.asNotificationFunction(),
            hidingFramework = it.hidingFramework.asHidingFramework(),
            unhidingFramework = it.unhidingFramework.asUnhidingFramework(),
            revertDefaults = RevertDefaults.decode(it.revertDefaultsList),
            managerRows = ManagerRows.decode(it.managerRowsList),
            // ⚠ **Read straight, since r17.** It used to be the one inversion in this file:
            // the field was named for the off state so that an install which had never touched
            // the switch got the blur. The author reversed that default, so the field is named
            // for the on state and there is nothing left to invert.
            // ⚠ **On until told otherwise — r27.** See progressiveBlurSet in the proto: the
            // companion bool is what lets the default change without discarding the choices
            // already stored against progressiveBlurOn.
            progressiveBlur = if (it.progressiveBlurSet) it.progressiveBlurOn else true,
            // ⚠ **All three or none of them.** The bool says whether the dialog has ever been
            // saved; reading each number against its own zero would let a half-written state
            // exist, and there is no way to write one from the dialog.
            blurRadiusDp = if (it.blurCustomised) it.blurRadiusDp else DEFAULT_RADIUS_DP,
            blurTintPercent = if (it.blurCustomised) it.blurTintPercent else DEFAULT_TINT_PERCENT,
            blurFadeDp = if (it.blurCustomised) it.blurFadeDp else DEFAULT_FADE_DP,
            oledBackground = it.oledBackground,
            // Both stored as the non-default state; see the proto comments on 77 and 78.
            drawerShortcutManager = !it.drawerShortcutManagerOff,
            drawerShortcutHideUnhide = it.drawerShortcutHideUnhideOn,
            autoHideDetectorManagedV3 = it.autoHideDetectorManagedV3,
            settingsToHide = SettingsToHide.decode(it.settingsToHideList),
            restoreWirelessDebugging = it.restoreWirelessDebugging,
            manageShizuku = it.manageShizuku,
            manageShizukuMigratedV3 = it.manageShizukuMigratedV3,
            autoUnhideResetV3 = it.autoUnhideResetV3,
            upgradedToV3 = it.upgradedToV3,
            // Empty means the dialog was never saved. Decoding hides that - an empty list
            // and a saved copy of the default produce the same map - so the raw fact is
            // carried alongside for the one thing that needs it.
            revertDefaultsConfigured = it.revertDefaultsList.isNotEmpty(),
            settingsToHideConfigured = it.settingsToHideList.isNotEmpty(),
            settingsToHideDefaultsV21 = it.settingsToHideDefaultsV21,
            settingsHiddenDeviceWide = it.settingsHiddenDeviceWide,
            autoHideEnabled = it.autoHideEnabled,
            autoHidePackages = it.autoHidePackagesList.toList(),
            autoHideNoKillOnLaunch = it.autoHideNoKillOnLaunch,
            autoHideEnabledBeforeHide = it.autoHideEnabledBeforeHide,
            autoHideRunning = it.autoHideRunning,
            autoUnhideEnabled = it.autoUnhideEnabled,
            // The triggers arrive unticked, which is what proto3 decodes an unwritten bool to
            // anyway - so unlike the pair below they need no flag remembering whether they were
            // ever saved. The switch refuses to move until one is chosen, which is the point.
            autoUnhideOnSwipe = it.autoUnhideOnSwipe,
            autoUnhideOnScreenLock = it.autoUnhideOnScreenLock,
            autoUnhideOnIdle = it.autoUnhideOnIdle,
            // These two do arrive on, so they need the flag: an unwritten false and a
            // deliberately cleared false are the same byte and want opposite answers.
            autoUnhideOnAppLaunch = !it.autoUnhideUsedForConfigured || it.autoUnhideOnAppLaunch,
            autoUnhideOnTile = !it.autoUnhideUsedForConfigured || it.autoUnhideOnTile,
            diagnosticsEnabled = it.diagnosticsEnabled,
            autoHideEverEnabled = it.autoHideEverEnabled,
            // A stored zero is "never written", not "revert the instant the screen goes off".
            autoUnhideScreenLockMinutes = it.autoUnhideScreenLockMinutes
                .takeIf { minutes -> minutes > 0 } ?: DEFAULT_AUTO_UNHIDE_SCREEN_LOCK_MINUTES,
            autoUnhideIdleMinutes = it.autoUnhideIdleMinutes
                .takeIf { minutes -> minutes > 0 } ?: DEFAULT_AUTO_UNHIDE_IDLE_MINUTES,
            notificationFunctionResetV16 = it.notificationFunctionResetV16,
            frameworksMigratedV3 = it.frameworksMigratedV3,
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
            settingsNoticeRevision = it.settingsNoticeRevision,
        )
    }

    suspend fun updateDynamicColor(dynamicTheme: Boolean) {
        userPreferences.updateData {
            it.copy {
                this.dynamicTheme = dynamicTheme

                // Both, always: the value is meaningless to the read above until this is true.
                dynamicThemeSet = true
            }
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

                // In the same write as the value, for the reason on favouriteAppsViewSet.
                this.sortFavouriteAppsSet = true
            }
        }
    }

    suspend fun updateIconStyle(iconStyle: IconStyle) {
        userPreferences.updateData {
            it.copy {
                this.iconStyle = iconStyle.asIconStyleProto()
            }
        }
    }

    suspend fun updateFavouriteAppsView(favouriteAppsView: FavouriteAppsView) {
        userPreferences.updateData {
            it.copy {
                this.favouriteAppsView = favouriteAppsView.asFavouriteAppsViewProto()

                // ⚠ In the same write as the value, never a second one. Choosing List is the
                // case this protects, and a marker that landed separately could be lost
                // between the two - leaving a deliberate List reading as "never chosen" and
                // being answered with Grid on the next launch.
                this.favouriteAppsViewSet = true
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

    suspend fun updateAutoRevertOnReturn(enabled: Boolean) {
        userPreferences.updateData {
            it.copy {
                autoRevertOnReturn = enabled
            }
        }
    }

    suspend fun updateRestoreWirelessDebugging(enabled: Boolean) {
        userPreferences.updateData {
            it.copy {
                restoreWirelessDebugging = enabled
            }
        }
    }

    suspend fun updateManageShizuku(enabled: Boolean) {
        userPreferences.updateData {
            it.copy {
                manageShizuku = enabled
            }
        }
    }

    suspend fun updateManageShizukuMigratedV3(done: Boolean) {
        userPreferences.updateData {
            it.copy {
                manageShizukuMigratedV3 = done
            }
        }
    }

    suspend fun updateAutoUnhideResetV3(done: Boolean) {
        userPreferences.updateData {
            it.copy {
                autoUnhideResetV3 = done
            }
        }
    }

    suspend fun updateSortFavouriteAppsSet(set: Boolean) {
        userPreferences.updateData {
            it.copy {
                sortFavouriteAppsSet = set
            }
        }
    }

    suspend fun updateFavouriteAppsViewSet(set: Boolean) {
        userPreferences.updateData {
            it.copy {
                favouriteAppsViewSet = set
            }
        }
    }

    suspend fun updateUpgradedToV3(upgraded: Boolean) {
        userPreferences.updateData {
            it.copy {
                upgradedToV3 = upgraded
            }
        }
    }

    suspend fun updateManageOverlay(enabled: Boolean) {
        userPreferences.updateData {
            it.copy {
                manageOverlay = enabled
            }
        }
    }

    /**
     * Writes a key only if there is not one already, and returns whichever key now stands.
     *
     * Generate-if-absent rather than generate-on-open so the value is stable: the integration
     * screen can be opened any number of times and the macros set up against the first key go
     * on working. Done inside updateData so two screens opening at once cannot race two keys
     * into existence.
     */
    suspend fun ensureTaskerAuthKey(): String {
        var key = ""

        userPreferences.updateData {
            it.copy {
                if (taskerAuthKey.isBlank()) taskerAuthKey = newTaskerAuthKey()

                key = taskerAuthKey
            }
        }

        return key
    }

    /**
     * Turns the integration on or off, and makes sure a key exists when turning it on, so a
     * user who flips the switch without opening the screen still has something for a broadcast
     * to match against.
     */
    suspend fun updateTaskerIntegrationEnabled(enabled: Boolean) {
        userPreferences.updateData {
            it.copy {
                taskerIntegrationEnabled = enabled

                if (enabled && taskerAuthKey.isBlank()) taskerAuthKey = newTaskerAuthKey()
            }
        }
    }

    /** Replaces the key with a fresh one, which is what retires every macro built on the old. */
    suspend fun refreshTaskerAuthKey(): String {
        val key = newTaskerAuthKey()

        userPreferences.updateData {
            it.copy {
                taskerAuthKey = key
            }
        }

        return key
    }

    suspend fun updateOverlayRestoreFailed(failed: Boolean) {
        userPreferences.updateData {
            it.copy {
                overlayRestoreFailed = failed
            }
        }
    }

    suspend fun updateManagedOverlayPackages(packages: List<String>) {
        userPreferences.updateData {
            it.copy {
                managedOverlayPackages.clear()
                managedOverlayPackages.addAll(packages.distinct())
            }
        }
    }

    /**
     * The debt and the identities it was taken with, written together.
     *
     * One write rather than two, because a restore reads both and a process death between
     * them would leave a package recorded as held with no identity to check it against.
     */
    suspend fun updateHeldOverlayPackages(
        held: Map<String, List<String>>,
        identities: Map<String, String>,
    ) {
        userPreferences.updateData {
            it.copy {
                heldOverlayPackagesByHolder.clear()
                heldOverlayPackagesByHolder.putAll(
                    held.mapValues { entry -> AccessibilityServicePlan.encode(entry.value) },
                )

                heldOverlayIdentities.clear()
                heldOverlayIdentities.putAll(identities)
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

    suspend fun updateHidingFramework(hidingFramework: HidingFramework) {
        userPreferences.updateData {
            it.copy { this.hidingFramework = hidingFramework.asHidingFrameworkProto() }
        }
    }

    suspend fun updateUnhidingFramework(unhidingFramework: UnhidingFramework) {
        userPreferences.updateData {
            it.copy { this.unhidingFramework = unhidingFramework.asUnhidingFrameworkProto() }
        }
    }

    suspend fun updateFrameworksMigratedV3(done: Boolean) {
        userPreferences.updateData {
            it.copy { this.frameworksMigratedV3 = done }
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

    suspend fun updateProgressiveBlur(enabled: Boolean) {
        userPreferences.updateData {
            it.copy {
                progressiveBlurOn = enabled

                // Both, always: the value is meaningless to the read above until this is true.
                progressiveBlurSet = true
            }
        }
    }

    /**
     * The three slider values, written together with the bool that says they were chosen.
     *
     * Clamped here as well as on the sliders: this is the last place before the store, and a
     * radius of four hundred is a frame budget rather than a preference.
     */
    suspend fun updateBlurSettings(radiusDp: Int, tintPercent: Int, fadeDp: Int) {
        userPreferences.updateData {
            it.copy {
                blurCustomised = true

                this.blurRadiusDp = radiusDp.coerceIn(BLUR_RADIUS_RANGE)

                this.blurTintPercent = tintPercent.coerceIn(BLUR_TINT_RANGE)

                this.blurFadeDp = fadeDp.coerceIn(BLUR_FADE_RANGE)
            }
        }
    }

    suspend fun updateDrawerShortcuts(manager: Boolean, hideUnhide: Boolean) {
        userPreferences.updateData {
            it.copy {
                drawerShortcutManagerOff = !manager
                drawerShortcutHideUnhideOn = hideUnhide
            }
        }
    }

    suspend fun updateOledBackground(enabled: Boolean) {
        userPreferences.updateData {
            it.copy { oledBackground = enabled }
        }
    }

    suspend fun updateManagerRows(states: Map<ManualRevertTarget, Boolean>) {
        userPreferences.updateData {
            it.copy {
                managerRows.clear()
                managerRows.addAll(ManagerRows.encode(states))
            }
        }
    }

    suspend fun updateAutoHideDetectorManagedV3(done: Boolean) {
        userPreferences.updateData {
            it.copy { this.autoHideDetectorManagedV3 = done }
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

    suspend fun updateSettingsToHideDefaultsV21(done: Boolean) {
        userPreferences.updateData {
            it.copy { this.settingsToHideDefaultsV21 = done }
        }
    }

    suspend fun updateSettingsHiddenDeviceWide(hidden: Boolean) {
        userPreferences.updateData {
            it.copy { this.settingsHiddenDeviceWide = hidden }
        }
    }

    suspend fun updateAutoHideEnabled(enabled: Boolean) {
        userPreferences.updateData {
            it.copy { this.autoHideEnabled = enabled }
        }
    }

    suspend fun updateAutoHidePackages(packages: List<String>) {
        userPreferences.updateData {
            it.copy {
                this.autoHidePackages.clear()
                this.autoHidePackages.addAll(packages)
            }
        }
    }

    suspend fun updateAutoHideNoKillOnLaunch(noKill: Boolean) {
        userPreferences.updateData {
            it.copy { this.autoHideNoKillOnLaunch = noKill }
        }
    }

    suspend fun updateAutoHideEnabledBeforeHide(enabled: Boolean) {
        userPreferences.updateData {
            it.copy { this.autoHideEnabledBeforeHide = enabled }
        }
    }

    suspend fun updateAutoHideRunning(running: Boolean) {
        userPreferences.updateData {
            it.copy { this.autoHideRunning = running }
        }
    }

    suspend fun updateAutoUnhideEnabled(enabled: Boolean) {
        userPreferences.updateData {
            it.copy { this.autoUnhideEnabled = enabled }
        }
    }

    /** The three triggers, written together because the page always knows all three. */
    suspend fun updateAutoUnhideTriggers(
        onSwipe: Boolean,
        onScreenLock: Boolean,
        onIdle: Boolean,
    ) {
        userPreferences.updateData {
            it.copy {
                this.autoUnhideOnSwipe = onSwipe
                this.autoUnhideOnScreenLock = onScreenLock
                this.autoUnhideOnIdle = onIdle
            }
        }
    }

    suspend fun updateAutoUnhideScreenLockMinutes(minutes: Int) {
        userPreferences.updateData {
            it.copy { this.autoUnhideScreenLockMinutes = minutes }
        }
    }

    suspend fun updateAutoUnhideIdleMinutes(minutes: Int) {
        userPreferences.updateData {
            it.copy { this.autoUnhideIdleMinutes = minutes }
        }
    }

    /**
     * Both "used for" answers, and the flag that says they were chosen rather than defaulted.
     *
     * Together for the reason the flag exists at all: writing one without it would leave the
     * other reading as a default for ever, so the user could untick a box and watch it come
     * back on the next read.
     */
    suspend fun updateDiagnosticsEnabled(enabled: Boolean) {
        userPreferences.updateData {
            it.copy { this.diagnosticsEnabled = enabled }
        }
    }

    /**
     * Records that the user has switched IMD+ on at least once.
     *
     * One-way on purpose. Switching IMD+ off is not a withdrawal of consent to use it
     * - it already retires the detector, which is the whole of what off means - so
     * clearing this would only make the next setup ask again for no reason.
     */
    /** Records the newest "what changed" notice this install has been shown. */
    suspend fun updateSettingsNoticeRevision(revision: Int) {
        userPreferences.updateData {
            it.copy { this.settingsNoticeRevision = revision }
        }
    }

    suspend fun markAutoHideEverEnabled() {
        userPreferences.updateData {
            it.copy { this.autoHideEverEnabled = true }
        }
    }

    suspend fun updateAutoUnhideUsedFor(onAppLaunch: Boolean, onTile: Boolean) {
        userPreferences.updateData {
            it.copy {
                this.autoUnhideOnAppLaunch = onAppLaunch
                this.autoUnhideOnTile = onTile
                this.autoUnhideUsedForConfigured = true
            }
        }
    }
}

/** Five minutes locked before the screen-lock backup decides the session is over. */
private const val DEFAULT_AUTO_UNHIDE_SCREEN_LOCK_MINUTES = 5

/** Fifteen minutes out of the foreground before the idle backup decides the same. */
private const val DEFAULT_AUTO_UNHIDE_IDLE_MINUTES = 15

/**
 * A fresh Tasker auth key: 128 bits of SecureRandom as lower-case hex.
 *
 * SecureRandom rather than UUID.randomUUID() or Random, because this is the only thing
 * standing between the exported receiver and any app that sends its broadcast, so it must not
 * be guessable. Hex rather than Base64 so it survives being copied into a text field and
 * typed back without a stray + or / being mangled.
 */
private fun newTaskerAuthKey(): String {
    val bytes = ByteArray(16)

    SecureRandom().nextBytes(bytes)

    return bytes.joinToString("") { "%02x".format(it) }
}
