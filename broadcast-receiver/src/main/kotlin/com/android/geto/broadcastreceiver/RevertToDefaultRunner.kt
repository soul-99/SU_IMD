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
package com.android.geto.broadcastreceiver

import android.content.Context
import android.content.Intent
import com.android.geto.common.SettingsObservationGate
import com.android.geto.common.showRevertToDefaultToast
import com.android.geto.domain.model.RevertToDefaultResult
import com.android.geto.domain.usecase.RevertToDefaultUseCase
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

/**
 * The one way "Revert to default" is actually run.
 *
 * Five things can trigger it — a Quick Settings tile, a notification button, a launcher
 * shortcut, a button on the Favourites tab and a button in the settings manager — and every
 * one of them has to announce itself and clear the shade as well as doing the work. Three
 * copies of that in three modules is how the per-app notification's request-code bug got
 * written three times; this is the same lesson applied earlier.
 */
@Singleton
class RevertToDefaultRunner @Inject constructor(
    @param:ApplicationContext private val context: Context,
    private val revertToDefaultUseCase: RevertToDefaultUseCase,
    private val notificationManagerWrapper: AndroidNotificationManagerWrapper,
) {
    suspend operator fun invoke(): RevertToDefaultResult {
        // Said before the work rather than after it. Reverting takes a couple of seconds —
        // longer when Shizuku has to wait for adbd — and silence for that long from a tile
        // press reads as nothing having happened.
        context.showRevertToDefaultToast()

        // Every per-app Revert button now describes a device that no longer exists, and
        // pressing one would write remembered values back over the defaults just applied.
        // The observer service's own notification survives this: the system keeps a
        // foreground service's notification up regardless.
        SettingsObservationGate.pause()

        return try {
            notificationManagerWrapper.cancelAll()

            revertToDefaultUseCase()
        } finally {
            SettingsObservationGate.resume()

            // If the optional observer service is running, reset its foreground
            // notification after suppressing IMD's own burst of settings writes. An
            // explicit start to an already-running service only delivers this command.
            if (SettingsObservationGate.isRunning) {
                context.startService(
                    Intent()
                        .setClassName(context, SettingsObservationGate.SERVICE_CLASS_NAME)
                        .setAction(SettingsObservationGate.ACTION_RESET),
                )
            }
        }
    }
}
