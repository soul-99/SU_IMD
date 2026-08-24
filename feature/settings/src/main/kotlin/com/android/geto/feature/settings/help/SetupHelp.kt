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
package com.android.geto.feature.settings.help

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedCard
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.RectangleShape
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.designsystem.component.emphasised
import com.android.geto.feature.settings.R

/**
 * What someone has to set up themselves, and where.
 *
 * Lives here rather than in the onboarding package because it is shown from two places that
 * cannot see each other's code: the second page of first-run setup, in the app module, and a
 * Help button in Settings. One copy, so the instructions cannot drift apart — which for a
 * page whose entire content is navigation paths is exactly what would happen.
 *
 * Every menu path on the page goes through [HelpPath], so they are all one colour and one
 * weight. A path is the only part of a sentence a reader has to carry to another screen and
 * act on, and picking it out of body text is what the page is for.
 */
@Composable
fun SetupHelpContent(modifier: Modifier = Modifier) {
    Column(
        modifier = modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(
            text = stringResource(R.string.help_title),
            style = MaterialTheme.typography.headlineSmall,
            textAlign = TextAlign.Center,
        )

        Spacer(modifier = Modifier.height(12.dp))

        Text(
            text = stringResource(R.string.help_intro),
            style = MaterialTheme.typography.bodyMedium,
            textAlign = TextAlign.Center,
        )

        Spacer(modifier = Modifier.height(8.dp))

        // Where this page lives, on this page. Worth the line: it is reached from a button
        // most people meet once, during setup, and never look for again.
        val again = stringResource(R.string.help_again)

        val helpPath = stringResource(R.string.help_path_help)

        val pathStyle = pathSpanStyle()

        Text(
            text = buildAnnotatedString {
                append(again)
                append(" ")
                withStyle(pathStyle) { append(helpPath) }
            },
            style = MaterialTheme.typography.bodyMedium,
            textAlign = TextAlign.Center,
        )

        Spacer(modifier = Modifier.height(24.dp))

        // Cards, as the setup pages have always used — only the status circle and the
        // "Step N" label are gone. Those belonged to the permissions page, where each item
        // really is either done or not; nothing here can be checked, and a permanently
        // unticked circle beside every item read as four things having gone wrong.
        HelpSection(
            number = 1,
            title = emphasised(
                text = stringResource(R.string.help_hide_title),
                names = listOf(stringResource(R.string.help_name_mandatory)),
            ),
            path = stringResource(R.string.help_path_hide),
            body = stringResource(R.string.help_hide_body),
            pathFirst = true,
        )

        HelpSection(
            number = 2,
            title = emphasised(
                text = stringResource(R.string.help_revert_title),
                names = listOf(stringResource(R.string.help_name_revert)),
            ),
            path = stringResource(R.string.help_path_unhide),
            body = stringResource(R.string.help_revert_body),
            pathFirst = true,
        )

        // Body first here and in Shizuku below, because both explain *whether* the step
        // applies to you before saying where to go. The first two are unconditional, so
        // the path is the first useful thing on them.
        HelpSection(
            number = 3,
            title = AnnotatedString(stringResource(R.string.help_accessibility_title)),
            path = stringResource(R.string.help_path_accessibility),
            body = stringResource(R.string.help_accessibility_body),
            pathFirst = false,
        )

        GeneralInfoSection(number = 4)

        HelpSection(
            number = 5,
            title = AnnotatedString(stringResource(R.string.help_shizuku_title)),
            path = stringResource(R.string.help_path_shizuku),
            body = stringResource(R.string.help_shizuku_body),
            pathFirst = false,
        )
    }
}

/**
 * The same content as a full page, for the Help button in Settings.
 *
 * Full screen rather than a dialog. It was a dialog, height-capped and scrolling inside its
 * own box, which left the longest page in the app reading through a letterbox — and the
 * identical content is already shown full screen during setup, so the two presentations
 * disagreed about the same words.
 */
@Composable
fun SetupHelpDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(
        modifier = modifier.fillMaxSize(),
        shape = RectangleShape,
        fullScreen = true,
        onDismissRequest = onDismissRequest,
    ) {
        Column(modifier = Modifier.fillMaxSize()) {
            SetupHelpContent(
                modifier = Modifier
                    .weight(1f)
                    .verticalScroll(rememberScrollState())
                    .padding(horizontal = 20.dp)
                    .padding(top = 24.dp),
            )

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 20.dp, vertical = 8.dp),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(R.string.help_close))
                }
            }
        }
    }
}

