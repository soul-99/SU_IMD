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

import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.update
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Why Shizuku is being waited on, so the spinner can say so.
 *
 * [StartShizuku] is the plain case and the one that was missing: a revert that puts the Shizuku
 * service back without touching overlay access spends the same wait as any other start, and
 * used to spend it either in silence or - worse - under a spinner naming "Display over other
 * apps", which that revert is not touching at all.
 */
enum class OverlayStart { Hide, Restore, StopShizuku, StartShizuku }

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

    private val overlayHideAttempts = MutableStateFlow(0)

    private val overlayRestoreAttempts = MutableStateFlow(0)

    // Stopping has its own wait, and its own spinner: by the time it runs the overlay work
    // is done, so nothing else is on screen to explain the pause.
    private val shizukuStopAttempts = MutableStateFlow(0)

    // The plain start: Shizuku being brought up for its own sake rather than as a step on the
    // way to writing overlay AppOps. Counted separately so the spinner can say the plain
    // thing instead of naming a setting this run is not touching.
    private val shizukuStartAttempts = MutableStateFlow(0)

    val starting: Flow<Boolean> = attempts.map { it > 0 }.distinctUntilChanged()

    /**
     * Narrower than [starting]: only the starts made on the way to changing overlay AppOps,
     * and which way they are going.
     *
     * A launch has nowhere to report a ten second wait except over the app it is about to
     * open, so it needs to know that *this* start is the one holding it up - a restart
     * triggered from Settings is the same ten seconds and must not put a dialog over an
     * unrelated screen. The direction matters too: the same wait precedes hiding overlay
     * access and giving it back, and a spinner saying "to hide" during a revert is simply
     * wrong.
     *
     * Hiding wins when both are somehow in flight, because a hide is what holds up a launch
     * the user is waiting on.
     */
    val overlayStart: Flow<OverlayStart?> =
        combine(
            overlayHideAttempts,
            overlayRestoreAttempts,
            shizukuStopAttempts,
            shizukuStartAttempts,
        ) { hiding, restoring, stopping, starting ->
            when {
                hiding > 0 -> OverlayStart.Hide
                restoring > 0 -> OverlayStart.Restore
                // Last of the overlay reasons, because it happens after the overlay work in
                // the same launch: while both are somehow in flight the overlay wait is the
                // one that came first and the one the spinner is already describing.
                stopping > 0 -> OverlayStart.StopShizuku
                // Lowest priority of all, and deliberately: it names no setting, so any of
                // the three above is a more useful thing to be told.
                starting > 0 -> OverlayStart.StartShizuku
                else -> null
            }
        }.distinctUntilChanged()

    fun begin() {
        attempts.update { it + 1 }
    }

    fun beginOverlay(reason: OverlayStart) {
        counterFor(reason).update { it + 1 }
    }

    fun endOverlay(reason: OverlayStart) {
        counterFor(reason).update { (it - 1).coerceAtLeast(0) }
    }

    private fun counterFor(reason: OverlayStart) = when (reason) {
        OverlayStart.Hide -> overlayHideAttempts
        OverlayStart.Restore -> overlayRestoreAttempts
        OverlayStart.StopShizuku -> shizukuStopAttempts
        OverlayStart.StartShizuku -> shizukuStartAttempts
    }

    fun end() {
        // Floored at zero so an unbalanced end — a crash between begin and finally, say —
        // cannot drive this negative and leave the spinner stuck on forever.
        attempts.update { (it - 1).coerceAtLeast(0) }
    }
}
