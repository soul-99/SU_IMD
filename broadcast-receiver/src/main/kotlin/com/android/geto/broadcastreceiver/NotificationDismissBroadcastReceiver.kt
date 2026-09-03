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

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import androidx.core.app.NotificationManagerCompat
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.NOTIFICATION_EXTRA_NOTIFICATION_ID

/**
 * Clears the notification that sent it, and nothing else.
 *
 * The one receiver in this app that changes no device state, holds no dependencies and reads
 * nothing but the id it was handed — which is why it is a plain receiver with no Hilt entry
 * point and no `goAsync`: cancelling a notification is immediate and cannot fail in a way
 * worth reporting.
 *
 * Not exported, and reached only through this app's own PendingIntent. Even if it were
 * reached from elsewhere the worst available outcome is one of this app's own notifications
 * being dismissed.
 */
class NotificationDismissBroadcastReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val notificationId = intent.getIntExtra(NOTIFICATION_EXTRA_NOTIFICATION_ID, -1)

        if (notificationId == -1) return

        NotificationManagerCompat.from(context).cancel(notificationId)
    }
}