/**
 * One numbered card: a heading, a menu path, and a line of prose.
 *
 * [pathFirst] decides which of the last two comes first. They were numbered sub-items and
 * are now plain paragraphs — numbering both made a page of five steps look like a page of
 * nine, and the card's own number was already doing that work.
 */
@Composable
private fun HelpSection(
    modifier: Modifier = Modifier,
    number: Int,
    title: AnnotatedString,
    path: String,
    body: String,
    pathFirst: Boolean,
) {
    OutlinedCard(modifier = modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = buildAnnotatedString {
                    append(stringResource(R.string.help_numbered_title, number, ""))
                    append(title)
                },
                style = MaterialTheme.typography.titleMedium,
            )

            if (pathFirst) {
                Spacer(modifier = Modifier.height(12.dp))

                HelpPath(path = path)

                Spacer(modifier = Modifier.height(10.dp))

                Text(text = body, style = MaterialTheme.typography.bodySmall)
            } else {
                Spacer(modifier = Modifier.height(12.dp))

                Text(text = body, style = MaterialTheme.typography.bodySmall)

                Spacer(modifier = Modifier.height(10.dp))

                HelpPath(path = path)
            }
        }
    }

    Spacer(modifier = Modifier.height(12.dp))
}

/**
 * The card that is not a setup step.
 *
 * Two headed blocks rather than a numbered list, because they answer different questions —
 * how to use the app at all, and what the services manager is for — and numbering them
 * alongside the four things to configure implied this one was a fifth thing to do.
 */
@Composable
private fun GeneralInfoSection(
    modifier: Modifier = Modifier,
    number: Int,
) {
    OutlinedCard(modifier = modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = stringResource(
                    R.string.help_numbered_title,
                    number,
                    stringResource(R.string.help_general_title),
                ),
                style = MaterialTheme.typography.titleMedium,
            )

            SubHeading(text = stringResource(R.string.help_general_how_title))

            Text(
                text = stringResource(R.string.help_general_launch),
                style = MaterialTheme.typography.bodySmall,
            )

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = stringResource(R.string.help_general_shortcuts),
                style = MaterialTheme.typography.bodySmall,
            )

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = emphasised(
                    text = stringResource(R.string.help_general_revert),
                    names = listOf(stringResource(R.string.help_name_revert_button)),
                ),
                style = MaterialTheme.typography.bodySmall,
            )

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                modifier = Modifier.padding(start = 16.dp),
                text = stringResource(R.string.help_general_revert_places),
                style = MaterialTheme.typography.bodySmall,
            )

            Text(
                modifier = Modifier.padding(start = 24.dp, top = 4.dp),
                text = stringResource(R.string.help_general_revert_items),
                style = MaterialTheme.typography.bodySmall,
            )

            SubHeading(text = stringResource(R.string.help_general_manager_title))

            Text(
                text = stringResource(R.string.help_general_manager),
                style = MaterialTheme.typography.bodySmall,
            )

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = stringResource(R.string.help_general_manager_places),
                style = MaterialTheme.typography.bodySmall,
            )

            Text(
                modifier = Modifier.padding(start = 16.dp, top = 4.dp),
                text = stringResource(R.string.help_general_manager_items),
                style = MaterialTheme.typography.bodySmall,
            )
        }
    }

    Spacer(modifier = Modifier.height(12.dp))
}

@Composable
private fun SubHeading(
    modifier: Modifier = Modifier,
    text: String,
) {
    Spacer(modifier = Modifier.height(16.dp))

    Text(
        modifier = modifier,
        text = text,
        style = MaterialTheme.typography.labelLarge,
        color = MaterialTheme.colorScheme.primary,
    )

    Spacer(modifier = Modifier.height(10.dp))
}

/** A menu path, in the one style every menu path on this page uses. */
@Composable
private fun HelpPath(
    modifier: Modifier = Modifier,
    path: String,
) {
    Text(
        modifier = modifier,
        text = path,
        style = MaterialTheme.typography.bodySmall,
        color = MaterialTheme.colorScheme.primary,
        fontWeight = FontWeight.Medium,
    )
}

/** The same colour and weight [HelpPath] uses, for a path inside a longer sentence. */
@Composable
private fun pathSpanStyle() = SpanStyle(
    color = MaterialTheme.colorScheme.primary,
    fontWeight = FontWeight.Medium,
)
