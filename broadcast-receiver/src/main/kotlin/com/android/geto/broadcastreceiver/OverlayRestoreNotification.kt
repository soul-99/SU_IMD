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
import com.android.geto.common.SettingsObservationGate
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.ACTION_RETRY_OVERLAY_RESTORE
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.OVERLAY_RESTORE_NOTIFICATION_ID
import com.android.geto.framework.notificationmanager.R

/**
 * Posted when a revert could not put overlay access back.
 *
 * This is the one failure in the app the user has to be told about out of band. Everything
 * else a failed revert leaves behind is visible in the services manager and reversible from
 * there; this one leaves other apps without a permission they had, with nothing on screen to
 * connect that to IMD, and it cannot be fixed until Shizuku is running again.
 *
 * The action retries the restore and nothing else. It deliberately does not try to start
 * Shizuku: this notification exists precisely because starting it automatically did not work,
 * and the text has just asked the user to start it by hand. Trying again on their behalf
 * would burn another ten seconds and fail the same way.
 *
 * A heads-up banner rather than a quiet line in the shade, on a channel of its own at
 * IMPORTANCE_HIGH. The device has been left changed in a way nothing on screen explains, and
 * a notification that only appears when the shade is pulled down is one the user finds out
 * about by accident, if at all.
 *
 * Ongoing, so it stays until a restore actually succeeds - the device is still changed until
 * then, and a prompt that disappeared on a tap or a stray swipe would be retiring a problem
 * that has not gone away. Tapping the body opens the **current Shizuku app** instead of
 * dismissing it - r4n, the author's instruction, and the same thing its sibling
 * [buildShizukuRevertFailedNotification] does: the text has just asked the user to start
 * Shizuku by hand, and the tap should put them where they can.
 *
 * [shizukuPackage] is the fork configured in IMD. If it is blank, or has no launcher entry -
 * uninstalled since it was configured, or a stealth build with no icon - the tap falls back to
 * IMD's own services manager, which can at least report the state and offer to start it.
 *
 * Nothing is lost even if it is cleared - by the system, or by the user swiping it away, which
 * Android 14 allows even on an ongoing notification. The held-packages debt is persisted and is
 * never cleared by a failure, so **Revert to default** still puts overlay access back
 * afterwards, from the manager or the tile or the ongoing revert notification.
 */
fun buildOverlayRestoreFailedNotification(
    context: Context,
    shizukuPackage: String,
): Notification {
    val retryIntent = Intent(context, OverlayRestoreRetryBroadcastReceiver::class.java).apply {
        action = ACTION_RETRY_OVERLAY_RESTORE
    }

    val retryPendingIntent = PendingIntent.getBroadcast(
        context,
        OVERLAY_RESTORE_NOTIFICATION_ID,
        retryIntent,
        FLAG_UPDATE_CURRENT or FLAG_IMMUTABLE,
    )

    // ⚠ **The Shizuku app, not the services manager - r4n.** The text tells the user to
    // start Shizuku by hand and this is where they do it. The restore itself stays on the
    // Try again button, which is still in the shade because the tap does not clear it - and
    // which remains the only way back through the UI when overlay management is switched
    // off, since the overlay row is not drawn at all then.
    //
    // The fallback is the services manager, for a package that is blank or has no launcher
    // entry: uninstalled since it was configured, or a stealth build with no icon. NEW_TASK
    // because the shade is not an activity context, CLEAR_TOP so a manager already open is
    // reused rather than stacked behind itself.
    val launchIntent = shizukuPackage
        .takeIf { it.isNotBlank() }
        ?.let { context.packageManager.getLaunchIntentForPackage(it) }
        ?.apply { addFlags(Intent.FLAG_ACTIVITY_NEW_TASK) }
        ?: Intent()
            .setClassName(context, SettingsObservationGate.SERVICES_ACTIVITY_CLASS_NAME)
            .setFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)

    val launchPendingIntent = PendingIntent.getActivity(
        context,
        OVERLAY_RESTORE_NOTIFICATION_ID,
        launchIntent,
        FLAG_UPDATE_CURRENT or FLAG_IMMUTABLE,
    )

    return NotificationCompat.Builder(
        context,
        AndroidNotificationManagerWrapper.ALERT_NOTIFICATION_CHANNEL_ID,
    ).apply {
        setSmallIcon(R.drawable.ic_failure_notification_small)
        setContentTitle(context.getString(R.string.overlay_restore_failed_title))
        setContentText(context.getString(R.string.overlay_restore_failed_text))

        // The text is two lines of instruction and the whole point is that it can be read
        // and acted on, so it must not be truncated to one collapsed line.
        setStyle(
            NotificationCompat.BigTextStyle()
                .bigText(context.getString(R.string.overlay_restore_failed_text)),
        )
        // PRIORITY_HIGH is what produces the banner below API 26; the channel's importance
        // is what does it from 26 up. Both are set because the app still supports API 24.
        setContentIntent(launchPendingIntent)

        // Stays up, and survives the tap. Overlay access is still withdrawn from apps that
        // had it until a restore actually succeeds, so a prompt that vanished on the first
        // tap - or on an accidental swipe - would be reporting a device state that is still
        // true. It is cleared by the restore succeeding and by nothing else.
        setAutoCancel(false)
        setOngoing(true)

        setPriority(NotificationCompat.PRIORITY_HIGH)
        setCategory(NotificationCompat.CATEGORY_ERROR)
        setDefaults(NotificationCompat.DEFAULT_ALL)
        addAction(
            R.drawable.ic_failure_notification_small,
            context.getString(R.string.overlay_restore_retry),
            retryPendingIntent,
        )
    }.build()
}
