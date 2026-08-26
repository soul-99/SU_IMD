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
import com.android.geto.domain.model.memoryHeldComponents
import com.android.geto.domain.repository.UserDataRepository
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withContext
import javax.inject.Inject

/**
 * Reverts every app the memory function is still holding something for, in one call.
 *
 * The stateless "revert using memory" the automation intent needs. The per-app notification
 * reverts one named app, but a macro fired long after the launch - with IMD not even running -
 * has no notification to press and no app in mind, so this sweeps the lot: it asks which
 * components still have a memory record and hands each to [RevertAppSettingsUseCase], the same
 * revert the notification button runs.
 *
 * Only the memory records, never the device-wide one. A "Settings to hide" launch or a manager
 * toggle records its holds under the device-wide marker, and those are the province of
 * "Revert to default" - see [memoryHeldComponents], which leaves that marker out.
 *
 * Each revert re-reads the stored data, so the components are gathered once up front rather
 * than from a moving snapshot; the set cannot grow while this runs, because nothing here
 * launches an app.
 */
class RevertAllMemoryUseCase @Inject constructor(
    private val userDataRepository: UserDataRepository,
    private val revertAppSettingsUseCase: RevertAppSettingsUseCase,
    @param:Dispatcher(GetoDispatchers.Default) private val defaultDispatcher: CoroutineDispatcher,
) {
    suspend operator fun invoke() = withContext(defaultDispatcher) {
        // Not cancellable for the same reason the individual revert is not: this is fired from
        // a broadcast whose process can be reclaimed the moment onReceive returns, and a
        // half-reverted app is the one outcome worth avoiding.
        withContext(NonCancellable) {
            val userData = userDataRepository.userData.first()

            val components = memoryHeldComponents(
                settingStateBefore = userData.settingStateBefore,
                heldAccessibilityServices = userData.heldAccessibilityServices,
            )

            components.forEach { componentName ->
                revertAppSettingsUseCase(componentName = componentName)
            }
        }
    }
}
