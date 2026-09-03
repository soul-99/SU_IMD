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

import com.android.geto.domain.common.Diagnostics
import com.android.geto.domain.repository.UserDataRepository
import javax.inject.Inject

/**
 * Forget every outstanding revert, and take the device as it stands now.
 *
 * ⚠ **This writes nothing to the device and undoes nothing.** It is the *record* that is
 * discarded, not the hide: developer options that are off stay off, and afterwards nothing in
 * IMD knows they were ever on. The only way to a known state from here is `Revert to default`.
 *
 * ⚠ **Permanent, on the author's explicit confirmation.** It is what the popup's
 * `'Ignore all previous reverts'` button does, and the label was written to say so — an earlier
 * draft called it just `'Ignore'`, which read as "carry on" rather than "throw the record away".
 * Keeping a shadow copy to undo it later was considered and rejected: nothing in the UI could
 * reach such a copy, so it would be a second record that only ever disagreed with the first.
 *
 * **Five stores, and all five matter.** The per-app records and the device-wide record are the
 * memory function's debt; the accessibility and overlay holds are what IMD is holding down on
 * somebody's behalf; `autoHideRunning` is IMD+'s claim on the device. Leaving any of them would
 * leave `settingsHidden` reading true, which is the flag the popup's own trigger reads — so a
 * partial discard would show the popup again on the very next launch.
 */
class DiscardPendingRevertsUseCase @Inject constructor(
    private val userDataRepository: UserDataRepository,
) {
    suspend operator fun invoke() {
        Diagnostics.log(tag = "revert", message = "discarding every pending revert")

        userDataRepository.updateSettingStateBefore(states = emptyMap())

        userDataRepository.updateHeldAccessibilityServices(held = emptyMap())

        userDataRepository.updateHeldOverlayPackages(held = emptyMap(), identities = emptyMap())

        userDataRepository.updateSettingsHiddenDeviceWide(hidden = false)

        userDataRepository.updateAutoHideRunning(running = false)
    }
}
