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
import com.android.geto.common.AutoRevertPending
import com.android.geto.common.showAutoRevertFromMemoryToast
import com.android.geto.common.showRevertOverlayFailedToast
import com.android.geto.domain.model.NotificationFunction
import com.android.geto.domain.usecase.GetAutoRevertSettingsUseCase
import com.android.geto.domain.usecase.RevertAppSettingsUseCase
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Puts the device back when the user comes home to IMD.
 *
 * Runs whichever revert the notification function is set to, because those two are not
 * interchangeable: "Revert to default" drives the whole device to a configured state, while
 * the memory function puts back only what one app's profile changed, and reverting the wrong
 * one leaves the user somewhere they did not ask to be.
 *
 * Nothing here decides *whether* to revert - [AutoRevertPending] answers that, and it only
 * says yes for a launch made from inside IMD that actually applied something and has since
 * left the app. A shortcut launch never arms it, which is why auto revert does not apply to
 * shortcuts.
 */
@Singleton
class AutoRevertRunner @Inject constructor(
    @param:ApplicationContext private val context: Context,
    private val getAutoRevertSettingsUseCase: GetAutoRevertSettingsUseCase,
    private val revertAppSettingsUseCase: RevertAppSettingsUseCase,
    private val revertToDefaultRunner: RevertToDefaultRunner,
    private val overlayRestoreRunner: OverlayRestoreRunner,
    private val notificationManagerWrapper: AndroidNotificationManagerWrapper,
) {
    /**
     * Reverts if there is anything pending and the setting is on. Safe to call on every
     * return to the app, which is exactly how it is called.
     */
    suspend operator fun invoke() {
        val settings = getAutoRevertSettingsUseCase()

        if (!settings.enabled) {
            // Switched off since the launch. Drop the marker rather than leave it armed for
            // whenever it is switched back on.
            AutoRevertPending.clear()

            return
        }

        val componentName = AutoRevertPending.consume() ?: return

        when (settings.notificationFunction) {
            NotificationFunction.RevertToDefault -> revertToDefaultRunner(auto = true)

            NotificationFunction.Memory -> {
                revertAppSettingsUseCase(componentName = componentName)

                // The per-app notification is posted under the component name's hash code,
                // and it now offers to undo a device that has already been put back.
                notificationManagerWrapper.cancel(componentName.hashCode())

                if (overlayRestoreRunner.reportIfFailed()) {
                    context.showRevertOverlayFailedToast()
                } else {
                    context.showAutoRevertFromMemoryToast()
                }
            }
        }
    }
}
