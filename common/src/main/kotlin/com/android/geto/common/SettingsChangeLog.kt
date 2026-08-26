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
import kotlinx.coroutines.flow.update

/**
 * How many changes to keep. Settings churn in bursts - one screen rotation can write a
 * handful - so this has to be deep enough to still hold the change you were looking for
 * after the noise around it, and shallow enough not to grow without bound.
 */
private const val CAPACITY = 300

/**
 * What the settings observer saw, in the shape you need to write it into a profile.
 *
 * The observer used to say only that *something* under System, Secure or Global had changed,
 * in a notification that was replaced by the next change a moment later. That is enough to
 * know an app is touching settings and useless for finding out which - which was the entire
 * reason to run it.
 *
 * An object rather than an injected singleton, matching [SettingsObservationGate]: the writer
 * is a foreground service and the reader is a settings screen in another module, and neither
 * has a natural place to hold the other's instance.
 *
 * In memory only, and deliberately. The window that matters is "while the observer is
 * running", the process stays alive for exactly that long because a foreground service holds
 * it up, and writing every settings change to disk would mean IO on a callback that fires in
 * bursts. A log that survives the service being stopped would also be a log describing a
 * device that has since moved on.
 */
object SettingsChangeLog {

    /** Which of Android's three settings tables the key lives in. */
    enum class Table { System, Secure, Global, Unknown }

    /**
     * One observed change, carrying everything the "Add setting" form asks for.
     *
     * [previousValue] is what this log last saw for the same key rather than what the setting
     * held before the app started, so the first sighting of a key has none. That is still the
     * useful half: a profile needs a value to apply and a value to put back, and a change
     * caught in the act gives you both ends of it.
     */
    data class Entry(
        val table: Table,
        val label: String,
        val key: String,
        val previousValue: String?,
        val value: String?,
    )

    private val _entries = MutableStateFlow<List<Entry>>(emptyList())

    /** Newest first, because the change you just made is the one you are looking for. */
    val entries: StateFlow<List<Entry>> = _entries.asStateFlow()

    fun record(table: Table, key: String, value: String?) {
        _entries.update { current ->
            val previous = current.firstOrNull { it.table == table && it.key == key }

            // A settings write that does not change the value still notifies observers, and
            // some of them fire several times for one change. Recording those would push the
            // interesting line off the end of the log with copies of itself.
            if (previous != null && previous.value == value) return@update current

            val entry = Entry(
                table = table,
                label = labelFor(key),
                key = key,
                previousValue = previous?.value,
                value = value,
            )

            (listOf(entry) + current).take(CAPACITY)
        }
    }

    fun clear() {
        _entries.value = emptyList()
    }

    /**
     * A readable name for a settings key, which Android does not provide one of.
     *
     * `adb_wifi_enabled` becomes `Adb wifi enabled`. Not a translation and not a lookup
     * table - it is a starting point for the Label field on the form, which is the user's to
     * name anyway.
     */
    private fun labelFor(key: String): String = key
        .replace('_', ' ')
        .trim()
        .replaceFirstChar { it.uppercase() }
}
