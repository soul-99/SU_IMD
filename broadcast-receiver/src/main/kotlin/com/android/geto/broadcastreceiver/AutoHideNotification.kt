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
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.ACTION_AUTO_HIDE_REVERT
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.ACTION_REPOST_REVERT_NOTIFICATION
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.AUTO_HIDE_NOTIFICATION_ID
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.NOTIFICATION_EXTRA_COMPONENT_NAME
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.NOTIFICATION_EXTRA_NOTIFICATION_ID
import com.android.geto.framework.notificationmanager.R

/** Matches the revert notification's icon, so the two never look like different sizes. */
private const val LARGE_ICON_PIXELS = 192

/**
 * The notification an Auto-hide settings (IMD+) run leaves behind.
 *
 * The only way back, and the only thing on screen saying anything happened: an IMD+ run starts
 * from tapping an app icon, not from opening IMD, so the user may never have looked at this app
 * today. It says the settings are hidden and that a tap puts them back, and the tap does that —
 * one line, one target, the same shape as the revert-to-default notification for the same
 * reasons.
 *
 * Its button is [ACTION_AUTO_HIDE_REVERT] rather than the plain revert-to-default one, because
 * only IMD+ knows which of the two mechanisms hid these settings and therefore which revert
 * puts them back.
 *
 * **[componentName] is what says which.** Null means the device-wide "Settings to hide" list
 * was applied and a revert-to-default undoes it. Non-null means the memory function was in
 * force and this is the app whose own page was applied, so the revert is that app's record and
 * nothing else — and the text says so, because "click to revert" and "click to revert from
 * memory" undo genuinely different things.
 *
 * Carrying the name here rather than storing it is deliberate. It has to survive process
 * death, and it does: the system holds the PendingIntent. A stored field would be a second
 * copy of the same fact, free to disagree with this one.
 *
 * **It comes back if it is swiped away.** `setOngoing` stops that up to Android 13; from 14 an
 * ongoing notification can be dismissed like any other, and losing this one leaves a device
 * with settings hidden by something the user never opened and nothing on screen to undo it.
 */
fun buildAutoHideNotification(context: Context, componentName: String? = null): Notification {
    // Through the same trampoline as the other reverts: tapping a notification does not close
    // the shade, and only starting an activity does. It cancels this notification, collapses
    // the shade and hands the work to the receiver.
    val revertIntent = Intent(context, RevertTrampolineActivity::class.java).apply {
        action = ACTION_AUTO_HIDE_REVERT
        putExtra(NOTIFICATION_EXTRA_NOTIFICATION_ID, AUTO_HIDE_NOTIFICATION_ID)
        putExtra(NOTIFICATION_EXTRA_COMPONENT_NAME, componentName)
    }

    val revertPendingIntent = PendingIntent.getActivity(
        context,
        AUTO_HIDE_NOTIFICATION_ID,
        revertIntent,
        FLAG_UPDATE_CURRENT or FLAG_IMMUTABLE,
    )

    // Fires only when a person removes the notification, never when this app cancels it.
    val repostIntent = Intent(context, NotificationRepostBroadcastReceiver::class.java).apply {
        action = ACTION_REPOST_REVERT_NOTIFICATION
        putExtra(NOTIFICATION_EXTRA_NOTIFICATION_ID, AUTO_HIDE_NOTIFICATION_ID)
        // So a swipe rebuilds a notification that reverts the same thing this one would.
        putExtra(NOTIFICATION_EXTRA_COMPONENT_NAME, componentName)
    }

    val repostPendingIntent = PendingIntent.getBroadcast(
        context,
        AUTO_HIDE_NOTIFICATION_ID,
        repostIntent,
        FLAG_UPDATE_CURRENT or FLAG_IMMUTABLE,
    )

    val revertText = context.getString(
        if (componentName == null) {
            R.string.auto_hide_hidden_revert
        } else {
            R.string.auto_hide_hidden_revert_memory
        },
    )

    return NotificationCompat.Builder(
        context,
        AndroidNotificationManagerWrapper.AUTO_HIDE_CHANNEL_ID,
    ).apply {
        setSmallIcon(R.drawable.ic_revert_notification_small)

        ContextCompat.getDrawable(context, R.drawable.ic_revert_notification_large)
            ?.toBitmap(width = LARGE_ICON_PIXELS, height = LARGE_ICON_PIXELS)
            ?.let(::setLargeIcon)

        // Body text with a big-text style rather than a title, so the whole sentence shows
        // instead of being ellipsised to one line on a narrow screen. The header already
        // carries the app's name.
        setContentText(revertText)
        setStyle(NotificationCompat.BigTextStyle().bigText(revertText))
        setPriority(NotificationCompat.PRIORITY_DEFAULT)
        setOngoing(true)
        setAutoCancel(false)
        setContentIntent(revertPendingIntent)
        setDeleteIntent(repostPendingIntent)
    }.build()
}
