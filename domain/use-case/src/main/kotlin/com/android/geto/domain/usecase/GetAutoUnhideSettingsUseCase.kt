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

import com.android.geto.domain.model.UnhidingFramework
import com.android.geto.domain.repository.UserDataRepository
import kotlinx.coroutines.flow.first
import javax.inject.Inject

/**
 * Everything the session watcher needs to decide whether a session has ended, in one read.
 *
 * One use case rather than six reads, for the reason [GetAutoRevertSettingsUseCase] gives:
 * they have to come from the same snapshot, or the watcher can act on a trigger the user
 * unticked between two of them. It is also the seam that lets the broadcast-receiver module
 * ask without depending on the repository.
 *
 * The intervals arrive in **milliseconds** rather than the minutes they are stored as. The
 * conversion belongs here rather than at the two comparison sites: doing it twice is how one
 * of them ends up comparing minutes against `elapsedRealtime`, and that mistake reads as the
 * backup simply never firing.
 */
class GetAutoUnhideSettingsUseCase @Inject constructor(
    private val userDataRepository: UserDataRepository,
) {
    data class Settings(
        val enabled: Boolean,
        val onSwipe: Boolean,
        val onScreenLock: Boolean,
        val onIdle: Boolean,
        val screenLockMillis: Long,
        val idleMillis: Long,
        val onAppLaunch: Boolean,
        val onTile: Boolean,
        val unhidingFramework: UnhidingFramework,
    ) {
        /**
         * Whether anything at all would end a session.
         *
         * The watcher checks this before it starts rather than only before it acts: a
         * foreground service and its notification, running for a feature that has no trigger
         * ticked, is a battery cost and a shade entry in exchange for nothing.
         */
        val anyTrigger: Boolean get() = onSwipe || onScreenLock || onIdle
    }

    suspend operator fun invoke(): Settings {
        val userData = userDataRepository.userData.first()

        return Settings(
            enabled = userData.autoUnhideEnabled,
            onSwipe = userData.autoUnhideOnSwipe,
            onScreenLock = userData.autoUnhideOnScreenLock,
            onIdle = userData.autoUnhideOnIdle,
            screenLockMillis = userData.autoUnhideScreenLockMinutes * MILLIS_PER_MINUTE,
            idleMillis = userData.autoUnhideIdleMinutes * MILLIS_PER_MINUTE,
            onAppLaunch = userData.autoUnhideOnAppLaunch,
            onTile = userData.autoUnhideOnTile,
            unhidingFramework = userData.unhidingFramework,
        )
    }
}

/** Long rather than Int, so the multiplication above does not overflow at 36 days. */
private const val MILLIS_PER_MINUTE = 60_000L
