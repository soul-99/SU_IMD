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

    /**
     * The inverse of [idOf], for a caller holding a recorded id and nothing else.
     *
     * v3's `Revert to default` needs it: a per-app profile can record any setting by key, and
     * the ones the configured defaults do not drive have to be written back from the record
     * alone — there is no `AppSetting` to read the type off, because the profile that made it
     * is not what this revert is walking.
     *
     * Null for [SHIZUKU_STOPPED_ID] and [OVERLAY_HIDDEN_ID], whose first field is deliberately
     * not the name of any [SettingType] so no real row can collide with them. A caller that
     * treated those as settings would try to write a row called `shizuku_stopped`.
     */
    fun settingOf(id: String): Pair<SettingType, String>? {
        val separator = id.indexOf(UNIT)

        if (separator <= 0) return null

        val typeName = id.substring(0, separator)

        val type = SettingType.entries.firstOrNull { it.name == typeName } ?: return null

        return type to id.substring(separator + 1)
    }

    /**
     * A reserved id — not a real setting — under which a per-app record notes that this app
     * stopped the Shizuku service, so its revert (and only its revert) starts it again.
     *
     * It lives in the same per-app map as the settings snapshots so it is cleared together
     * with them on revert, which is what keeps the memory from cumulating: once an app's
     * record is dropped, its claim on restarting Shizuku is gone. Only the presence of this id
     * matters — the value is a constant.
     *
     * Deliberately *not* built from [idOf]: its first field is not the name of any
     * [SettingType], so no real row — including the profile's own `shizuku_service` marker
     * row, which would otherwise produce this very string — can ever collide with it. The
     * write-loop filters stay as well; this is the half that does not depend on remembering
     * them.
     */
    val SHIZUKU_STOPPED_ID: String = "IMD" + UNIT + "shizuku_stopped"

    /**
     * The same idea for overlay access: a per-app note that *this* app's launch is the one
     * that withdrew "Display over other apps", so its revert (and only its revert) gives it
     * back.
     *
     * Without it, a second app launched while overlay access was already withdrawn - which
     * hides nothing, because there is nothing left to hide - would still restore it on revert,
     * undoing the first app's hide while the first app is very much still open. The record is
     * only written when the launch actually did the withdrawing, so an app that found the work
     * already done has no claim on undoing it.
     *
     * Cleared with the rest of that app's record on revert, so the claim cannot outlive the
     * launch that earned it. Built the same non-colliding way as [SHIZUKU_STOPPED_ID].
     */
    val OVERLAY_HIDDEN_ID: String = "IMD" + UNIT + "overlay_hidden"

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
     * Adds readings for settings that have no record yet, and leaves existing ones alone.
     *
     * The first apply since the last revert is the one that saw the device untouched, so
     * it is the only one whose readings mean anything. Launching the same app a second
     * time — from a shortcut, say — reads back the values this app itself just wrote, and
     * overwriting with those is how "developer options were off beforehand" turns into
     * "developer options were off, so leave them off" and the revert quietly stops working.
     *
     * Per setting rather than per app, so a setting added to the profile between launches
     * still gets its own first reading.
     *
     * This is the same rule [AccessibilityServicePlan.hold] follows for services, and for
     * the same reason.
     */
    fun merge(
        existing: Map<String, String?>,
        measured: Map<String, String?>,
    ): Map<String, String?> = existing + measured.filterKeys { it !in existing }

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
