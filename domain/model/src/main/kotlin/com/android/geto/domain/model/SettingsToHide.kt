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
 * because the settings a locked-down app objects to are the same four whichever app it is.
 *
 * Per-app profiles still exist and are still the more precise tool; they are what the
 * memory notification function uses. This is the answer for everyone who wants the common
 * case to work without configuring anything.
 *
 * Shizuku is deliberately not one of the targets. It is not a setting an app reads, and
 * hiding it is Shizuku's own job — its "Hide Shizuku from other apps" switch. What does
 * happen is that switching USB debugging off takes the Shizuku service down with it, which
 * is why the configuration dialog says so next to that row rather than offering a toggle
 * that cannot do what its name would imply.
 */
object SettingsToHide {
    private const val SEPARATOR = '='
    private const val ON = "1"
    private const val OFF = "0"

    /**
     * The four an app can actually detect, in the order the dialog lists them.
     *
     * [ManualRevertTarget] carries a fifth, Shizuku, which belongs to reverting and not to
     * hiding; taking a subset here rather than adding a second enum keeps one vocabulary
     * of targets across both configurations, so the dialogs and the audits line up.
     */
    val Targets: List<ManualRevertTarget> = listOf(
        ManualRevertTarget.DeveloperSettings,
        ManualRevertTarget.UsbDebugging,
        ManualRevertTarget.WirelessDebugging,
        ManualRevertTarget.AccessibilityServices,
    )

    /**
     * All four, unlike [RevertDefaults.Default].
     *
     * The two defaults differ because the risks are not symmetrical. Switching something
     * *on* that the user keeps off is a change to their device they never asked for, so
     * reverting starts conservative. Switching something off before launching an app is
     * the entire point of the app, is undone by the very next revert, and hiding only some
     * of the four is the case that fails in a way nobody can diagnose: the app still sees
     * developer mode and still refuses to run.
     */
    val Default: Map<ManualRevertTarget, Boolean> = Targets.associateWith { true }

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
