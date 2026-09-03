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
 * What gets switched off when any app is launched.
 *
 * One configuration for the whole device, and the counterpart to [RevertDefaults]: this
 * says what to hide on the way in, that one says what to put back on the way out. Together
 * they replace having to write a profile for every app before any of them can be opened —
 * which was the single largest thing standing between installing this app and using it,
 * because the settings a locked-down app objects to are the same whichever app it is.
 *
 * Per-app profiles still exist and are still the more precise tool; they are what the
 * memory notification function uses. This is the answer for everyone who wants the common
 * case to work without configuring anything.
 *
 * Shizuku is one of the targets, stopped on the way in through its fork's stop intent — and,
 * when the fork has no stop intent, by briefly cycling USB debugging to drop the transport it
 * rides on. Stopping it before a launch is what keeps a fork's watchdog from flagging the app.
 * It is opt-in because it only does anything once Shizuku is configured, and, like overlay
 * access, is handled on its own terms rather than through the generic hide loop.
 */
object SettingsToHide {
    private const val SEPARATOR = '='
    private const val ON = "1"
    private const val OFF = "0"

    /**
     * The targets, in the order the dialog lists them. Reusing [ManualRevertTarget] rather
     * than a second enum keeps one vocabulary of targets across both configurations, so the
     * dialogs and the audits line up. Shizuku and Display over other apps are the two that are
     * not plain settings rows: both are stopped/hidden on their own terms (see the hide loop),
     * not written through the secure-settings wrapper.
     */
    val Targets: List<ManualRevertTarget> = listOf(
        ManualRevertTarget.DeveloperSettings,
        ManualRevertTarget.UsbDebugging,
        ManualRevertTarget.WirelessDebugging,
        ManualRevertTarget.AccessibilityServices,
        ManualRevertTarget.Shizuku,
        ManualRevertTarget.DisplayOverOtherApps,
    )

    /**
     * Nothing, on a fresh install.
     *
     * Every target here switches something off on the user's device, and this app is handed
     * `WRITE_SECURE_SETTINGS` to do it. A default that arrives already ticked means an
     * install nobody has configured is changing debugging settings the first time an app is
     * launched from it — before its owner has read what those four rows are, and without
     * ever having said yes to any of them. So: nothing, until somebody says what.
     *
     * The launch path refuses to run with nothing ticked rather than launching and doing
     * nothing, and the setup page's first step is where to tick them, so an unconfigured
     * install says what it needs instead of quietly behaving like a launcher.
     *
     * Only for installs that start here. [LegacyDefault] is what an install from before this
     * change has been behaving as, and MigrateRevertDefaultsUseCase writes that for them:
     * a default is a starting point, never a decision made on somebody's behalf after the
     * fact.
     */
    val Default: Map<ManualRevertTarget, Boolean> = Targets.associateWith { false }

    /**
     * What every install before v2.1 behaved as when it had never opened the dialog: the four
     * settings backed by `WRITE_SECURE_SETTINGS` on, overlay access and stopping the Shizuku
     * service off.
     *
     * Kept as its own constant so the migration that preserves it cannot drift when [Default]
     * changes again. Nothing reads this except that migration.
     */
    val LegacyDefault: Map<ManualRevertTarget, Boolean> = Targets.associateWith {
        it != ManualRevertTarget.DisplayOverOtherApps && it != ManualRevertTarget.Shizuku
    }

    /**
     * The order to switch things off in — the reverse of the order to switch them on in.
     *
     * [RevertToDefaultUseCase] works down the enum because each target sets up the next:
     * USB debugging is meaningless with developer options off. Coming back the other way
     * the dependency runs the other way too, so developer options must go last, after the
     * things that live underneath it have already been dealt with.
     */
    val HideOrder: List<ManualRevertTarget> = Targets.reversed()

    fun encode(states: Map<ManualRevertTarget, Boolean>): List<String> =
        Targets.map { target ->
            target.name + SEPARATOR + if (states[target] == true) ON else OFF
        }

    /**
     * Unknown names are dropped and missing ones fall back to [Default], so neither a
     * downgrade nor a target added in a later version can poison the stored configuration.
     */
    fun decode(encoded: List<String>): Map<ManualRevertTarget, Boolean> {
        if (encoded.isEmpty()) return Default

        val byName = Targets.associateBy { it.name }

        val stored = encoded.mapNotNull { entry ->
            val at = entry.indexOf(SEPARATOR)

            if (at <= 0) return@mapNotNull null

            val target = byName[entry.substring(0, at)] ?: return@mapNotNull null

            target to (entry.substring(at + 1) == ON)
        }.toMap()

        return Targets.associateWith { stored[it] ?: Default.getValue(it) }
    }
}
