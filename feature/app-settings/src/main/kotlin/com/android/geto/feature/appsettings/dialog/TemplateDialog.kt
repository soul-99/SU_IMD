/*
 *
 *   Copyright 2023 Einstein Blanco
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
package com.android.geto.feature.appsettings.dialog

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.designsystem.icon.GetoIcons
import com.android.geto.domain.model.AppSetting
import com.android.geto.domain.model.AppSettingTemplate
import com.android.geto.feature.appsettings.R
import com.android.geto.feature.appsettings.getSettingTypeTitle

/**
 * The list of ready-made settings rows a profile can be built from.
 *
 * Adding one leaves the dialog open. Most profiles want more than one row — the four secure
 * settings are usually taken together — and closing after each meant reopening the dialog and
 * scrolling back to where you were, once per row. It closes on back or a tap outside, like
 * every other dialog here, so there is nothing new to learn.
 */
@Composable
internal fun TemplateDialog(
    modifier: Modifier = Modifier,
    appSettingTemplates: List<AppSettingTemplate>,
    componentName: String,
    /**
     * The keys IMD cannot act on right now, drawn greyed rather than left out.
     *
     * ⚠ **Offered and refused, not withheld.** A template that quietly vanished left the user
     * with no way to find out that the feature exists or what it needs; greyed, a press says
     * both. The author's instruction for open item 2.
     */
    blockedKeys: Set<String>,
    onBlockedClick: (String) -> Unit,
    onAddAppSetting: (AppSetting) -> Unit,
    onDismissRequest: () -> Unit,
) {
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
                text = stringResource(id = R.string.templates),
                style = MaterialTheme.typography.titleLarge,
            )

            LazyColumn(modifier = Modifier.fillMaxWidth()) {
                items(appSettingTemplates) { appSettingTemplate ->
                    AppSettingTemplateItem(
                        appSettingTemplate = appSettingTemplate,
                        componentName = componentName,
                        enabled = appSettingTemplate.key !in blockedKeys,
                        onBlockedClick = { onBlockedClick(appSettingTemplate.key) },
                        onAddAppSetting = onAddAppSetting,
                    )
                }
            }
        }
    }
}

@Composable
private fun AppSettingTemplateItem(
    modifier: Modifier = Modifier,
    appSettingTemplate: AppSettingTemplate,
    componentName: String,
    enabled: Boolean,
    onBlockedClick: () -> Unit,
    onAddAppSetting: (AppSetting) -> Unit,
) {
    // Material's disabled pair, restated rather than inherited: this row draws its own text
    // colours, so `LocalContentColor` alone would leave the label at full strength.
    val contentColour = if (enabled) {
        MaterialTheme.colorScheme.onSurface
    } else {
        MaterialTheme.colorScheme.onSurface.copy(alpha = DISABLED_CONTENT_ALPHA)
    }

    val supportColour = if (enabled) {
        MaterialTheme.colorScheme.onSurfaceVariant
    } else {
        MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = DISABLED_CONTENT_ALPHA)
    }

    Row(
        modifier = modifier
            .fillMaxWidth()
            // ⚠ **The whole row answers, and only while it is refusing.** A greyed template
            // that did nothing at all when tapped reads as a broken list; an enabled one keeps
            // its single affordance, the + button, so a stray tap on the text cannot add a row
            // nobody asked for.
            .then(if (enabled) Modifier else Modifier.clickable(onClick = onBlockedClick))
            .padding(10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = appSettingTemplate.label,
                style = MaterialTheme.typography.bodyLarge,
                color = contentColour,
            )

            // Directly under the label rather than below the key, because it is a condition
            // on using the template at all - the two lines under it describe what the row
            // writes, which is no use to someone who cannot use it yet.
            appSettingTemplate.description?.let { description ->
                Spacer(modifier = Modifier.height(2.dp))

                Text(
                    text = description,
                    style = MaterialTheme.typography.bodySmall,
                    color = supportColour,
                )
            }

            Spacer(modifier = Modifier.height(5.dp))

            Text(
                text = appSettingTemplate.settingType.getSettingTypeTitle(),
                style = MaterialTheme.typography.bodySmall,
                color = contentColour,
            )

            Spacer(modifier = Modifier.height(5.dp))

            Text(
                text = appSettingTemplate.key,
                style = MaterialTheme.typography.bodySmall,
                color = contentColour,
            )
        }

        // ⚠ **Enabled and branching, rather than disabled.** A disabled IconButton swallows
        // the press inside its own bounds, so the row's `clickable` above never sees it and
        // the one place a user is most likely to tap would be the one place that says nothing.
        IconButton(
            onClick = {
                if (!enabled) {
                    onBlockedClick()

                    return@IconButton
                }

                onAddAppSetting(
                    AppSetting(
                        enabled = true,
                        settingType = appSettingTemplate.settingType,
                        componentName = componentName,
                        label = appSettingTemplate.label,
                        key = appSettingTemplate.key,
                        valueOnLaunch = appSettingTemplate.valueOnLaunch,
                        valueOnRevert = appSettingTemplate.valueOnRevert,
                    ),
                )
            },
        ) {
            Icon(
                imageVector = GetoIcons.Add,
                contentDescription = null,
                tint = contentColour,
            )
        }
    }
}

/** Material's disabled content alpha, restated where a row draws its own colours. */
private const val DISABLED_CONTENT_ALPHA = 0.38f
