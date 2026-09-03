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
import com.android.geto.common.ApplicationScope
import com.android.geto.common.showHiddenToast
import com.android.geto.common.showRestoredToast
import com.android.geto.domain.common.PriorHide
import com.android.geto.domain.model.AppSettingsResult
import com.android.geto.domain.model.TaskerIntegration
import com.android.geto.domain.usecase.ApplySettingsToHideUseCase
import com.android.geto.domain.usecase.GetTaskerAuthKeyUseCase
import com.android.geto.domain.usecase.RevertAllMemoryUseCase
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.PERMISSIONS_LOST_NOTIFICATION_ID
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * The one door another app - Tasker, MacroDroid, anything - can knock on to drive IMD.
 *
 * Exported, which none of the other receivers are, because that is the whole point: it has to
 * be reachable from outside, and it has to work with IMD not running, which a manifest
 * receiver gets for free - the system starts the process to deliver the broadcast. What stands
 * in for the export it gives up is the auth key: every action is refused unless the key in the
 * broadcast matches the one the user set up, and until they set one up nothing matches at all.
 * That is the same bargain Shizuku's own start/stop broadcasts make.
 *
 * Opening the services manager is not here. It is an activity, and a background receiver
 * cannot raise one on modern Android; it is an exported activity the caller launches directly
 * instead, and it needs no key because it only shows switches to flip by hand.
 *
 * The key is read, never generated - see [GetTaskerAuthKeyUseCase] - so the first stranger's
 * broadcast cannot be the thing that creates the secret it is then checked against.
 */
@AndroidEntryPoint
class TaskerIntegrationBroadcastReceiver : BroadcastReceiver() {

    @Inject
    @ApplicationScope
    lateinit var appScope: CoroutineScope

    @Inject
    lateinit var getTaskerAuthKeyUseCase: GetTaskerAuthKeyUseCase

    @Inject
    lateinit var revertAllMemoryUseCase: RevertAllMemoryUseCase

    @Inject
    lateinit var settingsHiddenRunner: SettingsHiddenRunner

    @Inject
    lateinit var applySettingsToHideUseCase: ApplySettingsToHideUseCase

    @Inject
    lateinit var notificationManagerWrapper: AndroidNotificationManagerWrapper

    override fun onReceive(context: Context?, intent: Intent?) {
        val action = intent?.action ?: return

        // Read once, off the intent, before any suspend point. onReceive's intent is only
        // valid for the length of the call, and the coroutine below outlives it.
        val providedKey = intent.getStringExtra(TaskerIntegration.EXTRA_AUTH_KEY)

        // The revert writes secure settings and may wait on Shizuku; without goAsync the
        // process is cached the moment this returns and the work races the killer.
        val pendingResult = goAsync()

        appScope.launch {
            try {
                val state = getTaskerAuthKeyUseCase()

                if (!TaskerIntegration.authorises(
                        enabled = state.enabled,
                        storedKey = state.authKey,
                        providedKey = providedKey,
                    )
                ) {
                    return@launch
                }

                when (action) {
                    // Runs the same revert the notification button and the tile do; it shows
                    // its own toast, so none is added here. `explicit` because this **is** the
                    // named function — the author listed the intent among the three routes that
                    // still say "reverted".
                    TaskerIntegration.ACTION_REVERT_TO_DEFAULT ->
                        settingsHiddenRunner.revertToDefault()

                    TaskerIntegration.ACTION_REVERT_USING_MEMORY -> {
                        revertAllMemoryUseCase()

                        // The offer to undo a hide that this has just undone. Same gap as
                        // AutoRevertRunner's memory branch: the sweep had no notification
                        // handling of its own, so an automation could restore the device and
                        // leave the notification standing over it.
                        settingsHiddenRunner.clearRevertOfferIfSettled()

                        context?.showRestoredToast(fromMemory = true)
                    }

                    // Settles whatever is outstanding the way the Unhiding framework says.
                    // flushPendingReverts rather than a revert-to-default: an automation
                    // firing this on a device with nothing hidden must change nothing, and
                    // applying the user's defaults to a device that never asked is exactly
                    // what "nothing hidden" must not mean.
                    TaskerIntegration.ACTION_UNHIDE_SETTINGS -> {
                        settingsHiddenRunner.flushPendingReverts()
                    }

                    // ⚠ **The author's "Hide/ unhide settings": one action, whichever way the
                    // device currently is.** It goes through the same toggle() the Quick
                    // Settings tile presses, so the two routes cannot come to disagree about
                    // what a press means - which is the whole reason it is not written here as
                    // "read the flag, then call one of the two branches below".
                    //
                    // ⚠ **Silent on every outcome but one.** An automation has no window to
                    // put a dialog in and the tile's three answers are all shade-bound. The one
                    // exception is a lost permission, which is the app unable to write anything
                    // at all until somebody re-grants it over adb - the same notification the
                    // hide branch below raises, and for the same reason.
                    TaskerIntegration.ACTION_TOGGLE_SETTINGS -> {
                        // Same suppression as the hide branch: there is nobody to ask.
                        PriorHide.suppress()

                        when (settingsHiddenRunner.toggle()) {
                            HideToggle.Done -> Unit

                            HideToggle.NothingToHide -> Unit

                            HideToggle.OverlayFailure -> Unit

                            HideToggle.PermissionsLost -> context?.let {
                                notificationManagerWrapper.notify(
                                    id = PERMISSIONS_LOST_NOTIFICATION_ID,
                                    notification = buildPermissionsLostNotification(context = it),
                                )
                            }
                        }
                    }

                    TaskerIntegration.ACTION_HIDE_SETTINGS -> {
                        val result = applySettingsToHideUseCase()

                        // ⚠ **No popup on this route, and it is the only one.** An
                        // automation has no window to ask in, and one that stopped to ask a
                        // question would simply never run — which is worse than proceeding,
                        // because the first-owner rule means a hide over an older hide records
                        // nothing for what is already down and strands nothing.
                        PriorHide.suppress()

                        // ⚠ **The toast used to fire whatever came back**, so an
                        // automation on a device that could hide nothing still said
                        // "Settings hidden" — which is how somebody goes on trusting a
                        // profile that has quietly stopped working. Now only the two
                        // outcomes where the device may actually have changed say it.
                        val hidSomething = result == AppSettingsResult.Success ||
                            result == AppSettingsResult.Failure

                        // This is the one route in the app with no window of its own, so
                        // the shade is the only place left to say it. Every other route
                        // shows the same sentence in a popup.
                        if (result == AppSettingsResult.NoPermission) {
                            context?.let {
                                notificationManagerWrapper.notify(
                                    id = PERMISSIONS_LOST_NOTIFICATION_ID,
                                    notification = buildPermissionsLostNotification(
                                        context = it,
                                    ),
                                )
                            }
                        } else if (hidSomething) {
                            context?.showHiddenToast()
                        }
                    }
                }
            } finally {
                pendingResult.finish()
            }
        }
    }
}
