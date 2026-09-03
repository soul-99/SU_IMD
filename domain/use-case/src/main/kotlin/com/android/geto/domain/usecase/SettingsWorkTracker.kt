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
 * Whether *anything* is currently hiding or reverting settings, whoever started it.
 *
 * The Hide settings tile shows a state rather than firing an action, and the state it shows is
 * the **result**. Between a press and its result there is nothing to look at: the shade
 * collapses, ten seconds pass while Shizuku comes up, and a tile still reading the way it did
 * before invites a second press at the worst possible moment. This is what lets it read as busy
 * instead - the platform draws `STATE_UNAVAILABLE` dimmed and refuses the tap for us.
 *
 * **It used to cover only the tile's own press, and that was too narrow.** A hide or a revert
 * can begin from a dozen places the tile knows nothing about: IMD+ noticing a watched app, a
 * launch from inside IMD or from one of its pinned shortcuts, the revert notification, a
 * Tasker intent, the services manager. During any of those the device is mid-change, and a tile
 * press landing in the middle would start a second hide or revert over the top of the first.
 * The tile is now unavailable for all of them.
 *
 * **Signalled from the use cases rather than from the callers**, which is the whole reason this
 * works. There are around eighteen call sites that start a hide or a revert and only four use
 * cases underneath them — [ApplySettingsToHideUseCase], [ApplyAppSettingsUseCase],
 * [RevertToDefaultUseCase] and [RevertAppSettingsUseCase]. Wrapping the callers would have meant
 * eighteen chances to forget one, and a nineteenth caller added later would silently not be
 * covered. Wrapping the use cases means a path cannot start work without saying so.
 *
 * IMD+ wraps `AutoHideRunner.run` as well, on top of the use case inside it: an IMD+ run
 * force-stops the app and can spend the whole Shizuku budget doing it *before* it reaches the
 * hide, and the author asked for the tile to be unavailable while IMD+ is starting, not only
 * while it is writing settings. That overlap is exactly why this is a count.
 *
 * **A count rather than a flag**, for the same reason [ShizukuStartTracker] is one: these
 * genuinely nest — an IMD+ revert is a [RevertToDefaultUseCase] inside an
 * `AutoHideRunner.revert` - and the inner one finishing must not clear the outer one's claim.
 *
 * **In memory, and that is the safe direction.** If the process dies mid-run this resets to
 * zero and the tile is pressable again — which is right, because the run it was waiting on died
 * with the process. A flag persisted to disk would survive the death and leave the tile
 * permanently unpressable with nothing left running to clear it.
 */
@Singleton
class SettingsWorkTracker @Inject constructor() {
    private val running = MutableStateFlow(0)

    private val hiding = MutableStateFlow(0)

    private val unhiding = MutableStateFlow(0)

    /** True while at least one hide or revert is in flight. */
    val inFlight: Flow<Boolean> = running.map { it > 0 }.distinctUntilChanged()

    /**
     * Which way the work in flight is going, or null when nothing is running.
     *
     * Separate from [inFlight] rather than replacing it, because the two answer different
     * questions and one of them can be answered when the other cannot. The tile only needs to
     * know that *something* is happening; the settings manager names it out loud, and a screen
     * that says "hiding" while a revert runs would be worse than one that says nothing.
     *
     * **Null is a real state, not just idle.** A press claims this tracker before it reads which
     * way it is about to go — see the note on [begin] — so there is a short window where work is
     * genuinely in flight with no direction yet decided. Callers must render that as "busy
     * without a name" rather than assuming a default.
     *
     * Hiding wins if both counts are somehow up at once. That should not happen, and if it ever
     * does the honest thing is to name the more surprising of the two.
     */
    val work: Flow<SettingsWorkKind?> = combine(hiding, unhiding) { hidingNow, unhidingNow ->
        when {
            hidingNow > 0 -> SettingsWorkKind.Hiding
            unhidingNow > 0 -> SettingsWorkKind.Unhiding
            else -> null
        }
    }.distinctUntilChanged()

    /**
     * The same answer as a plain read, for the one place that cannot wait for a flow.
     *
     * `onClick` has to decide now: the platform will not deliver a tap on an unavailable tile,
     * but the state it is *drawn* in and the state it is *in* can be a frame apart, and the one
     * press that must never get through twice is this one.
     */
    val inFlightNow: Boolean
        get() = running.value > 0

    /**
     * Run [block] with the tile held unavailable.
     *
     * Preferred over [begin] and [end] by hand: the release is the part that matters, and a
     * `finally` that is written once here cannot be the one somebody forgets. A hide that threw
     * without releasing would leave the tile dimmed until the process restarted.
     */
    suspend fun <T> track(kind: SettingsWorkKind? = null, block: suspend () -> T): T {
        begin(kind = kind)

        try {
            return block()
        } finally {
            end(kind = kind)
        }
    }

    /**
     * Claims the tracker, optionally saying which way the work is going.
     *
     * ⚠ **The kind is optional on purpose, and the one caller that omits it is not an
     * oversight.** The Hide tile claims this before it reads whether it is about to hide or to
     * unhide, so that the tile is drawn unavailable from the press rather than from the write.
     * It genuinely does not know yet. A moment later the use case underneath it claims again
     * *with* a kind, and [work] starts naming it.
     *
     * ⚠ **An [end] must be passed the same kind as its [begin]**, or the counters drift and a
     * direction is left standing with nothing running. [track] is the reason to prefer it over
     * calling these by hand.
     */
    fun begin(kind: SettingsWorkKind? = null) {
        running.update { it + 1 }

        counterFor(kind = kind)?.update { it + 1 }
    }

    fun end(kind: SettingsWorkKind? = null) {
        // Floored at zero so an unbalanced end cannot drive this negative and leave the tile
        // stuck as unavailable forever. The same applies to the per-direction counts, where the
        // cost of drifting below zero would be a settings manager stuck reading "please wait".
        running.update { (it - 1).coerceAtLeast(0) }

        counterFor(kind = kind)?.update { (it - 1).coerceAtLeast(0) }
    }

    private fun counterFor(kind: SettingsWorkKind?): MutableStateFlow<Int>? = when (kind) {
        SettingsWorkKind.Hiding -> hiding
        SettingsWorkKind.Unhiding -> unhiding
        null -> null
    }
}

/**
 * Which way a piece of settings work is going.
 *
 * Top level rather than nested inside [SettingsWorkTracker] for a mundane reason worth writing
 * down: `check16_when` cannot read an indented enum — it needs the closing brace at column 0 —
 * and this project has already moved one declaration out of a class for exactly that.
 */
enum class SettingsWorkKind {
    Hiding,
    Unhiding,
}
