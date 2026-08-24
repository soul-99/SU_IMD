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
import com.android.geto.domain.model.RevertDefaults
import com.android.geto.domain.repository.UserDataRepository
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withContext
import javax.inject.Inject

/**
 * Resets the revert configuration to the narrowed v1.6.6 default, once.
 *
 * Until v1.6.6 the default switched USB debugging, the Shizuku service and the accessibility
 * services back on. Three of those are debugging surfaces, and a Revert can be fired from a
 * Quick Settings tile or a notification with nothing on screen — so an install carrying that
 * default forward could re-open a device at a moment its owner was not watching, in a way
 * they never chose and would have no reason to check.
 *
 * Overriding a stored configuration is not a small thing, and this one does it whether or
 * not the user edited it, because the risk is in the outcome rather than in how the outcome
 * was arrived at. Two things soften that: it is a state anyone can see and change in one
 * screen, and it is not done silently — [UserDataRepository.updateRevertDefaultsNoticePending]
 * leaves a notice for the next time there is a screen to show it on.
 *
 * A marker rather than a version comparison, matching MigrateNotificationFunctionUseCase: a
 * user who reconfigures afterwards and then updates again keeps their own answer.
 *
 * The notice is only queued for an install that has been through setup. A first run already
 * starts on the new default, and telling somebody their configuration was reset before they
 * have made one would be confusing rather than transparent.
 */
class MigrateRevertDefaultsUseCase @Inject constructor(
    private val userDataRepository: UserDataRepository,
    @param:Dispatcher(GetoDispatchers.Default) private val defaultDispatcher: CoroutineDispatcher,
) {
    suspend operator fun invoke() = withContext(defaultDispatcher) {
        val userData = userDataRepository.userData.first()

        if (userData.revertDefaultsResetV166) return@withContext

        // Written first, and whether or not anything else changes, so a process that dies
        // part way through does not reset the configuration a second time.
        userDataRepository.updateRevertDefaultsResetV166(done = true)

        val alreadyNarrow = userData.revertDefaults == RevertDefaults.Default

        userDataRepository.updateRevertDefaults(states = RevertDefaults.Default)

        // setupNoticeVersion is zero until somebody finishes setup, which is the closest
        // thing to "this install existed before today" that the app stores.
        val upgrading = userData.setupNoticeVersion != 0

        if (upgrading && !alreadyNarrow) {
            userDataRepository.updateRevertDefaultsNoticePending(pending = true)
        }
    }
}
