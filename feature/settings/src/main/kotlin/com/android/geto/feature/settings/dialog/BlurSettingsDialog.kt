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
package com.android.geto.feature.settings.dialog

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Slider
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.designsystem.component.supportsWindowBlur
import com.android.geto.domain.model.BLUR_FADE_RANGE
import com.android.geto.domain.model.BLUR_RADIUS_RANGE
import com.android.geto.domain.model.BLUR_TINT_RANGE
import com.android.geto.domain.model.DEFAULT_FADE_DP
import com.android.geto.domain.model.DEFAULT_RADIUS_DP
import com.android.geto.domain.model.DEFAULT_TINT_PERCENT
import com.android.geto.feature.settings.R

/**
 * The three numbers behind the author's "Progressive UI blur".
 *
 * ⚠ **Live, not a draft, and this dialog is the exception rather than the rule.** Every other
 * picker in this app holds its changes until Save, because a half-made selection of accessibility
 * services is a state the device should never be put into. These are three sliders whose only
 * effect is how the app looks, and the whole reason for a slider rather than three text fields is
 * that you drag it and watch. Holding the value until Save would mean choosing a blur without
 * seeing it — which is how the app came to have a 6 dp blur nobody could see for four rounds.
 *
 * ⚠ **Reset rather than Cancel.** With a live dialog, Cancel would have to remember and restore
 * three numbers, and a Cancel that silently rewrites settings is worse than no Cancel. Reset says
 * what it does and goes back to the defaults, which is the state somebody who has made a mess of
 * the sliders actually wants.
 *
 * ⚠ **One set of numbers for the pages and the window**, at the author's instruction: *"This blur
 * settings applies to both the UI as well as the window"*. Radius and tint reach the settings
 * manager's frosted card as well as the page bands; the ramp length is a page idea and has nothing
 * to say about a window, which is why it is described as the fade rather than as a third dimension
 * of the blur.
 */
@Composable
internal fun BlurSettingsDialog(
    modifier: Modifier = Modifier,
    radiusDp: Int,
    tintPercent: Int,
    fadeDp: Int,
    onDismissRequest: () -> Unit,
    onUpdateBlurSettings: (radiusDp: Int, tintPercent: Int, fadeDp: Int) -> Unit,
) {
    // Keyed on the stored values, so a write from anywhere else while this is open is picked up
    // rather than fought over.
    var radius by remember(radiusDp) { mutableIntStateOf(radiusDp) }

    var tint by remember(tintPercent) { mutableIntStateOf(tintPercent) }

    var fade by remember(fadeDp) { mutableIntStateOf(fadeDp) }

    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = stringResource(R.string.blur_settings_title),
                style = MaterialTheme.typography.titleLarge,
            )

            Spacer(modifier = Modifier.height(12.dp))

            Text(
                text = stringResource(R.string.blur_settings_description),
                style = MaterialTheme.typography.bodyMedium,
            )

            Spacer(modifier = Modifier.height(8.dp))

            // ⚠ **A readout, not a warning — r23.** The author asked whether his S22 Ultra simply
            // cannot frost a window. It is the platform's answer to give, not this app's guess, so
            // the dialog asks and prints it. The page bands do not depend on this and keep working
            // either way, which is what the second line says.
            Text(
                text = if (supportsWindowBlur()) {
                    stringResource(R.string.blur_settings_window_supported)
                } else {
                    stringResource(R.string.blur_settings_window_unsupported)
                },
                style = MaterialTheme.typography.bodySmall,
                color = if (supportsWindowBlur()) {
                    MaterialTheme.colorScheme.primary
                } else {
                    MaterialTheme.colorScheme.onSurfaceVariant
                },
            )

            Spacer(modifier = Modifier.height(16.dp))

            BlurSlider(
                label = stringResource(R.string.blur_settings_radius),
                hint = stringResource(R.string.blur_settings_radius_hint),
                value = radius,
                range = BLUR_RADIUS_RANGE,
                readout = stringResource(R.string.blur_settings_dp, radius),
                onValueChange = {
                    radius = it

                    onUpdateBlurSettings(it, tint, fade)
                },
            )

            BlurSlider(
                label = stringResource(R.string.blur_settings_tint),
                hint = stringResource(R.string.blur_settings_tint_hint),
                value = tint,
                range = BLUR_TINT_RANGE,
                readout = stringResource(R.string.blur_settings_percent, tint),
                onValueChange = {
                    tint = it

                    onUpdateBlurSettings(radius, it, fade)
                },
            )

            BlurSlider(
                label = stringResource(R.string.blur_settings_fade),
                hint = stringResource(R.string.blur_settings_fade_hint),
                value = fade,
                range = BLUR_FADE_RANGE,
                readout = stringResource(R.string.blur_settings_dp, fade),
                onValueChange = {
                    fade = it

                    onUpdateBlurSettings(radius, tint, it)
                },
            )

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                TextButton(
                    onClick = {
                        radius = DEFAULT_RADIUS_DP

                        tint = DEFAULT_TINT_PERCENT

                        fade = DEFAULT_FADE_DP

                        onUpdateBlurSettings(
                            DEFAULT_RADIUS_DP,
                            DEFAULT_TINT_PERCENT,
                            DEFAULT_FADE_DP,
                        )
                    },
                ) {
                    Text(text = stringResource(R.string.blur_settings_reset))
                }

                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(R.string.close))
                }
            }
        }
    }
}

/**
 * One slider, its name, what it does and where it currently is.
 *
 * ⚠ **`steps` is the range minus the two ends**, so every stop is a whole unit. A slider that can
 * land on 13.4 dp reports 13 and stores 13, and the next time the dialog opens the handle is
 * somewhere the user did not leave it.
 */
@Composable
private fun BlurSlider(
    label: String,
    hint: String,
    value: Int,
    range: IntRange,
    readout: String,
    onValueChange: (Int) -> Unit,
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(
            modifier = Modifier.weight(1f),
            text = label,
            style = MaterialTheme.typography.bodyLarge,
        )

        Text(
            text = readout,
            style = MaterialTheme.typography.labelLarge,
            color = MaterialTheme.colorScheme.primary,
        )
    }

    Text(
        text = hint,
        style = MaterialTheme.typography.bodySmall,
        color = MaterialTheme.colorScheme.onSurfaceVariant,
    )

    Slider(
        value = value.toFloat(),
        onValueChange = { onValueChange(it.toInt()) },
        valueRange = range.first.toFloat()..range.last.toFloat(),
        steps = (range.last - range.first - 1).coerceAtLeast(0),
    )

    Spacer(modifier = Modifier.height(8.dp))
}
