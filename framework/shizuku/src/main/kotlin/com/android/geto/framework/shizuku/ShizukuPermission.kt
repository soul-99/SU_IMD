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
package com.android.geto.framework.shizuku

import android.content.pm.PackageManager
import android.util.Log
import com.android.geto.domain.model.ShizukuGrant
import kotlinx.coroutines.suspendCancellableCoroutine
import rikka.shizuku.Shizuku
import kotlin.coroutines.resume

private const val TAG = "ShizukuPermission"

/** Any int; it only has to match between the request and the callback. */
private const val REQUEST_CODE = 4919

/**
 * Everything that talks to the Shizuku client library, kept in one file.
 *
 * Every call is wrapped: the library throws `IllegalStateException` from `requireService()`
 * when no binder has arrived, and `NoClassDefFoundError` is possible on a device where
 * something has gone wrong with the AAR. None of that should take down first-run setup,
 * whose whole job is to explain what is missing.
 */
internal object ShizukuPermission {

    fun isRunning(): Boolean = runCatching { Shizuku.pingBinder() }.getOrDefault(false)

    suspend fun grantWriteSecureSettings(packageName: String): ShizukuGrant {
        if (!isRunning()) return ShizukuGrant.NotRunning

        if (!ensurePermission()) return ShizukuGrant.PermissionDenied

        // Shizuku's shell runs as the adb user, which is exactly the identity
        // `adb shell pm grant` runs under — WRITE_SECURE_SETTINGS carries the
        // `development` protection flag, and that is what makes it grantable at all.
        //
        // pm grant rather than a direct IPermissionManager call because the framework
        // renamed and re-signed that interface repeatedly (permissions moved off
        // IPackageManager in API 30, and grantRuntimePermission grew a fourth argument in
        // API 35). One command string works unchanged across all of them.
        val granted = runShell(
            "pm grant $packageName android.permission.WRITE_SECURE_SETTINGS",
        )

        return if (granted) ShizukuGrant.Granted else ShizukuGrant.Failed
    }

    private suspend fun ensurePermission(): Boolean {
        val current = runCatching { Shizuku.checkSelfPermission() }.getOrNull()

        if (current == PackageManager.PERMISSION_GRANTED) return true

        // True once the user has refused and ticked "don't ask again" — the prompt would
        // never appear, so asking again would just look broken.
        if (runCatching { Shizuku.shouldShowRequestPermissionRationale() }.getOrDefault(false)) {
            return false
        }

        return awaitPermission()
    }

    private suspend fun awaitPermission(): Boolean = suspendCancellableCoroutine { continuation ->
        val listener = object : Shizuku.OnRequestPermissionResultListener {
            override fun onRequestPermissionResult(requestCode: Int, grantResult: Int) {
                if (requestCode != REQUEST_CODE) return

                Shizuku.removeRequestPermissionResultListener(this)

                if (continuation.isActive) {
                    continuation.resume(grantResult == PackageManager.PERMISSION_GRANTED)
                }
            }
        }

        Shizuku.addRequestPermissionResultListener(listener)

        continuation.invokeOnCancellation {
            runCatching { Shizuku.removeRequestPermissionResultListener(listener) }
        }

        runCatching { Shizuku.requestPermission(REQUEST_CODE) }.onFailure {
            Log.w(TAG, "Could not ask Shizuku for permission", it)

            Shizuku.removeRequestPermissionResultListener(listener)

            if (continuation.isActive) continuation.resume(false)
        }
    }

    /**
     * `Shizuku.newProcess` is private and deprecated as of API 13.1.5 — the library wants
     * apps to move to a bound UserService — but it is still the only route to a shell, and
     * a UserService for one `pm grant` would be a lot of machinery for a single line. Kept
     * behind reflection with a matching keep rule in proguard-rules.pro; if it ever
     * disappears this returns false and the ADB instructions on the same screen still work.
     */
    private fun runShell(command: String): Boolean = runCatching {
        val newProcess = Shizuku::class.java.getDeclaredMethod(
            "newProcess",
            Array<String>::class.java,
            Array<String>::class.java,
            String::class.java,
        )

        newProcess.isAccessible = true

        val process = newProcess.invoke(
            null,
            arrayOf("sh", "-c", command),
            null,
            null,
        ) as Process

        process.waitFor() == 0
    }.getOrElse {
        Log.w(TAG, "Shizuku shell failed", it)

        false
    }
}
