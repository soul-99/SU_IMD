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
 * What to put in the Shizuku fields the moment a fork family is chosen.
 *
 * Everything here is a guess made from what is installed, and every guess is written into
 * an editable field rather than applied invisibly — the values differ between forks and
 * change between their releases, so the user has to be able to see and correct them.
 *
 * Matching is by app label rather than package name on purpose. The package is the thing
 * people change: stealth builds rename it, and a rename is the whole reason the field is
 * editable. The label survives that far more often.
 */
object ShizukuForkDefaults {
    const val SHIZUKU_LABEL = "Shizuku"
    const val SHEVERY_LABEL = "Shevery"

    /** thedjchi's fork keeps the action upstream Shizuku's package name implies. */
    const val THEDJCHI_ACTION = "moe.shizuku.privileged.api.START"

    /** Shevery moved the receiver under its manager package. */
    const val SHEVERY_ACTION = "moe.shizuku.manager.action.START_SERVER"

    /**
     * The package to preselect, or blank when nothing plausible is installed.
     *
     * [ShizukuForkMode.Other] prefers Shevery and falls back to Shizuku, because that mode
     * covers "Shevery and anything else that speaks a token-free start action" — if
     * Shevery itself is not here, a differently-named Shizuku build is the next best
     * guess. Blank is a valid answer: an empty field the user fills in beats a confidently
     * wrong package that makes the toggle look ready.
     */
    fun packageFor(mode: ShizukuForkMode, apps: List<InstalledAppData>): String = when (mode) {
        ShizukuForkMode.Unset -> ""
        ShizukuForkMode.Thedjchi -> apps.findByLabel(SHIZUKU_LABEL)
        ShizukuForkMode.Other -> apps.findByLabel(SHEVERY_LABEL).ifBlank {
            apps.findByLabel(SHIZUKU_LABEL)
        }
    }

    /**
     * The start action to preselect for [mode], given the label of whichever package is
     * selected.
     *
     * In [ShizukuForkMode.Other] an unrecognised label gets Shevery's action rather than
     * nothing: that mode's forks descend from it, so it is the likeliest of the two, and
     * the hint beside the field tells the user where to look when it is wrong.
     */
    fun actionFor(mode: ShizukuForkMode, selectedLabel: String?): String = when (mode) {
        ShizukuForkMode.Unset -> ""
        ShizukuForkMode.Thedjchi -> THEDJCHI_ACTION
        ShizukuForkMode.Other -> if (selectedLabel.matches(SHIZUKU_LABEL)) {
            THEDJCHI_ACTION
        } else {
            SHEVERY_ACTION
        }
    }

    private fun List<InstalledAppData>.findByLabel(label: String): String = firstOrNull { it.label.matches(label) }?.packageName.orEmpty()

    private fun String?.matches(label: String): Boolean = this?.trim().equals(label, ignoreCase = true)
}
