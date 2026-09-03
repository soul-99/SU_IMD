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
package com.android.geto.onboarding

import android.view.View
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.selectableGroup
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import com.android.geto.R
import com.android.geto.common.AppLocale
import com.android.geto.common.R as commonR

/**
 * The first thing a new install shows, ahead of the permissions screen.
 *
 * It comes first for a plain reason: every screen after it is instructions, and instructions
 * in a language the reader does not have are worse than no instructions. Sending someone
 * through the setup steps and only then offering to change the language would mean asking
 * them to read the important part twice.
 *
 * Shown once. After that the same list lives in Settings under UI.
 */
@Composable
fun LanguageSetupScreen(
    modifier: Modifier = Modifier,
    initialTag: String,
    onContinue: (String) -> Unit,
) {
    var draft by rememberSaveable { mutableStateOf(initialTag) }

    val baseContext = LocalContext.current

    // Resolve this screen's own strings against the tapped language, so the page redraws itself
    // in whatever the reader is previewing the moment they tap it - the title, the notes and the
    // Continue button, all in that language - without committing the choice, which the Continue
    // button still does through onContinue. The endonyms in the list stay in their own script.
    val preview = remember(draft) { AppLocale.previewContext(baseContext, draft) }

    val pageDirection = if (
        preview.resources.configuration.layoutDirection == View.LAYOUT_DIRECTION_RTL
    ) {
        LayoutDirection.Rtl
    } else {
        LayoutDirection.Ltr
    }

    CompositionLocalProvider(LocalLayoutDirection provides pageDirection) {
        Surface(modifier = modifier.fillMaxSize()) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .windowInsetsPadding(WindowInsets.safeDrawing)
                    .padding(horizontal = 24.dp),
            ) {
                Text(
                    modifier = Modifier.padding(top = 32.dp),
                    text = preview.getString(R.string.language_setup_title),
                    style = MaterialTheme.typography.headlineMedium,
                )

                Text(
                    modifier = Modifier.padding(top = 12.dp),
                    text = preview.getString(R.string.language_setup_subtitle),
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )

                Text(
                    modifier = Modifier.padding(top = 16.dp),
                    text = preview.getString(commonR.string.language_ai_notice),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )

                Column(
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxWidth()
                        .padding(top = 16.dp)
                        .verticalScroll(rememberScrollState())
                        .selectableGroup(),
                ) {
                    LanguageChoice(
                        label = preview.getString(commonR.string.language_system),
                        selected = draft == AppLocale.SYSTEM,
                        onClick = { draft = AppLocale.SYSTEM },
                    )

                    AppLocale.LANGUAGES.forEach { (tag, endonym) ->
                        LanguageChoice(
                            label = endonym,
                            selected = draft == tag,
                            onClick = { draft = tag },
                        )
                    }
                }

                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 16.dp),
                    horizontalArrangement = Arrangement.Center,
                ) {
                    Button(onClick = { onContinue(draft) }) {
                        Text(text = preview.getString(R.string.language_setup_continue))
                    }
                }
            }
        }
    }
}

/**
 * One language, written in its own script and always laid out left to right.
 *
 * ⚠ **Script direction and row direction are not the same question**, and this row used to
 * answer the first with the second. Arabic text renders right to left from its own characters
 * whatever the row does; [LayoutDirection] only decides which end of the row the radio button
 * sits at. So the Arabic entry gained nothing from a right-to-left row and lost the thing a
 * picker needs, which is one column of radio buttons the eye can run down - the author's
 * *"show all languages from left and the toggle too"*.
 *
 * Pinned rather than left to follow the page, so previewing Arabic does not flip the list under
 * the reader while they are still choosing from it. The page around it still follows the
 * preview, which is what makes the preview worth having.
 */
@Composable
private fun LanguageChoice(
    modifier: Modifier = Modifier,
    label: String,
    selected: Boolean,
    onClick: () -> Unit,
) {
    CompositionLocalProvider(LocalLayoutDirection provides LayoutDirection.Ltr) {
        Row(
            modifier = modifier
                .fillMaxWidth()
                .height(56.dp)
                .selectable(
                    selected = selected,
                    role = Role.RadioButton,
                    onClick = onClick,
                ),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            RadioButton(selected = selected, onClick = null)

            Text(
                modifier = Modifier.padding(start = 12.dp),
                text = label,
                style = MaterialTheme.typography.bodyLarge,
                textAlign = TextAlign.Start,
            )
        }
    }
}
