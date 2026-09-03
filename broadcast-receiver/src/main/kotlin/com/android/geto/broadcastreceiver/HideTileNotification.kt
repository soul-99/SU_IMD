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
import com.android.geto.common.SettingsObservationGate
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.ACTION_DISMISS_NOTIFICATION
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.HIDE_TILE_NOTIFICATION_ID
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.NOTIFICATION_EXTRA_NOTIFICATION_ID
import com.android.geto.framework.notificationmanager.R

/**
 * What a "Hide settings" tile press says when Shizuku was needed for Display over other apps
 * and would not come up.
 *
 * **It exists because a failed press stopped collapsing the shade.** This used to be shown as a
 * dialog in the window that the collapse opened; the author asked for the shade to stay open
 * through the work and to stay open on a failure, so that window is now only launched after a
 * press that got somewhere — and a press that did not has nowhere left to draw. The shade it
 * deliberately left open is where the answer goes instead.
 *
 * **Alert channel, banner, auto-cancel**, matching every other failure this app reports: it is
 * about something that did not happen, and a warning nobody sees is not a warning.
 *
 * Tapping opens the settings manager, the same place the three Shizuku notifications point at —
 * Shizuku's own row there shows whether the service is really down and offers to start it.
 *
 * ⚠ **The words are passed in rather than read here.** They are the ones the dialog showed, and
 * those strings live in `feature/apps`, which this module cannot see. Passing them from the
 * `app` module — which sees both — keeps one copy of each sentence in one language file, rather
 * than a second copy here that could be corrected in only one place.
 *
 * ⚠ **"Nothing ticked to hide" deliberately does not come through here.** On the author's
 * instruction that outcome keeps the behaviour it always had: the shade collapses and
 * `HideActivity` shows the dialog. It is not a failure — nothing went wrong, there was simply
 * nothing set up to do.
 */
fun buildHideTileOverlayFailedNotification(
    context: Context,
    title: String,
    text: String,
): Notification {
    val managerIntent = Intent()
        .setClassName(context, SettingsObservationGate.SERVICES_ACTIVITY_CLASS_NAME)
        .setFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)

    val dismissIntent = Intent(context, NotificationDismissBroadcastReceiver::class.java).apply {
        action = ACTION_DISMISS_NOTIFICATION

        putExtra(NOTIFICATION_EXTRA_NOTIFICATION_ID, HIDE_TILE_NOTIFICATION_ID)
    }

    val dismissPendingIntent = PendingIntent.getBroadcast(
        context,
        HIDE_TILE_NOTIFICATION_ID,
        dismissIntent,
        FLAG_UPDATE_CURRENT or FLAG_IMMUTABLE,
    )

    val managerPendingIntent = PendingIntent.getActivity(
        context,
        HIDE_TILE_NOTIFICATION_ID,
        managerIntent,
        FLAG_UPDATE_CURRENT or FLAG_IMMUTABLE,
    )

    return NotificationCompat.Builder(
        context,
        AndroidNotificationManagerWrapper.ALERT_NOTIFICATION_CHANNEL_ID,
    ).apply {
        setSmallIcon(R.drawable.ic_failure_notification_small)
        setContentTitle(title)
        setContentText(text)

        // The text is the whole point and is longer than one collapsed line, so it must not be
        // truncated to the first few words.
        setStyle(NotificationCompat.BigTextStyle().bigText(text))

        setContentIntent(managerPendingIntent)

        // Nothing is lost by clearing it: this reports a press that changed nothing, and the
        // tile beside it still reads the state the device is actually in.
        setAutoCancel(true)
        setOngoing(false)

        // PRIORITY_HIGH is what produces the banner below API 26; the channel's importance does
        // it from 26 up. Both, because the app still supports API 24.
        setPriority(NotificationCompat.PRIORITY_HIGH)
        setCategory(NotificationCompat.CATEGORY_STATUS)
        setDefaults(NotificationCompat.DEFAULT_ALL)
        addAction(
            R.drawable.ic_failure_notification_small,
            context.getString(R.string.notification_ok),
            dismissPendingIntent,
        )
    }.build()
}
