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

import com.android.geto.domain.repository.UserDataRepository
import kotlinx.coroutines.flow.first
import javax.inject.Inject

/**
 * Whether overlay access is still owed after a failed attempt to give it back.
 *
 * One line, and it exists only so the broadcast-receiver module can ask the question without
 * depending on the repository directly. Reaching across that boundary is what made Hilt fail
 * to resolve `UserDataRepository` the first time; a use case is the seam that module already
 * has.
 *
 * "Revert to default" does not need this - its own result carries the answer. The per-app
 * revert does, because it reports one enum for the whole profile and the overlay step is
 * deliberately not allowed to fail the rest of it.
 */
class GetOverlayRestoreFailedUseCase @Inject constructor(
    private val userDataRepository: UserDataRepository,
) {
    suspend operator fun invoke(): Boolean =
        userDataRepository.userData.first().overlayRestoreFailed
}
