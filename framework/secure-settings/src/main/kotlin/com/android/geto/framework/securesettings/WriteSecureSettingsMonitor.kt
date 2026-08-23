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
import android.content.Intent
import android.content.pm.PackageManager
import android.util.Log
import androidx.core.content.ContextCompat
import dagger.hilt.android.qualifiers.ApplicationContext
import java.util.concurrent.atomic.AtomicLong
import javax.inject.Inject
import javax.inject.Singleton

private const val TAG = "WriteSecureSettings"

/**
 * How long to wait before bringing the setup screen up again after having just done so.
 *
 * A single revert can attempt several writes in a row, and every one of them fails the same
 * way. Without this the user would be handed the same activity four or five times in a
 * second, and each launch would interrupt the one before it.
 */
private const val RELAUNCH_COOLDOWN_MILLIS = 5_000L

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
    private val lastLaunchUptime = AtomicLong(Long.MIN_VALUE)

    fun hasPermission(): Boolean = ContextCompat.checkSelfPermission(
        context,
        Manifest.permission.WRITE_SECURE_SETTINGS,
    ) == PackageManager.PERMISSION_GRANTED

    /**
     * Called when a write was refused. Returns true when the permission really is gone, so
     * the caller can tell that apart from a write that failed on its own merits.
     */
    fun onWriteRefused(): Boolean {
        if (hasPermission()) return false

        Log.w(TAG, "WRITE_SECURE_SETTINGS has been revoked; reopening setup")

        openSetup()

        return true
    }

    /**
     * Brings the app's own launcher activity to the front.
     *
     * It needs no extra telling it why: the setup screen is shown whenever the permission is
     * missing and re-checked on every resume, so arriving there with no grant lands on step
     * one and staying there until it is fixed is the existing behaviour rather than
     * something added here.
     *
     * Resolved through the package manager instead of naming MainActivity, which lives in a
     * module this one cannot see.
     */
    private fun openSetup() {
        val now = android.os.SystemClock.uptimeMillis()

        val previous = lastLaunchUptime.get()

        if (now - previous < RELAUNCH_COOLDOWN_MILLIS) return

        if (!lastLaunchUptime.compareAndSet(previous, now)) return

        val intent = context.packageManager
            .getLaunchIntentForPackage(context.packageName)
            ?.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)
            ?: return

        runCatching { context.startActivity(intent) }.onFailure {
            // A background activity start can be blocked outright on Android 10 and up. The
            // permission is still gone and the app is still broken, but there is nothing
            // more to be done from here — the next time the user opens it themselves, the
            // setup gate will catch them.
            Log.w(TAG, "Could not reopen setup", it)
        }
    }
}
