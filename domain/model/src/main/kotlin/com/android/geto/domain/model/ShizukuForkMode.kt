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
 * Which family of Shizuku fork the start-service broadcast is aimed at.
 *
 * The families do not share a contract. thedjchi's fork listens for a broadcast carrying
 * an "auth" token copied out of its own *View intents* screen; Shevery and the forks that
 * grew alongside it expose a start action with no token at all. Neither complains when it
 * receives the other's shape — the broadcast is simply ignored — so the user names the
 * family and the fields follow from it, rather than the app guessing.
 *
 * [Unset] exists because there is no safe default. Guessing produces the one outcome worth
 * avoiding: a toggle that looks configured and silently does nothing.
 */
enum class ShizukuForkMode {
    Unset,
    Thedjchi,
    Other,
    ;

    /** Only thedjchi's fork authenticates the broadcast. */
    val requiresAuthKey: Boolean get() = this == Thedjchi
}

/**
 * Whether enough has been filled in for a start broadcast to be worth sending.
 *
 * One definition for the switch that gates the feature, the automatic restart on revert
 * and the manual re-enable button, so the three can never disagree about what "set up"
 * means. The auth key is required only where the chosen fork actually reads it.
 */
val UserData.isShizukuConfigured: Boolean
    get() = shizukuForkMode != ShizukuForkMode.Unset &&
        shizukuPackageName.isNotBlank() &&
        shizukuStartAction.isNotBlank() &&
        (!shizukuForkMode.requiresAuthKey || shizukuAuthKey.isNotBlank())
