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
import com.android.geto.domain.repository.UserDataRepository
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withContext
import javax.inject.Inject

/**
 * Keeps IMD+'s own detector in `managedAccessibilityServices` for exactly as long as IMD+ is on.
 *
 * ## The bug this closes
 *
 * The author reported the settings manager's Accessibility row **greyed and unmovable** while the
 * picker plainly showed one thing ticked — IMD+'s own detector. Both were telling the truth. The
 * picker draws that row ticked and unclickable by itself while IMD+ is on (see
 * `accessibilityServicesForPicker`), but the tick was decoration: nothing was ever written, so
 * `managedAccessibilityServices` stayed empty, and the manager greys the row on
 * `accessibilityManaged`, which is that list being non-empty. A tick and a dead switch.
 *
 * The author's decision was to *"store it for real"* and to keep it un-untickable, which is what
 * this does. Once it is an ordinary entry every reader downstream works with no further change:
 * the greying, the row's own on/off reading, and the hold and release the switch performs.
 *
 * ## Why it is a sync rather than two writes at the switch
 *
 * ⚠ **An install that already had IMD+ on has an empty list and no event coming.** A hook on the
 * IMD+ switch alone reaches every future change and none of the existing ones — the author's own
 * device among them, which is where the report came from. So this is written to be **idempotent
 * and safe to call at any time**: it compares what is stored against what IMD+ is doing and writes
 * only when they disagree. `GetoApplication` calls it once at start behind
 * [UserData.autoHideDetectorManagedV3] for installs that predate the change, and the IMD+ switch
 * calls it on every flip.
 *
 * ⚠ **It never writes when nothing has changed**, which matters more than it looks: this store is
 * a `Flow` the settings screen and the manager both collect, and a write on every start would
 * re-emit user data to every collector for no reason.
 *
 * ## What it deliberately does not touch
 *
 * ⚠ **Only the selection.** It does not enable the detector, does not disable it, and does not go
 * near `heldAccessibilityServices`. Switching IMD+ off already retires the detector through
 * `RetireAutoHideServiceUseCase`, and a hide already takes it down through
 * `DisableAutoHideServiceUseCase` and records it under its own holder — none of which this
 * changes. All that moves is whether the user's managed list names it.
 *
 * ⚠ **The protection that stops a hide leaving IMD+ blind is unaffected**, and that is worth
 * saying plainly because making the detector an ordinary selection puts it in reach of
 * `AccessibilityServicePlan.enable(wanted = …)` in `SetManualTargetUseCase`. That call is what the
 * manager's Accessibility switch uses on the way *on*, and it is already gated: the same branch
 * only reaches `restoreAutoHideServiceUseCase` when `!userData.settingsHidden`, and a hide holds
 * the detector under `AUTO_HIDE_HOLD`, which `releaseAll` is explicitly told to leave alone. The
 * switch going on during a hide therefore re-enables the user's own services and still cannot hand
 * IMD+ its eyes back early.
 */
class SyncAutoHideDetectorSelectionUseCase @Inject constructor(
    private val userDataRepository: UserDataRepository,
    private val accessibilityServicesWrapper: AccessibilityServicesWrapper,
    @param:Dispatcher(GetoDispatchers.Default) private val defaultDispatcher: CoroutineDispatcher,
) {
    /**
     * True when the stored selection already matched, or was made to match.
     *
     * Never throws. The component lookup goes through the framework and this is called from
     * application start and from a preference write, neither of which has anywhere to report a
     * failure that would be worth reporting.
     */
    suspend operator fun invoke(): Boolean = withContext(defaultDispatcher) {
        runCatching { sync() }.getOrDefault(false)
    }

    private suspend fun sync(): Boolean {
        val component = accessibilityServicesWrapper.autoHideServiceComponent()

        // Nothing to add or remove without a component to name. A blank answer is the framework
        // failing to resolve this app's own service, which is not a state worth writing about.
        if (component.isBlank()) return false

        val userData = userDataRepository.userData.first()

        val managed = userData.managedAccessibilityServices

        val present = component in managed

        // The two agreeing is the common case by a long way - every start after the first.
        if (present == userData.autoHideEnabled) return true

        val updated = if (userData.autoHideEnabled) {
            // Appended rather than inserted at the front: the picker sorts what it draws, and the
            // stored order is the order the user built. Adding at the end changes nothing they
            // can see and keeps the list stable for everything that reads it as a set.
            managed + component
        } else {
            managed - component
        }

        userDataRepository.updateManagedAccessibilityServices(components = updated)

        return true
    }
}
