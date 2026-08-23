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
import com.android.geto.domain.model.NotificationFunction
import com.android.geto.domain.repository.UserDataRepository
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withContext
import javax.inject.Inject

/**
 * Puts every install upgrading into v1.6 onto "Revert to default", once.
 *
 * v1.6 moves the app onto one device-wide "Settings to hide" configuration, and everything
 * that is not a notification's own Revert button now reads it. An install carrying the
 * memory function forward from an earlier version lands in the one combination that looks
 * broken from the outside: launching an app it has no profile for does nothing but say so,
 * while the tile and the shortcut revert against a configuration the user has never seen.
 *
 * Deliberately overrides a deliberate choice, which is not something to do lightly — it is
 * done here because the choice was made about a different app. The memory function of v1.5
 * and the memory function of v1.6 are not the same offer, and the picker now spells out
 * what it costs. Anyone who still wants it switches back and the flag below keeps that.
 *
 * Runs once per install rather than once per version: a marker, not a version number, so
 * switching back to the memory function and updating again does not undo the switch.
 */
class MigrateNotificationFunctionUseCase @Inject constructor(
    private val userDataRepository: UserDataRepository,
    @param:Dispatcher(GetoDispatchers.Default) private val defaultDispatcher: CoroutineDispatcher,
) {
    suspend operator fun invoke() = withContext(defaultDispatcher) {
        val userData = userDataRepository.userData.first()

        if (userData.notificationFunctionResetV16) return@withContext

        // The marker is written whether or not the function had to change, so an install
        // already on Revert to default is not asked again on every launch.
        userDataRepository.updateNotificationFunctionResetV16(done = true)

        if (userData.notificationFunction == NotificationFunction.RevertToDefault) {
            return@withContext
        }

        userDataRepository.updateNotificationFunction(
            notificationFunction = NotificationFunction.RevertToDefault,
        )
    }
}
