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
import com.android.geto.domain.framework.ShizukuFallbackNotifier
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.SHIZUKU_FALLBACK_NOTIFICATION_ID
import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Raises the "Shizuku was killed through USB debugging" warning as a notification.
 *
 * Lives here rather than in the domain because it is a notification; the use case that calls
 * it knows only [ShizukuFallbackNotifier]. A notification rather than a dialog because the
 * moment it happens is the middle of a launch, with an app about to come to the front — there
 * is often no screen of this app's left to put a dialog on.
 */
internal class DefaultShizukuFallbackNotifier @Inject constructor(
    @param:ApplicationContext private val context: Context,
    private val notificationManagerWrapper: AndroidNotificationManagerWrapper,
) : ShizukuFallbackNotifier {

    override suspend fun warnKilledViaUsbDebugging(overlayHidden: Boolean) {
        // Posting under the fixed id replaces any copy already showing, so several launches
        // that all fall back leave one warning rather than a stack of identical ones. The
        // wrapper drops it silently when notifications are switched off, which is the same
        // rule every other notification in the app follows.
        notificationManagerWrapper.notify(
            id = SHIZUKU_FALLBACK_NOTIFICATION_ID,
            notification = buildShizukuFallbackNotification(
                context = context,
                overlayHidden = overlayHidden,
            ),
        )
    }
}

@Module
@InstallIn(SingletonComponent::class)
internal interface ShizukuFallbackNotifierModule {

    @Binds
    @Singleton
    fun shizukuFallbackNotifier(impl: DefaultShizukuFallbackNotifier): ShizukuFallbackNotifier
}
