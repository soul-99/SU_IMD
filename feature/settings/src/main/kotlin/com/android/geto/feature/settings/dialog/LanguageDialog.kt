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
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.selectableGroup
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import com.android.geto.common.AppLocale
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.feature.settings.R
import com.android.geto.common.R as commonR

/**
 * Which language the app draws itself in.
 *
 * Every entry is written in its own language rather than in the language currently on
 * screen. Somebody who has the app in a language they cannot read is exactly the person
 * most likely to open this dialog, and "Japanese" spelled in Russian is no help to them.
 *
 * Each row is also laid out in its own script's direction, so the Arabic entry reads
 * right to left even while the rest of the dialog is left to right.
 */
@Composable
internal fun LanguageDialog(
    modifier: Modifier = Modifier,
    selectedTag: String,
    onDismissRequest: () -> Unit,
    onSelect: (String) -> Unit,
) {
    var draft by remember(selectedTag) { mutableStateOf(selectedTag) }

    DialogContainer(
        modifier = modifier,
        onDismissRequest = onDismissRequest,
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(10.dp),
        ) {
            Text(
                modifier = Modifier.padding(10.dp),
                text = stringResource(R.string.language),
                style = MaterialTheme.typography.titleLarge,
            )

            // Above the list, not below it: it qualifies every option except the first two,
            // and a caveat read after choosing is a caveat that did no work.
            Text(
                modifier = Modifier.padding(horizontal = 10.dp),
                text = stringResource(commonR.string.language_ai_notice),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )

            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(max = 380.dp)
                    .verticalScroll(rememberScrollState())
                    .selectableGroup(),
            ) {
                LanguageRow(
                    label = stringResource(commonR.string.language_system),
                    selected = draft == AppLocale.SYSTEM,
                    onClick = { draft = AppLocale.SYSTEM },
                )

                AppLocale.LANGUAGES.forEach { (tag, endonym) ->
                    LanguageRow(
                        label = endonym,
                        selected = draft == tag,
                        rtl = tag == "ar",
                        onClick = { draft = tag },
                    )
                }
            }

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(10.dp),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(R.string.cancel))
                }

                TextButton(onClick = { onSelect(draft) }) {
                    Text(text = stringResource(R.string.change))
                }
            }
        }
    }
}

@Composable
private fun LanguageRow(
    modifier: Modifier = Modifier,
    label: String,
    selected: Boolean,
    rtl: Boolean = false,
    onClick: () -> Unit,
) {
    val direction = if (rtl) LayoutDirection.Rtl else LayoutDirection.Ltr

    CompositionLocalProvider(
        LocalLayoutDirection provides direction,
    ) {
        Row(
            modifier = modifier
                .fillMaxWidth()
                .height(56.dp)
                .selectable(
                    selected = selected,
                    role = Role.RadioButton,
                    onClick = onClick,
                )
                .padding(horizontal = 16.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            RadioButton(selected = selected, onClick = null)

            Text(
                modifier = Modifier.padding(start = 10.dp),
                text = label,
                style = MaterialTheme.typography.bodyLarge,
                textAlign = TextAlign.Start,
            )
        }
    }
}
