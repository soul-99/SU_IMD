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
package com.android.geto.feature.settings

import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.width
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.android.geto.common.R as commonR

/**
 * The right-hand end of a setup step's footer: Back, then Next.
 *
 * The author, from the flow: *"put it left of next button, make naxt button bold with solid
 * background"*. Next is a filled [Button] rather than a `TextButton`, and its label is bold — six
 * steps of two identical flat words gave no clue which one carries the flow.
 *
 * ⚠ **It opens with a weighted spacer, and that is what makes it drop into six different
 * footers.** Every one of them arranges **SpaceBetween** so that Skip sits at the left edge; with
 * three buttons SpaceBetween would spread all three evenly and leave Back stranded mid-width. A
 * weighted spacer consumes the free space instead, so there is none left to distribute and the
 * arrangement becomes a no-op — which means not one of those six `horizontalArrangement`
 * expressions had to change, and the Settings case they also serve still behaves exactly as it
 * did.
 *
 * ⚠ **Setup only.** Five of these dialogs also open from the settings list, where this footer
 * reads Cancel/Update or Save and stays two flat text buttons. That is the author's own scope —
 * *"in the setup screens"* — and the callers branch on `onSkip != null` to honour it.
 *
 * @param onBack null on the first step that has nothing behind it, which draws Next alone.
 */
@Composable
internal fun RowScope.SetupNextButtons(
    onBack: (() -> Unit)?,
    onNext: () -> Unit,
    enabled: Boolean = true,
) {
    Spacer(modifier = Modifier.weight(1f))

    if (onBack != null) {
        TextButton(onClick = onBack) {
            Text(text = stringResource(commonR.string.back))
        }

        // The two are a pair and read as one control; the gap is what stops the filled button
        // looking like it has swallowed the word beside it.
        Spacer(modifier = Modifier.width(4.dp))
    }

    Button(onClick = onNext, enabled = enabled) {
        Text(
            text = stringResource(commonR.string.next),
            fontWeight = FontWeight.Bold,
        )
    }
}
