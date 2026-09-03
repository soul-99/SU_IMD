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
import com.android.geto.domain.model.SettingsToHide
import com.android.geto.domain.model.UserData
import com.android.geto.domain.repository.UserDataRepository
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withContext
import javax.inject.Inject

/**
 * The one-shot fixups for the two default configurations - what a Revert restores, and what a
 * launch hides. One class because they are two halves of one decision, and because a single
 * owner per preference is what keeps two writers from racing for the same field.
 *
 * Each half has its own marker and runs independently of the other.
 *
 * ## What a Revert restores - the v1.6.6 narrowing
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
 *
 * ## What a launch hides - the v2.1 default
 *
 * v2.1 changes what a fresh install starts with from "the four secure settings" to "nothing":
 * an install nobody has configured should not be switching debugging settings off on somebody's
 * device before they have read what those rows are. That is right for a first run and wrong for
 * everybody else - an install that has been launching apps successfully for weeks would suddenly
 * hide nothing, and the app it was launching would start refusing to run for no visible reason.
 *
 * So the old default is not simply dropped. An install that predates this version and never
 * opened the dialog has been behaving as [SettingsToHide.LegacyDefault], and that map is written
 * as its stored answer - the same configuration it already had, now recorded rather than implied,
 * and editable in the same one screen it always was.
 *
 * Three states, and only the first is touched: upgrading and never configured, where the old
 * default is written down and nothing changes; upgrading and configured, where the stored answer
 * is already there and is left alone; and a first run, which starts on the new default with
 * nothing hidden, which is the point.
 */
class MigrateRevertDefaultsUseCase @Inject constructor(
    private val userDataRepository: UserDataRepository,
    @param:Dispatcher(GetoDispatchers.Default) private val defaultDispatcher: CoroutineDispatcher,
) {
    suspend operator fun invoke() = withContext(defaultDispatcher) {
        // One snapshot for both halves. They read different fields and write different
        // fields, so neither can see stale state the other left behind.
        val userData = userDataRepository.userData.first()

        migrateRevertDefaults(userData = userData)

        migrateSettingsToHide(userData = userData)
    }

    private suspend fun migrateRevertDefaults(userData: UserData) {
        if (userData.revertDefaultsResetV166) return

        // Written first, and whether or not anything else changes, so a process that dies
        // part way through does not reset the configuration a second time.
        userDataRepository.updateRevertDefaultsResetV166(done = true)

        // setupNoticeVersion is zero until somebody finishes setup, which is the closest
        // thing to "this install existed before today" that the app stores.
        val upgrading = userData.setupNoticeVersion != 0

        // A first run has nothing to reset. It starts on RevertDefaults.Default - nothing
        // restored until the user says what - and writing the v1.6.6 map over that would
        // hand a brand-new install a configuration it never chose, which is the exact thing
        // this class exists to prevent.
        if (!upgrading) return

        // Never configured reads as the current default, which is no longer the v1.6.6 map -
        // so ask whether it was ever saved rather than comparing the decoded map, or an
        // install that had made no choice at all would be told its choice had been changed.
        val alreadyNarrow = !userData.revertDefaultsConfigured ||
            userData.revertDefaults == RevertDefaults.NarrowedV166

        userDataRepository.updateRevertDefaults(states = RevertDefaults.NarrowedV166)

        if (!alreadyNarrow) {
            userDataRepository.updateRevertDefaultsNoticePending(pending = true)
        }
    }

    private suspend fun migrateSettingsToHide(userData: UserData) {
        if (userData.settingsToHideDefaultsV21) return

        // Written first, and whether or not anything else changes, so a process that dies
        // part way through cannot run this a second time against a configuration the user
        // has since edited.
        userDataRepository.updateSettingsToHideDefaultsV21(done = true)

        // A first run has nothing to preserve and must be left on the new default.
        if (userData.setupNoticeVersion == 0) return

        // Already has an answer of its own. Overwriting it would be this migration deciding
        // something the user already decided.
        if (userData.settingsToHideConfigured) return

        userDataRepository.updateSettingsToHide(states = SettingsToHide.LegacyDefault)
    }
}
