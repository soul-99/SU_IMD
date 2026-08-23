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
import com.android.geto.domain.framework.ShizukuWrapper
import com.android.geto.domain.model.isShizukuConfigured
import com.android.geto.domain.repository.UserDataRepository
import javax.inject.Inject
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withContext

/**
 * How long to keep asking whether Shizuku came up before calling it a failure.
 *
 * Starting Shizuku is a broadcast, not a call: the app asks and Shizuku is free to take its
 * time or ignore it entirely. Forks differ by seconds — Shevery in particular is slow off the
 * mark — so anything much under this reports failures that were only slowness.
 */
private const val CONFIRM_TIMEOUT_MILLIS = 10_000L

private const val CONFIRM_POLL_MILLIS = 500L

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
class StartShizukuUseCase @Inject constructor(
    private val shizukuWrapper: ShizukuWrapper,
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
            val sent = shizukuWrapper.startShizuku(
                packageName = userData.shizukuPackageName,
                action = userData.shizukuStartAction.ifBlank {
                    userData.shizukuPackageName + ShizukuWrapper.ACTION_START_SUFFIX
                },
                authKey = userData.shizukuAuthKey,
            )

            // No receiver resolved the broadcast, which is the vanilla-Shizuku case. There
            // is nothing to wait for.
            if (!sent) return@withContext record(started = false)

            record(started = awaitRunning())
        } finally {
            shizukuStartTracker.end()
        }
    }

    /**
     * Polls rather than waits a fixed time, so a fork that comes up in one second is not
     * held behind a ten-second spinner.
     */
    private suspend fun awaitRunning(): Boolean {
        repeat((CONFIRM_TIMEOUT_MILLIS / CONFIRM_POLL_MILLIS).toInt()) {
            delay(CONFIRM_POLL_MILLIS)

            val running = runCatching { shizukuWrapper.isShizukuRunning() }.getOrDefault(false)

            if (running) return true
        }

        return false
    }

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
