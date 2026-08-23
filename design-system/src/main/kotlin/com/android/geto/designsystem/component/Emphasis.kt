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
package com.android.geto.designsystem.component

import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight

/**
 * Bolds the named phrases wherever they appear in a sentence.
 *
 * For instructions that point at something on screen — a button label, a feature name. The
 * emphasis is what lets a reader match the sentence to the control without reading the whole
 * paragraph, and passing the *same* string resource the control uses is what keeps the two
 * in step when one of them is renamed.
 *
 * Done by searching the finished text rather than by splitting the sentence into fragments
 * around each name, so a translator gets a whole sentence to work with and a translation
 * that reorders it still gets the emphasis in the right places. A name that does not appear
 * is skipped rather than treated as an error: a translation is free to phrase around it.
 */
@Composable
fun emphasised(text: String, names: List<String>): AnnotatedString = remember(text, names) {
    buildAnnotatedString {
        append(text)

        names.forEach { name ->
            val start = text.indexOf(name)

            if (start >= 0) {
                addStyle(
                    style = SpanStyle(fontWeight = FontWeight.Bold),
                    start = start,
                    end = start + name.length,
                )
            }
        }
    }
}
