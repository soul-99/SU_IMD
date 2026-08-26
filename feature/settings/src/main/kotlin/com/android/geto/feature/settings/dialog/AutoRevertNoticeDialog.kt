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

import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.unit.dp
import com.android.geto.designsystem.component.emphasised
import com.android.geto.feature.settings.R

/** Indent for a sub-point, so it reads as part of the numbered point above it. */
private val SUB_POINT_INSET = 24.dp

/**
 * What switching auto revert on actually signs the user up for.
 *
 * Shown before the switch moves rather than after, and the buttons say what they do rather
 * than OK and Cancel, because the third point is the one that surprises people: coming back
 * to IMD is the trigger, so coming back too early puts the settings back while the app that
 * needed them hidden is still open. That is not a bug and there is no way to tell the two
 * apart, so the only honest answer is to say so first.
 */
@Composable
internal fun AutoRevertNoticeDialog(
    modifier: Modifier = Modifier,
    onConfirm: () -> Unit,
    onDismissRequest: () -> Unit,
) {
    SettingsPage(
        modifier = modifier,
        title = stringResource(R.string.auto_revert),
        onDismissRequest = onDismissRequest,
        actions = {
            TextButton(onClick = onDismissRequest) {
                Text(text = stringResource(R.string.auto_revert_keep_off))
            }

            TextButton(onClick = onConfirm) {
                Text(text = stringResource(R.string.auto_revert_turn_on))
            }
        },
    ) {
        NumberedPoint(
            number = 1,
            text = emphasised(
                text = stringResource(R.string.auto_revert_notice_scope),
                names = listOf(stringResource(R.string.auto_revert_name_shortcuts)),
            ),
        )

        NumberedPoint(
            number = 2,
            text = AnnotatedString(stringResource(R.string.auto_revert_notice_trigger)),
        )

        SubPoint(text = stringResource(R.string.auto_revert_notice_trigger_example))

        SubPoint(text = stringResource(R.string.auto_revert_notice_trigger_both))

        NumberedPoint(
            number = 3,
            text = emphasised(
                text = stringResource(R.string.auto_revert_notice_early),
                names = listOf(stringResource(R.string.auto_revert_name_early)),
            ),
        )

        SubPoint(text = stringResource(R.string.auto_revert_notice_early_relaunch))

        SubPoint(text = stringResource(R.string.auto_revert_notice_early_resume))
    }
}

/**
 * The number is drawn beside the text rather than typed into the string, so a translation
 * cannot lose it and a right-to-left language puts it on the correct side by itself.
 */
@Composable
private fun NumberedPoint(
    modifier: Modifier = Modifier,
    number: Int,
    text: AnnotatedString,
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .padding(horizontal = 10.dp, vertical = 6.dp),
    ) {
        Text(
            text = stringResource(R.string.auto_revert_notice_number, number),
            style = MaterialTheme.typography.bodyMedium,
        )

        Spacer(modifier = Modifier.width(8.dp))

        Text(
            modifier = Modifier.weight(1f),
            text = text,
            style = MaterialTheme.typography.bodyMedium,
        )
    }
}

/** A consequence of the point above, indented to its text rather than to its number. */
@Composable
private fun SubPoint(
    modifier: Modifier = Modifier,
    text: String,
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .padding(start = SUB_POINT_INSET, end = 10.dp, top = 2.dp, bottom = 2.dp),
    ) {
        Text(text = "•", style = MaterialTheme.typography.bodySmall)

        Spacer(modifier = Modifier.width(8.dp))

        Text(
            modifier = Modifier.weight(1f),
            text = text,
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}
