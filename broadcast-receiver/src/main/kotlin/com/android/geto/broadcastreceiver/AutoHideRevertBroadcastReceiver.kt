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
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.NOTIFICATION_EXTRA_COMPONENT_NAME
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * The Auto-hide settings (IMD+) notification's revert.
 *
 * Its own receiver rather than [RevertToDefaultBroadcastReceiver], because an IMD+ revert has a
 * step of its own before the ordinary one: the watched apps are force-stopped, so none of them
 * sees its settings come back while it is running.
 */
@AndroidEntryPoint
class AutoHideRevertBroadcastReceiver : BroadcastReceiver() {

    @Inject
    @ApplicationScope
    lateinit var appScope: CoroutineScope

    @Inject
    lateinit var autoHideRunner: AutoHideRunner

    override fun onReceive(context: Context?, intent: Intent?) {
        // Without goAsync the process drops to a cached state as soon as onReceive returns,
        // and this run starts Shizuku, stops apps, writes secure settings and restores
        // accessibility services — none of which fits inside a broadcast.
        val pendingResult = goAsync()

        // Which app's record to put back, or null for the device-wide revert. It rides in from
        // the notification rather than from storage - see buildAutoHideNotification.
        val componentName = intent?.getStringExtra(NOTIFICATION_EXTRA_COMPONENT_NAME)

        appScope.launch {
            try {
                autoHideRunner.revert(componentName = componentName)
            } finally {
                pendingResult.finish()
            }
        }
    }
}
