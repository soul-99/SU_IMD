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
package com.android.geto.feature.settings.dialog

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.LinkAnnotation
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.TextLinkStyles
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.text.withLink
import androidx.compose.ui.unit.dp
import com.android.geto.common.ProjectLinks
import com.android.geto.common.shareProject
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.designsystem.icon.GetoIcons
import com.android.geto.feature.settings.R

/**
 * The author's ask, opened from the Support button in About.
 *
 * Everything here is free to the person reading it - that is the whole framing, and why the
 * only two things it offers to actually do, share and open the repo, cost nothing.
 *
 * A scrolling dialog rather than a full page: it is read once and dismissed, not configured,
 * so the familiar tap-outside-to-close of a dialog fits it better than a screen with a back
 * arrow.
 */
@Composable
internal fun SupportDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {
    val context = LocalContext.current

    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(
            modifier = Modifier
                .verticalScroll(rememberScrollState())
                .padding(20.dp),
        ) {
            // The emoji in the label is the heart, so the title needs no icon beside it.
            Text(
                text = stringResource(R.string.support_button),
                style = MaterialTheme.typography.titleLarge,
            )

            Spacer(modifier = Modifier.height(16.dp))

            // The author's note, as four separate paragraphs with air between them rather than
            // one block - the third is the turn from "why" to "how you can help", so it is bold
            // and it is what the numbered list below answers.
            Paragraph(text = stringResource(R.string.support_intro_1))

            Paragraph(text = stringResource(R.string.support_intro_2))

            Paragraph(
                text = stringResource(R.string.support_intro_3),
                bold = true,
            )

            Paragraph(text = stringResource(R.string.support_intro_4))

            Spacer(modifier = Modifier.height(12.dp))

            SupportPoint(number = 1, text = stringResource(R.string.support_point_share))

            // Right under its point, because it is that point made doable. Tonal rather than a
            // link so it reads as the one thing on this list the reader can finish in a tap.
            FilledTonalButton(
                modifier = Modifier.padding(start = POINT_INSET, top = 4.dp, bottom = 8.dp),
                onClick = { context.shareProject(context.getString(R.string.support_share_message)) },
            ) {
                Icon(
                    modifier = Modifier.size(18.dp),
                    imageVector = GetoIcons.Share,
                    contentDescription = null,
                )

                Spacer(modifier = Modifier.width(8.dp))

                Text(text = stringResource(R.string.support_share_button))
            }

            StarPoint(number = 2)

            SupportPoint(number = 3, text = stringResource(R.string.support_point_bugs))

            SupportPoint(number = 4, text = stringResource(R.string.support_point_discuss))

            SupportPoint(number = 5, text = stringResource(R.string.support_point_contribute))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(R.string.close))
                }
            }
        }
    }
}

/** One paragraph of the note, with a little air under it so the four read as separate. */
@Composable
private fun Paragraph(
    text: String,
    bold: Boolean = false,
) {
    Text(
        modifier = Modifier.padding(bottom = 10.dp),
        text = text,
        style = MaterialTheme.typography.bodyMedium,
        fontWeight = if (bold) FontWeight.Bold else null,
    )
}

/**
 * The star point. A yellow star sits inline at the head of the sentence, in the text flow
 * rather than as a separate icon, and only the words "GitHub repo" are the link - the rest of
 * the line is plain text, so the whole row is not one big tap target.
 *
 * The link phrase is its own resource, matched as a substring of the sentence, the same shape
 * the About section's links use. If a translation does not contain it verbatim the sentence is
 * still shown, just without the link, rather than crashing on a bad index.
 */
@Composable
private fun StarPoint(number: Int) {
    val sentence = stringResource(R.string.support_point_star)

    val linkPhrase = stringResource(R.string.support_point_star_link)

    val linkColour = MaterialTheme.colorScheme.primary

    val body = remember(sentence, linkPhrase, linkColour) {
        val styles = TextLinkStyles(
            style = SpanStyle(color = linkColour, textDecoration = TextDecoration.Underline),
        )

        buildAnnotatedString {
            // The gold star as a glyph, so it flows and wraps with the words instead of
            // floating beside them.
            append("⭐ ")

            val at = sentence.indexOf(linkPhrase)

            if (at < 0) {
                append(sentence)
            } else {
                append(sentence.substring(0, at))

                withLink(LinkAnnotation.Url(url = ProjectLinks.REPOSITORY, styles = styles)) {
                    append(linkPhrase)
                }

                append(sentence.substring(at + linkPhrase.length))
            }
        }
    }

    NumberedRow(number = number) {
        Text(text = body, style = MaterialTheme.typography.bodyMedium)
    }
}

/** One plain numbered line. */
@Composable
private fun SupportPoint(
    number: Int,
    text: String,
) {
    NumberedRow(number = number) {
        Text(text = text, style = MaterialTheme.typography.bodyMedium)
    }
}

/**
 * The number beside its body. Drawn rather than typed into the string, so a translation cannot
 * drop it and a right-to-left language puts it on the correct side by itself.
 *
 * The body sits in a weighted box so it takes the rest of the row and wraps under itself; the
 * caller's content needs no width modifier of its own.
 */
@Composable
private fun NumberedRow(
    number: Int,
    body: @Composable () -> Unit,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 6.dp),
    ) {
        Text(
            text = stringResource(R.string.support_point_number, number),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurface,
        )

        Spacer(modifier = Modifier.width(8.dp))

        Box(modifier = Modifier.weight(1f)) {
            body()
        }
    }
}

/** Indent for the share button, so it sits under its point's text rather than its number. */
private val POINT_INSET = 22.dp
