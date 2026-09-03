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
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * The "Revert to default" button on the notification.
 *
 * Carries no extras, unlike the per-app receiver: there is nothing to identify, because this
 * action is about the device rather than about whichever app happened to be launched last.
 */
@AndroidEntryPoint
class RevertToDefaultBroadcastReceiver : BroadcastReceiver() {

    @Inject
    @ApplicationScope
    lateinit var appScope: CoroutineScope

    @Inject
    lateinit var settingsHiddenRunner: SettingsHiddenRunner

    override fun onReceive(context: Context?, intent: Intent?) {
        // Same reason as the per-app receiver: without goAsync the process drops to a
        // cached state as soon as onReceive returns, and this run writes secure settings,
        // restores accessibility services and may wait on adbd before poking Shizuku.
        val pendingResult = goAsync()

        appScope.launch {
            try {
                // ⚠ **The framework-following unhide, not the named `Revert to default`
                // function — and v3 is where those stopped being the same thing.** This is
                // the button on the notification a hide posted: it is the way back from that
                // hide, so it has to undo it the way the Unhiding framework says. Calling
                // RevertToDefaultRunner straight would drive the configured defaults under
                // UnhidingFramework.Memory too, which is precisely the "app switches on a
                // setting I never had on" that the memory function exists to avoid — and it
                // would do it to every new install, since IMD defaults + Memory is what one
                // gets. The explicit Revert to default routes still call the runner directly.
                settingsHiddenRunner.unhide()
            } finally {
                pendingResult.finish()
            }
        }
    }
}
