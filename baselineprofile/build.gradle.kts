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

import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    // ⚠ **Bare ids, both of them, and this is the thing r29's first two builds got wrong.**
    // `com.android.test` is part of AGP, which build-logic has already put on the classpath at an
    // unknown version, so naming a version here is refused. `androidx.baselineprofile` carries its
    // version once in the root build file. Every other module in this project applies its Android
    // plugin the same way, through a convention plugin that uses the id alone.
    id("com.android.test")
    id("androidx.baselineprofile")
}

/**
 * ⚠ **A `com.android.test` module, not a library.** It builds its own APK, installs it beside the
 * app and drives the app from outside — which is the only way to watch a cold start, because the
 * process being measured has to be one this code did not start.
 *
 * It is not on any release path. Nothing in `:app` depends on it at build time; `:app` consumes
 * the *file* it produces, and only if it has been run.
 *
 * ⚠ **No Kotlin plugin alias here, and that is not an omission.** Under AGP 9 the Android plugins
 * bring Kotlin themselves — the catalog has no `kotlin-android` entry at all, and none of the
 * twenty-nine existing modules applies one. Adding it would be a second, differently-versioned
 * Kotlin plugin on the same project.
 */
android {
    namespace = "com.android.geto.baselineprofile"

    compileSdk = 36

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }

    defaultConfig {
        // ⚠ **28, not the app's 24.** Macrobenchmark cannot drive a device below P, and this is the
        // generator's own floor rather than the app's — the profile it writes still installs back
        // to 24 through profileinstaller.
        minSdk = 28

        targetSdk = 36

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    targetProjectPath = ":app"
}

// ⚠ **Outside `android { }`.** This is the Kotlin Gradle Plugin's own extension, not an AGP one -
// there is no `kotlin` block inside `android`. The convention plugins reach the same extension as
// `extensions.configure<KotlinAndroidProjectExtension>`; in a build script it is simply top level.
kotlin {
    compilerOptions {
        jvmTarget = JvmTarget.JVM_11
    }
}

// ⚠ **`useConnectedDevices`, because this project has no managed-device configuration.** Gradle
// will not invent an emulator; the device the author already tests on is the device this runs on.
baselineProfile {
    useConnectedDevices = true
}

dependencies {
    implementation(libs.androidx.test.ext.junit.ktx)
    implementation(libs.androidx.test.uiautomator)
    implementation(libs.androidx.benchmark.macro.junit4)
}
