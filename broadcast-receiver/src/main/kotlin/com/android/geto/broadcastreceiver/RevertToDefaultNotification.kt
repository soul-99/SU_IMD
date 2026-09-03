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
import androidx.core.content.ContextCompat
import androidx.core.graphics.drawable.toBitmap
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.ACTION_REPOST_REVERT_NOTIFICATION
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.ACTION_REVERT_TO_DEFAULT
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.NOTIFICATION_EXTRA_NOTIFICATION_ID
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.REVERT_TO_DEFAULT_NOTIFICATION_ID
import com.android.geto.framework.notificationmanager.R

/**
 * How big the launched-app icon on the per-app notification comes out, so the revert icon
 * beside it in the shade is the same size rather than noticeably smaller or blurrier.
 */
private const val LARGE_ICON_PIXELS = 192

/**
 * The notification posted after a hide — every hide, since r3.
 *
 * ⚠ **Deliberately says nothing about which app was launched, and that is now the author's
 * rule for every route rather than for one mode.** He was offered the launched app's icon on
 * the first notification of a chain and chose the opposite: *"no need to send app icon
 * notifications and make it easy and uniform, IMD send only generic revert notifications from
 * now"*. The revert icon is there instead, and it is the same drawing as the tile and the
 * shortcut, so all three routes to the same action look like the same action.
 *
 * Its button is the framework-following unhide rather than the named `Revert to default`
 * function — see `RevertToDefaultBroadcastReceiver` — so one notification is honest under all
 * four framework combinations: it puts back what the hide did, whatever the hide did.
 *
 * Posted under [REVERT_TO_DEFAULT_NOTIFICATION_ID], which is what makes the "one notification
 * only" rule work: launching a second app replaces this notification rather than adding
 * another.
 *
 * **One line, and the whole notification is the button.** It had a Revert action beside a
 * title and a body, which is three things to read and two places to press for one outcome.
 * The text now says what has happened and what a tap does, and the tap does it.
 *
 * **It comes back if it is swiped away.** `setOngoing` stops that up to Android 13; from 14
 * an ongoing notification can be dismissed like any other, and losing this one leaves a
 * device with developer options switched off and nothing on screen to undo it. The delete
 * intent puts it back — and fires only on a dismissal by a person, so a finished revert
 * cancelling it is final.
 */
fun buildRevertToDefaultNotification(context: Context): Notification {
    // Through the trampoline, like the per-app notification: it cancels this one immediately
    // and collapses the shade, then hands the revert to the receiver that still runs it. The
    // notification id is carried so the trampoline knows which to cancel.
    val revertIntent = Intent(context, RevertTrampolineActivity::class.java).apply {
        action = ACTION_REVERT_TO_DEFAULT
        putExtra(NOTIFICATION_EXTRA_NOTIFICATION_ID, REVERT_TO_DEFAULT_NOTIFICATION_ID)
    }

    val revertPendingIntent = PendingIntent.getActivity(
        context,
        REVERT_TO_DEFAULT_NOTIFICATION_ID,
        revertIntent,
        FLAG_UPDATE_CURRENT or FLAG_IMMUTABLE,
    )

    // Fires only when a person removes the notification, never when this app cancels it.
    val repostIntent = Intent(context, NotificationRepostBroadcastReceiver::class.java).apply {
        action = ACTION_REPOST_REVERT_NOTIFICATION
        putExtra(NOTIFICATION_EXTRA_NOTIFICATION_ID, REVERT_TO_DEFAULT_NOTIFICATION_ID)
    }

    val repostPendingIntent = PendingIntent.getBroadcast(
        context,
        REVERT_TO_DEFAULT_NOTIFICATION_ID,
        repostIntent,
        FLAG_UPDATE_CURRENT or FLAG_IMMUTABLE,
    )

    val revertText = context.getString(R.string.hidden_revert_default)

    return NotificationCompat.Builder(
        context,
        AndroidNotificationManagerWrapper.REVERT_TO_DEFAULT_CHANNEL_ID,
    ).apply {
        setSmallIcon(R.drawable.ic_revert_notification_small)

        // The colour artwork is a vector, and setLargeIcon wants a bitmap. Rasterised at a
        // fixed size rather than the drawable's intrinsic one so it does not come out at
        // 108px on a screen expecting far more.
        ContextCompat.getDrawable(context, R.drawable.ic_revert_notification_large)
            ?.toBitmap(width = LARGE_ICON_PIXELS, height = LARGE_ICON_PIXELS)
            ?.let(::setLargeIcon)

        // The title alone, with no body: a notification with one line of text is one line
        // tall, and this has exactly one thing to say.
        // The whole sentence, and all of it visible: as a title it was one line tall and
        // ellipsised on a narrow screen, which cut off the half that says what a tap does.
        // As body text with a big-text style behind it, the shade shows the line in full
        // whenever the notification is expanded - and Android expands the top one by
        // default. No content title, so the expanded view does not print the same sentence
        // twice; the header already carries the app's name and icon.
        setContentText(revertText)
        setStyle(NotificationCompat.BigTextStyle().bigText(revertText))
        setPriority(NotificationCompat.PRIORITY_DEFAULT)
        setOngoing(true)
        setAutoCancel(false)
        setContentIntent(revertPendingIntent)
        setDeleteIntent(repostPendingIntent)
    }.build()
}
