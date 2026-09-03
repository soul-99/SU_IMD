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
 * Puts IMD's own accessibility service — the IMD+ detector — back on.
 *
 * Run at the end of "Revert to default", and at the end of the last of the pending per-app
 * reverts under the memory function. Those are the two moments at which nothing IMD hid is
 * still hidden, and therefore the two moments at which the detector may listen again.
 *
 * **It switches the service on, rather than only releasing a hold.** Releasing is what puts a
 * *user's* service back, and it is right for those: IMD only ever owes back what it took. The
 * detector is IMD's own, and while IMD+ is switched on the user has already said they want it
 * running — so a revert that found no hold recorded, because the record was lost or because
 * something outside this app switched the service off, should still leave IMD+ working rather
 * than quietly deaf until somebody opens the settings screen and notices.
 *
 * With IMD+ off it does the ordinary thing and only releases, so a device that never asked for
 * IMD+ never has an accessibility service switched on for it.
 */
class RestoreAutoHideServiceUseCase @Inject constructor(
    private val accessibilityServicesWrapper: AccessibilityServicesWrapper,
    private val userDataRepository: UserDataRepository,
    @param:Dispatcher(GetoDispatchers.Default) private val defaultDispatcher: CoroutineDispatcher,
) {
    /**
     * True when the detector is on afterwards, or when there was nothing to do.
     *
     * Never throws: this is the last step of a revert that has already changed the device, and
     * an exception here would be a revert reported as failed over the one part of it the user
     * cannot see.
     */
    suspend operator fun invoke(): Boolean = withContext(defaultDispatcher) {
        withContext(NonCancellable) {
            runCatching { restore() }.getOrDefault(false)
        }
    }

    private suspend fun restore(): Boolean {
        val userData = userDataRepository.userData.first()

        val held = userData.heldAccessibilityServices

        val owed = held[AccessibilityServicePlan.AUTO_HIDE_HOLD].orEmpty()

        // Nothing owed and IMD+ is off: there is no reason for this app to switch an
        // accessibility service on, so it does not.
        if (owed.isEmpty() && !userData.autoHideEnabled) return true

        val component = accessibilityServicesWrapper.autoHideServiceComponent()

        val currentlyEnabled = runCatching {
            accessibilityServicesWrapper.getEnabledAccessibilityServices()
        }.getOrNull() ?: return false

        // The component this build actually has, plus whatever the hold recorded - which on a
        // renamed or re-flavoured build could be a different string, and is worth putting back
        // either way rather than stranding it in the record forever.
        val wanted = if (userData.autoHideEnabled) owed + component else owed

        val enabledAfter = AccessibilityServicePlan.enable(
            wanted = wanted,
            currentlyEnabled = currentlyEnabled,
        )

        val written = if (enabledAfter.size == currentlyEnabled.size) {
            // Already on. Nothing to write, and writing anyway would touch the system setting
            // for no reason at the end of every single revert.
            true
        } else {
            runCatching {
                accessibilityServicesWrapper.setEnabledAccessibilityServices(enabledAfter)
            }.getOrDefault(false)
        }

        // The record is dropped only once the service is actually back, so a failed write
        // leaves the debt standing for the next revert to settle.
        if (written && AccessibilityServicePlan.AUTO_HIDE_HOLD in held) {
            userDataRepository.updateHeldAccessibilityServices(
                held = held - AccessibilityServicePlan.AUTO_HIDE_HOLD,
            )
        }

        return written
    }
}
