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
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.designsystem.component.emphasised
import com.android.geto.designsystem.icon.GetoIcons
import com.android.geto.feature.settings.R

/**
 * The four setup steps a fork needs before IMD can drive it, with the two paragraphs that
 * follow them.
 *
 * Shared by [ThedjchiSetupDialog] and `SheveryNoticeDialog`, which say the same four things
 * about different apps. The numbering is inside each string because that is how the author
 * wrote them; the ON / OFF word in each is bolded by name rather than by position, so a step
 * that never carries one simply passes null.
 *
 * The first paragraph is in the error colour and the second is bold, both on the author's
 * instruction — one is a security note and the other is the thing people forget after a
 * reboot.
 */
@Composable
internal fun ShizukuSetupBody(
    modifier: Modifier = Modifier,
    steps: List<Pair<Int, Int?>>,
    rebootId: Int,
) {
    Column(modifier = modifier) {
        Text(
            text = stringResource(R.string.shizuku_setup_lead),
            style = MaterialTheme.typography.titleMedium,
        )

        Spacer(modifier = Modifier.height(10.dp))

        // Read by property rather than destructured: `(a, b) ->` on a Pair inside a lambda is
        // the component1()/component2() ambiguity this project has hit four times.
        for (step in steps) {
            val boldId = step.second

            Text(
                modifier = Modifier.padding(start = 12.dp, bottom = 4.dp),
                text = if (boldId == null) {
                    emphasised(text = stringResource(step.first), names = emptyList())
                } else {
                    emphasised(
                        text = stringResource(step.first),
                        names = listOf(stringResource(boldId)),
                    )
                },
                style = MaterialTheme.typography.bodyMedium,
            )
        }

        Spacer(modifier = Modifier.height(10.dp))

        Text(
            text = stringResource(R.string.shizuku_setup_tcp_port),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.error,
        )

        Spacer(modifier = Modifier.height(8.dp))

        Text(
            text = stringResource(rebootId),
            style = MaterialTheme.typography.bodyMedium,
            fontWeight = FontWeight.Bold,
        )
    }
}

/**
 * What to set in the Shizuku app before IMD can drive the Thedjchi fork.
 *
 * Raised when the Thedjchi option is picked, and from the ⓘ beside its name at any time.
 *
 * ⚠ **It does not gate the choice, unlike the Shevery one.** Thedjchi is the recommended fork
 * and this is a setup checklist rather than a warning, so the option commits and then explains
 * — which is also what lets the ⓘ open it without changing anything.
 */
@Composable
fun ThedjchiSetupDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(
            modifier = Modifier
                .verticalScroll(rememberScrollState())
                .padding(20.dp),
        ) {
            ShizukuSetupBody(
                steps = listOf(
                    R.string.thedjchi_setup_1 to R.string.shizuku_setup_off,
                    R.string.thedjchi_setup_2 to R.string.shizuku_setup_on,
                    R.string.thedjchi_setup_3 to R.string.shizuku_setup_off,
                    R.string.thedjchi_setup_4 to null,
                ),
                rebootId = R.string.thedjchi_setup_reboot,
            )

            Spacer(modifier = Modifier.height(12.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(R.string.understood))
                }
            }
        }
    }
}

/**
 * Why 'Manage Shizuku' will not switch on yet.
 *
 * The switch cannot stand on with a blank field below it, and a disabled Switch swallows the
 * tap — so the press lands here instead of doing nothing at all.
 */
@Composable
internal fun ManageShizukuBlockedDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = stringResource(R.string.manage_shizuku),
                style = MaterialTheme.typography.titleLarge,
            )

            Spacer(modifier = Modifier.height(12.dp))

            Text(
                text = stringResource(R.string.manage_shizuku_blocked),
                style = MaterialTheme.typography.bodyMedium,
            )

            Spacer(modifier = Modifier.height(12.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(R.string.understood))
                }
            }
        }
    }
}

