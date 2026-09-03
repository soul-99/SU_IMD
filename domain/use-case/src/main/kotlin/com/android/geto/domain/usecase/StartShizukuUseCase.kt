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
import com.android.geto.domain.framework.PackageManagerWrapper
import com.android.geto.domain.framework.SecureSettingsWrapper
import com.android.geto.domain.framework.ShizukuWrapper
import com.android.geto.domain.model.AppSettingKeys
import com.android.geto.domain.model.SettingType
import com.android.geto.domain.model.UserData
import com.android.geto.domain.model.isShizukuConfigured
import com.android.geto.domain.repository.UserDataRepository
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withContext
import javax.inject.Inject

/**
 * How long to wait between one look at the service and the next.
 *
 * The total wait is not a constant any more: it comes from
 * [ShizukuForkMode.serviceWaitMillis], because the two fork families are waiting on entirely
 * different things — a broadcast being answered, or a watchdog coming round.
 */
private const val CONFIRM_POLL_MILLIS = 500L

/**
 * How many polls between one start broadcast and the next resend, so the wait holds a handful
 * of attempts rather than one. At 500 ms a poll, every fourth is about two seconds - often
 * enough that a fork which dropped the first broadcast still gets one, rare enough not to
 * hammer a fork that is simply slow to come up. Only used for the fork family that has a
 * broadcast to resend.
 */
private const val RESEND_EVERY_POLLS = 4

/**
 * Asks Shizuku to start, then waits to find out whether it did.
 *
 * The one place a start is attempted, which is the point. Before this, sending the broadcast
 * *was* the result: the switch went on, the app reported success, and if Shizuku never came
 * up nothing said so — the switch would simply be back off the next time anyone looked, with
 * no explanation and nothing to act on.
 *
 * The outcome is recorded so the manager dialog can show it later. That matters because most
 * attempts happen where nobody is looking: a revert from a tile or a notification starts
 * Shizuku with no UI on screen at all, and the failure needs to survive until there is
 * somewhere to report it.
 */
private const val ON = "1"

private const val OFF = "0"

