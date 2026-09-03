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
import com.android.geto.common.AutoUnhideWatch
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.REVERT_TO_DEFAULT_NOTIFICATION_ID

/**
 * Posts the notification that offers the way back from a launch.
 *
 * **One notification, one id, whatever the two frameworks say** — the author's instruction in
 * r3, replacing a branch that posted a per-app notification under the memory function and the
 * generic one otherwise.
 *
 * Its button is the framework-following unhide rather than the named `Revert to default`
 * function — see `RevertToDefaultBroadcastReceiver`, which is what makes one notification
 * correct in all four combinations. Under the memory function it puts back what the hide
 * measured; under Revert to default it drives the configured list. That is handover_3 §2.3's
 * rule: a notification is the way back from *this* hide, so it follows the framework.
 *
 * ⚠ **The old per-app branch was wrong under IMD defaults + Memory**, which is what every new
 * install gets. The hide there is the device-wide list, but the notification it posted offered
 * a per-app revert — and `RevertAppSettingsUseCase` opens on `getAppSettingsByComponentName`,
 * so with no profile for that app the tap cancelled the notification and wrote nothing. The
 * uniform answer closes that by construction rather than by another branch.
 *
 * The fixed id is also what makes the "one notification only" rule work: a second launch lands
 * on the same id and replaces the first, rather than leaving a row of offers behind it.
 *
 * A free function taking the wrapper rather than a class holding it, because all the callers
 * already have the wrapper to hand — two of them as a composition local — and plumbing an
 * injected object into a composable to save one argument is not a trade worth making.
 */
fun postAppliedSettingsNotification(
    context: Context,
    notificationManager: AndroidNotificationManagerWrapper,
) {
    // ⚠ **The cascade, and it still earns its place.** This launch arrived into a window
    // something else had already hidden, so there is one shared debt — and IMD+'s own
    // notification, which is posted under an id of its own by a different builder, is standing
    // beside this one offering to undo its share of it. `cancelAll` sweeps it, and the post
    // below replaces the lot.
    //
    // ⚠ **A state, not an event, and that is `AutoUnhideWatch.collapsed`'s job.** The launch
    // sites derive it from the persisted records *before* they apply anything, so a process
    // death does not break a chain: the next launch reads the records, finds a debt
    // outstanding, and collapses again.
    if (AutoUnhideWatch.collapsed) notificationManager.cancelAll()

    notificationManager.notify(
        id = REVERT_TO_DEFAULT_NOTIFICATION_ID,
        notification = buildRevertToDefaultNotification(context = context),
    )
}
