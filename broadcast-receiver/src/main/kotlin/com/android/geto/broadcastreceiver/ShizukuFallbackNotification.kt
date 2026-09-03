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
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.NOTIFICATION_EXTRA_NOTIFICATION_ID
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.SHIZUKU_FALLBACK_NOTIFICATION_ID
import com.android.geto.framework.notificationmanager.R

/**
 * Posted when the Shizuku service would not answer its stop intent and had to be taken down
 * by cycling USB debugging instead.
 *
 * ⚠ **Removed by r3, not r2 — deliberately, after a false start.** v3 spec item 7 says this
 * notification is no longer needed, and it will not be: the redesigned stop sends the intent
 * and then manages debugging itself, so there is no fallback left to warn about. But the
 * fallback still exists until that lands, and taking the warning away first would leave a
 * round in which Shizuku can be killed this way, may not come back on the revert, and nothing
 * on screen says so. The warning goes **with** the mechanism it describes, not before it.
 *
 * The user is told because the two routes are not equally reversible. A fork that ignores its
 * stop action is usually one this app cannot reliably start again either, so the Revert that
 * follows may not bring the service back — and with it may not bring back Display over other
 * apps, which is written through Shizuku and is named in the text only when this same run
 * actually hid it.
 *
 * On the alert channel, so it arrives as a banner rather than a line found later in the shade:
 * it is about something that already happened, silently, in the middle of opening an app, and
 * a warning nobody sees is not a warning. Unlike the overlay-restore notification it is not
 * ongoing — there is nothing to retry and nothing to keep watching, so **OK** clears it and so
 * does a swipe. It reports; it does not ask.
 */
