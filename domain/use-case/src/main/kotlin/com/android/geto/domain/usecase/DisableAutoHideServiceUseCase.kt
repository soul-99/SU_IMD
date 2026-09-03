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
import com.android.geto.domain.model.AccessibilityServicePlan
import com.android.geto.domain.repository.UserDataRepository
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withContext
import javax.inject.Inject

/**
 * Switches IMD's own detector off, and records that IMD owes it back.
 *
 * **Why a run does this at all.** IMD+ kills the watched app, hides the settings and opens the
 * app again — and that reopening is another app coming to the foreground, which is precisely
 * what the detector listens for. Left running it would detect its own relaunch and start over,
 * forever. So the run switches the detector off as soon as the kill has succeeded, before it
 * launches anything. That is a state rather than a timer: nothing depends on how long a kill or
 * a launch happens to take on a given device.
 *
 * The hold goes under [AccessibilityServicePlan.AUTO_HIDE_HOLD] rather than the device-wide
 * holder, because it is placed whether or not this hide touches accessibility services at all.
 * [AccessibilityServicePlan.releaseAll] flattens every holder, so "Revert to default" and the
 * manager's own accessibility switch bring the detector back with everything else — and a
 * per-app memory revert, which releases only its own holder, correctly leaves it off.
 *
 * The other accessibility services are switched off, or not, by the ordinary hide logic. This
 * touches one component and no others.
 */
class DisableAutoHideServiceUseCase @Inject constructor(
    private val accessibilityServicesWrapper: AccessibilityServicesWrapper,
    private val userDataRepository: UserDataRepository,
    @param:Dispatcher(GetoDispatchers.Default) private val defaultDispatcher: CoroutineDispatcher,
) {
    /**
     * True when the detector is off — including when it was already off, which is not a
     * failure but the ordinary state of a second run.
     *
     * Never throws. This sits between a kill and a launch inside a run that has already changed
     * the device, and an exception here would abandon the run half-done.
     */
    suspend operator fun invoke(): Boolean = withContext(defaultDispatcher) {
        withContext(NonCancellable) {
            runCatching { disable() }.getOrDefault(false)
        }
    }

    private suspend fun disable(): Boolean {
        val userData = userDataRepository.userData.first()

        // IMD+ is off, so its detector is off too and no hide has any business touching it.
        // Placing a hold here would record a debt nothing will pay: RestoreAutoHideServiceUseCase
        // only switches the detector back on while IMD+ is on, so the hold would sit in storage
        // until some later revert restored a service the user had deliberately switched off.
        if (!userData.autoHideEnabled) return true

        val component = accessibilityServicesWrapper.autoHideServiceComponent()

        val currentlyEnabled = runCatching {
            accessibilityServicesWrapper.getEnabledAccessibilityServices()
        }.getOrNull() ?: return false

        // Already off, and nothing owed. A second run finds it here and has nothing to do.
        if (component !in currentlyEnabled) return true

        val held = userData.heldAccessibilityServices

        // Persisted before the write, so process death between the two cannot leave the
        // detector switched off with no record capable of restoring it. The opposite order is
        // the one that loses a service permanently.
        userDataRepository.updateHeldAccessibilityServices(
            held = AccessibilityServicePlan.withHold(
                held = held,
                componentName = AccessibilityServicePlan.AUTO_HIDE_HOLD,
                services = listOf(component),
            ),
        )

        val written = runCatching {
            accessibilityServicesWrapper.setEnabledAccessibilityServices(
                AccessibilityServicePlan.disable(
                    unwanted = listOf(component),
                    currentlyEnabled = currentlyEnabled,
                ),
            )
        }.getOrDefault(false)

        // Nothing changed, so nothing is owed. Leaving the hold would have the next revert
        // "restore" a service that never went off.
        if (!written) userDataRepository.updateHeldAccessibilityServices(held = held)

        return written
    }
}
