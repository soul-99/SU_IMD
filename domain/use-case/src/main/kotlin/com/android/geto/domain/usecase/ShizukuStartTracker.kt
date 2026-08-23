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
package com.android.geto.domain.usecase

import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.update

/**
 * Whether a Shizuku start attempt is in flight right now.
 *
 * Shared state rather than something the manager dialog owns, because the attempt often does
 * not start there. A revert — from the tile, the notification, a shortcut — can begin one
 * while the dialog is shut, and if the user opens the dialog during those ten seconds the
 * switch has to show what is actually happening rather than a stale "off".
 *
 * A count rather than a flag: revert-to-default and a manual toggle can overlap, and the
 * first of them finishing must not clear the spinner for the second.
 */
@Singleton
class ShizukuStartTracker @Inject constructor() {
    private val attempts = MutableStateFlow(0)

    val starting: Flow<Boolean> = attempts.map { it > 0 }.distinctUntilChanged()

    fun begin() {
        attempts.update { it + 1 }
    }

    fun end() {
        // Floored at zero so an unbalanced end — a crash between begin and finally, say —
        // cannot drive this negative and leave the spinner stuck on forever.
        attempts.update { (it - 1).coerceAtLeast(0) }
    }
}
