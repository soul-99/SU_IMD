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
package com.android.geto.feature.settings

import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.annotation.VisibleForTesting
import androidx.compose.foundation.Image
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.runtime.snapshotFlow
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.graphics.ColorFilter
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.LinkAnnotation
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.TextLinkStyles
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.text.withLink
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.designsystem.icon.GetoIcons
import com.android.geto.designsystem.theme.supportsDynamicTheming
import com.android.geto.domain.model.AccessibilityServiceData
import com.android.geto.domain.model.Theme
import com.android.geto.domain.model.UserData
import com.android.geto.feature.settings.dialog.AccessibilityServicesDialog
import com.android.geto.feature.settings.dialog.ThemeDialog
import com.android.geto.service.SettingsObserverService
import kotlinx.coroutines.FlowPreview
import kotlinx.coroutines.flow.debounce
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.drop
import kotlin.time.Duration.Companion.milliseconds

/** How long the Shizuku text fields wait after the last keystroke before persisting. */
private val COMMIT_DEBOUNCE = 500.milliseconds

private const val AUTHOR_LINK_TAG = "author"
private const val AUTHOR_EMAIL = "utkarshrajput1999@gmail.com"
private const val AUTHOR_GITHUB_URL = "https://github.com/soul-99"
private const val GETO_REPOSITORY_URL = "https://github.com/JackEblan/Geto"
private const val LICENCE_URL = "https://www.gnu.org/licenses/gpl-3.0"
private const val SHIZUKU_FORK_URL = "https://github.com/thedjchi/Shizuku/releases"

@Composable
internal fun SettingsRoute(
    modifier: Modifier = Modifier,
    viewModel: SettingsViewModel = hiltViewModel(),
) {
    val settingsUiState by viewModel.settingsUiState.collectAsStateWithLifecycle()

    val isServiceRunning by viewModel.isServiceRunning.collectAsStateWithLifecycle()

    val accessibilityServices by viewModel.accessibilityServices.collectAsStateWithLifecycle()

    LaunchedEffect(Unit) {
        viewModel.refreshAccessibilityServices()
    }

    SettingsScreen(
        modifier = modifier,
        settingsUiState = settingsUiState,
        isServiceRunning = isServiceRunning,
        accessibilityServices = accessibilityServices,
        onUpdateTheme = viewModel::updateTheme,
        onUpdateDynamicTheme = viewModel::updateDynamicTheme,
        onUpdateRestartShizuku = viewModel::updateRestartShizuku,
        onUpdateShizukuAuthKey = viewModel::updateShizukuAuthKey,
        onUpdateShizukuPackageName = viewModel::updateShizukuPackageName,
        onUpdateShizukuStartAction = viewModel::updateShizukuStartAction,
        onUpdateManagedAccessibilityServices = viewModel::updateManagedAccessibilityServices,
        onRefreshAccessibilityServices = viewModel::refreshAccessibilityServices,
    )
}

@VisibleForTesting
@Composable
internal fun SettingsScreen(
    modifier: Modifier = Modifier,
    settingsUiState: SettingsUiState,
    isServiceRunning: Boolean,
    accessibilityServices: List<AccessibilityServiceData>,
    onUpdateTheme: (Theme) -> Unit,
    onUpdateDynamicTheme: (Boolean) -> Unit,
    onUpdateRestartShizuku: (Boolean) -> Unit,
    onUpdateShizukuAuthKey: (String) -> Unit,
    onUpdateShizukuPackageName: (String) -> Unit,
    onUpdateShizukuStartAction: (String) -> Unit,
    onUpdateManagedAccessibilityServices: (List<String>) -> Unit,
    onRefreshAccessibilityServices: () -> Unit,
) {
    // The scroll modifier lives on the content column rather than here: a Box that scrolls
    // measures its child with an infinite height, so it would wrap the spinner and centre
    // it inside itself, i.e. at the top of the screen.
    Box(modifier = modifier.fillMaxSize()) {
        when (settingsUiState) {
            SettingsUiState.Loading -> {
                CircularProgressIndicator(modifier = Modifier.align(Alignment.Center))
            }

            is SettingsUiState.Success -> {
                Success(
                    userData = settingsUiState.userData,
                    isServiceRunning = isServiceRunning,
                    accessibilityServices = accessibilityServices,
                    onUpdateDynamicTheme = onUpdateDynamicTheme,
                    onUpdateTheme = onUpdateTheme,
                    onUpdateRestartShizuku = onUpdateRestartShizuku,
                    onUpdateShizukuAuthKey = onUpdateShizukuAuthKey,
                    onUpdateShizukuPackageName = onUpdateShizukuPackageName,
                    onUpdateShizukuStartAction = onUpdateShizukuStartAction,
                    onUpdateManagedAccessibilityServices = onUpdateManagedAccessibilityServices,
                    onRefreshAccessibilityServices = onRefreshAccessibilityServices,
                )
            }
        }
    }
}

