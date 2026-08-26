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

/** The two things the exported receiver has to check before it acts: is it on, and the key. */
data class TaskerAuthState(
    val enabled: Boolean,
    val authKey: String,
)

/**
 * Reads the Tasker integration's gate - never generates it.
 *
 * A read, deliberately: the exported receiver must not be able to create the key or flip the
 * switch. Only the settings screen does either, by a user who has decided to turn the
 * integration on. A receiver that generated a key on first contact would let the very first
 * unauthorised broadcast mint the secret it was supposed to be checked against.
 */
class GetTaskerAuthKeyUseCase @Inject constructor(
    private val userDataRepository: UserDataRepository,
) {
    suspend operator fun invoke(): TaskerAuthState {
        val userData = userDataRepository.userData.first()

        return TaskerAuthState(
            enabled = userData.taskerIntegrationEnabled,
            authKey = userData.taskerAuthKey,
        )
    }
}