class StartShizukuUseCase @Inject constructor(
    private val shizukuWrapper: ShizukuWrapper,
    private val secureSettingsWrapper: SecureSettingsWrapper,
    private val packageManagerWrapper: PackageManagerWrapper,
    private val userDataRepository: UserDataRepository,
    private val shizukuStartTracker: ShizukuStartTracker,
    @param:Dispatcher(GetoDispatchers.Default) private val defaultDispatcher: CoroutineDispatcher,
) {
    suspend operator fun invoke(): Boolean = withContext(defaultDispatcher) {
        val userData = userDataRepository.userData.first()

        if (!userData.isShizukuConfigured) return@withContext record(started = false)

        // Asking a package that is not there to start would burn the full ten seconds and
        // then report a failure the user cannot act on, when the real answer is simply that
        // the configured Shizuku app is not installed.
        val installed = runCatching {
            packageManagerWrapper.isInstalled(packageName = userData.shizukuPackageName)
        }.getOrDefault(false)

        if (!installed) return@withContext record(started = false)

        shizukuStartTracker.begin()

        try {
            record(started = startAndAwait(userData))
        } finally {
            shizukuStartTracker.end()
        }
    }

    /**
     * Sends the start broadcast, then polls for the fork's whole budget, resending the
     * broadcast every couple of seconds until Shizuku is running or the budget is spent.
     *
     * ⚠ **The budget is per fork and lives in `ShizukuForkMode.serviceWaitMillis`** — 8 s for
     * Thedjchi, 40 s for Shevery, both the author's numbers in v3. This comment used to say
     * "ten seconds", which is a figure no build has used since the per-fork budgets arrived.
     *
     * One send is not always enough: a fork whose app is closed can miss the first broadcast
     * while its process is still starting, and the old single-shot start then waited out the
     * whole budget for a service that would have come up on a second nudge. The window is
     * unchanged - the resends happen inside it, not after it - so a revert that cannot bring
     * Shizuku up still gives up when it always did and raises its notification then.
     *
     * Returns as soon as Shizuku is seen running, so a fork that answers the first broadcast
     * is not held for the resends it no longer needs.
     */
    private suspend fun startAndAwait(userData: UserData): Boolean {
        // Shevery is not asked - it is enabled. See sheveryStart below.
        if (userData.shizukuForkMode.isShevery) return sheveryStart(userData = userData)

        val action = userData.shizukuStartAction.ifBlank {
            userData.shizukuPackageName + ShizukuWrapper.ACTION_START_SUFFIX
        }

        repeat(pollsFor(userData)) { poll ->
            if (poll % RESEND_EVERY_POLLS == 0) {
                shizukuWrapper.startShizuku(
                    packageName = userData.shizukuPackageName,
                    action = action,
                    authKey = userData.shizukuAuthKey,
                )
            }

            delay(CONFIRM_POLL_MILLIS)

            if (isRunning()) return true
        }

        return false
    }

    /**
     * Brings Shevery's service up the only way it can be brought up: by giving the debugging
     * transport back and waiting for Shevery to notice.
     *
     * Shevery has no start intent. What restarts its server is Shevery's own **ErrorProtect**
     * watchdog, which polls on roughly a ten-second cycle and starts the server itself once
     * the transport is available - and, unlike this app, it will not switch debugging on to do
     * it. So the whole of IMD's part is: switch USB and wireless debugging on, then watch.
     *
     * On failure the two switches are put back exactly as they were found. That is the
     * difference between this and every other start in the app: this one changes the device in
     * order to ask, so it owes an undo when the asking comes to nothing. A user who had
     * debugging off and asked for an overlay hide must not be left with debugging on because
     * their Shizuku never came up.
     */
    private suspend fun sheveryStart(userData: UserData): Boolean {
        // Written through the settings wrapper rather than through SetManualTargetUseCase,
        // which would be the obvious call: that use case already injects *this* one, to start
        // Shizuku for its own Shizuku target, and asking for it back here is a dependency
        // cycle Dagger refuses to build. These two are plain Global settings writes anyway -
        // exactly what that use case would do with them.
        val transport = listOf(AppSettingKeys.ADB_ENABLED, AppSettingKeys.ADB_WIFI_ENABLED)

        // Only the ones that are actually off, so nothing is "restored" to a state it was
        // never in, and a device that already had both on is left completely alone.
        val switchedOn = transport.filterNot { isDebuggingOn(key = it) }

        switchedOn.forEach { setDebugging(key = it, on = true) }

        repeat(pollsFor(userData)) {
            delay(CONFIRM_POLL_MILLIS)

            if (isRunning()) return true
        }

        // Nothing came up, so put the transport back where it was found.
        withContext(NonCancellable) {
            switchedOn.forEach { setDebugging(key = it, on = false) }
        }

        return false
    }

    private suspend fun isDebuggingOn(key: String): Boolean = runCatching {
        secureSettingsWrapper.getSecureSettingValue(
            settingType = SettingType.GLOBAL,
            key = key,
        ) == ON
    }.getOrDefault(false)

    private suspend fun setDebugging(key: String, on: Boolean) {
        runCatching {
            secureSettingsWrapper.canWriteSecureSettings(
                settingType = SettingType.GLOBAL,
                key = key,
                value = if (on) ON else OFF,
            )
        }
    }

    private fun pollsFor(userData: UserData): Int =
        (userData.shizukuForkMode.serviceWaitMillis / CONFIRM_POLL_MILLIS).toInt()

    private suspend fun isRunning(): Boolean =
        runCatching { shizukuWrapper.isShizukuRunning() }.getOrDefault(false)

    /**
     * Written under [NonCancellable] because this is the whole point of the exercise: a
     * failure the user is never told about is the bug being fixed here, and the caller's
     * scope going away mid-write would recreate it.
     */
    private suspend fun record(started: Boolean): Boolean {
        withContext(NonCancellable) {
            userDataRepository.updateShizukuStartFailed(failed = !started)
        }

        return started
    }
}
