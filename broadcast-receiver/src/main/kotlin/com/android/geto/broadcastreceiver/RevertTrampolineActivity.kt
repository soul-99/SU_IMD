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

import android.app.Activity
import android.content.Intent
import android.os.Bundle
import androidx.core.app.NotificationManagerCompat
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.ACTION_REVERT_SETTINGS
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.ACTION_REVERT_TO_DEFAULT
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.NOTIFICATION_EXTRA_COMPONENT_NAME
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.NOTIFICATION_EXTRA_NOTIFICATION_ID

/**
 * What the notification's Revert button opens instead of firing a broadcast straight off.
 *
 * It exists for one reason the broadcast could not do on its own: collapse the notification
 * shade. Tapping a notification's action button does not close the shade - only launching an
 * activity does, and a broadcast is not one. So the button now opens this, which takes no
 * window, does two things, and finishes before it can draw:
 *
 *  1. Cancels the tapped notification immediately, before the revert runs. The revert can
 *     spend ten seconds starting Shizuku, and a notification that sat in the shade looking
 *     stuck for that whole time was the complaint. Nothing is lost by retiring it now - the
 *     one failure worth reporting, a restore that could not put overlay access back, raises
 *     its own separate notification when it happens.
 *  2. Hands the revert straight to the receiver that already owns it, unchanged, so all of
 *     that logic stays in one place.
 *
 * Finishing in onCreate with no content is what makes the shade close over nothing rather
 * than over a blank window. This is a plain Activity, not a Compose or Hilt one, because it
 * needs neither: it draws nothing and injects nothing.
 *
 * Not a notification trampoline in the sense Android 12 restricts - that rule is about a
 * broadcast or service *starting* an activity. Here the notification starts this activity
 * directly, and an activity sending a broadcast is allowed.
 */
class RevertTrampolineActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val notificationId = intent.getIntExtra(NOTIFICATION_EXTRA_NOTIFICATION_ID, -1)

        if (notificationId != -1) {
            NotificationManagerCompat.from(this).cancel(notificationId)
        }

        forwardIntentFor(action = intent.action)?.let(::sendBroadcast)

        finish()
    }

    /**
     * The broadcast that actually reverts, aimed explicitly at the receiver that already
     * handles it. Null for anything else, so a malformed or unexpected launch quietly does
     * nothing rather than guessing.
     */
    private fun forwardIntentFor(action: String?): Intent? {
        val receiver: Class<*> = when (action) {
            ACTION_REVERT_SETTINGS -> RevertSettingsBroadcastReceiver::class.java
            ACTION_REVERT_TO_DEFAULT -> RevertToDefaultBroadcastReceiver::class.java
            else -> return null
        }

        return Intent(this, receiver).apply {
            this.action = action

            // Only the per-app revert identifies a target; "Revert to default" is about the
            // whole device and carries nothing.
            if (action == ACTION_REVERT_SETTINGS) {
                putExtra(
                    NOTIFICATION_EXTRA_COMPONENT_NAME,
                    intent.getStringExtra(NOTIFICATION_EXTRA_COMPONENT_NAME),
                )
                putExtra(
                    NOTIFICATION_EXTRA_NOTIFICATION_ID,
                    intent.getIntExtra(NOTIFICATION_EXTRA_NOTIFICATION_ID, -1),
                )
            }
        }
    }
}
