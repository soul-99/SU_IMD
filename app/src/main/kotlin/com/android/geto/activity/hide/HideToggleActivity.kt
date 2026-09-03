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
package com.android.geto.activity.hide

import android.content.Context
import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import com.android.geto.broadcastreceiver.HideToggle
import com.android.geto.broadcastreceiver.SettingsHiddenRunner
import com.android.geto.broadcastreceiver.buildHideTileOverlayFailedNotification
import com.android.geto.common.AppLocale
import com.android.geto.common.ApplicationScope
import com.android.geto.domain.common.PriorHide
import com.android.geto.domain.usecase.SettingsWorkTracker
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.HIDE_TILE_NOTIFICATION_ID
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.launch
import javax.inject.Inject
import com.android.geto.feature.apps.R as appsR

/**
 * What the app drawer's "Hide/unhide Settings" entry starts: one press, whichever way the device
 * currently is, and no window of its own.
 *
 * ⚠ **The same `toggle()` the Quick Settings tile presses**, at the author's *"make it function
 * just like the hide settings qs toggle"*. Not a copy of the tile's logic - the same call - so the
 * two routes cannot come to disagree about what a press means. What differs is only what there is
 * to say afterwards: the tile has a shade to collapse and a tile face to move, and this has
 * neither, so the two outcomes that need words are handed to [HideActivity], which is the dialog
 * host both routes already share.
 *
 * ⚠ **This activity is exported, and it has to be.** A launcher entry is reached by the launcher,
 * which is another app; there is no way to publish an app-drawer icon that only IMD can start. The
 * author was asked about this before it was built and said to build it. What it means in practice
 * is that a hide or an unhide can be triggered by any app that knows this component's name,
 * *without* the auth key the Tasker broadcasts require - the same exposure the Quick Settings tile
 * already has to anyone holding the device, and the reason `HideActivity` and `RevertActivity`
 * beside it are both `exported="false"`.
 *
 * ⚠ **The application scope, not this activity's.** A press can take ten seconds and this window
 * finishes immediately; a job on a scope that dies with the activity would be cancelled in the
 * middle of a hide.
 */
@AndroidEntryPoint
class HideToggleActivity : ComponentActivity() {
    override fun attachBaseContext(newBase: Context) {
        super.attachBaseContext(AppLocale.wrap(newBase))
    }

    @Inject
    @ApplicationScope
    lateinit var appScope: CoroutineScope

    @Inject
    lateinit var settingsWorkTracker: SettingsWorkTracker

    @Inject
    lateinit var settingsHiddenRunner: SettingsHiddenRunner

    @Inject
    lateinit var notificationManagerWrapper: AndroidNotificationManagerWrapper

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // The same guard the tile has: a second press while the first is still running must not
        // start a second toggle, which would race the first and could land on either state.
        if (settingsWorkTracker.inFlightNow) {
            finish()

            return
        }

        val context = applicationContext

        appScope.launch {
            // ⚠ **No prior-hide popup on this route.** There is no window to ask in - this one
            // is already finishing - and the first-owner rule means a hide over an older hide
            // records nothing for what is already down and strands nothing. The Tasker branch
            // suppresses it for the same reason.
            PriorHide.suppress()

            when (settingsHiddenRunner.toggle()) {
                // The launcher icon follows the stored state on its own; nothing to say.
                HideToggle.Done -> Unit

                HideToggle.NothingToHide -> context.showHideDialog(HideDialog.NothingToHide)

                // ⚠ **A notification, not a dialog, and it is the tile's notification.** This
                // outcome has no dialog anywhere in the app: what the user needs is three lines
                // about Shizuku and overlay permission, which the shade can hold and a
                // disappearing window cannot. Built by the same function the tile calls.
                HideToggle.OverlayFailure -> notificationManagerWrapper.notify(
                    id = HIDE_TILE_NOTIFICATION_ID,
                    notification = buildHideTileOverlayFailedNotification(
                        context = context,
                        title = context.getString(appsR.string.overlay_failure_title),
                        text = listOf(
                            appsR.string.overlay_failure_check,
                            appsR.string.overlay_failure_point_permission,
                            appsR.string.overlay_failure_point_configuration,
                        ).joinToString(separator = "\n") { context.getString(it) },
                    ),
                )

                HideToggle.PermissionsLost -> context.showHideDialog(HideDialog.PermissionsLost)
            }
        }

        // Finished before the work returns, deliberately: this window draws nothing, and leaving
        // an invisible activity on the stack for ten seconds is how a launcher ends up showing
        // IMD in recents for a press that had no screen.
        finish()
    }
}

/**
 * Raises one of [HideActivity]'s dialogs from outside it.
 *
 * A new task, because the caller has already finished by the time this runs and there is no task
 * of ours left to join.
 */
private fun Context.showHideDialog(dialog: HideDialog) {
    startActivity(
        Intent(this, HideActivity::class.java).apply {
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)

            putExtra(HIDE_EXTRA_DIALOG, dialog.name)
        },
    )
}
