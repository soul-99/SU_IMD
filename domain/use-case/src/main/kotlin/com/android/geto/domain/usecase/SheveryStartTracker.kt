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
package com.android.geto.domain.usecase

import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * A Shevery start begun from the settings manager, held where the dialog cannot take it away.
 *
 * ⚠ **Born from a bug report.** *"when sheevry is toggled on, but during the wait time settings
 * manager closed and opened again all toggles which were blocked are not blocked, countdown is
 * not shown, just shevery toggle spinner showing"*. Everything about the wait used to live in
 * `SettingsManagerViewModel`, which dies with the dialog; the spinner survived because it reads
 * [ShizukuStartTracker], which is a singleton. So is this.
 *
 * The forty seconds are not a request. Shevery is never asked to start: the debugging transport
 * goes up, its ErrorProtect watchdog notices, and the server appears on its own cycle. Nothing
 * can shorten that, which is why it is worth surviving a dialog dismissal — someone who closes
 * the manager and reopens it fifteen seconds later should see twenty-five, not a clean slate.
 *
 * ⚠ **Seconds counted, not a deadline compared against a clock.** This module is plain JVM with
 * no `SystemClock.elapsedRealtime`, and `System.currentTimeMillis` is wrong across a clock
 * change or a time-zone hop. The job doing the counting is itself the thing that survives, so it
 * publishes what it has counted and nothing has to be recomputed.
 *
 * ⚠ **Holds the job so a second dialog can cancel the first one's start.** The ViewModel that
 * began the wait may be long gone by the time somebody presses the switch again.
 */
@Singleton
class SheveryStartTracker @Inject constructor() {
    private val _secondsLeft = MutableStateFlow<Int?>(null)

    /** Seconds still to wait, or null when nothing is waiting. Survives the dialog. */
    val secondsLeft = _secondsLeft.asStateFlow()

    private var job: Job? = null

    /** Whether a start begun anywhere is still counting down. */
    val waiting: Boolean
        get() = _secondsLeft.value != null

    /**
     * Whether wireless debugging should be switched back on once the start comes up.
     *
     * ⚠ **A latch, and it only ever goes one way.** Two things set it: wireless debugging was
     * already on when Shevery was pressed, and the user switching it on at any point during the
     * wait — the author's *"if user himself enabled wireless debugging during the wait then keep
     * that as a yes"*. Nothing clears it, because Shevery is expected to switch that row off on
     * its way up and there is no way here to tell its write from a person's.
     */
    var wirelessWanted: Boolean = false
        private set

    fun begin(job: Job, seconds: Int, wirelessOn: Boolean) {
        this.job = job

        wirelessWanted = wirelessOn

        _secondsLeft.value = seconds
    }

    /** The user switched wireless debugging on mid-wait, which is a yes however it started. */
    fun noteWirelessTurnedOn() {
        if (waiting) wirelessWanted = true
    }

    fun tick(secondsLeft: Int) {
        // Only while one is actually running. A tick arriving after a cancel would put the
        // countdown back on screen with nothing behind it.
        if (_secondsLeft.value != null) _secondsLeft.value = secondsLeft
    }

    /**
     * Stops a wait in flight, if there is one, and says whether there was.
     *
     * The caller is expected to do the switching off; this only takes the countdown down and
     * stops the job that would otherwise finish it.
     */
    fun cancel(): Boolean {
        val running = waiting

        job?.cancel()

        clear()

        return running
    }

    fun clear() {
        job = null

        wirelessWanted = false

        _secondsLeft.value = null
    }
}
