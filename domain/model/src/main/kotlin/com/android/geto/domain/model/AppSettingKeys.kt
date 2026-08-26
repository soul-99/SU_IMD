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
}
