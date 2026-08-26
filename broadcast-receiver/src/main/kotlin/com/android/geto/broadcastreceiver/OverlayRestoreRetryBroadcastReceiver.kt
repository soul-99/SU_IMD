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
 * The "Try again" button on the overlay restore notification.
 *
 * Carries no extras: what to restore is already written down in the held-packages debt, which
 * is the only record of which apps had overlay access taken away and is deliberately not
 * cleared until they get it back.
 */
@AndroidEntryPoint
class OverlayRestoreRetryBroadcastReceiver : BroadcastReceiver() {

    @Inject
    @ApplicationScope
    lateinit var appScope: CoroutineScope

    @Inject
    lateinit var overlayRestoreRunner: OverlayRestoreRunner

    override fun onReceive(context: Context?, intent: Intent?) {
        // Same reason as the other receivers: without goAsync the process is cached as soon
        // as onReceive returns, and this run talks to Shizuku over a shell command.
        val pendingResult = goAsync()

        appScope.launch {
            try {
                overlayRestoreRunner.retry()
            } finally {
                pendingResult.finish()
            }
        }
    }
}
