/*
 *
 *   Copyright 2023 Einstein Blanco
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
package com.android.geto.framework.notificationmanager

import android.app.Notification
import android.os.Build
import androidx.annotation.RequiresApi

interface AndroidNotificationManagerWrapper {
    fun notify(
        id: Int,
        notification: Notification,
    )

    @RequiresApi(Build.VERSION_CODES.O)
    fun createNotificationChannel(
        channelId: String,
        name: String,
        importance: Int,
    )

    /**
     * Removes a channel the app no longer posts to, so it stops appearing in Android's
     * notification settings for this app.
     *
     * Needed because a channel's importance is fixed at creation: moving one from LOW to MIN
     * means creating a new id and clearing the old one away, or the user is left with two
     * entries and only one of them doing anything.
     */
    fun deleteNotificationChannel(channelId: String)

    fun cancel(id: Int)

    /**
     * Clears every notification this app has posted.
     *
     * Used by "Revert to default", which puts the whole device into a known state and so
     * makes every outstanding per-app Revert button describe a device that no longer
     * exists. Leaving them up would invite a press that writes stale values back over the
     * defaults that were just applied.
     */
    fun cancelAll()

    companion object {
        const val NOTIFICATION_CHANNEL_ID = "geto_notification_channel_id"

        /**
         * A second channel, at IMPORTANCE_HIGH, for the one notification that has to
         * interrupt.
         *
         * Importance is fixed when a channel is created and cannot be raised afterwards, so
         * this could not simply be the existing channel turned up: every install since v1.0
         * already has that one registered at IMPORTANCE_DEFAULT, and Android would ignore the
         * change. A new id is the only way to get a heads-up banner on an existing install,
         * and it also leaves the user able to silence this one without losing the ongoing
         * Revert notification, which is the one they actually need.
         */
        const val ALERT_NOTIFICATION_CHANNEL_ID = "geto_alert_notification_channel_id"

        /**
         * A channel each for the two ongoing revert notifications, so the pair can be
         * silenced, sorted or muted independently in Android's own settings.
         *
         * They were one channel with the observer service, which meant turning down the
         * service's notification also turned down the only route back from hidden settings.
         * Separate ids are the only way to undo that: a channel's importance and name are
         * fixed once created, so an existing install cannot be moved by editing the old one.
         *
         * ⚠ **Only the first of the two is registered now.** r3 replaced the per-app
         * revert notification with the single generic one, so the second has nothing left to
         * post to it and `GetoApplication` deletes it on start rather than creating it. The
         * one that remains is registered whichever framework is in use - a channel with
         * nothing posted to it is invisible in settings until it has something, and
         * registering on demand would mean the first post arriving before its channel exists.
         */
        const val REVERT_TO_DEFAULT_CHANNEL_ID = "imd_revert_to_default_channel"

        /**
         * ⚠ **Kept only so that it can be deleted.** Nothing posts to it since r3. A device
         * that saw a per-app revert notification before the upgrade still carries this channel
         * in Android's settings, where it would sit for ever with nothing able to use it, so
         * `GetoApplication` deletes it on start exactly as it does [AUTO_UNHIDE_CHANNEL_ID_LOW].
         */
        const val REVERT_MEMORY_CHANNEL_ID = "imd_revert_memory_channel"

        /**
         * A channel of its own for Auto-hide settings (IMD+).
         *
         * IMD+ posts the one notification a user may see without having opened this app at
         * all — it appears because an app they tapped happened to be on the watched list — so
         * it is the notification most likely to be wanted quieter, or sorted apart from the
         * ones a deliberate press produced. Sharing the revert-to-default channel would tie
         * the two together, and turning IMD+ down would have turned down the route back from
         * a hide the user did ask for.
         */
        const val AUTO_HIDE_CHANNEL_ID = "imd_auto_hide_channel"

        /**
         * The developer's note, on a channel of its own at IMPORTANCE_HIGH.
         *
         * The author asked for an alerting popup, and it is the one notification in the app
         * that is not about the device's state — so sharing a channel with the failures would
         * mean turning those down to silence this, or the reverse.
         */
        const val DEVELOPER_NOTE_CHANNEL_ID = "imd_app_update_notice"

        /**
         * A channel of its own for the auto unhide watcher's foreground service.
         *
         * Registered at **IMPORTANCE_MIN**, which is what Android's own per-channel
         * "Minimise" switch sets: silent, unbadged, collapsed at the bottom of the shade, and
         * **no icon in the status bar**. A foreground service still has to show *something* —
         * that part cannot be avoided — but it does not have to sit in the status bar, and at
         * LOW it did.
         *
         * Its own id so it can be turned down without touching the revert notifications
         * beside it. Those are the route back from a hide by hand; this one only says the
         * watcher is alive, and is the one a user is most likely to want out of the way.
         */
        const val AUTO_UNHIDE_CHANNEL_ID = "imd_auto_unhide_channel_min"

        /**
         * The r12 id, registered at IMPORTANCE_LOW and therefore drawn with a status bar icon.
         *
         * A channel's importance cannot be changed once it exists —
         * `createNotificationChannel` updates only the name, description and group — so
         * "minimised" could not be turned on by editing it. The id above is a new channel at
         * IMPORTANCE_MIN, and this one is deleted on the next start so an upgrading install is
         * not left with two entries in Android's settings, one of them dead.
         */
        const val AUTO_UNHIDE_CHANNEL_ID_LOW = "imd_auto_unhide_channel"

        /**
         * ⚠ **Legacy, and reachable only from a notification posted by a build before r3.**
         * Nothing creates a PendingIntent with it any more; `RevertTrampolineActivity` maps it
         * to the framework-following unhide so that a per-app notification still standing in
         * an upgrading install's shade does what it promised when it is tapped.
         */
        const val ACTION_REVERT_SETTINGS = "ACTION_REVERT_SETTINGS"
        const val ACTION_REVERT_TO_DEFAULT = "ACTION_REVERT_TO_DEFAULT"

        /**
         * The IMD+ notification's own revert.
         *
         * Not [ACTION_REVERT_TO_DEFAULT], although it ends by running exactly that: an IMD+
         * revert kills the watched apps first, so they never see the settings coming back
         * underneath them, and that step belongs to this action rather than to every revert
         * in the app.
         */
        const val ACTION_AUTO_HIDE_REVERT = "ACTION_AUTO_HIDE_REVERT"
        const val ACTION_RETRY_OVERLAY_RESTORE = "ACTION_RETRY_OVERLAY_RESTORE"

        /**
         * Clears the notification named in [NOTIFICATION_EXTRA_NOTIFICATION_ID] and does
         * nothing else. The one action in the app that changes no state at all — it exists so
         * a notification that is purely a warning can be acknowledged with a button rather
         * than only by swiping, which reads as dismissing something unread.
         */
        const val ACTION_DISMISS_NOTIFICATION = "ACTION_DISMISS_NOTIFICATION"

        /**
         * Puts a revert notification back after the user has swiped it away.
         *
         * Both revert notifications are ongoing, which stops a swipe on Android 13 and
         * below but not on 14 and up, where an ongoing notification can be dismissed like
         * any other. Losing it there means losing the only thing on screen that says the
         * device is still hidden and how to put it back - so a dismissal re-posts it.
         *
         * Fired from the notification's delete intent, which Android runs only when a
         * *person* removes the notification. Cancelling it from this app - which is what a
         * finished revert does - does not fire it, so the notification stays gone when it
         * should.
         */
        const val ACTION_REPOST_REVERT_NOTIFICATION = "ACTION_REPOST_REVERT_NOTIFICATION"
        const val NOTIFICATION_EXTRA_COMPONENT_NAME = "component_name"
        const val NOTIFICATION_EXTRA_NOTIFICATION_ID = "notification_id"

        /**
         * The single id every "Revert to default" notification is posted under.
         *
         * Fixed rather than derived from the app being launched, which is what makes the
         * mode's "one notification only" rule work: posting under an id that is already
         * showing replaces it, so launching a second app through this app silently retires
         * the first notification instead of stacking another one beside it.
         *
         * Far away from the per-app ids, which are component-name hash codes, and from the
         * observer service's id 1.
         */
        const val REVERT_TO_DEFAULT_NOTIFICATION_ID = 1_000_001

        /**
         * The id the "could not give overlay access back" notification is posted under.
         *
         * Its own id rather than the revert one, because the two mean opposite things and
         * can be on screen together: the revert notification offers to change the device,
         * this one reports a change that did not finish. Reposting after a failed retry
         * replaces it rather than stacking, which is the same reasoning as above.
         */
        const val OVERLAY_RESTORE_NOTIFICATION_ID = 1_000_002

        /**
         * The id the "Shizuku had to be killed through USB debugging" warning is posted under.
         *
         * Its own id for the same reason as the one above: it reports something that already
         * happened and can sit alongside the ongoing revert notification without either
         * replacing the other. Posting again under it replaces rather than stacks, so a run of
         * launches that all fall back cannot fill the shade with copies of one warning.
         */
        const val SHIZUKU_FALLBACK_NOTIFICATION_ID = 1_000_003

        /**
         * The id the Auto-hide settings (IMD+) notification is posted under.
         *
         * Its own, and deliberately not the revert-to-default one, even though only one of the
         * two can be outstanding at a time. They say different things and their buttons do
         * different work, and posting IMD+'s under the shared id would have a tile press that
         * hides device-wide silently replace the notification describing an IMD+ run — leaving
         * a revert that no longer kills the watched apps.
         */
        const val AUTO_HIDE_NOTIFICATION_ID = 1_000_004

        /**
         * The auto unhide watcher's foreground-service notification.
         *
         * Public because two modules need it now: the service posts it, and the repost
         * receiver has to name it when somebody swipes it away. The value is the one it has
         * always had — changing it would leave an upgrading install with the old one stranded.
         */
        const val AUTO_UNHIDE_NOTIFICATION_ID = 4711

        /**
         * The id the "Hide settings tile could not start Shizuku" notification is posted under.
         *
         * It exists because a failed press stopped collapsing the shade. That outcome used to
         * be said in the window the collapse opened, and a press that fails now deliberately
         * leaves the shade open — so there is no window left to say it in, and the shade is
         * where the answer has to appear.
         *
         * Not the Shizuku family's id, even though this is a Shizuku failure: a press that
         * changed nothing must not silently replace a warning about a service that was killed
         * through USB debugging, which is about a device that *did* change.
         */
        const val HIDE_TILE_NOTIFICATION_ID = 1_000_005

        /**
         * The id the "WRITE_SECURE_SETTINGS has gone" notification is posted under.
         *
         * Only ever posted by the routes with no window of their own to draw a dialog in —
         * today that is an automation intent. Everywhere else says the same sentence in a
         * popup, so a user who hides settings from Tasker and from the tile in the same
         * minute is told once by each rather than twice by the shade.
         *
         * Its own id, and posting again under it replaces rather than stacks: a Tasker
         * profile that fires every ten minutes must not fill the shade with copies of one
         * permission that is still missing.
         */
        const val PERMISSIONS_LOST_NOTIFICATION_ID = 1_000_006

        /** The developer's note. Its own id, so acknowledging the dialog cancels only it. */
        const val DEVELOPER_NOTE_NOTIFICATION_ID = 1_000_007
    }
}
