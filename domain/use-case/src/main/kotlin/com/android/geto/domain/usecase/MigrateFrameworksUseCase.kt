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
import com.android.geto.domain.model.hidingFrameworkFor
import com.android.geto.domain.model.unhidingFrameworkFor
import com.android.geto.domain.repository.UserDataRepository
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withContext
import javax.inject.Inject

/**
 * Splits the pre-v3 "hiding-unhiding mechanism" into the Hiding framework and the Unhiding
 * framework, once per install.
 *
 * The old preference answered two questions with one switch, and it only ever offered the two
 * combinations where both answers agreed. So the migration is a straight pair-off:
 *
 * | stored `NotificationFunction` | becomes |
 * | --- | --- |
 * | `NotificationFunction.RevertToDefault` | `HidingFramework.ImdDefaults` + `UnhidingFramework.RevertToDefault` |
 * | `NotificationFunction.Memory` | `HidingFramework.PerApp` + `UnhidingFramework.Memory` |
 *
 * ⚠ **An upgrading install therefore never lands in one of the two new combinations.** Both of
 * those have to be chosen deliberately, which is the point: they are the ones no released
 * version has run.
 *
 * ⚠ **A fresh install is not this use case's business.** It has nothing stored to read, and
 * the mapper already answers an unset field with `HidingFramework.Default` and
 * `UnhidingFramework.Default` — which are *not* the pairing above. A new install gets
 * `HidingFramework.ImdDefaults` with `UnhidingFramework.Memory`, at the author's instruction,
 * because a revert to configured defaults can switch **on** a setting the user never had on
 * before the hide.
 *
 * ⚠ **The pairing itself lives in `:domain:model`** as `hidingFrameworkFor` and
 * `unhidingFrameworkFor`, because that is the only module the host runner compiles — and a
 * migration that pairs off wrongly is invisible until somebody's device is already on the
 * wrong framework.
 *
 * The marker is written whether or not anything changed, exactly like
 * [MigrateNotificationFunctionUseCase] — someone who migrates, then deliberately picks a
 * different pair, must not have that undone by the next launch. Runs once per install rather
 * than once per version, for the same reason.
 */
class MigrateFrameworksUseCase @Inject constructor(
    private val userDataRepository: UserDataRepository,
    @param:Dispatcher(GetoDispatchers.Default) private val defaultDispatcher: CoroutineDispatcher,
) {
    suspend operator fun invoke() = withContext(defaultDispatcher) {
        val userData = userDataRepository.userData.first()

        if (userData.frameworksMigratedV3) return@withContext

        userDataRepository.updateFrameworksMigratedV3(done = true)

        // ⚠ **The guard the KDoc above always described and the code never had.** Without it
        // this ran on a fresh install too, read a `notificationFunction` nobody had written -
        // which decodes to NotificationFunction.Default, RevertToDefault - and wrote the pair,
        // overriding UnhidingFramework.Default. A new install therefore landed on Revert to
        // default rather than the memory function, and the nested "Restore wireless debugging
        // also" checkbox, drawn only under the memory function, was never shown at all.
        //
        // setupNoticeVersion is the app's only record that an install existed before today, and
        // is what MigrateRevertDefaultsUseCase already asks for the same reason. Its
        // imprecision is inherited rather than introduced: an install never carried through
        // setup reads as fresh, which errs the safe way - nothing configured, nothing to
        // carry forward.
        val upgraded = userData.setupNoticeVersion != 0

        // Recorded because this is the last moment the two can be told apart: once setup has
        // been completed, a fresh install and an upgrade look identical. The developer's note
        // reads it.
        userDataRepository.updateUpgradedToV3(upgraded = upgraded)

        // ⚠ **Before the return below, because a fresh install needs the `false` too.** The
        // Favourites tab now opens on Grid until something has chosen, and an install that
        // existed before v3 has chosen - by using the tab at all - even though field 8 cannot
        // say so. Setting it to `upgraded` keeps an upgrader's list and leaves a new install
        // on the grid.
        userDataRepository.updateFavouriteAppsViewSet(set = upgraded)

        // The Favourites tab's other default, and the same argument: an install that existed
        // before v3 has an order it was already showing, and field 7 cannot say whether it
        // was chosen.
        userDataRepository.updateSortFavouriteAppsSet(set = upgraded)

        if (!upgraded) return@withContext

        // Read once, up front. The two writes below land separately and a reader could
        // otherwise see the old value for one half and the new for the other.
        val stored = userData.notificationFunction

        userDataRepository.updateHidingFramework(
            hidingFramework = hidingFrameworkFor(notificationFunction = stored),
        )

        userDataRepository.updateUnhidingFramework(
            unhidingFramework = unhidingFrameworkFor(notificationFunction = stored),
        )
    }
}
