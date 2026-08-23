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

import android.content.Context
import com.android.geto.domain.model.NotificationFunction
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.REVERT_TO_DEFAULT_NOTIFICATION_ID

/**
 * Posts whichever notification the user's chosen function calls for.
 *
 * The choice of id is the interesting half. The memory function keys on the target app, so
 * three apps launched in a row leave three notifications, each undoing its own share.
 * "Revert to default" posts under one fixed id, which is what makes its "one notification
 * only" rule work — a second launch lands on the same id and replaces the first, because
 * the button does the same thing either way and two of it would be two ways to press the
 * same button.
 *
 * A free function taking the wrapper rather than a class holding it, because all three
 * callers already have the wrapper to hand — two of them as a composition local — and
 * plumbing an injected object into a composable to save one argument is not a trade worth
 * making.
 */
fun postAppliedSettingsNotification(
    context: Context,
    notificationManager: AndroidNotificationManagerWrapper,
    notificationFunction: NotificationFunction,
    componentName: String,
    icon: ByteArray?,
    contentTitle: String,
    contentText: String,
) {
    when (notificationFunction) {
        NotificationFunction.Memory -> {
            // Keyed on the component name so each target app owns its own notification and
            // its own Revert action. Also the PendingIntent request code: identity ignores
            // extras, so a shared code would let one app's notification rewrite another's
            // component name and revert the wrong app.
            val notificationId = componentName.hashCode()

            notificationManager.notify(
                id = notificationId,
                notification = buildAppliedSettingsNotification(
                    context = context,
                    notificationId = notificationId,
                    componentName = componentName,
                    icon = icon,
                    contentTitle = contentTitle,
                    contentText = contentText,
                ),
            )
        }

        NotificationFunction.RevertToDefault -> {
            notificationManager.notify(
                id = REVERT_TO_DEFAULT_NOTIFICATION_ID,
                notification = buildRevertToDefaultNotification(
                    context = context,
                    contentTitle = contentTitle,
                    contentText = contentText,
                ),
            )
        }
    }
}
