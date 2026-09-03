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

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import com.android.geto.designsystem.icon.GetoIcons
import com.android.geto.domain.model.TaskerIntegration
import com.android.geto.feature.settings.R

// The intent field labels are shown in English on purpose: they name the exact fields Tasker
// and MacroDroid put in their own "Send Intent" editors, which are English whatever the device
// locale is, so translating them here would only make them harder to match up.
private const val FIELD_TYPE = "Type"
private const val FIELD_PACKAGE = "Package"
private const val FIELD_CLASS = "Class"
private const val FIELD_ACTION = "Action"
private const val FIELD_EXTRA = "Extra name"
private const val TYPE_BROADCAST = "Broadcast"
private const val TYPE_ACTIVITY = "Activity"

/**
 * Everything an automation app needs to drive IMD, laid out to be copied field by field.
 *
 * Four functions, three of them broadcasts guarded by the one auth key at the top and one an
 * activity that needs none. The values are the contract in [TaskerIntegration]; nothing here
 * is typed by hand, so the screen and the receiver cannot disagree about an action string.
 *
 * The key is ensured on open rather than generated on a button, so the screen always has one
 * to show and simply opening this page is what turns the integration on.
 */
@Composable
internal fun TaskerIntegrationPage(
    modifier: Modifier = Modifier,
    authKey: String,
    onEnsureAuthKey: () -> Unit,
    onRefreshAuthKey: () -> Unit,
    onDismissRequest: () -> Unit,
) {
    LaunchedEffect(Unit) { onEnsureAuthKey() }

    val packageName = LocalContext.current.packageName

    SettingsPage(
        modifier = modifier,
        title = stringResource(R.string.tasker_integration),
        onDismissRequest = onDismissRequest,
        actions = {
            TextButton(onClick = onDismissRequest) {
                Text(text = stringResource(R.string.close))
            }
        },
    ) {
        Text(
            modifier = Modifier.padding(horizontal = 10.dp),
            text = stringResource(R.string.tasker_integration_intro),
            style = MaterialTheme.typography.bodyMedium,
        )

        Spacer(modifier = Modifier.height(8.dp))

        // First, and red, because it is the one thing here that keeps the key private: an
        // intent sent by action alone reaches every app listening for it, key and all. Named
        // to the package, it reaches only IMD.
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 10.dp, vertical = 6.dp),
        ) {
            Icon(
                modifier = Modifier.size(16.dp),
                imageVector = GetoIcons.Info,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.error,
            )

            Spacer(modifier = Modifier.width(8.dp))

            Text(
                text = stringResource(R.string.tasker_integration_package_warning),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.error,
            )
        }

        Spacer(modifier = Modifier.height(12.dp))

        // The auth key itself, shared by all three broadcasts and shown once. Refresh is beside
        // it because rotating the key is the only way to revoke a macro that has the old one.
        ValueRow(label = stringResource(R.string.tasker_auth_key), value = authKey)

        Text(
            modifier = Modifier.padding(horizontal = 10.dp),
            text = stringResource(R.string.tasker_auth_key_note),
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )

        Row(modifier = Modifier.padding(horizontal = 6.dp)) {
            TextButton(onClick = onRefreshAuthKey) {
                Icon(
                    modifier = Modifier.size(18.dp),
                    imageVector = GetoIcons.Refresh,
                    contentDescription = null,
                )

                Spacer(modifier = Modifier.width(8.dp))

                Text(text = stringResource(R.string.tasker_refresh_key))
            }
        }

        FunctionSection(title = stringResource(R.string.tasker_fn_services)) {
            // The one function with no key, because it only opens a screen the user then
            // touches. Said here so its missing Extra row does not read as an omission.
            Text(
                modifier = Modifier.padding(horizontal = 10.dp),
                text = stringResource(R.string.tasker_fn_services_note),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )

            Spacer(modifier = Modifier.height(4.dp))

            ValueRow(label = FIELD_TYPE, value = TYPE_ACTIVITY)
            ValueRow(label = FIELD_PACKAGE, value = packageName)
            ValueRow(label = FIELD_CLASS, value = TaskerIntegration.SERVICES_MANAGER_CLASS)
            ValueRow(label = FIELD_ACTION, value = TaskerIntegration.ACTION_VIEW)
        }

        // ⚠ **Directly under the manager, at the author's instruction**, and before the two
        // one-way functions: it is the one an automation reaches for first, because it needs no
        // knowledge of which way the device currently is.
        BroadcastSection(
            title = stringResource(R.string.tasker_fn_toggle),
            packageName = packageName,
            action = TaskerIntegration.ACTION_TOGGLE_SETTINGS,
        )

        BroadcastSection(
            title = stringResource(R.string.tasker_fn_hide),
            packageName = packageName,
            action = TaskerIntegration.ACTION_HIDE_SETTINGS,
        )

        // ⚠ **Not conditional any more, and that is the change.** Its predecessor appeared
        // only under the memory function, because offering it in the other mode would have
        // documented a button the user had not chosen. This one settles whatever is
        // outstanding the way the current Unhiding framework says, so it is the right thing
        // to offer under either — and it is the route that answers the old objection to the
        // memory function, that a lost notification leaves no way back.
        BroadcastSection(
            title = stringResource(R.string.tasker_fn_unhide),
            packageName = packageName,
            action = TaskerIntegration.ACTION_UNHIDE_SETTINGS,
        )

        // ⚠ **Last, at the author's instruction**: manager, hide, unhide, revert. It is the
        // order of a session rather than the order these were built in.
        BroadcastSection(
            title = stringResource(R.string.tasker_fn_revert_default),
            packageName = packageName,
            action = TaskerIntegration.ACTION_REVERT_TO_DEFAULT,
        )
    }
}

