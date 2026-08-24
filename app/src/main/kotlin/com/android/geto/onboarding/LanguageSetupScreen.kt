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
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.res.stringResource
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
    var draft by remember { mutableStateOf(initialTag) }

    Surface(modifier = modifier.fillMaxSize()) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .windowInsetsPadding(WindowInsets.safeDrawing)
                .padding(horizontal = 24.dp),
        ) {
            Text(
                modifier = Modifier.padding(top = 32.dp),
                text = stringResource(R.string.language_setup_title),
                style = MaterialTheme.typography.headlineMedium,
            )

            Text(
                modifier = Modifier.padding(top = 12.dp),
                text = stringResource(R.string.language_setup_subtitle),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )

            Text(
                modifier = Modifier.padding(top = 16.dp),
                text = stringResource(commonR.string.language_ai_notice),
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
                    label = stringResource(commonR.string.language_system),
                    selected = draft == AppLocale.SYSTEM,
                    onClick = { draft = AppLocale.SYSTEM },
                )

                AppLocale.LANGUAGES.forEach { (tag, endonym) ->
                    LanguageChoice(
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
                    .padding(vertical = 16.dp),
                horizontalArrangement = Arrangement.Center,
            ) {
                Button(onClick = { onContinue(draft) }) {
                    Text(text = stringResource(R.string.language_setup_continue))
                }
            }
        }
    }
}

/**
 * One language, written in its own script and laid out in its own direction.
 *
 * The direction is per row rather than per screen: the page around it is still in whatever
 * language the app is currently using, and flipping the whole screen for one Arabic entry
 * in the list would move the scrollbar and the button under the reader's thumb.
 */
@Composable
private fun LanguageChoice(
    modifier: Modifier = Modifier,
    label: String,
    selected: Boolean,
    rtl: Boolean = false,
    onClick: () -> Unit,
) {
    CompositionLocalProvider(
        LocalLayoutDirection provides if (rtl) LayoutDirection.Rtl else LayoutDirection.Ltr,
    ) {
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
