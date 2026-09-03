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
 * What the settings manager's rows are set to, and whether Shizuku's row can be used at all.
 *
 * [shizukuAvailable] is separate from the on/off value because "off" and "there is nothing
 * to switch" are different situations that need different UI, and conflating them produced
 * a real bug: with Shizuku uninstalled, a stale binder handle kept reporting the service as
 * alive, so the switch sat there showing "on" and refusing to move. A switch that lies
 * about the device is worse than no switch.
 */
data class ManualTargetStates(
    val enabled: Map<ManualRevertTarget, Boolean> = emptyMap(),
    val shizukuAvailable: Boolean = false,
    /**
     * Whether the chosen fork can be started and stopped by intent at all.
     *
     * False for Shevery, whose service follows the debugging transport instead. Separate from
     * [shizukuAvailable] because the two are different refusals: "IMD has not been told how to
     * reach Shizuku" is something the user can fix in settings, while "this fork has no
     * intents" is a permanent property of what they installed, and the row says so differently.
     */
    val shizukuSupportsIntents: Boolean = true,
    /**
     * Whether any accessibility service is selected for IMD to manage.
     *
     * With nothing selected the row has nothing to report on and nothing to switch: IMD is
     * holding no service down, so it reads off and refuses to be moved rather than sitting on
     * an "on" that describes the device instead of anything this app is doing.
     */
    val accessibilityManaged: Boolean = false,
    /**
     * Whether any app is selected for IMD to withdraw "Display over other apps" from.
     *
     * The same distinction as [accessibilityManaged], and it matters for the same reason: with
     * nothing selected the row is not describing something IMD is doing, it is describing the
     * device - and a switch that reports the device while pretending to control it is the one
     * shape of control this app has already been bitten by. Nothing selected reads off and
     * refuses to move, and says which screen to go to.
     */
    val overlayManaged: Boolean = false,
) {
    fun isEnabled(target: ManualRevertTarget): Boolean = enabled[target] == true
}
