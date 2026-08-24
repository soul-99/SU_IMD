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
package com.android.geto.activity.revert

import android.content.Context
import android.os.Bundle
import androidx.activity.ComponentActivity
import com.android.geto.broadcastreceiver.RevertToDefaultRunner
import com.android.geto.common.AppLocale
import com.android.geto.common.ApplicationScope
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * "Revert to default" with no UI at all: it runs, says so with a toast, and finishes.
 *
 * An activity rather than a service because of what the two callers need. A Quick Settings
 * tile can only collapse the panel by launching an activity — there has been no API to
 * close the shade directly since Android 12 — and a launcher shortcut can only start one.
 * Both wants are satisfied by a window that never draws.
 *
 * Launched on the application scope, not the activity's: this window is gone within
 * milliseconds and the work takes seconds. Tying the two together would cancel the revert
 * halfway through, which is the one outcome worse than not starting it.
 */
@AndroidEntryPoint
class RevertActivity : ComponentActivity() {
    // The chosen language, applied before anything reads a string. A no-op on Android 13
    // and up, where the platform has already applied it to this context.
    override fun attachBaseContext(newBase: Context) {
        super.attachBaseContext(AppLocale.wrap(newBase))
    }


    @Inject
    @ApplicationScope
    lateinit var appScope: CoroutineScope

    @Inject
    lateinit var revertToDefaultRunner: RevertToDefaultRunner

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        appScope.launch { revertToDefaultRunner() }

        finish()

        // No transition either way. The default fade would show a translucent window
        // appearing and disappearing over the launcher for no reason — there is nothing in
        // it to see.
        overridePendingTransitionCompat()
    }

    @Suppress("DEPRECATION")
    private fun overridePendingTransitionCompat() {
        overridePendingTransition(0, 0)
    }
}