/**
 * Points 2 and 3 of the old Shevery notice, summarised as a vertical flow chart.
 *
 * Shape B of the three the author was shown: two labelled halves of two nodes each, rather
 * than one four-node chain, because the two halves answer different questions and a reader
 * arrives wanting one of them.
 *
 * ⚠ **Drawn rather than described.** The whole point of it is that Shevery is not asked to
 * stop or start: the debugging transport goes, the service follows, and the watchdog brings it
 * back. Four boxes and two arrows say that in less space than the two sentences did.
 */
@Composable
internal fun SheveryFlowChart(modifier: Modifier = Modifier) {
    Column(modifier = modifier) {
        FlowHalf(
            title = stringResource(R.string.shevery_flow_stop),
            first = stringResource(R.string.shevery_flow_hide),
            second = stringResource(R.string.shevery_flow_stopped),
        )

        Spacer(modifier = Modifier.height(12.dp))

        FlowHalf(
            title = stringResource(R.string.shevery_flow_restart),
            first = stringResource(R.string.shevery_flow_unhide),
            second = stringResource(R.string.shevery_flow_started),
        )
    }
}

/** One labelled half: a heading, a node, the arrow, and the node it leads to. */
@Composable
private fun FlowHalf(
    modifier: Modifier = Modifier,
    title: String,
    first: String,
    second: String,
) {
    Column(modifier = modifier) {
        Text(
            text = title,
            style = MaterialTheme.typography.labelLarge,
            color = MaterialTheme.colorScheme.primary,
        )

        Spacer(modifier = Modifier.height(6.dp))

        FlowNode(text = first)

        FlowArrow()

        FlowNode(text = second)
    }
}

/** One step of the chart. A filled surface rather than an outline, so the arrows read as the
 *  only lines in the picture. */
@Composable
private fun FlowNode(
    modifier: Modifier = Modifier,
    text: String,
) {
    Surface(
        modifier = modifier.fillMaxWidth(),
        color = MaterialTheme.colorScheme.surfaceVariant,
        shape = RoundedCornerShape(8.dp),
    ) {
        Text(
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 8.dp),
            text = text,
            style = MaterialTheme.typography.bodySmall,
        )
    }
}

/** The join between two nodes. Centred, because a chart whose arrows hug one edge reads as a
 *  list with decoration. */
@Composable
private fun FlowArrow(modifier: Modifier = Modifier) {
    Row(
        modifier = modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.Center,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Icon(
            modifier = Modifier
                .padding(vertical = 2.dp)
                .size(18.dp),
            imageVector = GetoIcons.ArrowDownward,
            contentDescription = null,
            tint = MaterialTheme.colorScheme.outline,
        )
    }
}

/** One numbered point of `How this works`. The number is drawn rather than baked into the
 *  string, because this list is assembled from strings that already existed. */
@Composable
internal fun HowThisWorksPoint(
    modifier: Modifier = Modifier,
    number: Int,
    text: String,
    color: Color = Color.Unspecified,
    /**
     * ⚠ **Two of these points are entirely bold**, which is how the author wrote them: they
     * state the scope of Shevery support rather than advising about it, and the pop-up is the
     * only place that scope is written down.
     */
    bold: Boolean = false,
    content: (@Composable () -> Unit)? = null,
) {
    Row(modifier = modifier.padding(bottom = 8.dp)) {
        Text(
            text = "$number.",
            style = MaterialTheme.typography.bodyMedium,
            color = color,
            fontWeight = if (bold) FontWeight.Bold else null,
        )

        Spacer(modifier = Modifier.width(8.dp))

        if (content == null) {
            Text(
                text = text,
                style = MaterialTheme.typography.bodyMedium,
                color = color,
                fontWeight = if (bold) FontWeight.Bold else null,
            )
        } else {
            content()
        }
    }
}

/** The rule above `How this works`, so the checklist above it reads as finished. */
@Composable
internal fun SetupDivider(modifier: Modifier = Modifier) {
    HorizontalDivider(modifier = modifier.padding(vertical = 14.dp))
}
