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
package com.android.geto.designsystem.component

import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.CubicBezierEasing
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.android.geto.designsystem.icon.GetoIcons

/**
 * One choice out of a handful, drawn as a row of soft pills.
 *
 * ⚠ **This replaces Material's `SingleChoiceSegmentedButtonRow` — the author's **D1** from the r12
 * template.** The segmented row is the right *component* and always was; what he was reacting to is
 * how it is drawn: a hairline outline around the whole group and a hard divider between every
 * segment, which is the sharpest thing on either dialog. Material's `SegmentedButton` has no way to
 * turn those off — the border is part of its shape contract — so the drawing is here instead.
 *
 * ⚠ **Still one control, not a row of buttons.** Each option gets its own container, but they share
 * a row, take equal width, and only one of them is ever filled — and the whole row carries
 * `Role.RadioButton` semantics, so a screen reader announces it as a single choice exactly as the
 * segmented row did.
 *
 * ⚠ **The tick stays.** It is what distinguishes "this is chosen" from "this one is a different
 * colour", and it is the rounded tick now, like every other icon in the app since r12.
 */
@Composable
fun <T> GetoChoiceRow(
    options: List<T>,
    selected: T,
    label: @Composable (T) -> String,
    onSelect: (T) -> Unit,
    modifier: Modifier = Modifier,
) {
    Row(
        modifier = modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(CHOICE_GAP),
    ) {
        options.forEach { option ->
            ChoiceItem(
                text = label(option),
                selected = option == selected,
                onClick = { onSelect(option) },
            )
        }
    }
}

@Composable
private fun RowScope.ChoiceItem(
    text: String,
    selected: Boolean,
    onClick: () -> Unit,
) {
    val scheme = MaterialTheme.colorScheme

    val container by animateColorAsState(
        targetValue = if (selected) scheme.primaryContainer else scheme.surfaceContainerHigh,
        animationSpec = tween(durationMillis = CHOICE_MILLIS, easing = ChoiceEasing),
        label = "choiceContainer",
    )

    val content by animateColorAsState(
        targetValue = if (selected) scheme.onPrimaryContainer else scheme.onSurfaceVariant,
        animationSpec = tween(durationMillis = CHOICE_MILLIS, easing = ChoiceEasing),
        label = "choiceContent",
    )

    Row(
        modifier = Modifier
            .weight(1f)
            .clip(CircleShape)
            .background(container)
            .selectable(selected = selected, role = Role.RadioButton, onClick = onClick)
            .padding(horizontal = CHOICE_PADDING, vertical = CHOICE_PADDING_VERTICAL),
        horizontalArrangement = Arrangement.Center,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        if (selected) {
            Icon(
                modifier = Modifier
                    .size(CHOICE_TICK_SIZE)
                    .padding(end = 0.dp),
                imageVector = GetoIcons.Check,
                contentDescription = null,
                tint = content,
            )
        }

        Text(
            modifier = Modifier.padding(start = if (selected) CHOICE_TICK_GAP else 0.dp),
            text = text,
            color = content,
            style = MaterialTheme.typography.labelLarge,
            fontWeight = if (selected) FontWeight.SemiBold else FontWeight.Normal,
            textAlign = TextAlign.Center,
            maxLines = 1,
        )
    }
}

/** The same emphasised curve the tab bar and the toggles animate on. */
private val ChoiceEasing = CubicBezierEasing(0.2f, 0f, 0f, 1f)

private const val CHOICE_MILLIS = 200

private val CHOICE_GAP: Dp = 8.dp

private val CHOICE_PADDING: Dp = 12.dp

private val CHOICE_PADDING_VERTICAL: Dp = 12.dp

private val CHOICE_TICK_SIZE: Dp = 18.dp

private val CHOICE_TICK_GAP: Dp = 6.dp
