/*
 *
 *   Copyright 2026 soul_99 (suIMD)
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
package com.android.geto.designsystem.theme

import androidx.compose.runtime.Immutable
import androidx.compose.runtime.staticCompositionLocalOf
import com.android.geto.domain.model.DEFAULT_FADE_DP
import com.android.geto.domain.model.DEFAULT_RADIUS_DP
import com.android.geto.domain.model.DEFAULT_TINT_PERCENT

/**
 * Everything the author's "Progressive UI blur" is, as one value.
 *
 * ⚠ **Published through the theme rather than passed down — r20.** Three things read these
 * numbers and they are nowhere near each other: the page edges (`Modifier.progressiveEdgeBlur`),
 * the settings manager's frosted window (`DialogContainer`), and the settings row that edits them.
 * A dialog is a window of its own with no view of user data; a design-system modifier has no
 * business taking a view model. The theme is the one thing all three already sit inside.
 *
 * ⚠ **Plain `Int`s in the units the user sees**, not `Dp` and not fractions. These come off three
 * sliders and go into a proto as they are — a dp of radius, a percent of tint, a dp of ramp — and
 * a value that means the same thing in the store, on the slider and in the draw is a value that
 * cannot be converted wrongly on the way between them.
 *
 * ⚠ **The defaults and the ranges are in `:domain:model`, not here.** The datastore resolves an
 * install that has never opened the dialog and must not depend on a UI module; `:domain:model`
 * depends on nothing and everything depends on it. [Default] is what an unwritten preference
 * resolves to, built from those.
 */
@Immutable
data class GetoBlurSettings(
    /** The author's switch. False means the shadow fade, not the absence of a treatment. */
    val enabled: Boolean = false,
    /**
     * How hard the blur is, in dp.
     *
     * The author's **P2** from the r10 template. Applied to the page bands as it stands and to the
     * frosted window at [WINDOW_RADIUS_FACTOR] times this — see that constant for why they differ.
     */
    val radiusDp: Int = DEFAULT_RADIUS_DP,
    /**
     * How dark the band gets at full strength, as a percentage.
     *
     * Also how solid the frosted window's card is: the same word means the same thing in both
     * places, which is what makes one slider honest.
     */
    val tintPercent: Int = DEFAULT_TINT_PERCENT,
    /** How long the ramp is once the solid part of a band ends, in dp. Pages only. */
    val fadeDp: Int = DEFAULT_FADE_DP,
) {
    /** [tintPercent] as the fraction a `Color.copy` wants. */
    val tintAlpha: Float get() = tintPercent.coerceIn(0, HUNDRED) / HUNDRED.toFloat()

    companion object {
        val Default = GetoBlurSettings()
    }
}

/** See [GetoBlurSettings]. Defaulted, so a preview outside a [GetoTheme] draws the ordinary thing. */
val LocalBlurSettings = staticCompositionLocalOf { GetoBlurSettings.Default }

/**
 * How much harder the frosted window blurs than a page band, for the same slider.
 *
 * ⚠ **They are doing different jobs and the same number would be wrong for one of them.** A band
 * only has to say *the list continues under here*, so it stays legible on purpose; a backdrop has
 * to stop being readable, or the window over it is competing with what it is covering. Tied to the
 * one slider rather than given a second so that "more blur" means more of both.
 */
const val WINDOW_RADIUS_FACTOR = 2

private const val HUNDRED = 100
