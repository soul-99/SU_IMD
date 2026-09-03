/*
 *
 *   Copyright 2026 soul_99 (suIMD)
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
import com.android.geto.domain.repository.UserDataRepository
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.first
import javax.inject.Inject
import javax.inject.Singleton

/**
 * The alerting notification a Shevery start raises when the forty seconds run out.
 *
 * The author's instruction for the services manager: *"display a popup alerting notification
 * 'Failed to start Shevery, please click here to start it manually.' on clicking it will open
 * the current shevery/shizuku app."*
 *
 * ⚠ **Its own class rather than a method on the ViewModel**, because the ViewModel lives in
 * `feature/apps` and the notification wrapper does not reach it. The same shape
 * [RevertOfferNotification] has, and for the same reason: a question that needs the
 * notification manager, asked from a module that only has the runner.
 *
 * ⚠ **Posted under the id its Thedjchi sibling uses.** A Shevery start that failed and a
 * Shizuku restart that failed are the same news about the same row, and the author's rule in
 * spec item 5 is that only one of them stands at a time. The Display-over-other-apps
 * restore-failure notification keeps its own id and is deliberately never touched — his
 * decision this round, because that one carries a Try again the user may still need.
 */
@Singleton
class SheveryStartFailureNotification @Inject constructor(
    @param:ApplicationContext private val context: Context,
    private val userDataRepository: UserDataRepository,
    private val notificationManagerWrapper: AndroidNotificationManagerWrapper,
) {
    suspend fun warnStartFailed() {
        notificationManagerWrapper.notify(
            id = AndroidNotificationManagerWrapper.SHIZUKU_FALLBACK_NOTIFICATION_ID,
            notification = buildSheveryStartFailedNotification(
                context = context,
                shizukuPackage = userDataRepository.userData.first().shizukuPackageName,
            ),
        )
    }
}