@Composable
private fun Success(
    modifier: Modifier = Modifier,
    userData: UserData,
    isServiceRunning: Boolean,
    accessibilityServices: List<AccessibilityServiceData>,
    onUpdateDynamicTheme: (Boolean) -> Unit,
    onUpdateTheme: (Theme) -> Unit,
    onUpdateRestartShizuku: (Boolean) -> Unit,
    onUpdateShizukuAuthKey: (String) -> Unit,
    onUpdateShizukuPackageName: (String) -> Unit,
    onUpdateShizukuStartAction: (String) -> Unit,
    onUpdateManagedAccessibilityServices: (List<String>) -> Unit,
    onRefreshAccessibilityServices: () -> Unit,
) {
    val context = LocalContext.current

    var showThemeDialog by remember { mutableStateOf(false) }

    var showAccessibilityServicesDialog by remember { mutableStateOf(false) }

    var selectedTheme by remember { mutableIntStateOf(Theme.entries.indexOf(userData.theme)) }

    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState()),
    ) {
        DynamicThemeSetting(
            dynamicTheme = userData.dynamicTheme,
            onUpdateDynamicTheme = onUpdateDynamicTheme,
        )

        SettingsColumn(
            title = stringResource(R.string.theme),
            subtitle = userData.theme.getTitle(),
            onClick = { showThemeDialog = true },
        )

        SettingsColumn(
            title = stringResource(R.string.settings_observer_service),
            subtitle = if (isServiceRunning) {
                stringResource(R.string.stop_service)
            } else {
                stringResource(R.string.start_service)
            },
            onClick = {
                val intent = Intent(context, SettingsObserverService::class.java)

                if (isServiceRunning) {
                    context.stopService(intent)
                } else {
                    ContextCompat.startForegroundService(context, intent)
                }
            },
        )

        SectionDivider(title = stringResource(R.string.shizuku))

        ShizukuSection(
            userData = userData,
            onUpdateRestartShizuku = onUpdateRestartShizuku,
            onUpdateShizukuAuthKey = onUpdateShizukuAuthKey,
            onUpdateShizukuPackageName = onUpdateShizukuPackageName,
            onUpdateShizukuStartAction = onUpdateShizukuStartAction,
        )

        SectionDivider(title = stringResource(R.string.accessibility))

        SettingsColumn(
            title = stringResource(R.string.accessibility_services),
            subtitle = accessibilityServicesSubtitle(
                accessibilityServices = accessibilityServices,
                managed = userData.managedAccessibilityServices,
            ),
            onClick = {
                onRefreshAccessibilityServices()

                showAccessibilityServicesDialog = true
            },
        )

        SectionDivider(title = stringResource(R.string.about))

        AboutSection()

        Spacer(modifier = Modifier.height(24.dp))

        FossFooter()

        Spacer(modifier = Modifier.height(24.dp))
    }

    if (showThemeDialog) {
        ThemeDialog(
            onDismissRequest = { showThemeDialog = false },
            selected = selectedTheme,
            onSelect = { selectedTheme = it },
            onChangeClick = {
                onUpdateTheme(Theme.entries[selectedTheme])

                showThemeDialog = false
            },
        )
    }

    if (showAccessibilityServicesDialog) {
        AccessibilityServicesDialog(
            accessibilityServices = accessibilityServices,
            selectedServices = userData.managedAccessibilityServices,
            onDismissRequest = { showAccessibilityServicesDialog = false },
            onUpdateManagedAccessibilityServices = onUpdateManagedAccessibilityServices,
        )
    }
}

