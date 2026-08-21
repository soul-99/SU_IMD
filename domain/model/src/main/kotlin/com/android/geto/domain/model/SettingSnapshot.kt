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
package com.android.geto.domain.model

/**
 * What each setting was actually set to just before an app's profile was applied.
 *
 * Upstream reverts to the value typed into the *Value on revert* box, which is a guess
 * made when the profile was written rather than a fact about the device. If developer
 * options were already off and a profile hides them, reverting switches them **on** —
 * leaving the device in a state the user never asked for. Recording the real value at
 * apply time and putting that back is the fix.
 *
 * Stored per target app as one string, because the preferences file is a proto and a map
 * of maps would need a nested message for no benefit. Settings values are arbitrary
 * strings, so the separators are ASCII control characters that cannot appear in a settings
 * key and are vanishingly unlikely in a value.
 */
object SettingSnapshot {
    private const val RECORD = '\u001E'
    private const val UNIT = '\u001F'

    /** Distinguishes "was unset" from "was empty", which revert has to treat differently. */
    private const val ABSENT = "\u0000"

    /** Uniquely identifies a setting: the same key can exist in more than one table. */
    fun idOf(settingType: SettingType, key: String): String = settingType.name + UNIT + key

    fun encode(values: Map<String, String?>): String = values.entries.joinToString(
        separator = RECORD.toString(),
    ) { (id, value) ->
        id + RECORD + (value ?: ABSENT)
    }

    fun decode(encoded: String): Map<String, String?> {
        if (encoded.isEmpty()) return emptyMap()

        val parts = encoded.split(RECORD)

        // Read in pairs; an odd tail means a truncated write, and half a pair is worse
        // than none at all — reverting to a value that was never recorded is the very bug
        // this exists to prevent.
        return (0 until parts.size - 1 step 2).associate { index ->
            parts[index] to parts[index + 1].takeIf { it != ABSENT }
        }
    }

    /**
     * What to write when reverting: the recorded value if there is one, otherwise the
     * value the user configured.
     *
     * A setting with no record falls back rather than being skipped — the profile may have
     * been applied by an older version, or the record may have been lost — and falling
     * back reproduces the old behaviour instead of doing nothing at all.
     */
    fun revertValue(
        recorded: Map<String, String?>,
        settingType: SettingType,
        key: String,
        configured: String,
    ): String {
        val id = idOf(settingType = settingType, key = key)

        if (!recorded.containsKey(id)) return configured

        return recorded[id] ?: configured
    }
}
