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
import com.android.geto.domain.framework.ShizukuWrapper
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.withContext
import javax.inject.Inject

/**
 * Asks Shizuku for its permission, showing its prompt.
 *
 * The loud half of the pair [GetAutoHideServiceStateUseCase] deliberately does not use. IMD+'s
 * settings page reports the requirement silently on every draw and only asks when the user
 * presses the row, which is the difference between a page that reports a state and a page that
 * interrupts every time it is opened.
 *
 * False when Shizuku is not there to ask, or the user refused — neither of which is worth
 * throwing over: both mean the same thing to the row that called, and the row is on screen.
 */
class RequestShizukuPermissionUseCase @Inject constructor(
    private val shizukuWrapper: ShizukuWrapper,
    @param:Dispatcher(GetoDispatchers.Default) private val defaultDispatcher: CoroutineDispatcher,
) {
    suspend operator fun invoke(): Boolean = withContext(defaultDispatcher) {
        runCatching { shizukuWrapper.requestShizukuPermission() }.getOrDefault(false)
    }
}
