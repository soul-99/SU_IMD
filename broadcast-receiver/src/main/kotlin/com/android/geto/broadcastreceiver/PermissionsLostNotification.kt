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

import android.app.Notification
import android.app.PendingIntent
import android.app.PendingIntent.FLAG_IMMUTABLE
import android.app.PendingIntent.FLAG_UPDATE_CURRENT
import android.content.Context
import android.content.Intent
import androidx.core.app.NotificationCompat
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.ACTION_DISMISS_NOTIFICATION
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.NOTIFICATION_EXTRA_NOTIFICATION_ID
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.PERMISSIONS_LOST_NOTIFICATION_ID
import com.android.geto.common.R as commonR
import com.android.geto.framework.notificationmanager.R as notificationR

/**
 * `WRITE_SECURE_SETTINGS` has gone, said to somebody who is not looking at a screen of IMD's.
 *
 * **The one route with no window of its own.** Every other way to hide settings ends somewhere a
 * dialog can be drawn — the tile collapses the shade into one, a launch and a pinned shortcut
 * each have their own transparent window, IMD+ draws over the app it just opened. An automation
 * intent has none: it arrives from Tasker with the screen showing whatever the user was doing,
 * or nothing at all, and the toast that used to fire here said "Settings hidden" whether or not
 * anything had been.
 *
 * **Alert channel, banner, sound**, on the author's rule that a failure is reported by an
 * alerting notification wherever there is no popup to show. This one earns it more than most:
 * an automation that silently stops hiding settings is an automation the user goes on trusting.
 *
 * Tapping it opens IMD, which is exactly what the message asks for. By launch intent rather than
 * by class name because that is the entry the launcher uses, so it lands on the front page — and
 * the setup gate there catches a missing grant on its own and shows what to run.
 */
fun buildPermissionsLostNotification(context: Context): Notification {
    val openIntent = context.packageManager
        .getLaunchIntentForPackage(context.packageName)
        ?.apply { addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP) }

    val openPendingIntent = openIntent?.let {
        PendingIntent.getActivity(
            context,
            PERMISSIONS_LOST_NOTIFICATION_ID,
            it,
            FLAG_UPDATE_CURRENT or FLAG_IMMUTABLE,
        )
    }

    val dismissIntent = Intent(context, NotificationDismissBroadcastReceiver::class.java).apply {
        action = ACTION_DISMISS_NOTIFICATION

        putExtra(NOTIFICATION_EXTRA_NOTIFICATION_ID, PERMISSIONS_LOST_NOTIFICATION_ID)
    }

    val dismissPendingIntent = PendingIntent.getBroadcast(
        context,
        PERMISSIONS_LOST_NOTIFICATION_ID,
        dismissIntent,
        FLAG_UPDATE_CURRENT or FLAG_IMMUTABLE,
    )

    // The same sentence every dialog shows, from the one module all of them can see.
    val text = context.getString(commonR.string.permissions_lost)

    return NotificationCompat.Builder(
        context,
        AndroidNotificationManagerWrapper.ALERT_NOTIFICATION_CHANNEL_ID,
    ).apply {
        setSmallIcon(notificationR.drawable.ic_failure_notification_small)
        setContentTitle(context.getString(notificationR.string.alert_notification_channel))
        setContentText(text)

        // Longer than one collapsed line, and every word of it is the instruction.
        setStyle(NotificationCompat.BigTextStyle().bigText(text))

        openPendingIntent?.let { setContentIntent(it) }

        setAutoCancel(true)
        setOngoing(false)

        // PRIORITY_HIGH is what produces the banner below API 26; the channel's importance does
        // it from 26 up. Both, because the app still supports API 24.
        setPriority(NotificationCompat.PRIORITY_HIGH)
        setCategory(NotificationCompat.CATEGORY_ERROR)
        setDefaults(NotificationCompat.DEFAULT_ALL)
        addAction(
            notificationR.drawable.ic_failure_notification_small,
            context.getString(notificationR.string.notification_ok),
            dismissPendingIntent,
        )
    }.build()
}
