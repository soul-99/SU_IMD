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

import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextDecoration

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

/**
 * Underlines the named phrases wherever they appear in a sentence.
 *
 * The third of this file's three marks, and the one for a phrase inside a line that is already
 * emphasised as a whole - underlining what the sentence is *about* when bolding it again would
 * say nothing, because the line around it is bold too.
 *
 * Built exactly like [emphasised], and the reasons there are the reasons here: the translator
 * gets a whole sentence rather than fragments, a translation that reorders it still gets its
 * marks in the right places, and a phrase a translation phrases around is skipped rather than
 * treated as an error.
 */
@Composable
fun underlined(text: String, names: List<String>): AnnotatedString = remember(text, names) {
    buildAnnotatedString {
        append(text)

        names.forEach { name ->
            val start = text.indexOf(name)

            if (start >= 0) {
                addStyle(
                    style = SpanStyle(textDecoration = TextDecoration.Underline),
                    start = start,
                    end = start + name.length,
                )
            }
        }
    }
}

/**
 * The same, in the theme's own accent colour as well as bold.
 *
 * For a phrase that names something the reader has to go and find — a Quick Settings tile, a
 * screen — where bold alone does not separate it enough from the rest of a paragraph. The
 * colour is the app's primary, so the phrase reads as part of this app rather than as a link
 * out of it, and it moves with the theme in both light and dark.
 *
 * [bold] is for phrases in the same sentence that want emphasis but not the colour — a button
 * label beside a tile name, say. Both lists are optional and either may be empty.
 *
 * Kept beside [emphasised] and built the same way, for the same reasons: whole sentences for
 * the translator, and a name that a translation phrases around is skipped rather than
 * breaking the line.
 */
@Composable
fun highlighted(
    text: String,
    names: List<String>,
    bold: List<String> = emptyList(),
): AnnotatedString {
    val colour = MaterialTheme.colorScheme.primary

    return remember(text, names, bold, colour) {
        buildAnnotatedString {
            append(text)

            // Plain emphasis first, so a coloured name that happens to sit inside a bolded
            // phrase still ends up coloured rather than being overwritten by it.
            bold.forEach { name ->
                val start = text.indexOf(name)

                if (start >= 0) {
                    addStyle(
                        style = SpanStyle(fontWeight = FontWeight.Bold),
                        start = start,
                        end = start + name.length,
                    )
                }
            }

            names.forEach { name ->
                val start = text.indexOf(name)

                if (start >= 0) {
                    addStyle(
                        style = SpanStyle(
                            fontWeight = FontWeight.Bold,
                            color = colour,
                        ),
                        start = start,
                        end = start + name.length,
                    )
                }
            }
        }
    }
}
