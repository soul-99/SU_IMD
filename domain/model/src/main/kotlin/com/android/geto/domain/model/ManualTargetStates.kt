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
) {
    fun isEnabled(target: ManualRevertTarget): Boolean = enabled[target] == true
}
