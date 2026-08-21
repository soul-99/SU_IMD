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
package com.android.geto.onboarding

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.Stable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.platform.LocalContext
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner

/**
 * Live view of the two permissions the app cannot function without.
 *
 * Deliberately derived from the real system state on every read rather than from a
 * "seen the intro" flag: the ADB grant is done outside the app and can be revoked by a
 * reinstall or by the user, and a stored flag would leave the app looking functional while
 * every settings write silently failed.
 */
@Stable
class SetupState internal constructor(private val context: Context) {

    var hasSecureSettings by mutableStateOf(context.hasWriteSecureSettings())
        private set

    var hasNotifications by mutableStateOf(context.hasNotificationsEnabled())
        private set

    val isComplete: Boolean get() = hasSecureSettings && hasNotifications

    fun refresh() {
        hasSecureSettings = context.hasWriteSecureSettings()

        hasNotifications = context.hasNotificationsEnabled()
    }
}

/**
 * Re-reads on every resume, which is what makes the ADB step work: the user leaves for a
 * terminal, comes back, and the screen has already caught up without them pressing
 * anything.
 */
@Composable
fun rememberSetupState(): SetupState {
    val context = LocalContext.current

    val setupState = remember(context) { SetupState(context) }

    val lifecycleOwner = LocalLifecycleOwner.current

    DisposableEffect(lifecycleOwner, setupState) {
        val observer = LifecycleEventObserver { _, event ->
            if (event == Lifecycle.Event.ON_RESUME) {
                setupState.refresh()
            }
        }

        lifecycleOwner.lifecycle.addObserver(observer)

        onDispose { lifecycleOwner.lifecycle.removeObserver(observer) }
    }

    return setupState
}

/**
 * WRITE_SECURE_SETTINGS is signature|privileged|development. The development flag is what
 * lets `pm grant` hand it to a normal app, and once granted checkSelfPermission reports it
 * like any other.
 */
private fun Context.hasWriteSecureSettings(): Boolean = ContextCompat.checkSelfPermission(
    this,
    Manifest.permission.WRITE_SECURE_SETTINGS,
) == PackageManager.PERMISSION_GRANTED

/**
 * Broader than the POST_NOTIFICATIONS runtime permission on purpose: notifications can also
 * be switched off for the app in system settings, which breaks the Revert action just as
 * thoroughly while the permission still reads as granted.
 */
private fun Context.hasNotificationsEnabled(): Boolean = NotificationManagerCompat.from(this).areNotificationsEnabled()
