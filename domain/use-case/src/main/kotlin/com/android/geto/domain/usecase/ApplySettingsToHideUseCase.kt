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
import com.android.geto.domain.model.AppSettingsResult
import com.android.geto.domain.model.SettingsToHide
import com.android.geto.domain.repository.UserDataRepository
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withContext
import javax.inject.Inject

/**
 * Switches off whatever the "Settings to hide" configuration names, for any app.
 *
 * The counterpart to [ApplyAppSettingsUseCase], which reads a profile written for one
 * specific app. This one reads a single device-wide configuration, so an app that has
 * never been configured can still be launched — which is the whole reason it exists.
 *
 * Returns an [AppSettingsResult] rather than a type of its own so it can be dropped into
 * the launch paths that already exist. Two of that type's cases cannot arise here and are
 * never returned: there is no per-app profile to be empty, and no per-app row to be
 * disabled. A configuration with nothing ticked is [AppSettingsResult.Success] with
 * nothing written, not a failure — the user has said they want nothing hidden, and
 * refusing to launch the app would be disobeying that rather than reporting a problem.
 */
class ApplySettingsToHideUseCase @Inject constructor(
    private val userDataRepository: UserDataRepository,
    private val getManualTargetStatesUseCase: GetManualTargetStatesUseCase,
    private val setManualTargetUseCase: SetManualTargetUseCase,
    @param:Dispatcher(GetoDispatchers.Default) private val defaultDispatcher: CoroutineDispatcher,
) {
    suspend operator fun invoke(): AppSettingsResult = withContext(defaultDispatcher) {
        // Half-hidden is the worst outcome available: the app still detects whatever is
        // left on and refuses to run, while the user's device has been changed anyway.
        // Launching an activity is exactly the sort of thing that tears this scope down.
        withContext(NonCancellable) { hide() }
    }

    private suspend fun hide(): AppSettingsResult {
        val wanted = userDataRepository.userData.first().settingsToHide

        val before = getManualTargetStatesUseCase()

        var failed = false

        for (target in SettingsToHide.HideOrder) {
            if (wanted[target] != true) continue

            // Already off. Writing it again is not harmless: for the accessibility
            // services target a second disable would record a fresh hold over services
            // that are already held, and nothing would ever discharge the duplicate.
            if (!before.isEnabled(target)) continue

            if (!setManualTargetUseCase(target = target, enabled = false)) failed = true
        }

        return if (failed) AppSettingsResult.Failure else AppSettingsResult.Success
    }
}
