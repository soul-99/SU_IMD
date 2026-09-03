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
package com.android.geto.feature.appsettings.shortcut

import android.widget.Toast
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.domain.model.GetPinShortcutResult
import com.android.geto.domain.model.RequestPinShortcutResult
import com.android.geto.feature.appsettings.R
import com.android.geto.feature.appsettings.dialog.RequestPinShortcutDialog
import com.android.geto.feature.appsettings.dialog.UpdatePinShortcutDialog
import kotlinx.coroutines.delay
import com.android.geto.common.R as commonR

/**
 * The create-shortcut dialog for one app, wherever it is opened from.
 *
 * Public and self-contained for the same reason [com.android.geto.feature.apps.manager]'s
 * manager route is: creating a shortcut is now a long press on an app in either tab, and
 * those live in another module. Keeping the use-case wiring in one place is what stops the
 * two entry points drifting from the one on the app-settings screen.
 *
 * Whether this shows "create" or "edit" is not the caller's business — it is decided by
 * whether a pinned shortcut for this component already exists, which only the use case can
 * answer.
 */
@Composable
fun ShortcutRoute(
    modifier: Modifier = Modifier,
    componentName: String,
    activityLabel: String,
    onDismissRequest: () -> Unit,
    viewModel: ShortcutViewModel = hiltViewModel(),
) {
    val context = LocalContext.current

    val target by viewModel.target.collectAsStateWithLifecycle()

    val requestResult by viewModel.requestPinShortcutResult.collectAsStateWithLifecycle()

    // Bumped by Retry, so a second attempt is a fresh read rather than a reopened dialog.
    var attempt by remember { mutableIntStateOf(0) }

    var waited by remember { mutableStateOf(false) }

    LaunchedEffect(componentName, attempt) {
        waited = false

        viewModel.start(componentName = componentName)

        delay(WAIT_MILLIS)

        waited = true
    }

    // A launcher that cannot pin is the one outcome the user has to be told about: nothing
    // appears on the homescreen and nothing else would explain why. The supported case
    // needs no message, because the launcher puts up its own confirmation.
    LaunchedEffect(requestResult) {
        when (requestResult) {
            RequestPinShortcutResult.UnsupportedLauncher -> {
                Toast.makeText(
                    context,
                    R.string.unsupported_launcher,
                    Toast.LENGTH_SHORT,
                ).show()

                viewModel.consumeRequestResult()

                onDismissRequest()
            }

            RequestPinShortcutResult.SupportedLauncher -> {
                viewModel.consumeRequestResult()

                onDismissRequest()
            }

            null -> Unit
        }
    }

    // Nothing is drawn until the lookup for *this* app has landed. The ViewModel belongs
    // to the tab and outlives the dialog, so without this check the previous app's result
    // is what the first composition sees -- and the label fields, seeded once, keep it.
    //
    // ⚠ **A spinner in front of it, since r4q.** The check is right and stays; what was wrong
    // was drawing *nothing*, because the lookup is an icon read plus a ShortcutManager query
    // and both are cold on the first press of a session. The author's report - "first time
    // create shortcut does not open but it does on second time, this bug does not occur every
    // time" - is that dead interval, and the second press feeling instant is the same lookup
    // being warm. Nothing of the previous app is drawn here, so the bug the return exists for
    // cannot come back through it.
    val loaded = target?.takeIf { it.componentName == componentName } ?: run {
        ShortcutLoadingDialog(
            modifier = modifier,
            failed = waited,
            onRetry = { attempt += 1 },
            onDismissRequest = onDismissRequest,
        )

        return
    }

    when (val result = loaded.result) {
        GetPinShortcutResult.RequestPinShortcut -> {
            RequestPinShortcutDialog(
                modifier = modifier,
                icon = loaded.icon,
                activityLabel = activityLabel,
                onDismissRequest = onDismissRequest,
                onRequestPinShortcut = { bytes, shortLabel, longLabel ->
                    viewModel.requestPinShortcut(
                        componentName = componentName,
                        icon = bytes,
                        shortLabel = shortLabel,
                        longLabel = longLabel,
                    )
                },
            )
        }

        is GetPinShortcutResult.UpdatePinShortcut -> {
            UpdatePinShortcutDialog(
                modifier = modifier,
                icon = loaded.icon,
                getoShortcutInfoCompat = result.getoShortcutInfoCompat,
                onDismissRequest = onDismissRequest,
                onUpdatePinShortcut = { bytes, shortLabel, longLabel ->
                    viewModel.updatePinShortcut(
                        componentName = componentName,
                        icon = bytes,
                        shortLabel = shortLabel,
                        longLabel = longLabel,
                    )

                    onDismissRequest()
                },
            )
        }

        // The launcher cannot pin anything. Nothing is drawn: a dialog that appears and
        // then reports that it cannot do what it was opened for is worse than silence, and
        // the toast above covers the case where the user has already pressed Add.
        GetPinShortcutResult.UnsupportedLauncher -> Unit
    }
}

/**
 * What a long press shows while the icon and the existing-shortcut lookup are still running —
 * and what it shows when they never finish.
 *
 * ⚠ **A dialog rather than nothing.** The lookup is fast once warm and slow exactly once per
 * session, and drawing nothing for that interval is indistinguishable from the press having been
 * missed - which is what the author reported and what made him press again.
 *
 * ⚠ **[failed] is a backstop, not the fix.** The fix is in `ShortcutViewModel.start`, which no
 * longer loses its target when a read throws. This is here because if the cause turns out to be
 * something else again, the author gets a button rather than a wedged dialog - and Retry re-runs
 * the read rather than reopening anything.
 *
 * Dismissible throughout, so a press that turns out to have been a mistake is not a wait.
 */
@Composable
private fun ShortcutLoadingDialog(
    modifier: Modifier = Modifier,
    failed: Boolean,
    onRetry: () -> Unit,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        if (!failed) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(32.dp),
                contentAlignment = Alignment.Center,
            ) {
                CircularProgressIndicator()
            }

            return@DialogContainer
        }

        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = stringResource(R.string.shortcut_lookup_failed),
                style = MaterialTheme.typography.bodyMedium,
            )

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(commonR.string.cancel))
                }

                TextButton(onClick = onRetry) {
                    Text(text = stringResource(commonR.string.retry))
                }
            }
        }
    }
}

/**
 * How long the spinner is held before it offers Retry.
 *
 * The same eight seconds the Display over other apps setup step waits, and for the same reason:
 * long enough not to accuse a slow device of failing, short enough that a wedged one does not
 * look like a hung app.
 */
private const val WAIT_MILLIS = 8_000L
