/*
 *
 *   Copyright 2026 soul_99 (suIMD)
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
import com.android.geto.domain.repository.UserDataRepository
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withContext
import javax.inject.Inject

/**
 * The one-shot v3 reset of auto unhide: every trigger and both conditions unticked, once.
 *
 * The author's instruction, when asked whether the screen-lock trigger should arrive ticked and
 * what that would cost: *"do one thing for everyone untick all triggers and all conditions"*.
 *
 * v3 couples the tile condition to the screen-lock trigger, and an install arriving from below
 * carries whatever combination it was left on — including the two conditions, which used to
 * arrive **on** by default and are the half most people never opened. Starting everyone from
 * nothing is one state rather than a matrix of inherited ones, and it is what the developer
 * note this version shows asks people to go and look at.
 *
 * ⚠ **Auto unhide switches itself off as a consequence, and nothing here does that.**
 * `autoUnhideSwitchOn` is `autoUnhideEnabled && requirements.satisfied`, and `satisfied` needs
 * a trigger and a condition — so with neither there is nothing to write. The stored answer is
 * left exactly as the user set it, which is what lets ticking one trigger bring the feature
 * back without asking them to find the master switch again.
 *
 * ⚠ **The marker is written first, and whether or not anything changed** — the rule every other
 * one-shot in this app follows. A process that dies part way through must not reset a second
 * time, and somebody who re-ticks a trigger afterwards must not have it undone by the next
 * launch. Once per install, not once per version.
 */
class MigrateAutoUnhideUseCase @Inject constructor(
    private val userDataRepository: UserDataRepository,
    @param:Dispatcher(GetoDispatchers.Default) private val defaultDispatcher: CoroutineDispatcher,
) {
    suspend operator fun invoke() = withContext(defaultDispatcher) {
        val userData = userDataRepository.userData.first()

        if (userData.autoUnhideResetV3) return@withContext

        userDataRepository.updateAutoUnhideResetV3(done = true)

        userDataRepository.updateAutoUnhideTriggers(
            onSwipe = false,
            onScreenLock = false,
            onIdle = false,
        )

        // ⚠ **Written through the repository, not through the ViewModel.** The page refuses to
        // clear the last condition — a rule about what a user may do to a working
        // configuration, which is exactly right there and exactly wrong here.
        userDataRepository.updateAutoUnhideUsedFor(onAppLaunch = false, onTile = false)
    }
}
