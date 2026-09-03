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

import com.android.geto.domain.model.memoryHoldsSettings
import com.android.geto.domain.repository.UserDataRepository
import kotlinx.coroutines.flow.first
import javax.inject.Inject

/**
 * What is hiding settings right now, split by which revert would undo it.
 *
 * Kept apart rather than collapsed to one boolean because a device can owe both at once — the
 * tile hides device-wide whichever mechanism is chosen, so pressing it and then launching an
 * app under the memory function leaves one debt of each kind, and each needs its own revert.
 */
data class SettingsHiddenState(
    /** The device-wide "Settings to hide" is applied. Undone by a revert to default. */
    val deviceWide: Boolean,
    /** At least one app's settings are still held by the memory function. */
    val memory: Boolean,
) {
    val hidden: Boolean get() = deviceWide || memory
}

/**
 * Reads whether IMD is currently hiding anything.
 *
 * A use case rather than a repository read at the call site, so the two callers that are not
 * in the app module — the tile's runner among them — do not have to reach past the domain for
 * it. Which half is which is decided in one place, and both halves come from one snapshot, so
 * they cannot describe two different moments.
 */
class GetSettingsHiddenUseCase @Inject constructor(
    private val userDataRepository: UserDataRepository,
) {
    suspend operator fun invoke(): SettingsHiddenState {
        val userData = userDataRepository.userData.first()

        return SettingsHiddenState(
            deviceWide = userData.settingsHiddenDeviceWide,
            memory = userData.memoryHoldsSettings,
        )
    }
}
