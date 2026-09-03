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

import com.android.geto.domain.framework.AccessibilityServicesWrapper
import com.android.geto.domain.model.AccessibilityServicePlan
import com.android.geto.domain.common.dispatcher.Dispatcher
import com.android.geto.domain.common.dispatcher.GetoDispatchers
import com.android.geto.domain.repository.UserDataRepository
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withContext
import javax.inject.Inject

/**
 * Switches IMD's own accessibility service off for good, when the user switches IMD+ off.
 *
 * **Different from [DisableAutoHideServiceUseCase], and the difference is the debt.** That one
 * switches the detector off *during* a run and records that IMD owes it back, because a revert
 * is coming to restore it. This one is the end of the arrangement: IMD+ has been turned off, so
 * nothing is coming, nothing is owed, and the hold is dropped rather than written.
 *
 * The author's rule, in their words: with IMD+ off, IMD's own accessibility service is disabled
 * *"permanently … until changed again"* and the hide and revert sequences stop touching it. It
 * comes back through [EnableAutoHideServiceUseCase] the next time IMD+ is switched on, which is
 * the "changed again".
 *
 * **Why it is worth doing at all.** IMD's detector is itself one of the things IMD exists to
 * hide, and a user who has switched IMD+ off has no reason left to be running an accessibility
 * service for it. Leaving it enabled would leave exactly the kind of trace the app is for
 * removing — visible to anything that enumerates accessibility services, for a feature that is
 * no longer on.
 */
class RetireAutoHideServiceUseCase @Inject constructor(
    private val accessibilityServicesWrapper: AccessibilityServicesWrapper,
    private val userDataRepository: UserDataRepository,
    @param:Dispatcher(GetoDispatchers.Default) private val defaultDispatcher: CoroutineDispatcher,
) {
    /**
     * True when the detector is off afterwards, or when there was nothing to do.
     *
     * Never throws, for the reason its two neighbours do not: this runs from a switch the user
     * has just moved, and an exception would leave the preference written and the service still
     * on with nothing to say so.
     */
    suspend operator fun invoke(): Boolean = withContext(defaultDispatcher) {
        withContext(NonCancellable) {
            runCatching { retire() }.getOrDefault(false)
        }
    }

    private suspend fun retire(): Boolean {
        val held = userDataRepository.userData.first().heldAccessibilityServices

        // Dropped whether or not the write below succeeds, and first. The hold means "a revert
        // owes this service back"; with IMD+ off no revert will pay it, and a hold nobody
        // settles is what would have RestoreAutoHideServiceUseCase switch the detector on again
        // at the end of some unrelated revert weeks later.
        if (AccessibilityServicePlan.AUTO_HIDE_HOLD in held) {
            userDataRepository.updateHeldAccessibilityServices(
                held = held - AccessibilityServicePlan.AUTO_HIDE_HOLD,
            )
        }

        val component = accessibilityServicesWrapper.autoHideServiceComponent()

        val currentlyEnabled = runCatching {
            accessibilityServicesWrapper.getEnabledAccessibilityServices()
        }.getOrNull() ?: return false

        // Already off — the ordinary case for anyone who never switched IMD+ on.
        if (component !in currentlyEnabled) return true

        return runCatching {
            accessibilityServicesWrapper.setEnabledAccessibilityServices(
                AccessibilityServicePlan.disable(
                    unwanted = listOf(component),
                    currentlyEnabled = currentlyEnabled,
                ),
            )
        }.getOrDefault(false)
    }
}