/** The Type/Package/Action/Extra a broadcast trigger needs, the same shape for all three. */
@Composable
private fun BroadcastSection(
    title: String,
    packageName: String,
    action: String,
) {
    FunctionSection(title = title) {
        ValueRow(label = FIELD_TYPE, value = TYPE_BROADCAST)
        ValueRow(label = FIELD_PACKAGE, value = packageName)
        ValueRow(label = FIELD_ACTION, value = action)
        // The name only; its value is the auth key at the top, which the note spells out so
        // the row does not have to repeat the whole key under every function.
        ValueRow(label = FIELD_EXTRA, value = TaskerIntegration.EXTRA_AUTH_KEY)
    }
}

@Composable
private fun FunctionSection(
    title: String,
    content: @Composable () -> Unit,
) {
    Spacer(modifier = Modifier.height(8.dp))

    HorizontalDivider()

    Spacer(modifier = Modifier.height(8.dp))

    Text(
        modifier = Modifier.padding(horizontal = 10.dp),
        text = title,
        style = MaterialTheme.typography.titleSmall,
        color = MaterialTheme.colorScheme.primary,
    )

    Spacer(modifier = Modifier.height(4.dp))

    content()
}

/**
 * A labelled value with a copy button.
 *
 * The value is monospaced because every one of them is something typed back verbatim into
 * another app - an action string, a package, a key - where a lower-case l read as a 1 is a
 * trigger that silently never fires.
 */
@Composable
private fun ValueRow(
    label: String,
    value: String,
) {
    val clipboard = LocalClipboardManager.current

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 10.dp, vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = label,
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )

            Text(
                text = value,
                style = MaterialTheme.typography.bodyMedium.copy(fontFamily = FontFamily.Monospace),
            )
        }

        IconButton(onClick = { clipboard.setText(AnnotatedString(value)) }) {
            Icon(
                modifier = Modifier.size(20.dp),
                imageVector = GetoIcons.Copy,
                contentDescription = stringResource(R.string.tasker_copy),
            )
        }
    }
}
