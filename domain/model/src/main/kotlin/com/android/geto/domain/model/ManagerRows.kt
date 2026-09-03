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
 * Which rows the settings manager draws, from the author's "Settings manager options".
 *
 * ⚠ **Shown, not managed, and the distinction is the whole of this file.** A row unticked here is
 * not switched off, not left out of a hide, and not skipped by "Revert to default" — it is simply
 * not drawn on that one card. Everything the engine does still walks [ManualRevertTarget.entries].
 * The one behaviour that follows the drawing is the manager's own All off / All on pill, and only
 * because it takes its list from what the card drew rather than from the enum — which is the
 * author's instruction that it *"only try to manage the displayed toggles"*, already true by
 * construction and now load-bearing.
 *
 * ⚠ **A state per target, not a list of the ones to show**, and this is [RevertDefaults]'s
 * reasoning rather than a new one: an absent name could not tell *"the user hid this row"* apart
 * from *"never configured"*, and those two must behave differently. Storing a list of shown rows
 * would make "unticked everything" and "never opened the dialog" the same empty list, and the
 * second has to mean every row.
 *
 * That case cannot arise through the dialog — it refuses to save with nothing ticked, at the
 * author's instruction — but it can arise through a cleared preference, an older install, or a
 * hand-edited store, and the encoding is what makes the answer to it unambiguous rather than
 * merely unlikely.
 */
object ManagerRows {
    private const val SEPARATOR = '='

    private const val ON = "1"

    private const val OFF = "0"

    /**
     * Every row, on a fresh install.
     *
     * The manager has always drawn all six and this preference exists to take some away, so the
     * default is what the app did before it existed. An install that never opens the dialog sees
     * no change at all.
     */
    val Default: Map<ManualRevertTarget, Boolean> = ManualRevertTarget.entries.associateWith { true }

    /**
     * ⚠ **Every target, every time, in enum order** — not only the ones switched on.
     *
     * The store is cleared and refilled on each save, so a target left out here would be a target
     * with no stored answer on the next read, which [decode] resolves to [Default]. A row the user
     * unticked would come back on its own, which is the one thing this preference exists to stop.
     */
    fun encode(states: Map<ManualRevertTarget, Boolean>): List<String> =
        ManualRevertTarget.entries.map { target ->
            target.name + SEPARATOR + if (states[target] == true) ON else OFF
        }

    /**
     * Back to a map, with anything unreadable falling to [Default] rather than to off.
     *
     * ⚠ **Falling back to *shown* is the safe direction.** A name this build does not recognise —
     * a target renamed, or a store written by a newer version — must not silently remove a switch
     * from the only screen that can put developer options back once they are off. Failing to hide
     * a row is visible and one dialog away from being fixed; hiding one nobody asked to hide takes
     * away the control that would fix it.
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

    /**
     * Whether a set of answers may be saved.
     *
     * ⚠ **At least one, at the author's instruction.** A manager with no rows is a card with a
     * title and two buttons, and — more to the point — the screen someone reaches for *because*
     * developer options are already off would have nothing on it to switch them back on with.
     */
    fun isSavable(states: Map<ManualRevertTarget, Boolean>): Boolean = states.containsValue(true)
}
