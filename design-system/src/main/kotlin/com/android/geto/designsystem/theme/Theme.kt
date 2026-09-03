/*
 *
 *   Copyright 2023 Einstein Blanco
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

import android.os.Build
import androidx.annotation.ChecksSdkIntAtLeast
import androidx.annotation.RequiresApi
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.ColorScheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.luminance
import androidx.compose.ui.platform.LocalContext
import com.android.geto.domain.model.Theme

private val LightGreenColorScheme = lightColorScheme(
    primary = Color(0xFF4E7819),
    onPrimary = Color(0xFFFFFFFF),
    primaryContainer = Color(0xFFCFFF91),
    onPrimaryContainer = Color(0xFF102000),
    secondary = Color(0xFF5A6A42),
    onSecondary = Color(0xFFFFFFFF),
    secondaryContainer = Color(0xFFDFF0BF),
    onSecondaryContainer = Color(0xFF152405),
    tertiary = Color(0xFF2A746F),
    onTertiary = Color(0xFFFFFFFF),
    tertiaryContainer = Color(0xFFAEFAF2),
    onTertiaryContainer = Color(0xFF00201E),
    error = Color(0xFFBA1A1A),
    onError = Color(0xFFFFFFFF),
    errorContainer = Color(0xFFFFDAD6),
    onErrorContainer = Color(0xFF410002),
    background = Color(0xFFF9FAEF),
    onBackground = Color(0xFF1A1C16),
    surface = Color(0xFFF9FAEF),
    onSurface = Color(0xFF1A1C16),
    surfaceVariant = Color(0xFFE1E4D5),
    onSurfaceVariant = Color(0xFF44483D),
    outline = Color(0xFF75796C),
    outlineVariant = Color(0xFFC5C8BA),
    scrim = Color(0xFF000000),
    inverseSurface = Color(0xFF2F312A),
    inverseOnSurface = Color(0xFFF1F2E6),
    inversePrimary = Color(0xFF8FAE6E),
    surfaceDim = Color(0xFFDADBD0),
    surfaceBright = Color(0xFFF9FAEF),
    surfaceContainerLowest = Color(0xFFFFFFFF),
    surfaceContainerLow = Color(0xFFF3F4E9),
    surfaceContainer = Color(0xFFEEEFE3),
    surfaceContainerHigh = Color(0xFFE8E9DE),
    surfaceContainerHighest = Color(0xFFE2E3D8),
)

private val DarkGreenColorScheme = darkColorScheme(
    primary = Color(0xFF8FAE6E),
    onPrimary = Color(0xFF1F3800),
    primaryContainer = Color(0xFF375F05),
    onPrimaryContainer = Color(0xFFCFFF91),
    secondary = Color(0xFFC1D4A4),
    onSecondary = Color(0xFF2B3918),
    secondaryContainer = Color(0xFF41512C),
    onSecondaryContainer = Color(0xFFDFF0BF),
    tertiary = Color(0xFF92DED6),
    onTertiary = Color(0xFF003735),
    tertiaryContainer = Color(0xFF115C57),
    onTertiaryContainer = Color(0xFFAEFAF2),
    error = Color(0xFFFFB4AB),
    onError = Color(0xFF690005),
    errorContainer = Color(0xFF93000A),
    onErrorContainer = Color(0xFFFFDAD6),
    // ⚠ **Lifted about nine points off Material's own #12140E — r13c.** The generated scheme's
    // page is very close to black, which the author reported as too dark with OLED mode off. The
    // whole surface ladder moves with it so that every container keeps its distance from the page
    // and from its neighbours; OLED mode overrides all of it to true black regardless.
    background = Color(0xFF1B1E16),
    onBackground = Color(0xFFE2E3D8),
    surface = Color(0xFF1B1E16),
    onSurface = Color(0xFFE2E3D8),
    surfaceVariant = Color(0xFF44483D),
    onSurfaceVariant = Color(0xFFC5C8BA),
    outline = Color(0xFF8F9285),
    outlineVariant = Color(0xFF44483D),
    scrim = Color(0xFF000000),
    inverseSurface = Color(0xFFE2E3D8),
    inverseOnSurface = Color(0xFF2F312A),
    inversePrimary = Color(0xFF4E7819),
    surfaceDim = Color(0xFF1B1E16),
    surfaceBright = Color(0xFF383A32),
    surfaceContainerLowest = Color(0xFF14160E),
    surfaceContainerLow = Color(0xFF21241C),
    surfaceContainer = Color(0xFF262920),
    surfaceContainerHigh = Color(0xFF31352B),
    surfaceContainerHighest = Color(0xFF3C4036),
)

@Composable
fun GetoTheme(
    theme: Theme,
    dynamicTheme: Boolean,
    /**
     * The author's "OLED background mode" - "pure black UI background".
     *
     * ⚠ **Ignored by a light scheme**, so a caller never has to ask which scheme it is about to
     * get. See [asOledBackground] for which four tokens move and why the containers do not.
     *
     * ⚠ **Defaulted, and only for the callers that genuinely have no user data.** Every activity
     * in this app passes it; the default is here so that a preview or a test harness building a
     * theme out of nothing gets the ordinary scheme rather than a compile error.
     */
    oledBackground: Boolean = false,
    /**
     * The author's "Progressive UI blur", switch and sliders both, published rather than used.
     *
     * ⚠ **Nothing in this file reads it.** It is here because a page modifier and a *dialog* both
     * need it — see [LocalBlurSettings] — and neither can reach user data: one lives in this
     * module and must not take a view model, the other is a window of its own. Every activity
     * already hands this theme the user's preferences, so this is the one place that can answer
     * without a second wiring.
     */
    blurSettings: GetoBlurSettings = GetoBlurSettings.Default,
    content: @Composable () -> Unit,
) {
    val chosen = if (supportsDynamicTheming() && dynamicTheme) {
        getDynamicColorScheme(
            theme = theme,
        )
    } else {
        getGreenColorScheme(
            theme = theme,
        )
    }

    val colorScheme = if (oledBackground) chosen.asOledBackground() else chosen

    // ⚠ **Identity, not the flag.** [asOledBackground] hands a light scheme straight back, so
    // the two are the same object exactly when the mode asked for nothing — which is the honest
    // reading of "is OLED in force here", and it cannot drift from what the scheme actually says.
    CompositionLocalProvider(
        LocalOledBackground provides (colorScheme !== chosen),
        LocalBlurSettings provides blurSettings,
    ) {
        MaterialTheme(
            colorScheme = colorScheme,
            content = content,
        )
    }
}

