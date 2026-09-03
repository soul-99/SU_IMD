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
package com.android.geto.designsystem.theme

import androidx.compose.material3.Typography
import androidx.compose.ui.text.font.FontWeight

private val Default = Typography()

/**
 * The Material type scale with a heavier hand on the parts that carry a screen - the emphasis
 * Material 3 Expressive puts on weight rather than size. Headlines, titles and button labels
 * come out bolder; body text is left exactly as Material sets it, so paragraphs stay easy to
 * read and only the structure gets louder.
 *
 * Overriding a handful of roles and copying the rest from [Default] keeps this to the styles
 * that actually change, and inherits every future Material tweak to the others for free.
 */
internal val GetoTypography = Default.copy(
    displaySmall = Default.displaySmall.copy(fontWeight = FontWeight.SemiBold),
    headlineLarge = Default.headlineLarge.copy(fontWeight = FontWeight.Bold),
    headlineMedium = Default.headlineMedium.copy(fontWeight = FontWeight.Bold),
    headlineSmall = Default.headlineSmall.copy(fontWeight = FontWeight.SemiBold),
    titleLarge = Default.titleLarge.copy(fontWeight = FontWeight.Bold),
    titleMedium = Default.titleMedium.copy(fontWeight = FontWeight.SemiBold),
    labelLarge = Default.labelLarge.copy(fontWeight = FontWeight.SemiBold),
)