@OptIn(FlowPreview::class)
@Composable
private fun ShizukuSection(
    modifier: Modifier = Modifier,
    userData: UserData,
    onUpdateRestartShizuku: (Boolean) -> Unit,
    onUpdateShizukuAuthKey: (String) -> Unit,
    onUpdateShizukuPackageName: (String) -> Unit,
    onUpdateShizukuStartAction: (String) -> Unit,
) {
    // Seeded once from the stored values and then owned locally. Reading them back out of
    // the preferences flow on every keystroke would fight the cursor.
    var startAction by rememberSaveable { mutableStateOf(userData.shizukuStartAction) }

    var packageName by rememberSaveable { mutableStateOf(userData.shizukuPackageName) }

    var authKey by rememberSaveable { mutableStateOf(userData.shizukuAuthKey) }

    // Plain remember, not rememberSaveable: Advanced is a "go and look something up"
    // panel, not a preference. Saving it meant that once it had been opened — which the
    // gated toggle does for you — it stayed open on every later visit.
    var showAdvanced by remember { mutableStateOf(false) }

    var showFillHint by rememberSaveable { mutableStateOf(false) }

    // Nothing can be sent without all three, so the toggle stays inert until they are set.
    val configured = startAction.isNotBlank() && packageName.isNotBlank() && authKey.isNotBlank()

    // Committed on a pause rather than per keystroke: each write is a full proto rewrite
    // plus an emission that recomposes this whole screen. drop(1) skips the seed value so
    // simply opening Settings does not write anything.
    LaunchedEffect(Unit) {
        snapshotFlow { startAction }.drop(1).debounce(COMMIT_DEBOUNCE)
            .distinctUntilChanged()
            .collect { onUpdateShizukuStartAction(it) }
    }

    LaunchedEffect(Unit) {
        snapshotFlow { packageName }.drop(1).debounce(COMMIT_DEBOUNCE)
            .distinctUntilChanged()
            .collect { onUpdateShizukuPackageName(it) }
    }

    LaunchedEffect(Unit) {
        snapshotFlow { authKey }.drop(1).debounce(COMMIT_DEBOUNCE)
            .distinctUntilChanged()
            .collect { onUpdateShizukuAuthKey(it) }
    }

    Column(modifier = modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier
                .clickable {
                    if (configured) {
                        onUpdateRestartShizuku(!userData.restartShizuku)
                    } else {
                        // Rather than a dead switch with no explanation, say what is
                        // missing and open the section that holds it.
                        showFillHint = true

                        showAdvanced = true
                    }
                }
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                modifier = Modifier.weight(1f),
                text = stringResource(R.string.restart_shizuku_service),
                style = MaterialTheme.typography.bodyLarge,
            )

            // A null onCheckedChange leaves the switch with no input modifier of its own,
            // so a tap on it falls through to the row above and shows the hint instead of
            // being silently swallowed by a disabled control.
            Switch(
                checked = userData.restartShizuku,
                enabled = configured,
                onCheckedChange = if (configured) onUpdateRestartShizuku else null,
            )
        }

        Text(
            modifier = Modifier.padding(horizontal = 16.dp),
            text = shizukuDescription(),
            style = MaterialTheme.typography.bodySmall,
        )

        if (showFillHint && !configured) {
            Text(
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 6.dp),
                text = stringResource(R.string.shizuku_fill_advanced),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.error,
            )
        }

        ExpandableHeader(
            title = stringResource(R.string.advanced),
            expanded = showAdvanced,
            onClick = { showAdvanced = !showAdvanced },
        )

        if (showAdvanced) {
            Text(
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 4.dp),
                text = stringResource(R.string.shizuku_view_intents_hint),
                style = MaterialTheme.typography.bodySmall,
            )

            ShizukuField(
                value = startAction,
                label = stringResource(R.string.shizuku_start_action),
                onValueChange = { startAction = it },
            )

            ShizukuField(
                value = packageName,
                label = stringResource(R.string.shizuku_package_name),
                onValueChange = { packageName = it },
            )

            ShizukuField(
                value = authKey,
                label = stringResource(R.string.shizuku_auth_key),
                secret = true,
                onValueChange = { authKey = it },
            )
        }
    }
}

/**
 * [secret] masks the value like a password and adds a reveal toggle. The auth key is the
 * one field here that is worth hiding: it is the token that lets anything start Shizuku,
 * and this screen gets opened in front of other people while explaining the app.
 */
