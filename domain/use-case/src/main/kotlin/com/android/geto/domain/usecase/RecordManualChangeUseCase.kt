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

import com.android.geto.domain.model.AccessibilityServicePlan
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.manualChangeRecord
import com.android.geto.domain.model.settingsHidden
import com.android.geto.domain.repository.UserDataRepository
import kotlinx.coroutines.flow.first
import javax.inject.Inject

/**
 * Records what a settings manager row was set to, just before a person changes it by hand.
 *
 * The author's rule: *moving any toggle adds to the total revert debt only if a pending
 * revert already exists in the background.* With nothing outstanding, a manual change is the
 * user managing their own device and nothing should undo it later. With a revert pending, the
 * dialog says in red that changes made here will be undone by it — and this is what makes
 * that sentence true rather than merely printed.
 *
 * ⚠ **Called before the write, never after.** The value being recorded is the one the row is
 * about to stop having.
 *
 * ⚠ **The three keyed targets only.** Accessibility services and Display over other apps
 * already record a hold on every switch-off, and that hold is written before the shell
 * command for crash safety as well as being the debt; Shizuku has no stored "before" value at
 * all. [manualChangeRecord] returns null for all three, so this is a no-op for them.
 */
class RecordManualChangeUseCase @Inject constructor(
    private val userDataRepository: UserDataRepository,
) {
    suspend operator fun invoke(target: ManualRevertTarget, currentlyEnabled: Boolean) {
        val userData = userDataRepository.userData.first()

        // The same pair the dialog draws its red line from, and deliberately the same pair:
        // the line promises the revert will undo this, so the test that records it has to be
        // the test that decided to make the promise.
        val revertPending = userData.autoHideRunning || userData.settingsHidden

        val record = manualChangeRecord(
            settingStateBefore = userData.settingStateBefore,
            target = target,
            currentlyEnabled = currentlyEnabled,
            revertPending = revertPending,
        ) ?: return

        userDataRepository.updateSettingStateBefore(
            states = userData.settingStateBefore +
                (AccessibilityServicePlan.DEVICE_WIDE_HOLD to record),
        )
    }
}
