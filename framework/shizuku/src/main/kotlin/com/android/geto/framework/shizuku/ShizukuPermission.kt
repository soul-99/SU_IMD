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

private val PACKAGE_NAME = Regex("""[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)+""")

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

    /**
     * Grants IMD `android.permission.DUMP`, which is what lets auto unhide ask Android why
     * *another* app's process died.
     *
     * Grantable for exactly the reason [grantWriteSecureSettings] describes: `DUMP` is
     * `signature|privileged|development`, and the `development` flag is what puts it within
     * reach of `pm grant`. Without it `getHistoricalProcessExitReasons` answers only about
     * IMD's own package, which is never the package auto unhide is watching.
     *
     * **Done once, at setup, and then never again.** This is the whole reason auto unhide can
     * work while Shizuku is dead: the permission outlives the session that granted it, so the
     * detection never touches Shizuku during the hidden window — which matters, because
     * Shizuku is one of the things IMD hides.
     */
    suspend fun grantDumpPermission(packageName: String): ShizukuGrant {
        if (!PACKAGE_NAME.matches(packageName)) return ShizukuGrant.Failed

        if (!isRunning()) return ShizukuGrant.NotRunning

        if (!ensurePermission()) return ShizukuGrant.PermissionDenied

        val granted = runShell("pm grant $packageName android.permission.DUMP")

        return if (granted) ShizukuGrant.Granted else ShizukuGrant.Failed
    }

    suspend fun getAllowedOverlayPackages(): Set<String>? {
        if (!isRunning() || !ensurePermission()) return null

        val output = runShellForOutput(
            "cmd appops query-op --user current SYSTEM_ALERT_WINDOW allow",
        ) ?: return null
        val allowed = output.lineSequence()
            .map(String::trim)
            .filter(PACKAGE_NAME::matches)
            .toSet()

        return allowed
    }

    suspend fun setOverlayPermission(
        packages: Set<String>,
        allowed: Boolean,
    ): Set<String>? {
        if (packages.isEmpty()) return emptySet()
        if (!packages.all(PACKAGE_NAME::matches)) return null
        if (!isRunning() || !ensurePermission()) return null

        val mode = if (allowed) "allow" else "ignore"
        val command = packages.joinToString(separator = ";") { packageName ->
            "cmd appops set --user current $packageName SYSTEM_ALERT_WINDOW $mode"
        }

        if (!runShell(command)) return emptySet()

        val allowedAfter = getAllowedOverlayPackages() ?: return null
        val changed = if (allowed) {
            packages.intersect(allowedAfter)
        } else {
            packages - allowedAfter
        }

        return changed
    }

    fun hasPermission(): Boolean = runCatching {
        Shizuku.checkSelfPermission() == PackageManager.PERMISSION_GRANTED
    }.getOrDefault(false)

    suspend fun requestPermission(): Boolean {
        if (!isRunning()) return false

        return ensurePermission()
    }

    /**
     * `am force-stop`, which is how IMD+ makes an app read the settings after they are hidden
     * rather than before.
     *
     * The package name is checked against the same pattern the AppOps commands use before it
     * reaches a shell. Everything here is built by interpolating a string into `sh -c`, so a
     * name carrying a semicolon would be a second command rather than an argument.
     */
    suspend fun forceStop(packageName: String): Boolean {
        if (!PACKAGE_NAME.matches(packageName)) return false
        if (!isRunning() || !ensurePermission()) return false

        return runShell("am force-stop --user current $packageName")
    }

    /**
     * Clears the Android 13+ "restricted setting" block, without which a sideloaded app's
     * accessibility service cannot be switched on by anybody, including a secure-settings
     * write.
     *
     * The AppOp is named rather than numbered: its number has moved between releases, and a
     * wrong number silently sets a different op.
     */
    suspend fun allowRestrictedSettings(packageName: String): Boolean {
        if (!PACKAGE_NAME.matches(packageName)) return false
        if (!isRunning() || !ensurePermission()) return false

        return runShell(
            "cmd appops set --user current $packageName ACCESS_RESTRICTED_SETTINGS allow",
        )
    }

    /**
     * Adds the package to the device idle whitelist — "not optimised" in Android's own words.
     *
     * IMD+ needs to be alive when the user leaves the app, and an optimised app is exactly the
     * one the system stops first.
     */
    suspend fun allowBatteryUnrestricted(packageName: String): Boolean {
        if (!PACKAGE_NAME.matches(packageName)) return false
        if (!isRunning() || !ensurePermission()) return false

        return runShell("dumpsys deviceidle whitelist +$packageName")
    }

    /**
     * Grants IMD usage access — the AppOp behind `PACKAGE_USAGE_STATS`.
     *
     * Auto unhide's "app not in foreground" backup reads usage events to learn when a watched
     * app stopped being used. The AppOp is what actually gates that read; the manifest
     * permission alone never grants it, which is why Android sends users to a settings list
     * for it rather than showing a prompt.
     *
     * Named rather than numbered, for the reason [allowRestrictedSettings] gives.
     */
    suspend fun allowUsageAccess(packageName: String): Boolean {
        if (!PACKAGE_NAME.matches(packageName)) return false
        if (!isRunning() || !ensurePermission()) return false

        return runShell("cmd appops set --user current $packageName GET_USAGE_STATS allow")
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
        runShellProcess(command).waitFor() == 0
    }.getOrElse {
        Log.w(TAG, "Shizuku shell failed", it)

        false
    }

    private fun runShellForOutput(command: String): String? = runCatching {
        // Some OEM cmd services write successful query output to stderr. Merge it into
        // stdout inside the remote shell because Shizuku's reflected Process exposes the
        // two streams separately.
        val process = runShellProcess("$command 2>&1")
        val output = process.inputStream.bufferedReader().use { it.readText() }

        if (process.waitFor() == 0) output else null
    }.getOrElse {
        Log.w(TAG, "Shizuku shell failed", it)

        null
    }

    private fun runShellProcess(command: String): Process {
        val newProcess = Shizuku::class.java.getDeclaredMethod(
            "newProcess",
            Array<String>::class.java,
            Array<String>::class.java,
            String::class.java,
        )

        newProcess.isAccessible = true

        return newProcess.invoke(
            null,
            arrayOf("sh", "-c", command),
            null,
            null,
        ) as Process
    }
}
