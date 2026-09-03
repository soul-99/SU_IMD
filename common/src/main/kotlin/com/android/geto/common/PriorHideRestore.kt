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
package com.android.geto.common

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/**
 * Whether the force-close popup's `'Restore settings first'` is running right now.
 *
 * A restore started from that popup can spend seconds writing overlay AppOps, the accessibility
 * list, four global settings and every per-app snapshot — and it starts at the moment the dialog
 * the user just answered disappears. Without this the screen goes back to normal and stays there
 * while the device is being changed underneath it, which reads as the answer having done nothing.
 *
 * **An object with a flow, like [SettingsChangeLog] beside it**, and for the same reason: the six
 * writers are spread across `feature/apps`, `feature/app-settings` and `app`, and the readers are
 * three separate windows. An injected singleton would have to reach all nine.
 *
 * ⚠ **Only the popup's own restore.** `SettingsHiddenRunner.flushPendingReverts` is also what the
 * Favourites tab's Unhide button calls, and what a change of framework runs before it takes
 * effect. Neither should raise a modal spinner — the first answers in a toast on a screen the
 * user is already looking at, and the second is not a thing the user is waiting on. So this is
 * wrapped around the call at the six sites the popup owns rather than set inside the runner.
 *
 * ⚠ **In memory, and that is not a compromise here.** It describes a call that is in flight in
 * this process; a value that survived the process would be describing a call that cannot be.
 */
object PriorHideRestore {

    private val _running = MutableStateFlow(false)

    /** True from the moment the answer is given until the restore has finished, or failed. */
    val running: StateFlow<Boolean> = _running.asStateFlow()

    /**
     * Run [block] with the flag up, and put it down however [block] ends.
     *
     * The `finally` is the whole point of this existing rather than two assignments at each of
     * the six sites: a restore that throws must not leave a spinner on screen forever.
     */
    suspend fun <T> track(block: suspend () -> T): T {
        _running.value = true

        return try {
            block()
        } finally {
            _running.value = false
        }
    }
}
