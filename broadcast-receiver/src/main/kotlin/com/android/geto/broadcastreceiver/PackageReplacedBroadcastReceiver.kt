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
package com.android.geto.broadcastreceiver

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import com.android.geto.common.ApplicationScope
import com.android.geto.domain.repository.UserDataRepository
import com.android.geto.domain.usecase.EnableAutoHideServiceUseCase
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * Puts IMD's own accessibility service — the IMD+ detector — back after IMD has been updated.
 *
 * Android disables an app's accessibility service when the app is replaced, on most versions.
 * IMD+ then reads as switched off for a reason the user had no part in and no way to see: the
 * switch on the settings page is drawn from the live service state, so the feature simply stops
 * working the next time the app is updated.
 *
 * ⚠ **[UserData.autoHideEnabled] is the "was on before" record, and there is deliberately no
 * second flag.** It is the user's stored answer and nothing else writes it: a hide takes the
 * detector away by recording a hold under [AccessibilityServicePlan.AUTO_HIDE_HOLD] and leaves
 * the switch alone, and the live requirement is read from the service state rather than from
 * here. A separate marker would be a second copy of one fact, free to drift from it — and it
 * would not protect the case it looks like it protects, a detector switched off by hand in
 * Android's settings, because that is not what would clear it either.
 *
 * ⚠ **[EnableAutoHideServiceUseCase] is idempotent and never throws.** Already running is
 * success; a refused write and a dead Shizuku binder are ordinary outcomes it reports rather
 * than raising. So there is nothing for this receiver to check beyond the user's answer, and
 * nothing it can usefully do about a failure — the settings page will show the requirement
 * unmet, exactly as it does today.
 *
 * ⚠ **`goAsync`, for the same reason as every other receiver in this package**: without it the
 * process can be cached the moment `onReceive` returns, and the enable writes a secure setting
 * and then waits up to two and a half seconds for the service to bind.
 */
@AndroidEntryPoint
class PackageReplacedBroadcastReceiver : BroadcastReceiver() {

    @Inject
    @ApplicationScope
    lateinit var appScope: CoroutineScope

    @Inject
    lateinit var userDataRepository: UserDataRepository

    @Inject
    lateinit var enableAutoHideServiceUseCase: EnableAutoHideServiceUseCase

    override fun onReceive(context: Context?, intent: Intent?) {
        // The manifest filter already narrows this to one action, and the system is the only
        // sender of it. Checked anyway, because a receiver that acts on whatever it is handed
        // is one refactor away from acting on something else.
        if (intent?.action != Intent.ACTION_MY_PACKAGE_REPLACED) return

        val pendingResult = goAsync()

        appScope.launch {
            try {
                if (userDataRepository.userData.first().autoHideEnabled) {
                    enableAutoHideServiceUseCase()
                }
            } finally {
                pendingResult.finish()
            }
        }
    }
}
