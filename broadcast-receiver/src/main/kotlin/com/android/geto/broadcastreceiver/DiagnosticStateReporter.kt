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
package com.android.geto.broadcastreceiver

import android.content.Context
import android.provider.Settings
import androidx.core.app.NotificationManagerCompat
import com.android.geto.domain.common.Diagnostics
import com.android.geto.domain.framework.AccessibilityServicesWrapper
import com.android.geto.domain.framework.SecureSettingsWrapper
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.effectiveRevertDefaults
import com.android.geto.domain.model.effectiveSettingsToHide
import com.android.geto.domain.model.isShizukuConfigured
import com.android.geto.domain.model.overlayManageable
import com.android.geto.domain.repository.UserDataRepository
import com.android.geto.domain.usecase.GetAutoUnhideChecksUseCase
import com.android.geto.domain.usecase.GetManualTargetStatesUseCase
import com.android.geto.domain.usecase.GetSettingsHiddenUseCase
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import javax.inject.Inject
import javax.inject.Singleton

/** The `state` lines' own tag, so a reader can filter the log down to configuration alone. */
private const val TAG = "state"

/** Short names for the six targets, so one line holds all of them. */
private val SHORT_NAMES = mapOf(
    ManualRevertTarget.DeveloperSettings to "dev",
    ManualRevertTarget.UsbDebugging to "usb",
    ManualRevertTarget.WirelessDebugging to "wifi",
    ManualRevertTarget.AccessibilityServices to "a11y",
    ManualRevertTarget.Shizuku to "shizuku",
    ManualRevertTarget.DisplayOverOtherApps to "overlay",
)

/**
 * What IMD is configured to do, and what it is actually allowed to do, written into the log.
 *
 * The diagnostic log records **events** — a write, a hide, a revert, a tile state change — and
 * an event log alone cannot answer the first question anybody asks of it: what was this install
 * set to at the time? A revert that restored two settings where three were expected reads as a
 * bug until you know the third was never in the list, and a hide that did nothing reads as a
 * bug until you know `WRITE_SECURE_SETTINGS` had been revoked. Both answers are configuration,
 * not events, so neither was ever in the file.
 *
 * ⚠ **A full block once, then only what changed.** A dump on every hide would multiply a busy
 * day's log several times over for lines that are identical to the last hundred copies of
 * themselves. So the first report writes everything and every report after it writes only the
 * lines whose value has moved — which makes a change genuinely visible instead of buried, and
 * costs nothing at all on the overwhelming majority of runs where nothing moved.
 *
 * ⚠ **Nothing here runs unless recording is on.** [Diagnostics.enabled] is one volatile read
 * and the first thing this asks; with the log off, a report is a branch and a return. That
 * matters because the two questions it asks Android — the live setting states and the Shizuku
 * service — are real I/O, and this is called at the start and the end of every hide and every
 * revert.
 *
 * ⚠ **Read-only, all of it.** Every source here is a getter. This is called from a collector
 * that runs beside a hide in flight, and a reporter that wrote anything could change the very
 * run it is describing.
 */