fun buildShizukuFallbackNotification(context: Context, overlayHidden: Boolean): Notification {
    val dismissIntent = Intent(context, NotificationDismissBroadcastReceiver::class.java).apply {
        action = ACTION_DISMISS_NOTIFICATION

        putExtra(NOTIFICATION_EXTRA_NOTIFICATION_ID, SHIZUKU_FALLBACK_NOTIFICATION_ID)
    }

    val dismissPendingIntent = PendingIntent.getBroadcast(
        context,
        SHIZUKU_FALLBACK_NOTIFICATION_ID,
        dismissIntent,
        FLAG_UPDATE_CURRENT or FLAG_IMMUTABLE,
    )

    // Tapping the body opens the services manager, which is where the aftermath is visible and
    // fixable: Shizuku's own row shows whether the service is really down and offers to start
    // it again. NEW_TASK because the shade is not an activity context, CLEAR_TOP so a manager
    // already open is reused rather than stacked behind itself.
    val managerIntent = Intent()
        .setClassName(context, SettingsObservationGate.SERVICES_ACTIVITY_CLASS_NAME)
        .setFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)

    val managerPendingIntent = PendingIntent.getActivity(
        context,
        SHIZUKU_FALLBACK_NOTIFICATION_ID,
        managerIntent,
        FLAG_UPDATE_CURRENT or FLAG_IMMUTABLE,
    )

    val text = context.getString(
        if (overlayHidden) {
            R.string.shizuku_usb_fallback_text_overlay
        } else {
            R.string.shizuku_usb_fallback_text
        },
    )

    return NotificationCompat.Builder(
        context,
        AndroidNotificationManagerWrapper.ALERT_NOTIFICATION_CHANNEL_ID,
    ).apply {
        setSmallIcon(R.drawable.ic_failure_notification_small)
        setContentTitle(context.getString(R.string.shizuku_usb_fallback_title))
        setContentText(text)

        // The text is the whole point and is longer than one collapsed line, so it must not
        // be truncated to the first few words.
        setStyle(NotificationCompat.BigTextStyle().bigText(text))
        setContentIntent(managerPendingIntent)

        // Cleared by OK, by opening the manager from it, or by a swipe. Nothing is lost either
        // way: this reports something that has already finished, and the state it warns about
        // is visible in the services manager afterwards. Not ongoing, unlike the overlay
        // restore notification - there is nothing here to retry and nothing to keep watching.
        setAutoCancel(true)
        setOngoing(false)

        // PRIORITY_HIGH is what produces the banner below API 26; the channel's importance
        // does it from 26 up. Both, because the app still supports API 24.
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


/**
 * IMD+ gave up because Shizuku would not start.
 *
 * Its own builder rather than a flag on the one above, because the two say different things:
 * that one reports a service that *was* stopped by a blunter means and warns the revert may
 * not bring it back, this one reports a hide that never happened at all.
 *
 * Shares the fallback notification's id on purpose. Both are "something went wrong with
 * Shizuku, here is the manager" and both are cleared the same way — two of them stacked would
 * be one problem reported twice.
 *
 * Alert channel, banner, auto-cancel, and the body opens the services manager where Shizuku's
 * own row shows whether the service is really down and offers to start it again.
 */
fun buildAutoHideShizukuFailedNotification(context: Context): Notification {
    val dismissIntent = Intent(context, NotificationDismissBroadcastReceiver::class.java).apply {
        action = ACTION_DISMISS_NOTIFICATION

        putExtra(NOTIFICATION_EXTRA_NOTIFICATION_ID, SHIZUKU_FALLBACK_NOTIFICATION_ID)
    }

    val dismissPendingIntent = PendingIntent.getBroadcast(
        context,
        SHIZUKU_FALLBACK_NOTIFICATION_ID,
        dismissIntent,
        FLAG_UPDATE_CURRENT or FLAG_IMMUTABLE,
    )

    val managerIntent = Intent()
        .setClassName(context, SettingsObservationGate.SERVICES_ACTIVITY_CLASS_NAME)
        .setFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)

    val managerPendingIntent = PendingIntent.getActivity(
        context,
        SHIZUKU_FALLBACK_NOTIFICATION_ID,
        managerIntent,
        FLAG_UPDATE_CURRENT or FLAG_IMMUTABLE,
    )

    val text = context.getString(R.string.auto_hide_shizuku_failed)

    return NotificationCompat.Builder(
        context,
        AndroidNotificationManagerWrapper.ALERT_NOTIFICATION_CHANNEL_ID,
    ).apply {
        setSmallIcon(R.drawable.ic_failure_notification_small)
        setContentTitle(context.getString(R.string.shizuku_usb_fallback_title))
        setContentText(text)
        setStyle(NotificationCompat.BigTextStyle().bigText(text))
        setContentIntent(managerPendingIntent)
        setAutoCancel(true)
        setOngoing(false)
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


/**
 * A revert could not bring the Shizuku service back up.
 *
 * v3 spec item 5. Tapping it opens the Shizuku app itself rather than IMD's services manager —
 * starting the service by hand is the only thing that fixes this, and it is done over there.
 *
 * ⚠ **Shares [SHIZUKU_FALLBACK_NOTIFICATION_ID] with its two siblings on purpose.** All three
 * say "something went wrong with Shizuku"; posting them under separate ids would stack up to
 * three notifications describing one broken service, and the author asked for one at a time.
 * The newest replaces whatever was there, which is also the one still true.
 *
 * ⚠ **The DOOA restore-failure notification is deliberately left alone**, on the author's
 * instruction. It is ongoing and carries a Try again button for a debt that is still
 * outstanding, so cancelling it to make room for this one would throw away a retry the user
 * may still need.
 *
 * [shizukuPackage] is the fork configured in IMD. If it is blank, or has no launcher entry —
 * uninstalled since it was configured, or a stealth build with no icon — the tap falls back to
 * IMD's own services manager, which can at least report the state and offer to start it.
 */
fun buildSheveryStartFailedNotification(
    context: Context,
    shizukuPackage: String,
): Notification = buildForkStartFailedNotification(
    context = context,
    shizukuPackage = shizukuPackage,
    text = context.getString(R.string.shevery_start_failed),
)

fun buildShizukuRevertFailedNotification(
    context: Context,
    shizukuPackage: String,
): Notification = buildForkStartFailedNotification(
    context = context,
    shizukuPackage = shizukuPackage,
    text = context.getString(R.string.shizuku_revert_failed),
)

/**
 * The shape both fork-failure notifications share: the fork's own app on a tap, an OK that
 * dismisses, and nothing else.
 *
 * ⚠ **One builder, two sentences.** They differ only in wording — a Shevery start that never
 * came up and a Shizuku restart that failed are the same news about the same row — and they
 * post under the same id so that only one of them stands at a time. Written once rather than
 * twice so a change to the tap behaviour cannot land on one and miss the other.
 */
private fun buildForkStartFailedNotification(
    context: Context,
    shizukuPackage: String,
    text: String,
): Notification {
    val launchIntent = shizukuPackage
        .takeIf { it.isNotBlank() }
        ?.let { context.packageManager.getLaunchIntentForPackage(it) }
        ?.apply { addFlags(Intent.FLAG_ACTIVITY_NEW_TASK) }
        ?: Intent()
            .setClassName(context, SettingsObservationGate.SERVICES_ACTIVITY_CLASS_NAME)
            .setFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)

    val launchPendingIntent = PendingIntent.getActivity(
        context,
        SHIZUKU_FALLBACK_NOTIFICATION_ID,
        launchIntent,
        FLAG_UPDATE_CURRENT or FLAG_IMMUTABLE,
    )

    val dismissIntent = Intent(context, NotificationDismissBroadcastReceiver::class.java).apply {
        action = ACTION_DISMISS_NOTIFICATION

        putExtra(NOTIFICATION_EXTRA_NOTIFICATION_ID, SHIZUKU_FALLBACK_NOTIFICATION_ID)
    }

    val dismissPendingIntent = PendingIntent.getBroadcast(
        context,
        SHIZUKU_FALLBACK_NOTIFICATION_ID,
        dismissIntent,
        FLAG_UPDATE_CURRENT or FLAG_IMMUTABLE,
    )

    return NotificationCompat.Builder(
        context,
        AndroidNotificationManagerWrapper.ALERT_NOTIFICATION_CHANNEL_ID,
    ).apply {
        setSmallIcon(R.drawable.ic_failure_notification_small)
        setContentTitle(context.getString(R.string.shizuku_usb_fallback_title))
        setContentText(text)
        setStyle(NotificationCompat.BigTextStyle().bigText(text))
        setContentIntent(launchPendingIntent)

        // "auto dismisses itself" on tap, as the author asked.
        setAutoCancel(true)
        setOngoing(false)
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