/**
 * Whether the OLED background mode is actually in force under this theme.
 *
 * ⚠ **For the few places a colour token cannot answer, and there is one so far.** The mode takes
 * the *page* to true black and deliberately leaves the containers alone, so that a card, a dialog
 * or the settings manager still separates from what it is drawn on — see [asOledBackground]. The
 * author asked for the opposite for the manager, twice: *"blackouts UI BG also for settings
 * manager"* in r10, *"Everywhere"* when asked the scope, and again in r13 when he found it still
 * grey. A dialog cannot work that out from `surface` alone, because its own colour is a container
 * and containers did not move. So the theme says it outright.
 *
 * False everywhere else, including in a preview or a test harness that never built a [GetoTheme].
 */
val LocalOledBackground = staticCompositionLocalOf { false }


@ChecksSdkIntAtLeast(api = Build.VERSION_CODES.S)
fun supportsDynamicTheming() = Build.VERSION.SDK_INT >= Build.VERSION_CODES.S

/** True black, which on an OLED panel is an unlit pixel. That is the whole point of the mode. */
private val Oled = Color(0xFF000000)

/**
 * The page behind everything, taken to true black.
 *
 * ⚠ **A light scheme is returned as it came.** The mode is about unlit pixels, and a light theme
 * has none to give; forcing black there would be a second dark theme wearing the wrong text
 * colours. The switch that sets it is not even drawn while the app is light.
 *
 * ⚠ **Four tokens and one near-miss, deliberately not the containers.** `background`, `surface`
 * and `surfaceDim` are the page; `surfaceContainerLowest` is what sits directly on it and would
 * otherwise draw a #0C0F09 rectangle on #000000. `surfaceContainerLow` follows them down but not
 * all the way, because it is used as page furniture in a few places where a hard edge against
 * black would read as a seam. Everything above it keeps its tint - that is what still separates a
 * card, a dialog or the settings manager from the page it is drawn on.
 */
private fun ColorScheme.asOledBackground(): ColorScheme {
    // Luminance rather than a flag: this is asked of dynamic schemes too, and there is no
    // "isDark" on a ColorScheme. A dark scheme is one whose page is darker than its ink.
    val dark = surface.luminance() < onSurface.luminance()

    if (!dark) return this

    return copy(
        background = Oled,
        surface = Oled,
        surfaceDim = Oled,
        surfaceContainerLowest = Oled,
        surfaceContainerLow = Color(0xFF0A0A0A),
    )
}

@Composable
private fun getGreenColorScheme(theme: Theme): ColorScheme = when (theme) {
    Theme.FOLLOW_SYSTEM -> {
        if (isSystemInDarkTheme()) DarkGreenColorScheme else LightGreenColorScheme
    }

    Theme.LIGHT -> {
        LightGreenColorScheme
    }

    Theme.DARK -> {
        DarkGreenColorScheme
    }
}

@RequiresApi(Build.VERSION_CODES.S)
@Composable
private fun getDynamicColorScheme(theme: Theme): ColorScheme {
    val context = LocalContext.current

    return when (theme) {
        Theme.FOLLOW_SYSTEM -> {
            if (isSystemInDarkTheme()) {
                dynamicDarkColorScheme(context)
            } else {
                dynamicLightColorScheme(
                    context,
                )
            }
        }

        Theme.LIGHT -> {
            dynamicLightColorScheme(
                context,
            )
        }

        Theme.DARK -> {
            dynamicDarkColorScheme(context)
        }
    }
}
