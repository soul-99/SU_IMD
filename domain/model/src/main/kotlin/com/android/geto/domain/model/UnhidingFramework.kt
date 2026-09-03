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
 * How a hide is undone.
 *
 * The other half of the old [NotificationFunction], and the half that decides which
 * notification is posted after a hide.
 *
 * * [Memory] restores each setting to the value it actually held before IMD switched it off,
 *   and touches nothing else. A setting the user had never turned on before the hide stays
 *   off afterwards.
 * * [RevertToDefault] drives every target named in *Revert to default configuration* to the
 *   state configured there, whatever was true beforehand.
 *
 * ⚠ **`Revert to default` remains reachable under both**, from the tile, the shortcut, the
 * settings manager, the Favourites button and its intent — it is a named function, not a
 * mode. Under either framework it now **flushes pending reverts first**, because a per-app
 * profile may have hidden something the defaults list does not name, and driving the defaults
 * alone would leave that setting hidden with nothing left to undo it.
 */
enum class UnhidingFramework {
    /** Put back exactly what was there, and only what IMD switched off. */
    Memory,

    /** Drive the configured defaults, regardless of what was there. */
    RevertToDefault,
    ;

    companion object {
        /**
         * What an install that has never opened the picker gets.
         *
         * [Memory], reversing the v1.6 recommendation at the author's instruction: a revert
         * to configured defaults can switch **on** a setting the user had never had on before
         * the hide, and the author does not want the app touching settings it did not hide.
         *
         * The v1.6 objection — that the memory function's notification is the only way back,
         * and a notification can be swiped away, culled by a launcher or lost to a battery
         * optimiser — is answered rather than ignored: the Hide settings QS toggle flushes
         * every pending revert at once without needing a notification at all, and the
         * `Unhide settings and services` intent does the same from an automation.
         */
        val Default: UnhidingFramework = Memory
    }
}
