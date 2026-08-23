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
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.RevertToDefaultResult
import com.android.geto.domain.repository.UserDataRepository
import javax.inject.Inject
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withContext

/**
 * Wireless and USB debugging do not come back the instant the Global flag is written; adbd
 * has to restart and re-advertise. Give it a moment before asking Shizuku to start,
 * otherwise the broadcast lands before there is anything to connect to.
 *
 * Only waited when this run actually switched debugging on. Reverting to a default where
 * debugging was already up has nothing to wait for, and a fixed pause on every press would
 * make the tile feel broken.
 */
private const val SHIZUKU_START_DELAY_MILLIS = 1_500L

/**
 * Drives every target to the state saved in the "Revert to default" configuration.
 *
 * Where [RevertAppSettingsUseCase] undoes what one app changed, this one ignores apps
 * entirely and puts the device into the state the user nominated as normal. That makes it
 * the answer to "I do not know what is switched off any more" — which is a different
 * question from "undo that app", and one the per-app revert cannot answer once its
 * notification has been swiped away.
 *
 * Targets already in the wanted state are left alone rather than written again. That is not
 * only about avoiding pointless writes: re-broadcasting a start to a Shizuku that is already
 * running is the kind of thing that shows up as a mystery service restart later.
 */
class RevertToDefaultUseCase @Inject constructor(
    private val userDataRepository: UserDataRepository,
    private val getManualTargetStatesUseCase: GetManualTargetStatesUseCase,
    private val setManualTargetUseCase: SetManualTargetUseCase,
    @param:Dispatcher(GetoDispatchers.Default) private val defaultDispatcher: CoroutineDispatcher,
) {
    suspend operator fun invoke(): RevertToDefaultResult = withContext(defaultDispatcher) {
        // A half-applied revert is worse than none — developer options on with USB debugging
        // still off is a state the user did not ask for and cannot see. A tile press whose
        // service is torn down mid-run must not be able to leave that behind.
        withContext(NonCancellable) { revert() }
    }

    private suspend fun revert(): RevertToDefaultResult {
        val wanted = userDataRepository.userData.first().revertDefaults

        val before = getManualTargetStatesUseCase()

        val changed = mutableSetOf<ManualRevertTarget>()
        val failed = mutableSetOf<ManualRevertTarget>()
        val unchanged = mutableSetOf<ManualRevertTarget>()

        // Declaration order, and it is load-bearing: USB debugging is meaningless with
        // developer options off, and Shizuku cannot start without USB debugging. Working
        // through the enum in order means each target is set up by the time the next one
        // needs it.
        for (target in ManualRevertTarget.entries) {
            val enabled = wanted[target] ?: continue

            if (before.isEnabled(target) == enabled) {
                unchanged += target

                continue
            }

            if (target == ManualRevertTarget.Shizuku && enabled && debuggingJustEnabled(changed)) {
                delay(SHIZUKU_START_DELAY_MILLIS)
            }

            if (setManualTargetUseCase(target = target, enabled = enabled)) {
                changed += target
            } else {
                failed += target
            }
        }

        return RevertToDefaultResult(
            changed = changed,
            failed = failed,
            unchanged = unchanged,
        )
    }

    private fun debuggingJustEnabled(changed: Set<ManualRevertTarget>): Boolean =
        ManualRevertTarget.UsbDebugging in changed || ManualRevertTarget.WirelessDebugging in changed
}
