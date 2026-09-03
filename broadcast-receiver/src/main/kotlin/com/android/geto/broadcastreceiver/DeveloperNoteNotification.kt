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
import com.android.geto.domain.repository.UserDataRepository
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.ACTION_REPOST_REVERT_NOTIFICATION
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.DEVELOPER_NOTE_NOTIFICATION_ID
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.NOTIFICATION_EXTRA_NOTIFICATION_ID
import com.android.geto.framework.notificationmanager.R
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.first
import javax.inject.Inject
import javax.inject.Singleton

/**
 * The developer's note, for the routes that have no window to put a dialog in.
 *
 * The author listed five triggers: the app, a hide from a shortcut or IMD+, the settings
 * manager, a toggle, and an intent. Four of those open an activity and get the dialog itself.
 * The **Hide settings tile** and the **Tasker intents** do not, and a background route cannot
 * raise a dialog at all.
 *
 * ⚠ **Posted from `GetoApplication.onCreate` rather than from each of those sites.** Every one
 * of them starts this process, so one call covers all of them and cannot fall out of step with a
 * sixth route added later. The moment an activity does appear, `MainActivity` shows the dialog
 * and acknowledging it calls [clear].
 *
 * ⚠ **Ongoing with a delete intent** — the author's *"non dismissible/ reappear on dismiss until
 * user clicks on it"*. `setOngoing` holds it up to Android 13; from 14 a swipe is allowed, and
 * [NotificationRepostBroadcastReceiver] puts it back. That receiver's own KDoc records why this
 * cannot fight the app: a delete intent fires only for a person's swipe, never for
 * `cancel`, so acknowledgement is final.
 */
@Singleton
class DeveloperNoteNotification @Inject constructor(
    @param:ApplicationContext private val context: Context,
    private val userDataRepository: UserDataRepository,
    private val notificationManagerWrapper: AndroidNotificationManagerWrapper,
) {
    /**
     * Posts the note if this install existed before v3 and has not read the dialog.
     *
     * @param currentRevision the revision `MainActivity` writes when the dialog is
     *        acknowledged. Passed in rather than read here, so the one place that decides what
     *        "read" means stays the one place.
     */
    suspend fun postIfUnread(currentRevision: Int) {
        val userData = userDataRepository.userData.first()

        // ⚠ **A fresh install has no previous settings to have had matched.** This used to ask
        // `setupNoticeVersion == 0`, which is "setup has never been completed" - true of a
        // fresh install for one launch and false for ever after, so a new user met the note the
        // second time they opened the app. `upgradedToV3` is decided once, by
        // MigrateFrameworksUseCase, while the two can still be told apart.
        if (!userData.upgradedToV3) return

        if (userData.settingsNoticeRevision >= currentRevision) return

        notificationManagerWrapper.notify(
            id = DEVELOPER_NOTE_NOTIFICATION_ID,
            notification = buildDeveloperNoteNotification(context = context),
        )
    }

    /** Takes it down once the dialog behind it has been read. */
    fun clear() {
        notificationManagerWrapper.cancel(id = DEVELOPER_NOTE_NOTIFICATION_ID)
    }
}

/**
 * ⚠ **`internal`, not private: [NotificationRepostBroadcastReceiver] rebuilds it after a swipe**,
 * and that lives in another file of this module. Private compiled here and would have failed in
 * the author's build.
 */
internal fun buildDeveloperNoteNotification(context: Context): Notification {
    // Opens IMD, which is where the dialog is. NEW_TASK because the shade is not an activity
    // context; CLEAR_TOP so an IMD already open is reused rather than stacked behind itself.
    val launchIntent = context.packageManager
        .getLaunchIntentForPackage(context.packageName)
        ?.apply {
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)
        }

    val launchPendingIntent = PendingIntent.getActivity(
        context,
        DEVELOPER_NOTE_NOTIFICATION_ID,
        launchIntent,
        FLAG_UPDATE_CURRENT or FLAG_IMMUTABLE,
    )

    val repostIntent = Intent(context, NotificationRepostBroadcastReceiver::class.java).apply {
        action = ACTION_REPOST_REVERT_NOTIFICATION

        putExtra(NOTIFICATION_EXTRA_NOTIFICATION_ID, DEVELOPER_NOTE_NOTIFICATION_ID)
    }

    val repostPendingIntent = PendingIntent.getBroadcast(
        context,
        DEVELOPER_NOTE_NOTIFICATION_ID,
        repostIntent,
        FLAG_UPDATE_CURRENT or FLAG_IMMUTABLE,
    )

    val text = context.getString(R.string.developer_note_notification)

    return NotificationCompat.Builder(
        context,
        AndroidNotificationManagerWrapper.DEVELOPER_NOTE_CHANNEL_ID,
    ).apply {
        setSmallIcon(R.drawable.ic_failure_notification_small)
        setContentTitle(text)
        setStyle(NotificationCompat.BigTextStyle().bigText(text))
        setContentIntent(launchPendingIntent)
        setDeleteIntent(repostPendingIntent)

        // Stays until the dialog behind it has been read, and comes back from a swipe.
        setAutoCancel(false)
        setOngoing(true)

        setPriority(NotificationCompat.PRIORITY_HIGH)
        setCategory(NotificationCompat.CATEGORY_STATUS)
        setDefaults(NotificationCompat.DEFAULT_ALL)
    }.build()
}
