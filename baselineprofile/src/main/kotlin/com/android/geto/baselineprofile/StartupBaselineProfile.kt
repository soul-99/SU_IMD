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
package com.android.geto.baselineprofile

import androidx.benchmark.macro.junit4.BaselineProfileRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/**
 * Writes the list of classes and methods a cold start actually uses, so ART can compile them ahead
 * of time instead of interpreting them on the user's first launch.
 *
 * ⚠ **Startup only, deliberately.** A profile is a budget: every method in it is compiled at
 * install time, and a profile that covers everything covers nothing in particular. The first frame
 * is where the app is slowest and where the user is least forgiving.
 *
 * ⚠ **This does not run in a normal build.** Run it against a connected device with
 *
 *     gradlew :app:generateReleaseBaselineProfile
 *
 * which installs both APKs, drives the app several times, and writes
 * `app/src/release/generated/baselineProfiles/baseline-prof.txt`. **Commit that file** — it is what
 * ships; the module exists to regenerate it when the startup path changes.
 *
 * ⚠ **The device must be rooted or `userdebug` for Macrobenchmark to collect a profile**, which is
 * the usual reason a first attempt reports nothing. An emulator image without Play Store is the
 * easiest way to satisfy that.
 */
@RunWith(AndroidJUnit4::class)
class StartupBaselineProfile {
    @get:Rule
    val rule = BaselineProfileRule()

    @Test
    fun startup() = rule.collect(packageName = TARGET_PACKAGE) {
        pressHome()

        // `startActivityAndWait` returns once the first frame is on screen, which is exactly the
        // span worth compiling ahead of time.
        startActivityAndWait()
    }
}

/**
 * ⚠ **The applicationId, not the namespace.** `:app` declares `namespace = "com.android.geto"` and
 * `applicationId = "com.soul_99.suIMD"`; what is installed on the device — and therefore what this
 * has to launch — is the second one.
 *
 * ⚠ **Not `PACKAGE_NAME`.** `:framework:shizuku` already declares a top-level constant by that
 * name, and `tools/check_symbol_imports.py` reads a second one as this file referencing that one
 * without importing it — which took the checker off its baseline of zero the first time round.
 */
private const val TARGET_PACKAGE = "com.soul_99.suIMD"
