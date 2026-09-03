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
import com.android.geto.domain.model.SettingsToHide
import com.android.geto.domain.repository.UserDataRepository
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withContext
import javax.inject.Inject

/**
 * Writes down what an existing install has been hiding, once, before the default changes
 * underneath it.
 *
 * v2.1 changes what a fresh install starts with from "the four secure settings" to
 * "nothing": an install nobody has configured should not be switching debugging settings off
 * on somebody's device before they have read what those rows are. That is right for a first
 * run and wrong for everybody else — an install that has been launching apps successfully
 * for weeks would suddenly hide nothing, and the app it was launching would start refusing
 * to run for no visible reason.
 *
 * So the old default is not simply dropped. An install that predates this version and never
 * opened the dialog has been behaving as [SettingsToHide.LegacyDefault], and that map is
 * written as its stored answer here — the same configuration it already had, now recorded
 * rather than implied, and editable in the same one screen it always was.
 *
 * Three states, and only the first is touched:
 *
 * * **Upgrading, never configured** — the old default is written down. Nothing changes.
 * * **Upgrading, configured** — the stored answer is already there and is left alone.
 * * **First run** — starts on the new default with nothing hidden, which is the point.
 *
 * A marker rather than a version comparison, matching the migrations either side of it: a
 * user who reconfigures afterwards and then updates again keeps their own answer.
 *
 * This is the only thing that writes `settingsToHide` outside the dialog, so the field has
 * exactly one migrating owner and no two writers can race for it.
 */
class MigrateSettingsToHideUseCase @Inject constructor(
    private val userDataRepository: UserDataRepository,
    @param:Dispatcher(GetoDispatchers.Default) private val defaultDispatcher: CoroutineDispatcher,
) {
    suspend operator fun invoke() = withContext(defaultDispatcher) {
        val userData = userDataRepository.userData.first()

        if (userData.settingsToHideDefaultsV21) return@withContext

        // Written first, and whether or not anything else changes, so a process that dies
        // part way through cannot run this a second time against a configuration the user
        // has since edited.
        userDataRepository.updateSettingsToHideDefaultsV21(done = true)

        // setupNoticeVersion is zero until somebody finishes setup, which is the closest
        // thing to "this install existed before today" that the app stores. A first run has
        // nothing to preserve and must be left on the new default.
        val upgrading = userData.setupNoticeVersion != 0

        if (!upgrading) return@withContext

        // Already has an answer of its own. Overwriting it would be this migration deciding
        // something the user already decided.
        if (userData.settingsToHideConfigured) return@withContext

        userDataRepository.updateSettingsToHide(states = SettingsToHide.LegacyDefault)
    }
}