@Singleton
class DiagnosticStateReporter @Inject constructor(
    @param:ApplicationContext private val context: Context,
    private val userDataRepository: UserDataRepository,
    private val getManualTargetStatesUseCase: GetManualTargetStatesUseCase,
    private val getSettingsHiddenUseCase: GetSettingsHiddenUseCase,
    private val getAutoUnhideChecksUseCase: GetAutoUnhideChecksUseCase,
    private val secureSettingsWrapper: SecureSettingsWrapper,
    private val accessibilityServicesWrapper: AccessibilityServicesWrapper,
) {
    // Two reports can be asked for at once — a hide beginning while a revert settles — and both
    // read and then rewrite [last]. Without this the second could compare against a map the
    // first had already replaced and report a change twice, or none at all.
    private val mutex = Mutex()

    private var last: Map<String, String> = emptyMap()

    /**
     * One report, named by what prompted it.
     *
     * [full] forces the whole block out even when nothing has changed. Used when recording is
     * switched on, because that is the moment the file has no baseline in it at all — and
     * without one, a delta line further down describes a change from a value the reader never
     * saw.
     */
    suspend fun report(reason: String, full: Boolean = false) {
        if (!Diagnostics.enabled) return

        val lines = runCatching { gather() }.getOrNull() ?: return

        mutex.withLock {
            val previous = last

            last = lines

            val changed = if (full || previous.isEmpty()) {
                lines
            } else {
                lines.filter { previous[it.key] != it.value }
            }

            if (changed.isEmpty()) return@withLock

            if (full || previous.isEmpty()) {
                Diagnostics.log(tag = TAG, message = "--- $reason ---")
            }

            for (key in lines.keys) {
                val value = changed[key] ?: continue

                Diagnostics.log(
                    tag = TAG,
                    message = if (full || previous.isEmpty()) {
                        "$key  $value"
                    } else {
                        "$reason: $key  $value"
                    },
                )
            }
        }
    }

    /**
     * Everything worth knowing, as an ordered map of one line each.
     *
     * A `LinkedHashMap` by construction, so the full block always comes out in the same order
     * and two logs can be read side by side.
     */
    private suspend fun gather(): Map<String, String> {
        val userData = userDataRepository.userData.first()

        val states = getManualTargetStatesUseCase()

        val hidden = getSettingsHiddenUseCase()

        val checks = getAutoUnhideChecksUseCase()

        val writeSecure = secureSettingsWrapper.hasWriteSecureSettingsPermission()

        val detectorRunning = accessibilityServicesWrapper.isAutoHideServiceRunning()

        val notifications = runCatching {
            NotificationManagerCompat.from(context).areNotificationsEnabled()
        }.getOrDefault(false)

        val overlayPermission = runCatching {
            Settings.canDrawOverlays(context)
        }.getOrDefault(false)

        return linkedMapOf(
            "frameworks" to listOf(
                "hiding=${userData.hidingFramework}",
                "unhiding=${userData.unhidingFramework}",
                "migrated=${yesNo(userData.frameworksMigratedV3)}",
            ).joinToString(separator = " "),

            // The effective lists rather than the stored ones: with overlay management off the
            // stored map can still carry a tick that nothing acts on, and what the log has to
            // answer is what this install actually hides.
            "hide list" to targets(userData.effectiveSettingsToHide) +
                " (configured=${yesNo(userData.settingsToHideConfigured)})",

            "revert list" to targets(userData.effectiveRevertDefaults) +
                " (configured=${yesNo(userData.revertDefaultsConfigured)})",

            "permissions" to listOf(
                "writeSecure=${yesNo(writeSecure)}",
                "notifications=${yesNo(notifications)}",
                "overlay=${yesNo(overlayPermission)}",
                "dump=${yesNo(checks.dumpPermission)}",
                "usage=${yesNo(checks.usageAccess)}",
                "exitReasons=${yesNo(checks.exitReasonsSupported)}",
            ).joinToString(separator = " "),

            "shizuku" to listOf(
                "fork=${userData.shizukuForkMode}",
                "configured=${yesNo(userData.isShizukuConfigured)}",
                "available=${yesNo(states.shizukuAvailable)}",
                "intents=${yesNo(states.shizukuSupportsIntents)}",
                "restartToggle=${yesNo(userData.restartShizuku)}",
                "lastStartFailed=${yesNo(userData.shizukuStartFailed)}",
                "pkg=${userData.shizukuPackageName.ifEmpty { "unset" }}",
            ).joinToString(separator = " "),

            "accessibility" to listOf(
                "managed=${userData.managedAccessibilityServices.size}",
                "held=${userData.heldAccessibilityServices.size}",
                "manageable=${yesNo(states.accessibilityManaged)}",
                "imd+service=${if (detectorRunning) "running" else "off"}",
            ).joinToString(separator = " "),

            "overlay" to listOf(
                "manage=${yesNo(userData.overlayManageable)}",
                "managed=${userData.managedOverlayPackages.size}",
                "held=${userData.heldOverlayPackages.size}",
                "manageable=${yesNo(states.overlayManaged)}",
                "restoreFailed=${yesNo(userData.overlayRestoreFailed)}",
            ).joinToString(separator = " "),

            "imd+" to listOf(
                "enabled=${yesNo(userData.autoHideEnabled)}",
                "running=${yesNo(userData.autoHideRunning)}",
                "apps=${userData.autoHidePackages.size}",
                "everEnabled=${yesNo(userData.autoHideEverEnabled)}",
                "noKillOnLaunch=${yesNo(userData.autoHideNoKillOnLaunch)}",
            ).joinToString(separator = " "),

            "auto unhide" to listOf(
                "enabled=${yesNo(userData.autoUnhideEnabled)}",
                "swipe=${yesNo(userData.autoUnhideOnSwipe)}",
                "idle=${yesNo(userData.autoUnhideOnIdle)}(${userData.autoUnhideIdleMinutes}m)",
                "screenLock=${yesNo(userData.autoUnhideOnScreenLock)}" +
                    "(${userData.autoUnhideScreenLockMinutes}m)",
                "onAppLaunch=${yesNo(userData.autoUnhideOnAppLaunch)}",
                "onTile=${yesNo(userData.autoUnhideOnTile)}",
            ).joinToString(separator = " "),

            "auto revert" to "onReturn=${yesNo(userData.autoRevertOnReturn)}",

            // What the app believes it owes. The pair the author's Favourites button reads, and
            // the pair a stale notification contradicts.
            "debts" to listOf(
                "deviceWide=${yesNo(hidden.deviceWide)}",
                "memory=${yesNo(hidden.memory)}",
                "records=${userData.settingStateBefore.size}",
            ).joinToString(separator = " "),

            // Asked of Android, not of storage — the row of switches the settings manager
            // draws, at the moment of the report.
            "live" to ManualRevertTarget.entries.joinToString(separator = " ") { target ->
                "${SHORT_NAMES[target]}=${if (states.isEnabled(target)) "on" else "off"}"
            },
        )
    }

    /** The ticked targets of one configuration map, in enum order, or `none`. */
    private fun targets(configuration: Map<ManualRevertTarget, Boolean>): String {
        val ticked = ManualRevertTarget.entries.filter { configuration[it] == true }

        if (ticked.isEmpty()) return "none"

        return ticked.joinToString(separator = ",") { SHORT_NAMES[it].orEmpty() }
    }

    /**
     * `yes` and `no` rather than `true` and `false`.
     *
     * These lines are read by a person looking for the one field that is wrong, often on a
     * phone. Two shapes that differ in their first letter scan far faster than two that share
     * three of their first four.
     */
    private fun yesNo(value: Boolean): String = if (value) "yes" else "no"
}
