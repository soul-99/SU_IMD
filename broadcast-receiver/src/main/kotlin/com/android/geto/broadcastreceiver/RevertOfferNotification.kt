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

import com.android.geto.domain.usecase.GetSettingsHiddenUseCase
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper
import javax.inject.Inject
import javax.inject.Singleton

/**
 * The offer to undo a hide, and the one question worth asking before taking it down.
 *
 * ⚠ **One notification serves every hide since r3**, under
 * [AndroidNotificationManagerWrapper.REVERT_TO_DEFAULT_NOTIFICATION_ID]. Before that each app
 * had its own, keyed on its component name's hash - and five revert routes were still
 * cancelling that hash, which nothing has posted under since. They restored the device and
 * left the offer standing over it. The author reported it twice, from auto unhide and from
 * IMD+.
 *
 * ⚠ **A class of its own rather than a method on [SettingsHiddenRunner], and the reason is a
 * dependency cycle the sandbox cannot see.** That runner already injects [AutoHideRunner], so
 * IMD+'s own revert - the fifth route, and the one that returns early before the sweep - could
 * not have asked it without Hilt refusing to build the graph. Nothing here depends on either
 * runner, so everything can reach it.
 *
 * ⚠ **Conditional, and it has to stay that way.** One shared notification means cancelling it
 * while a second app is still hidden would take away that app's only way back from the shade.
 * The records are asked rather than the revert that just ran, because a memory sweep and a
 * single profile revert both end here and only the records know whether anything is left.
 *
 * `cancelAll` rather than the one id: an install upgrading from before r3 can still have
 * per-app notifications keyed on hashes this cannot compute, and they describe a device that
 * no longer exists either. A foreground service's own notification survives it, which is what
 * keeps the auto unhide watcher's own notification out of this.
 */
@Singleton
class RevertOfferNotification @Inject constructor(
    private val getSettingsHiddenUseCase: GetSettingsHiddenUseCase,
    private val notificationManagerWrapper: AndroidNotificationManagerWrapper,
) {
    /** Returns whether it cleared, so a caller that also wants to settle can reuse the answer. */
    suspend fun clearIfSettled(): Boolean {
        val hidden = getSettingsHiddenUseCase()

        if (hidden.deviceWide || hidden.memory) return false

        notificationManagerWrapper.cancelAll()

        return true
    }
}
