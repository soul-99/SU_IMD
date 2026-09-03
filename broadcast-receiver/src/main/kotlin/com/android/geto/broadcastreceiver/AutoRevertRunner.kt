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
import com.android.geto.common.showRestoredToast
import com.android.geto.domain.framework.PackageManagerWrapper
import com.android.geto.domain.model.UnhidingFramework
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
    private val settingsHiddenRunner: SettingsHiddenRunner,
    private val overlayRestoreRunner: OverlayRestoreRunner,
    private val notificationManagerWrapper: AndroidNotificationManagerWrapper,
    private val packageManagerWrapper: PackageManagerWrapper,
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

        when (settings.unhidingFramework) {
            UnhidingFramework.RevertToDefault -> revertToDefaultRunner()

            UnhidingFramework.Memory -> {
                revertAppSettingsUseCase(componentName = componentName)

                // ⚠ **For a notification left standing by a build before r3.** Nothing
                // posts under a component name's hash code any more, but an upgrading
                // install can still have one in its shade, offering to undo a device that
                // has just been put back. Cancelling an id nothing holds costs nothing.
                notificationManagerWrapper.cancel(componentName.hashCode())

                // ⚠ **And the one that is actually standing.** The line above was the whole
                // of this route's notification handling, and it names an id nothing has
                // posted under since r3 - so the live offer, under the fixed id every hide
                // shares, was left in the shade over a restored device. The RevertToDefault
                // branch never had this gap: RevertToDefaultRunner sweeps for itself.
                settingsHiddenRunner.clearRevertOfferIfSettled()

                if (!overlayRestoreRunner.reportIfFailed()) {
                    context.showRestoredToast(
                        fromMemory = true,
                        appName = packageManagerWrapper.getActivityLabel(
                            componentName = componentName,
                        ),
                    )
                }
            }
        }
    }
}
