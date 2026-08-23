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
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.ACTION_REVERT_TO_DEFAULT
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.REVERT_TO_DEFAULT_NOTIFICATION_ID
import com.android.geto.framework.notificationmanager.R

/**
 * How big the launched-app icon on the per-app notification comes out, so the revert icon
 * beside it in the shade is the same size rather than noticeably smaller or blurrier.
 */
private const val LARGE_ICON_PIXELS = 192

/**
 * The single notification posted after a launch when the notification function is set to
 * "Revert to default".
 *
 * Deliberately says nothing about which app was launched. In this mode the button does not
 * undo that app — it drives the whole device to the configured default — so naming an app
 * or showing its icon would describe something the button does not do. The revert icon is
 * there instead, and it is the same drawing as the tile and the shortcut, so all three
 * routes to the same action look like the same action.
 *
 * Posted under [REVERT_TO_DEFAULT_NOTIFICATION_ID], which is what makes this mode's "one
 * notification only" rule work: launching a second app replaces this notification rather
 * than adding another.
 */
fun buildRevertToDefaultNotification(
    context: Context,
    contentTitle: String,
    contentText: String,
): Notification {
    val revertIntent = Intent(context, RevertToDefaultBroadcastReceiver::class.java).apply {
        action = ACTION_REVERT_TO_DEFAULT
    }

    val revertPendingIntent = PendingIntent.getBroadcast(
        context,
        REVERT_TO_DEFAULT_NOTIFICATION_ID,
        revertIntent,
        FLAG_UPDATE_CURRENT or FLAG_IMMUTABLE,
    )

    return NotificationCompat.Builder(
        context,
        AndroidNotificationManagerWrapper.NOTIFICATION_CHANNEL_ID,
    ).apply {
        setSmallIcon(R.drawable.ic_revert_notification_small)

        // The colour artwork is a vector, and setLargeIcon wants a bitmap. Rasterised at a
        // fixed size rather than the drawable's intrinsic one so it does not come out at
        // 108px on a screen expecting far more.
        ContextCompat.getDrawable(context, R.drawable.ic_revert_notification_large)
            ?.toBitmap(width = LARGE_ICON_PIXELS, height = LARGE_ICON_PIXELS)
            ?.let(::setLargeIcon)

        setContentTitle(contentTitle)
        setContentText(contentText)
        setPriority(NotificationCompat.PRIORITY_DEFAULT)
        addAction(
            R.drawable.ic_revert_notification_small,
            context.getString(R.string.revert_to_default),
            revertPendingIntent,
        )
    }.build()
}
