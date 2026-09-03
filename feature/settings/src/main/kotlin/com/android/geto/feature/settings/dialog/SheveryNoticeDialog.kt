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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.feature.settings.R

/**
 * What choosing Shevery actually means, shown from the caution beside the option and again
 * every time the option is switched on.
 *
 * ⚠ **Rewritten in v3.** It used to be six bullet points about how Shevery behaves. The author
 * replaced them with a setup checklist — the same four steps the Thedjchi pop-up carries, for
 * a different app — followed by a `How this works` section that keeps only the part of the old
 * dialog that explained the mechanism.
 *
 * Shevery is supported, but not driven. It has no start or stop intent, so IMD cannot ask it
 * for anything: the service goes down when the debugging transport does, and comes back when
 * Shevery's own ErrorProtect watchdog notices the transport again. The flow chart is that
 * sentence as a picture, and it is why the wait for Shevery is forty seconds where Thedjchi's
 * is eight.
 *
 * The last point is in the error colour because it is the one that is a risk rather than an
 * inconvenience.
 *
 * ⚠ **Two of the old points are gone rather than moved.** The "slight delay" point is now
 * carried by the DOOA picker's own first line, in red, where the delay actually applies; and
 * "Shizuku service toggles will become hidden under hide and unhide settings" is replaced by
 * points four and five, which say the same thing far more precisely — Shevery's service and
 * Display over other apps are operable in the **settings manager** and nowhere else, and an app
 * launch hides neither.
 */
@Composable
fun SheveryNoticeDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
    onUnderstood: () -> Unit = onDismissRequest,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(
            modifier = Modifier
                .verticalScroll(rememberScrollState())
                .padding(20.dp),
        ) {
            ShizukuSetupBody(
                steps = listOf(
                    R.string.shevery_setup_1 to R.string.shizuku_setup_on,
                    R.string.shevery_setup_2 to R.string.shizuku_setup_on,
                    R.string.shevery_setup_3 to R.string.shizuku_setup_off,
                    R.string.shevery_setup_4 to null,
                ),
                rebootId = R.string.shevery_setup_reboot,
            )

            SetupDivider()

            Text(
                text = stringResource(R.string.shevery_how_title),
                style = MaterialTheme.typography.titleMedium,
            )

            Spacer(modifier = Modifier.height(10.dp))

            HowThisWorksPoint(
                number = 1,
                text = stringResource(R.string.shevery_notice_point_errorprotect),
            )

            HowThisWorksPoint(number = 2, text = "") {
                SheveryFlowChart()
            }

            HowThisWorksPoint(number = 3, text = stringResource(R.string.shevery_how_delay))

            // ⚠ **Four and five are the scope of Shevery support, not advice about it** - the
            // author added them after r4a, and they are what settles where Shevery's two
            // targets can be operated at all. Bold and red for that reason.
            HowThisWorksPoint(
                number = 4,
                text = stringResource(R.string.shevery_how_manager_only),
                color = MaterialTheme.colorScheme.error,
                bold = true,
            )

            HowThisWorksPoint(
                number = 5,
                text = stringResource(R.string.shevery_how_no_launch),
                color = MaterialTheme.colorScheme.error,
                bold = true,
            )

            HowThisWorksPoint(
                number = 6,
                text = stringResource(R.string.shevery_how_warning),
                color = MaterialTheme.colorScheme.error,
            )

            Spacer(modifier = Modifier.height(12.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                // The only route that accepts the choice. Dismissing any other way - the
                // scrim, the back gesture - leaves the picker where it was, because this
                // dialog is the explanation the choice is conditional on.
                TextButton(onClick = onUnderstood) {
                    Text(text = stringResource(R.string.understood))
                }
            }
        }
    }
}
