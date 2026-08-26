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

import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.material3.Button
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.core.net.toUri
import com.android.geto.designsystem.icon.GetoIcons
import com.android.geto.feature.settings.R

/**
 * A way out to the Android screen that owns whatever is being picked from.
 *
 * Both pickers list something the user cannot change from inside IMD: which accessibility
 * services are installed and running, and which apps are allowed to draw over others. Both
 * are set on a system screen, and both lists are far more useful once you have been there -
 * so the way there sits at the top, under the description, rather than being something to
 * work out for yourself.
 *
 * A filled button rather than a link, because it is the only thing on these pages that
 * leaves the app.
 */
@Composable
internal fun SystemSettingsButton(
    modifier: Modifier = Modifier,
    text: String,
    intent: Intent,
) {
    val context = LocalContext.current

    Button(
        modifier = modifier.fillMaxWidth(),
        onClick = { context.startSystemSettings(intent) },
    ) {
        Icon(
            modifier = Modifier.size(18.dp),
            imageVector = GetoIcons.OpenInNew,
            contentDescription = null,
        )

        Spacer(modifier = Modifier.width(8.dp))

        Text(text = text)
    }
}

/**
 * NEW_TASK because these dialogs are shown from an activity that is sometimes transparent
 * and sometimes finishing, and the catch because not every Android build ships every one of
 * these screens - a missing one should say so rather than crash the app.
 */
private fun Context.startSystemSettings(intent: Intent) {
    try {
        startActivity(intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
    } catch (_: ActivityNotFoundException) {
        android.widget.Toast.makeText(
            this,
            R.string.system_settings_unavailable,
            android.widget.Toast.LENGTH_LONG,
        ).show()
    }
}

/** The overlay screen wants the package as data on some builds and ignores it on others. */
internal fun overlaySettingsIntent(context: Context): Intent =
    Intent(android.provider.Settings.ACTION_MANAGE_OVERLAY_PERMISSION)
        .setData("package:${context.packageName}".toUri())

internal fun accessibilitySettingsIntent(): Intent =
    Intent(android.provider.Settings.ACTION_ACCESSIBILITY_SETTINGS)
