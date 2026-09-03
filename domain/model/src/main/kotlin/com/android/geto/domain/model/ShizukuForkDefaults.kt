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
     * The stock package names, used only as a second guess when no label matches.
     *
     * A label is the better first guess — see the note above — but it is also the thing a
     * translated or re-branded build changes, and a user who has one of these installed under
     * an unexpected name is exactly the user least able to type the right package in by hand.
     * So: label first, then this, then nothing.
     */
    const val SHIZUKU_PACKAGE = "moe.shizuku.privileged.api"

    const val SHEVERY_PACKAGE = "com.hamondev.shevery"

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
        // Unset still answers, because the picker now starts on a family rather than on
        // nothing: a fresh install should arrive with the field already filled if the app
        // is there to find.
        ShizukuForkMode.Unset, ShizukuForkMode.Thedjchi ->
            apps.findByLabel(SHIZUKU_LABEL).ifBlank { apps.findByPackage(SHIZUKU_PACKAGE) }

        // Shevery first and by both routes, then the Shizuku pair as a last resort: this
        // family covers "Shevery and anything else speaking a token-free start action", so a
        // differently-named Shizuku build is the next best guess when Shevery is not here.
        ShizukuForkMode.Other ->
            apps.findByLabel(SHEVERY_LABEL)
                .ifBlank { apps.findByPackage(SHEVERY_PACKAGE) }
                .ifBlank { apps.findByLabel(SHIZUKU_LABEL) }
                .ifBlank { apps.findByPackage(SHIZUKU_PACKAGE) }
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

    /**
     * The stop action that pairs with a configured start action.
     *
     * Derived rather than looked up. Both known families spell the pair the same way —
     * `…api.START` / `…api.STOP`, `…action.START_SERVER` / `…action.STOP_SERVER` — so
     * rewriting the word the user already gave us is right for a fork nobody here has
     * heard of, where a hardcoded table would simply be wrong.
     *
     * Only the last occurrence is rewritten, so a package that happens to contain "START"
     * earlier in the string is left alone. A start action with no "START" in it has no
     * derivable stop action, and blank is returned rather than a guess.
     */
    fun stopActionFor(startAction: String): String {
        val at = startAction.lastIndexOf(START)

        if (at < 0) return ""

        return startAction.substring(0, at) + STOP + startAction.substring(at + START.length)
    }

    /**
     * Which package the dialog's Shizuku shortcut should open.
     *
     * The configured package first — it is what the restart actually talks to, and on a
     * renamed install it is the only correct answer. Falling back to a label search covers
     * the case where the field was never filled in, which is exactly when someone is most
     * likely to be poking at the shortcut to find out what is installed.
     */
    fun launchPackageFor(configuredPackage: String, apps: List<InstalledAppData>): String {
        if (apps.any { it.packageName == configuredPackage }) return configuredPackage

        return apps.findByLabel(SHIZUKU_LABEL).ifBlank { apps.findByLabel(SHEVERY_LABEL) }
    }

    private const val START = "START"

    private const val STOP = "STOP"

    private fun List<InstalledAppData>.findByLabel(label: String): String = firstOrNull { it.label.matches(label) }?.packageName.orEmpty()

    private fun List<InstalledAppData>.findByPackage(packageName: String): String = firstOrNull { it.packageName == packageName }?.packageName.orEmpty()

    private fun String?.matches(label: String): Boolean = this?.trim().equals(label, ignoreCase = true)
}
