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
     * Nothing, on a fresh install - the mirror of [SettingsToHide.Default].
     *
     * The two configurations are one decision made twice: what this app switches off on the
     * way in, and what it switches back on on the way out. An install that hides nothing has
     * nothing to put back, so a restore ticked in advance would be a switch that does nothing
     * and still has to be explained - and the moment it did do something, it would be this
     * app switching a debugging surface *on* for somebody who never asked.
     *
     * That asymmetry is the whole argument. Failing to restore something leaves the device
     * more closed than its owner keeps it, which they can see and fix in one screen. Restoring
     * something they keep off leaves it more open, on a schedule they did not choose, possibly
     * from a tile with nothing on screen to say so.
     *
     * A default, not a policy. The dialog exists precisely so this can be overridden, and
     * once saved the stored answer wins for every target.
     */
    val Default: Map<ManualRevertTarget, Boolean> = ManualRevertTarget.entries.associateWith { false }

    /**
     * The v1.6.6 default: accessibility services alone.
     *
     * What an install that predates v2.1 has been behaving as, and the only thing
     * MigrateRevertDefaultsUseCase ever writes. Accessibility services were the one target on,
     * because the app switched them off itself, they are not a debugging surface, and leaving
     * them off silently breaks a screen reader.
     *
     * Frozen here rather than tracking [Default], so a later change to what a fresh install
     * starts with cannot quietly rewrite what an existing install was promised.
     */
    val NarrowedV166: Map<ManualRevertTarget, Boolean> = mapOf(
        ManualRevertTarget.DeveloperSettings to false,
        ManualRevertTarget.UsbDebugging to false,
        ManualRevertTarget.WirelessDebugging to false,
        ManualRevertTarget.AccessibilityServices to true,
        ManualRevertTarget.Shizuku to false,
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
