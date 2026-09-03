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
package com.android.geto.domain.usecase

import com.android.geto.domain.common.dispatcher.Dispatcher
import com.android.geto.domain.common.dispatcher.GetoDispatchers
import com.android.geto.domain.framework.AccessibilityServicesWrapper
import com.android.geto.domain.framework.PackageManagerWrapper
import com.android.geto.domain.framework.ShizukuWrapper
import com.android.geto.domain.model.AccessibilityServicePlan
import com.android.geto.domain.repository.UserDataRepository
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withContext
import javax.inject.Inject

/**
 * How long between one look at the service and the next while waiting for it to bind.
 *
 * Binding is a handful of milliseconds when it works at all; the wait exists for the case where
 * the system is slow rather than refusing, so it is short.
 */
private const val BIND_POLL_MILLIS = 250L

/** Total wait for a bind, in polls. Two and a half seconds. */
private const val BIND_POLLS = 10

/**
 * Switches IMD's own accessibility service — the IMD+ detector — on, and confirms it.
 *
 * The order is the user's, and it is deliberate:
 *
 * 1. **Write the secure setting.** IMD holds WRITE_SECURE_SETTINGS, so this is the direct path
 *    and it is the one that works on Android 12 and below.
 * 2. **If the service does not come up, go through Shizuku automatically** — allow the
 *    restricted-settings AppOp for IMD's own package, then write again. From Android 13 a
 *    sideloaded app's accessibility service cannot be bound until that AppOp is allowed: the
 *    write itself succeeds and the system simply declines to bind, which is why step 1 can
 *    report success and leave nothing running.
 * 3. **If it still does not come up, say so** and let the caller raise the popup offering the
 *    two things the user can do by hand.
 *
 * The result is what the system did, not what the writes returned. Nothing here trusts a
 * `true` from [AccessibilityServicesWrapper.setEnabledAccessibilityServices]: the whole failure
 * this guards against is a write that lands on a service that never binds.
 */
class EnableAutoHideServiceUseCase @Inject constructor(
    private val accessibilityServicesWrapper: AccessibilityServicesWrapper,
    private val shizukuWrapper: ShizukuWrapper,
    private val packageManagerWrapper: PackageManagerWrapper,
    private val userDataRepository: UserDataRepository,
    @param:Dispatcher(GetoDispatchers.Default) private val defaultDispatcher: CoroutineDispatcher,
) {
    /**
     * True once the detector is bound and running.
     *
     * False means every automatic route has been tried and none worked — the caller shows the
     * two-item popup. It never throws: a dead Shizuku binder and a refused write are both
     * ordinary outcomes here, and a settings screen that crashed on either would be worse than
     * one that reports the failure.
     */
    suspend operator fun invoke(): Boolean = withContext(defaultDispatcher) {
        // Half of this is a secure-settings write and a record of a released hold. Navigating
        // away part-way through would leave the record disagreeing with the device.
        withContext(NonCancellable) {
            runCatching { enable() }.getOrDefault(false)
        }
    }

    private suspend fun enable(): Boolean {
        // Already running. Said first because the settings page calls this on a switch the user
        // may press twice, and because a repeat write would drop the hold record below for a
        // detector that no run had switched off.
        if (isRunning()) {
            releaseOwnHold()

            return true
        }

        if (writeEnabled() && awaitBind()) {
            releaseOwnHold()

            return true
        }

        // The Android 13+ path. Asking Shizuku for its own permission is what raises its prompt,
        // so it happens here rather than on the way into the screen.
        val viaShizuku = runCatching {
            (shizukuWrapper.hasShizukuPermission() || shizukuWrapper.requestShizukuPermission()) &&
                shizukuWrapper.allowRestrictedSettings(
                    packageName = packageManagerWrapper.ownPackageName(),
                )
        }.getOrDefault(false)

        if (!viaShizuku) return false

        if (writeEnabled() && awaitBind()) {
            releaseOwnHold()

            return true
        }

        return false
    }

    /**
     * Adds the detector to enabled_accessibility_services, leaving every other service in the
     * list exactly where it was.
     *
     * [AccessibilityServicePlan.enable] rather than a bare append: it is the same arithmetic
     * the manual re-enable control uses, and it will not write a duplicate into a list the
     * system stores as plain colon-separated text.
     */
    private suspend fun writeEnabled(): Boolean {
        val component = accessibilityServicesWrapper.autoHideServiceComponent()

        val currentlyEnabled = runCatching {
            accessibilityServicesWrapper.getEnabledAccessibilityServices()
        }.getOrNull() ?: return false

        val wanted = AccessibilityServicePlan.enable(
            wanted = listOf(component),
            currentlyEnabled = currentlyEnabled,
        )

        return runCatching {
            accessibilityServicesWrapper.setEnabledAccessibilityServices(wanted)
        }.getOrDefault(false)
    }

    /**
     * Waits for the system to bind the service, or gives up.
     *
     * The setting is written and the bind follows some moments later, so asking once
     * immediately afterwards would report failure for a service that was about to come up.
     */
    private suspend fun awaitBind(): Boolean {
        repeat(BIND_POLLS) {
            if (isRunning()) return true

            delay(BIND_POLL_MILLIS)
        }

        return isRunning()
    }

    private suspend fun isRunning(): Boolean = runCatching {
        accessibilityServicesWrapper.isAutoHideServiceRunning()
    }.getOrDefault(false)

    /**
     * Clears IMD+'s own hold once its detector is back on.
     *
     * A run switches the detector off and records a hold so a revert can put it back. Switching
     * it on by hand settles the same debt, and leaving the record standing would have the next
     * revert "restore" a service that is already running — harmless in itself, but the record
     * would then never empty, and a stale hold is exactly what makes these bugs hard to see.
     */
    private suspend fun releaseOwnHold() {
        val held = userDataRepository.userData.first().heldAccessibilityServices

        if (AccessibilityServicePlan.AUTO_HIDE_HOLD !in held) return

        userDataRepository.updateHeldAccessibilityServices(
            held = held - AccessibilityServicePlan.AUTO_HIDE_HOLD,
        )
    }
}
