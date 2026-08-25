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

import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicBoolean

/**
 * Prevents the diagnostic settings observer from reporting changes IMD is making itself.
 *
 * The counter supports nested callers without letting an inner completion resume
 * observation while an outer operation is still writing settings.
 */
object SettingsObservationGate {
    const val SERVICE_CLASS_NAME = "com.android.geto.service.SettingsObserverService"
    const val ACTION_RESET = "com.android.geto.action.RESET_SETTINGS_OBSERVER"

    private val pauseCount = AtomicInteger(0)
    private val running = AtomicBoolean(false)

    val isPaused: Boolean get() = pauseCount.get() > 0
    val isRunning: Boolean get() = running.get()

    fun setRunning(value: Boolean) {
        running.set(value)
    }

    fun pause() {
        pauseCount.incrementAndGet()
    }

    fun resume() {
        pauseCount.updateAndGet { count -> (count - 1).coerceAtLeast(0) }
    }
}
