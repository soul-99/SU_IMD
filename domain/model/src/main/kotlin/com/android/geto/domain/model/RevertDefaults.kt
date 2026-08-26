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
 * The state each target should be left in when "Revert to default" runs.
 *
 * Deliberately a state per target rather than a set of things to switch on. "Revert to
 * default" means putting the device back the way this user keeps it, and for some people
 * that includes leaving wireless debugging *off* — a set of things to enable cannot say
 * that, and would quietly turn on something they had never used.
 *
 * Stored as one encoded entry per target rather than as a list of enabled names, for the
 * same reason: an absent name would be ambiguous between "off" and "not configured yet",
 * and those need different behaviour.
 *
 * Every target is independent. An earlier version tied Shizuku to USB debugging, reasoning
 * that the service runs over ADB — but which transport it needs depends on how Shizuku was
 * started, and Shizuku re-enables the right one itself. Deciding that on the user's behalf
 * was overriding a choice they had deliberately made.
 */
object RevertDefaults {
    private const val SEPARATOR = '='
    private const val ON = "1"
    private const val OFF = "0"

    /**
     * What the dialog starts out with when it has never been saved.
     *
     * Accessibility services only, as of v1.6.6, and the reasoning is about safety rather
     * than convenience. Every other target here is a debugging surface: developer settings,
     * USB debugging, wireless debugging, and the Shizuku service that rides on one of them.
     * Switching those back on automatically means a Revert can leave a device more open
     * than the person pressing the button realised, on a schedule they did not choose -
     * including a Revert fired from a tile with nothing on screen to report what happened.
     *
     * Accessibility services are the exception because the app switched them off itself,
     * they are not a debugging surface, and leaving them off silently breaks a screen
     * reader. Restoring what this app turned off is the whole promise of the button.
     *
     * Earlier versions also defaulted USB debugging and Shizuku to on. v1.6.6 resets any
     * install carrying that forward - see MigrateRevertDefaultsUseCase - and tells the user
     * it has done so, because a default quietly changing underneath somebody is worse than
     * the original default.
     *
     * A default, not a policy. The dialog exists precisely so this can be overridden, and
     * once saved the stored answer wins for every target including this one.
     */
    val Default: Map<ManualRevertTarget, Boolean> = mapOf(
        ManualRevertTarget.DeveloperSettings to false,
        ManualRevertTarget.UsbDebugging to false,
        ManualRevertTarget.WirelessDebugging to false,
        ManualRevertTarget.AccessibilityServices to true,
        ManualRevertTarget.Shizuku to false,
        // Off to match SettingsToHide.Default. Restoring only ever puts back what IMD
        // itself switched off, so leaving it on would be safe in isolation — but hiding is
        // opt-in, and a restore configured on by default while nothing is ever hidden is a
        // switch that does nothing and still has to be explained. The pair is turned on
        // together, by someone who has decided they want overlay hiding.
        ManualRevertTarget.DisplayOverOtherApps to false,
    )

    fun encode(states: Map<ManualRevertTarget, Boolean>): List<String> =
        ManualRevertTarget.entries.map { target ->
            target.name + SEPARATOR + if (states[target] == true) ON else OFF
        }

    /**
     * Unknown names are dropped and missing ones fall back to [Default], so neither a
     * downgrade nor a target added in a later version can poison the stored configuration.
     */
    fun decode(encoded: List<String>): Map<ManualRevertTarget, Boolean> {
        if (encoded.isEmpty()) return Default

        val byName = ManualRevertTarget.entries.associateBy { it.name }

        val stored = encoded.mapNotNull { entry ->
            val at = entry.indexOf(SEPARATOR)

            if (at <= 0) return@mapNotNull null

            val target = byName[entry.substring(0, at)] ?: return@mapNotNull null

            target to (entry.substring(at + 1) == ON)
        }.toMap()

        return ManualRevertTarget.entries.associateWith { stored[it] ?: Default.getValue(it) }
    }
}
