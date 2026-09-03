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
package com.android.geto.framework.securesettings

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.util.Log
import androidx.core.content.ContextCompat
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

private const val TAG = "WriteSecureSettings"

/**
 * Watches for the WRITE_SECURE_SETTINGS grant disappearing underneath the app.
 *
 * The grant is made from outside — over ADB, or through Shizuku — and it does not survive
 * everything. A reinstall drops it, some ROM "permission managers" revoke it, and on a few
 * devices a system update quietly clears it. What makes that bad is not the failure itself
 * but how it presents: every switch still moves, every button still responds, and nothing on
 * the device actually changes. The app looks like it is working and is not.
 *
 * So this hooks the one place every write goes through, rather than polling from a service.
 * A service could only ever notice the same fact later and would have to be running all the
 * time to do it; the write itself already knows, immediately and for certain.
 *
 * Confirming the permission is genuinely gone before reacting matters: [SecurityException]
 * from a settings write can also mean a key this app is not allowed to touch at all, which
 * is a bug in a profile and not something onboarding can fix.
 */
@Singleton
class WriteSecureSettingsMonitor @Inject constructor(
    @param:ApplicationContext private val context: Context,
) {
    fun hasPermission(): Boolean = ContextCompat.checkSelfPermission(
        context,
        Manifest.permission.WRITE_SECURE_SETTINGS,
    ) == PackageManager.PERMISSION_GRANTED

    /**
     * Called when a write was refused. Returns true when the permission really is gone, so
     * the caller can tell that apart from a write that failed on its own merits.
     *
     * ⚠ **It used to drag the app to the foreground from here, and no longer does**, on the
     * author's instruction. The message the user now gets asks them to open IMD and re-grant
     * the permission; an app that yanks itself in front of whatever they were doing and *then*
     * tells them to open it is saying two different things, and the one they read is stale
     * before they finish reading it. Every route that hides settings now reports the loss for
     * itself — see `permissions_lost`.
     */
    fun onWriteRefused(): Boolean {
        if (hasPermission()) return false

        Log.w(TAG, "WRITE_SECURE_SETTINGS has been revoked")

        return true
    }
}
