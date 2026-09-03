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
 * Setting keys suIMD has to reason about specifically, rather than just writing
 * through like every other key.
 */
object AppSettingKeys {
    const val DEVELOPMENT_SETTINGS_ENABLED = "development_settings_enabled"
    const val ADB_ENABLED = "adb_enabled"
    const val ADB_WIFI_ENABLED = "adb_wifi_enabled"

    /** Secure, not Global. Upstream Geto had this one in the wrong table. */
    const val ACCESSIBILITY_ENABLED = "accessibility_enabled"

    const val ENABLED_ACCESSIBILITY_SERVICES = "enabled_accessibility_services"

    /**
     * A marker, not a settings key. There is no Settings row behind overlay access: it is an
     * AppOp held per package, written through Shizuku.
     *
     * It is shaped like a key anyway so a per-app profile can carry it in the same list as
     * everything else, and it is named after the AppOp so it reads as what it is rather than
     * as an invented string. Filtered out of the plain write loop wherever it appears -
     * handing it to the secure settings wrapper would be writing a key Android has never
     * heard of.
     */
    const val SYSTEM_ALERT_WINDOW = "op_system_alert_window"

    /**
     * A marker, not a settings key — the same idea as [SYSTEM_ALERT_WINDOW]. There is no
     * Settings row behind stopping the Shizuku service: it is done by broadcasting the fork's
     * stop intent (or, when the fork has no stop intent, by cycling USB debugging to drop the
     * transport it rides on). A per-app profile carries it in the same list as everything
     * else, and it is filtered out of the plain write loop wherever it appears — handing it
     * to the secure settings wrapper would be writing a key Android has never heard of.
     */
    const val SHIZUKU_SERVICE = "shizuku_service"

    /**
     * The real Settings rows this app writes, and nothing else.
     *
     * Exists so the settings observer can tell a change that matters from the constant
     * background traffic in those three tables - screen brightness, ringer volume, wallpaper,
     * a dozen keys a launcher touches - which is most of what a content observer on
     * System/Secure/Global actually sees.
     *
     * [SYSTEM_ALERT_WINDOW] and [SHIZUKU_SERVICE] are deliberately absent. They are markers,
     * not keys: there is no Settings row behind either, so neither can ever arrive as the last
     * path segment of a changed URI, and listing them would suggest a watch that cannot exist.
     */
    val MANAGED_KEYS = setOf(
        DEVELOPMENT_SETTINGS_ENABLED,
        ADB_ENABLED,
        ADB_WIFI_ENABLED,
        ACCESSIBILITY_ENABLED,
        ENABLED_ACCESSIBILITY_SERVICES,
    )

    /**
     * Turning any of these back on is what Shizuku needs in order to be startable again.
     *
     * Kept as a set even though only [ADB_ENABLED] triggers the restart now, because the
     * other two are still what Shizuku depends on — developer options off takes USB
     * debugging with it — and a future caller asking "does this profile touch Shizuku's
     * transport" wants all three.
     */
    val SHIZUKU_DEPENDENT_KEYS = setOf(
        DEVELOPMENT_SETTINGS_ENABLED,
        ADB_ENABLED,
        ADB_WIFI_ENABLED,
    )

    /**
     * True when reverting a profile puts back the USB debugging that same profile switched
     * off.
     *
     * Narrower than it used to be, in two ways. Only USB debugging counts: it is the
     * transport Shizuku's service actually runs over, and restarting Shizuku because a
     * profile happened to restore *wireless* debugging was firing the broadcast at devices
     * where nothing had gone down in the first place.
     *
     * And the profile must have been what switched it off — [AppSetting.valueOnLaunch] of
     * "0". A profile that leaves USB debugging alone, or turns it on, did not stop Shizuku,
     * so there is nothing for this to put right.
     */
    fun triggersShizukuRestart(appSettings: List<AppSetting>): Boolean = appSettings.any {
        it.enabled &&
            it.key == ADB_ENABLED &&
            it.valueOnLaunch == "0" &&
            it.valueOnRevert == "1"
    }

    /**
     * True when applying these settings is meant to take accessibility services down.
     * Only a launch value of "0" counts, so a setting that turns accessibility *on* does
     * not accidentally suspend anything.
     */
    fun hidesAccessibilityServices(appSettings: List<AppSetting>): Boolean = appSettings.any {
        it.enabled && it.key == ACCESSIBILITY_ENABLED && it.valueOnLaunch == "0"
    }

    /** True when reverting these settings should put suspended services back. */
    fun restoresAccessibilityServices(appSettings: List<AppSetting>): Boolean = appSettings.any {
        it.enabled && it.key == ACCESSIBILITY_ENABLED
    }

    /**
     * True when applying this profile is meant to withdraw overlay access. As above, only a
     * launch value of "0" counts, so a row that grants it cannot trigger a hide.
     */
    fun hidesOverlayAccess(appSettings: List<AppSetting>): Boolean = appSettings.any {
        it.enabled && it.key == SYSTEM_ALERT_WINDOW && it.valueOnLaunch == "0"
    }

    /** True when reverting this profile should give overlay access back. */
    fun restoresOverlayAccess(appSettings: List<AppSetting>): Boolean = appSettings.any {
        it.enabled && it.key == SYSTEM_ALERT_WINDOW
    }

    /**
     * True when applying this profile is meant to stop the Shizuku service. As with the
     * overlay marker, only a launch value of "0" counts, so a row that is present but not
     * set to stop the service cannot trigger a stop.
     *
     * There is deliberately no `restoresShizukuService` counterpart to this. Whether a revert
     * starts the service again is not a question about the profile but about what actually
     * happened on the way in: only an app that took a *running* service down has anything to
     * put back, and that is recorded per app under [SettingSnapshot.SHIZUKU_STOPPED_ID] at the
     * moment it happens. Reading it off the profile instead would have every app carrying the
     * marker start Shizuku on revert, including the ones that found it already stopped.
     */
    fun stopsShizukuService(appSettings: List<AppSetting>): Boolean = appSettings.any {
        it.enabled && it.key == SHIZUKU_SERVICE && it.valueOnLaunch == "0"
    }
}
