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

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import androidx.core.app.NotificationManagerCompat
import com.android.geto.common.AutoUnhideWatch
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.AUTO_HIDE_NOTIFICATION_ID
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.AUTO_UNHIDE_NOTIFICATION_ID
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.DEVELOPER_NOTE_NOTIFICATION_ID
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.NOTIFICATION_EXTRA_COMPONENT_NAME
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.NOTIFICATION_EXTRA_NOTIFICATION_ID
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.REVERT_TO_DEFAULT_NOTIFICATION_ID

/**
 * Puts a revert notification back after somebody has swiped it away.
 *
 * Both revert notifications are the only thing on screen saying the device is still changed
 * and how to change it back. `setOngoing` keeps them there up to Android 13; from Android 14
 * an ongoing notification can be dismissed like any other, and a dismissal there would strand
 * a device with developer options switched off and nothing left to undo it with.
 *
 * **This cannot fight the app's own cancels.** A notification's delete intent is fired only
 * when a person removes it — `NotificationManager.cancel` and `cancelAll` do not fire it. So
 * a finished revert, which cancels, is final; only a swipe reaches here.
 *
 * Which notification to rebuild is decided by the id it was posted under, which the intent
 * carries, and since r3 every id this app posts under is one of the three named below. IMD+'s
 * carries a component name with it, so the notification that comes back reverts the same app
 * the swiped one would have.
 *
 * A plain receiver with no Hilt entry point: rebuilding a notification reads no stored state
 * and changes nothing on the device.
 */
class NotificationRepostBroadcastReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val notificationId = intent.getIntExtra(NOTIFICATION_EXTRA_NOTIFICATION_ID, -1)

        if (notificationId == -1) return

        // ⚠ The one id here whose notification belongs to a running service rather than to a
        // standing debt. Reposting it for a service that has already stopped would leave an
        // *ongoing* notification in the shade with nothing left able to cancel it — so the
        // service's own liveness is asked first, and a process death answers false for free.
        if (notificationId == AUTO_UNHIDE_NOTIFICATION_ID && !AutoUnhideWatch.serviceRunning) {
            return
        }

        val notification = if (notificationId == DEVELOPER_NOTE_NOTIFICATION_ID) {
            // r4n: the developer's note. Ongoing holds it up to Android 13, and from 14 a
            // swipe is allowed - the author's "reappear on dismiss until user clicks on it".
            // Acknowledging the dialog cancels it, and a cancel never reaches this receiver.
            //
            // ⚠ In the chain rather than returned early, so it goes through the permission
            // check at the bottom like every other repost.
            buildDeveloperNoteNotification(context = context)
        } else if (notificationId == REVERT_TO_DEFAULT_NOTIFICATION_ID) {
            buildRevertToDefaultNotification(context = context)
        } else if (notificationId == AUTO_UNHIDE_NOTIFICATION_ID) {
            buildAutoUnhideNotification(context = context)
        } else if (notificationId == AUTO_HIDE_NOTIFICATION_ID) {
            // IMD+'s own. Rebuilt from its id like the one above, but it does carry the
            // component name through: under the memory function that is the app whose page the
            // run applied, and a rebuilt notification that lost it would offer a revert with
            // nothing to revert. Null under "Revert to default", which is what that mode means.
            buildAutoHideNotification(
                context = context,
                componentName = intent.getStringExtra(NOTIFICATION_EXTRA_COMPONENT_NAME),
            )
        } else {
            // ⚠ **Every id this app posts under is named above.** Until r3 anything else was a
            // per-app revert notification keyed on `componentName.hashCode()`, and that route
            // is gone - so an unrecognised id can now only be one left standing by a build
            // before this one. A swipe there is taken at face value and it stays gone; the
            // generic notification the new build posts is what offers the way back.
            return
        }

        // Posting needs the notification permission on Android 13 and up. It was granted to
        // post the notification that was just swiped, so the only way this can fail is the
        // user revoking it in between - in which case there is nothing to put back anyway.
        if (NotificationManagerCompat.from(context).areNotificationsEnabled()) {
            NotificationManagerCompat.from(context).notify(notificationId, notification)
        }
    }
}
