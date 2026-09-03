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
package com.android.geto.domain.framework

import com.android.geto.domain.model.ShizukuGrant

interface ShizukuWrapper {
    /**
     * Asks Shizuku to run `pm grant <packageName> android.permission.WRITE_SECURE_SETTINGS`,
     * requesting Shizuku's own permission first if it has not been given yet.
     *
     * This is the no-PC path through first-run setup. It goes entirely through the binder
     * Shizuku publishes, never through its package name, so a renamed or hidden install
     * works exactly the same — which matters here, because the people most likely to want
     * this app are also the ones most likely to be running Shizuku under another name.
     */
    suspend fun grantWriteSecureSettings(packageName: String): ShizukuGrant

    /** Whether a Shizuku binder is alive right now, without prompting for anything. */
    suspend fun isShizukuRunning(): Boolean

    /**
     * Whether Shizuku has already granted this app its permission — asking nothing.
     *
     * Separate from every call that *uses* the permission, because IMD+ has to report the
     * requirement on a settings page without a prompt appearing every time the page is drawn.
     */
    suspend fun hasShizukuPermission(): Boolean

    /** Asks Shizuku for its permission, showing its prompt. False if refused or unavailable. */
    suspend fun requestShizukuPermission(): Boolean

    /**
     * Force-stops a package.
     *
     * What IMD+ does to an app on its first launch, so the app reads the settings after they
     * have been hidden rather than before. `am force-stop` needs FORCE_STOP_PACKAGES, which no
     * ordinary app can hold — Shizuku's shell runs as the adb user, which can.
     */
    suspend fun forceStop(packageName: String): Boolean

    /**
     * Clears the "restricted setting" block on a package.
     *
     * From Android 13, a sideloaded app's accessibility service cannot be switched on — not by
     * the user in Settings, and not by writing the secure setting either — until this AppOp is
     * allowed. IMD is sideloaded by definition, so IMD+ cannot enable its own detector on a
     * modern device without this.
     */
    suspend fun allowRestrictedSettings(packageName: String): Boolean

    /** Exempts a package from battery optimisation, so it survives long enough to be useful. */
    suspend fun allowBatteryUnrestricted(packageName: String): Boolean

    /**
     * Grants IMD `android.permission.DUMP` once, so auto unhide can read another app's process
     * exit reasons without Shizuku ever being alive again afterwards.
     */
    suspend fun grantDumpPermission(packageName: String): ShizukuGrant

    /** Grants the usage-access AppOp, the alternative to sending the user to a settings list. */
    suspend fun allowUsageAccess(packageName: String): Boolean

    /**
     * Packages whose SYSTEM_ALERT_WINDOW AppOp is currently allowed, or null when the
     * Shizuku shell is unavailable.
     */
    suspend fun getAllowedOverlayPackages(): Set<String>?

    /**
     * Changes SYSTEM_ALERT_WINDOW and returns the packages successfully changed, or null
     * when no Shizuku shell was available. Packages are attempted independently.
     */
    suspend fun setOverlayPermission(packages: Set<String>, allowed: Boolean): Set<String>?

    /**
     * Fires the "start Shizuku" broadcast at the Shizuku manager app.
     *
     * Two fork families are supported. thedjchi's listens for an explicit broadcast
     * carrying the string extra "auth", the token shown under "View intents"; Shevery
     * and the forks alongside it expose a start action with no token, so [authKey] is
     * blank and the extra is left off. Vanilla RikkaApps Shizuku listens for neither,
     * in which case there is no receiver to resolve and this returns false.
     *
     * Returns false when the manager package is not installed or the broadcast
     * could not be sent.
     */
    suspend fun startShizuku(
        packageName: String,
        action: String,
        authKey: String,
    ): Boolean

    /**
     * The same broadcast with the fork's stop action instead.
     *
     * Separate from [startShizuku] only so call sites read honestly; the mechanism is
     * identical, and the action is supplied by the caller because it is derived from
     * whatever the user configured rather than known here.
     */
    suspend fun stopShizuku(
        packageName: String,
        action: String,
        authKey: String,
    ): Boolean

    companion object {
        const val DEFAULT_SHIZUKU_PACKAGE_NAME = "moe.shizuku.privileged.api"
        const val ACTION_START_SUFFIX = ".START"
        const val EXTRA_AUTH = "auth"
    }
}
