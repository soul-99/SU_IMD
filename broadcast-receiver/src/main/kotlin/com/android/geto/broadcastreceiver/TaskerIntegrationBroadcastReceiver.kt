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
import com.android.geto.common.showRevertFromMemoryToast
import com.android.geto.common.showSettingsHiddenToast
import com.android.geto.domain.model.TaskerIntegration
import com.android.geto.domain.usecase.ApplySettingsToHideUseCase
import com.android.geto.domain.usecase.GetTaskerAuthKeyUseCase
import com.android.geto.domain.usecase.RevertAllMemoryUseCase
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
    lateinit var revertToDefaultRunner: RevertToDefaultRunner

    @Inject
    lateinit var revertAllMemoryUseCase: RevertAllMemoryUseCase

    @Inject
    lateinit var applySettingsToHideUseCase: ApplySettingsToHideUseCase

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
                    // its own toast, so none is added here.
                    TaskerIntegration.ACTION_REVERT_TO_DEFAULT -> revertToDefaultRunner()

                    TaskerIntegration.ACTION_REVERT_USING_MEMORY -> {
                        revertAllMemoryUseCase()

                        context?.showRevertFromMemoryToast()
                    }

                    TaskerIntegration.ACTION_HIDE_SETTINGS -> {
                        applySettingsToHideUseCase()

                        context?.showSettingsHiddenToast()
                    }
                }
            } finally {
                pendingResult.finish()
            }
        }
    }
}
