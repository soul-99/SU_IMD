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

import android.app.Notification
import android.app.PendingIntent
import android.app.PendingIntent.FLAG_IMMUTABLE
import android.app.PendingIntent.FLAG_UPDATE_CURRENT
import android.content.Context
import android.content.Intent
import androidx.core.app.NotificationCompat
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.ACTION_REPOST_REVERT_NOTIFICATION
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.AUTO_UNHIDE_NOTIFICATION_ID
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.NOTIFICATION_EXTRA_NOTIFICATION_ID
import com.android.geto.framework.notificationmanager.R

/**
 * The auto unhide watcher's foreground-service notification.
 *
 * Silent, minimum priority and collapsed — as close to out of the way as Android allows. It
 * cannot be hidden altogether: a foreground service must show one, and a channel at
 * `IMPORTANCE_MIN` is raised to `LOW` when a service posts to it. The floor is: no sound, no
 * vibration, no badge, no heads-up, sorted to the bottom.
 *
 * **Here rather than in the service that posts it**, because the repost receiver has to be able
 * to rebuild it after a swipe and lives in this module — the same reason every other notification
 * this app can repost is built by a top-level function beside its neighbours.
 *
 * Nothing to press: this says the watcher is alive and nothing else, and the revert notification
 * beside it is still the way back by hand.
 */
fun buildAutoUnhideNotification(context: Context): Notification {
    // Fires only when a person removes the notification, never when this app cancels it — so a
    // watcher that settles and takes its own notification down does not trigger a repost.
    val repostIntent = Intent(context, NotificationRepostBroadcastReceiver::class.java).apply {
        action = ACTION_REPOST_REVERT_NOTIFICATION

        putExtra(NOTIFICATION_EXTRA_NOTIFICATION_ID, AUTO_UNHIDE_NOTIFICATION_ID)
    }

    val repostPendingIntent = PendingIntent.getBroadcast(
        context,
        AUTO_UNHIDE_NOTIFICATION_ID,
        repostIntent,
        FLAG_UPDATE_CURRENT or FLAG_IMMUTABLE,
    )

    return NotificationCompat.Builder(
        context,
        AndroidNotificationManagerWrapper.AUTO_UNHIDE_CHANNEL_ID,
    )
        .setSmallIcon(R.drawable.ic_revert_notification_small)
        .setContentTitle(context.getString(R.string.auto_unhide_running))
        .setPriority(NotificationCompat.PRIORITY_MIN)
        // Android 12 holds a foreground service's notification back for ten seconds so that
        // short-lived services do not flash one up. That deferral is what made this appear
        // seconds after the revert notification it belongs beside, so it is opted out of.
        .setForegroundServiceBehavior(NotificationCompat.FOREGROUND_SERVICE_IMMEDIATE)
        .setSilent(true)
        .setShowWhen(false)
        .setOngoing(true)
        .setDeleteIntent(repostPendingIntent)
        .build()
}
