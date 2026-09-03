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
import com.android.geto.domain.framework.ShizukuWrapper
import com.android.geto.domain.model.AutoHideServiceState
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.withContext
import javax.inject.Inject

/**
 * The two live IMD+ requirements that have to be asked for rather than read from storage.
 *
 * Asks nothing of the user: [ShizukuWrapper.hasShizukuPermission] is the silent half of the
 * permission pair precisely so a settings page can report the requirement without Shizuku's
 * prompt appearing every time the page is drawn.
 *
 * Neither answer is ever cached beyond the screen that asked. A permission can be revoked and
 * an accessibility service switched off by somebody who is not this app — a system update, a
 * battery optimiser, the user in Android's own settings — and a stored copy would go on saying
 * IMD+ was working long after it had stopped.
 */
class GetAutoHideServiceStateUseCase @Inject constructor(
    private val accessibilityServicesWrapper: AccessibilityServicesWrapper,
    private val shizukuWrapper: ShizukuWrapper,
    @param:Dispatcher(GetoDispatchers.Default) private val defaultDispatcher: CoroutineDispatcher,
) {
    suspend operator fun invoke(): AutoHideServiceState = withContext(defaultDispatcher) {
        AutoHideServiceState(
            accessibilityRunning = runCatching {
                accessibilityServicesWrapper.isAutoHideServiceRunning()
            }.getOrDefault(false),
            shizukuPermission = runCatching {
                shizukuWrapper.hasShizukuPermission()
            }.getOrDefault(false),
            // Asked separately from the permission, because a Shizuku that is asleep answers
            // "no permission" to every question and the switch must not read that as a refusal.
            shizukuRunning = runCatching {
                shizukuWrapper.isShizukuRunning()
            }.getOrDefault(false),
            ownDetector = runCatching {
                accessibilityServicesWrapper.autoHideServiceComponent()
            }.getOrDefault(""),
        )
    }
}
