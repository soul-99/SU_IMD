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

import com.android.geto.domain.model.NotificationFunction
import com.android.geto.domain.repository.UserDataRepository
import kotlinx.coroutines.flow.first
import javax.inject.Inject

/**
 * The two answers the auto revert needs before it can run: whether it is switched on at all,
 * and which of the two reverts to perform.
 *
 * One use case rather than two reads, so both come from the same snapshot - the alternative
 * is a window where the setting is read as on and the function is read after the user has
 * changed it. It is also the seam that lets the broadcast-receiver module ask without
 * depending on the repository, the same reason [GetOverlayRestoreFailedUseCase] exists.
 */
class GetAutoRevertSettingsUseCase @Inject constructor(
    private val userDataRepository: UserDataRepository,
) {
    data class Settings(
        val enabled: Boolean,
        val notificationFunction: NotificationFunction,
    )

    suspend operator fun invoke(): Settings {
        val userData = userDataRepository.userData.first()

        return Settings(
            enabled = userData.autoRevertOnReturn,
            notificationFunction = userData.notificationFunction,
        )
    }
}