@Composable
private fun ShizukuField(
    modifier: Modifier = Modifier,
    value: String,
    label: String,
    secret: Boolean = false,
    onValueChange: (String) -> Unit,
) {
    var revealed by remember { mutableStateOf(false) }

    OutlinedTextField(
        modifier = modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 6.dp),
        value = value,
        onValueChange = onValueChange,
        label = { Text(text = label) },
        singleLine = true,
        textStyle = MaterialTheme.typography.bodyMedium.copy(fontFamily = FontFamily.Monospace),
        visualTransformation = if (secret && !revealed) {
            PasswordVisualTransformation()
        } else {
            VisualTransformation.None
        },
        trailingIcon = if (!secret) {
            null
        } else {
            {
                IconButton(onClick = { revealed = !revealed }) {
                    Icon(
                        imageVector = if (revealed) GetoIcons.Hidden else GetoIcons.Visible,
                        contentDescription = stringResource(
                            if (revealed) R.string.hide_value else R.string.show_value,
                        ),
                    )
                }
            }
        },
    )
}

@Composable
private fun AboutSection(modifier: Modifier = Modifier) {
    var showAuthorDialog by rememberSaveable { mutableStateOf(false) }

    // Every composable read is hoisted out of the builder lambdas: resources and theme
    // colours are resolved once per recomposition rather than once per span.
    val linkStyles = linkStyles()

    val createdBy = stringResource(R.string.about_created_by)

    val authorName = stringResource(R.string.about_author_name)

    val forkOf = stringResource(R.string.about_fork_of)

    val getoApp = stringResource(R.string.about_geto_app)

    val licenceName = stringResource(R.string.about_licence_name)

    val author = remember(createdBy, authorName, linkStyles) {
        buildAnnotatedString {
            append(createdBy)
            append(" ")
            withLink(
                LinkAnnotation.Clickable(
                    tag = AUTHOR_LINK_TAG,
                    styles = linkStyles,
                    linkInteractionListener = { showAuthorDialog = true },
                ),
            ) {
                append(authorName)
            }
        }
    }

    val fork = remember(forkOf, getoApp, linkStyles) {
        buildAnnotatedString {
            append(forkOf)
            append(" ")
            withLink(LinkAnnotation.Url(url = GETO_REPOSITORY_URL, styles = linkStyles)) {
                append(getoApp)
            }
        }
    }

    val licence = remember(licenceName, linkStyles) {
        buildAnnotatedString {
            withLink(LinkAnnotation.Url(url = LICENCE_URL, styles = linkStyles)) {
                append(licenceName)
            }
        }
    }

    Column(modifier = modifier.padding(horizontal = 16.dp)) {
        Text(text = author, style = MaterialTheme.typography.bodyMedium)

        Spacer(modifier = Modifier.height(8.dp))

        Text(text = fork, style = MaterialTheme.typography.bodyMedium)

        Spacer(modifier = Modifier.height(8.dp))

        Text(text = licence, style = MaterialTheme.typography.bodyMedium)
    }

    if (showAuthorDialog) {
        AuthorDialog(onDismissRequest = { showAuthorDialog = false })
    }
}

/** The Shizuku explanation, with the fork name as a link to its release page. */
@Composable
private fun shizukuDescription(): AnnotatedString {
    val linkStyles = linkStyles()

    val description = stringResource(R.string.restart_shizuku_service_description)

    val needs = stringResource(R.string.shizuku_needs)

    val forkName = stringResource(R.string.shizuku_fork_link)

    return remember(description, needs, forkName, linkStyles) {
        buildAnnotatedString {
            append(description)
            append(" ")
            append(needs)
            append(" ")
            withLink(LinkAnnotation.Url(url = SHIZUKU_FORK_URL, styles = linkStyles)) {
                append(forkName)
            }
            append(".")
        }
    }
}

@Composable
private fun AuthorDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {
    val context = LocalContext.current

    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                modifier = Modifier.padding(bottom = 8.dp),
                text = stringResource(R.string.about_author_name),
                style = MaterialTheme.typography.titleLarge,
            )

            LinkRow(
                text = stringResource(R.string.about_view_github),
                onClick = { context.openUri(AUTHOR_GITHUB_URL) },
            )

            LinkRow(
                text = AUTHOR_EMAIL,
                onClick = { context.openUri("mailto:$AUTHOR_EMAIL") },
            )

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(R.string.close))
                }
            }
        }
    }
}

@Composable
private fun linkStyles(): TextLinkStyles {
    val colour = MaterialTheme.colorScheme.primary

    return remember(colour) {
        TextLinkStyles(
            style = SpanStyle(color = colour, textDecoration = TextDecoration.Underline),
        )
    }
}

