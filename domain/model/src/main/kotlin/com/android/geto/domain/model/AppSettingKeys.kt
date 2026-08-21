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
     * Turning any of these back on is what Shizuku needs in order to be startable
     * again, so a revert that touches one of them is the trigger for the restart.
     */
    val SHIZUKU_DEPENDENT_KEYS = setOf(
        DEVELOPMENT_SETTINGS_ENABLED,
        ADB_ENABLED,
        ADB_WIFI_ENABLED,
    )

    /**
     * True when reverting these settings actually switches the transport Shizuku needs
     * back on. A revert value other than "1" leaves it off, so there would be nothing for
     * Shizuku to reconnect through and firing the start broadcast would be noise.
     */
    fun triggersShizukuRestart(appSettings: List<AppSetting>): Boolean = appSettings.any {
        it.enabled && it.key in SHIZUKU_DEPENDENT_KEYS && it.valueOnRevert == "1"
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
}
