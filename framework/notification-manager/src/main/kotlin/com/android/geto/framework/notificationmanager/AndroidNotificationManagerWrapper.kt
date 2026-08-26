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
        const val ACTION_REVERT_SETTINGS = "ACTION_REVERT_SETTINGS"
        const val ACTION_REVERT_TO_DEFAULT = "ACTION_REVERT_TO_DEFAULT"
        const val ACTION_RETRY_OVERLAY_RESTORE = "ACTION_RETRY_OVERLAY_RESTORE"
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
    }
}