@Composable
private fun FossFooter(modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .alpha(0.38f)
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
    ) {
        Image(
            modifier = Modifier.size(96.dp),
            painter = painterResource(R.drawable.ic_foss),
            contentDescription = null,
            colorFilter = ColorFilter.tint(MaterialTheme.colorScheme.onSurface),
        )

        Spacer(modifier = Modifier.height(10.dp))

        Text(
            text = stringResource(R.string.long_live_foss),
            style = MaterialTheme.typography.bodyMedium,
            textAlign = TextAlign.Center,
        )
    }
}

@Composable
private fun ExpandableHeader(
    modifier: Modifier = Modifier,
    title: String,
    expanded: Boolean,
    onClick: () -> Unit,
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
            .padding(horizontal = 16.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(
            modifier = Modifier.weight(1f),
            text = title,
            style = MaterialTheme.typography.bodyLarge,
        )

        Icon(
            imageVector = if (expanded) GetoIcons.ExpandLess else GetoIcons.ExpandMore,
            contentDescription = null,
        )
    }
}

@Composable
private fun SectionDivider(
    modifier: Modifier = Modifier,
    title: String,
) {
    Column(modifier = modifier.fillMaxWidth()) {
        Spacer(modifier = Modifier.height(12.dp))

        HorizontalDivider()

        Text(
            modifier = Modifier.padding(start = 16.dp, top = 12.dp, bottom = 4.dp),
            text = title,
            style = MaterialTheme.typography.titleSmall,
            color = MaterialTheme.colorScheme.primary,
        )
    }
}

@Composable
private fun LinkRow(
    modifier: Modifier = Modifier,
    text: String,
    onClick: () -> Unit,
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
            .padding(vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(
            modifier = Modifier.weight(1f),
            text = text,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.primary,
        )

        Icon(
            modifier = Modifier.size(16.dp),
            imageVector = GetoIcons.Link,
            contentDescription = null,
            tint = MaterialTheme.colorScheme.primary,
        )
    }
}

@Composable
private fun SwitchSetting(
    modifier: Modifier = Modifier,
    title: String,
    subtitle: String,
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit,
) {
    Row(
        modifier = modifier
            .clickable { onCheckedChange(!checked) }
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(text = title, style = MaterialTheme.typography.bodyLarge)

            Spacer(modifier = Modifier.height(4.dp))

            Text(text = subtitle, style = MaterialTheme.typography.bodySmall)
        }

        Switch(checked = checked, onCheckedChange = onCheckedChange)
    }
}

@Composable
private fun DynamicThemeSetting(
    modifier: Modifier = Modifier,
    dynamicTheme: Boolean,
    onUpdateDynamicTheme: (Boolean) -> Unit,
) {
    if (supportsDynamicTheming()) {
        SwitchSetting(
            modifier = modifier,
            title = stringResource(R.string.dynamic_theme),
            subtitle = stringResource(R.string.available_on_android_12),
            checked = dynamicTheme,
            onCheckedChange = onUpdateDynamicTheme,
        )
    }
}

@Composable
private fun SettingsColumn(
    modifier: Modifier = Modifier,
    title: String,
    subtitle: String,
    onClick: () -> Unit,
) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
            .padding(horizontal = 16.dp, vertical = 12.dp),
    ) {
        Text(text = title, style = MaterialTheme.typography.bodyLarge)

        Spacer(modifier = Modifier.height(6.dp))

        Text(text = subtitle, style = MaterialTheme.typography.bodySmall)
    }
}

@Composable
private fun accessibilityServicesSubtitle(
    accessibilityServices: List<AccessibilityServiceData>,
    managed: List<String>,
): String {
    val enabledCount = accessibilityServices.count { it.enabled }

    return if (managed.isEmpty()) {
        stringResource(R.string.accessibility_services_none_selected, enabledCount)
    } else {
        stringResource(R.string.accessibility_services_selected, managed.size, enabledCount)
    }
}

private fun Context.openUri(uri: String) {
    runCatching {
        startActivity(
            Intent(Intent.ACTION_VIEW, Uri.parse(uri)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK),
        )
    }.onFailure {
        if (it !is ActivityNotFoundException) throw it
    }
}

@Composable
internal fun Theme.getTitle() = when (this) {
    Theme.FOLLOW_SYSTEM -> stringResource(R.string.follow_system)
    Theme.LIGHT -> stringResource(R.string.light)
    Theme.DARK -> stringResource(R.string.dark)
}
