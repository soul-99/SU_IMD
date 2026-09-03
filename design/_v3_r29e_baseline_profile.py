#!/usr/bin/env python3
"""
r29e — a baseline profile, and a narrower R8 keep rule.

## What was and was not already there

⚠ **R8 is configured**, contrary to §6 of the handover's *"worth checking whether either is
configured at all"*. `app/build.gradle.kts` already has `isMinifyEnabled = true`,
`isShrinkResources = true` and `proguard-android-optimize.txt`. Nothing to switch on.

**A baseline profile was genuinely absent** — no `androidx.baselineprofile` plugin, no
`profileinstaller` dependency, no generator module, no `baseline-prof.txt` anywhere in the tree.
That is the one thing on the shortlist that buys cold-start and first-scroll time rather than
steady-state frame time, and it costs nothing in either of the two files the author touches every
round.

## The two halves, and why both are needed

* **`profileinstaller`** in `:app` is what actually *installs* a profile at first run. Without it a
  `baseline-prof.txt` inside the APK is inert on most devices.
* **`:baselineprofile`**, a `com.android.test` module, is what *generates* one. It drives the app
  through its startup path with Macrobenchmark and writes the classes and methods that were used;
  the `androidx.baselineprofile` plugin on `:app` then folds that output into the APK.

⚠ **The generator does not run itself.** It needs a connected device or an emulator, and it is the
author who has those. `gradlew :app:generateReleaseBaselineProfile` produces the profile; until it
is run the wiring is present and the APK simply ships without one, which is exactly where the app
is today.

⚠ **The versions here were looked up, not guessed — the first attempt was guessed and it failed.**
r29's first zip pinned `androidxBenchmark = "1.5.0"`, which is not a published version, and the
plugin marker `androidx.baselineprofile:androidx.baselineprofile.gradle.plugin:1.5.0` failed to
resolve, taking down `:app:assembleDebug` before anything else in the round could be tested. The
three versions now come from developer.android.com's release pages:

| | published state |
|---|---|
| `androidx.benchmark` | 1.4.1 stable (Sept 2025); **1.5.0-rc02** (26 Aug 2026) heads the 1.5 line; no 1.5.0 final |
| `androidx.profileinstaller` | 1.4.1 stable |
| `androidx.test.uiautomator` | 2.4.0 stable (July 2026) |

See the note above the version pin for why the release candidate is right and the stable one is
not.

## The keep rule

`-keep class com.android.geto.domain.model.** { *; }` kept **every member of every class** in the
project's largest model package, which is a blanket opt-out of shrinking and obfuscation for it.
What the comment above it says it wants is the *names*, and what actually needs the members is the
enums — which are kept by the rule immediately below it, already. Narrowed to the classes rather
than their members: `-keep class … { *; }` becomes `-keepnames class …`.

⚠ **The enum rule is untouched.** `values()`/`valueOf()` are reached reflectively by the proto
mappers, and that is a real member-level need, not a naming one.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CATALOG = ROOT / "gradle/libs.versions.toml"
SETTINGS_GRADLE = ROOT / "settings.gradle.kts"
ROOT_GRADLE = ROOT / "build.gradle.kts"
APP_GRADLE = ROOT / "app/build.gradle.kts"
PROGUARD = ROOT / "app/proguard-rules.pro"

MODULE = ROOT / "baselineprofile"

failures: list[str] = []
writes: dict[Path, str] = {}


def check(condition: bool, message: str) -> bool:
    if not condition:
        failures.append(message)

    return condition


def replace_once(text: str, old: str, new: str, label: str) -> str:
    found = text.count(old)

    if not check(found == 1, f"{label}: found {found}x, expected 1"):
        return text

    return text.replace(old, new, 1)


LICENCE = """/*
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
"""

# ---------------------------------------------------------------- the catalog

catalog = CATALOG.read_text(encoding="utf-8")

check("androidxBenchmark" not in catalog, "catalog: androidxBenchmark is already defined")

# ⚠ **1.5.0-rc02, and the release candidate is the deliberate part.**
#
# r29's first attempt pinned "1.5.0", which does not exist — the plugin marker failed to resolve and
# took the whole app build down at `app/build.gradle.kts` line 21. The published state, checked
# against developer.android.com rather than guessed a second time: **1.4.1 is the latest stable**
# (Sept 2025) and **1.5.0-rc02** (26 Aug 2026) is the head of the 1.5 line. There is no 1.5.0 final.
#
# 1.4.1 is not the safe choice here despite being stable. The 1.5 line's own notes say, at
# 1.5.0-alpha02: *"Baseline Profile Gradle Plugin no longer requires newDsl=false in AGP 9.0"* —
# which is to say the 1.4 line **does** require that flag under AGP 9, and this project is on AGP
# 9.1.0. Pinning the stable version would trade a resolution failure for a configuration one.
#
# ⚠ **If this still fails to configure, it is two lines to switch off**, and nothing else in r29
# depends on it: delete `alias(libs.plugins.androidx.baselineprofile)` from `app/build.gradle.kts`
# and `baselineProfile(projects.baselineprofile)` from its dependencies. The `:baselineprofile`
# module and `profileinstaller` can both stay where they are.
catalog = replace_once(
    catalog,
    'androidxComposeBom = "2026.03.01"\n',
    'androidxBenchmark = "1.5.0-rc02"\n'
    'androidxComposeBom = "2026.03.01"\n',
    "catalog: the benchmark version",
)

catalog = replace_once(
    catalog,
    'androidxNavigationCompose = "2.9.7"\n',
    'androidxNavigationCompose = "2.9.7"\n'
    'androidxProfileInstaller = "1.4.1"\n'
    'androidxUiAutomator = "2.4.0"\n',
    "catalog: the profileinstaller and uiautomator versions",
)

catalog = replace_once(
    catalog,
    "androidx-navigation-compose = ",
    "androidx-benchmark-macro-junit4 = { group = \"androidx.benchmark\", name = \"benchmark-macro-junit4\", version.ref = \"androidxBenchmark\" }\n"
    "androidx-profileinstaller = { group = \"androidx.profileinstaller\", name = \"profileinstaller\", version.ref = \"androidxProfileInstaller\" }\n"
    "androidx-test-uiautomator = { group = \"androidx.test.uiautomator\", name = \"uiautomator\", version.ref = \"androidxUiAutomator\" }\n"
    "androidx-navigation-compose = ",
    "catalog: the three libraries",
)

catalog = replace_once(
    catalog,
    'android-application = { id = "com.android.application", version.ref = "androidGradlePlugin" }\n',
    'android-application = { id = "com.android.application", version.ref = "androidGradlePlugin" }\n'
    'androidx-baselineprofile = { id = "androidx.baselineprofile", version.ref = "androidxBenchmark" }\n',
    "catalog: the baselineprofile plugin",
)

writes[CATALOG] = catalog

for needle in (
    'androidxBenchmark = "1.5.0-rc02"',
    "androidx-benchmark-macro-junit4 = ",
    "androidx-profileinstaller = ",
    "androidx-test-uiautomator = ",
    'androidx-baselineprofile = { id = "androidx.baselineprofile"',
):
    check(catalog.count(needle) == 1, f"catalog: {needle!r} did not land exactly once")

# ---------------------------------------------------------------- root build.gradle.kts

# ⚠ **Declared once here with `apply false`, and applied by bare id everywhere else.** That is not
# style, it is the only arrangement this build accepts. `build-logic` puts AGP on the root
# buildscript classpath as a plain dependency rather than through a plugin marker, so Gradle knows
# it is there but not what version it is — and a child project that asks for a plugin *with a
# version* when it is already on the classpath at an unknown one is refused outright:
#
#     Error resolving plugin [id: 'com.android.test', version: '9.1.0']
#     > the plugin is already on the classpath with an unknown version
#
# That is exactly why not one of the twenty-nine existing modules names an Android plugin with a
# version: they all go through a convention plugin that calls
# `apply(plugin = libs.plugins.android.library.get().pluginId)` — the id alone. r29's first
# `:baselineprofile` used `alias(...)`, carried a version, and hit the wall on its second build.

root_gradle = ROOT_GRADLE.read_text(encoding="utf-8")

root_gradle = replace_once(
    root_gradle,
    "    alias(libs.plugins.android.library) apply false\n",
    "    alias(libs.plugins.android.library) apply false\n"
    "    alias(libs.plugins.androidx.baselineprofile) apply false\n",
    "root: the baselineprofile plugin",
)

writes[ROOT_GRADLE] = root_gradle

# ---------------------------------------------------------------- settings.gradle.kts

settings_gradle = SETTINGS_GRADLE.read_text(encoding="utf-8")

settings_gradle = replace_once(
    settings_gradle,
    'include(":broadcast-receiver")\n',
    'include(":baselineprofile")\n'
    'include(":broadcast-receiver")\n',
    "settings: the module include",
)

writes[SETTINGS_GRADLE] = settings_gradle

# ---------------------------------------------------------------- app/build.gradle.kts

app = APP_GRADLE.read_text(encoding="utf-8")

app = replace_once(
    app,
    "    alias(libs.plugins.kotlin.serialization)\n",
    "    alias(libs.plugins.kotlin.serialization)\n"
    "    // Bare id: the version is declared once in the root build file. See the note there.\n"
    "    id(\"androidx.baselineprofile\")\n",
    "app: the plugin",
)

app = replace_once(
    app,
    "            isMinifyEnabled = true\n"
    "            isShrinkResources = true\n",
    "            isMinifyEnabled = true\n"
    "            isShrinkResources = true\n"
    "\n"
    "            // ⚠ **Minification stays ON, and the profile survives it.** A baseline profile\n"
    "            // names classes and methods and R8 renames them, so the plugin rewrites the\n"
    "            // profile through the obfuscation map that this build already produces. Nothing\n"
    "            // to set here; the note is so a later round does not \"fix\" a profile that looks\n"
    "            // wrong by turning minification off, which would cost more than it saved.\n",
    "app: the minify note",
)

app = replace_once(
    app,
    "    implementation(libs.androidx.navigation.compose)\n",
    "    implementation(libs.androidx.navigation.compose)\n"
    "\n"
    "    // What installs the baseline profile on first run. Without it the profile ships inside\n"
    "    // the APK and is never applied on most devices.\n"
    "    implementation(libs.androidx.profileinstaller)\n",
    "app: the profileinstaller dependency",
)

app = replace_once(
    app,
    "    androidTestImplementation(libs.androidx.test.ext.junit.ktx)\n",
    "    androidTestImplementation(libs.androidx.test.ext.junit.ktx)\n"
    "\n"
    "    // Where the generated profile comes from. ⚠ This does not run at build time — see\n"
    "    // baselineprofile/README.md for the one command that produces it.\n"
    "    baselineProfile(projects.baselineprofile)\n",
    "app: the baselineProfile dependency",
)

writes[APP_GRADLE] = app

# ---------------------------------------------------------------- the keep rule

proguard = PROGUARD.read_text(encoding="utf-8")

proguard = replace_once(
    proguard,
    "# Keep the package name\n"
    "-keep class com.android.geto.domain.model.** { *; }\n",
    "# Keep the names, not every member — r29.\n"
    "#\n"
    "# ⚠ `-keep class … { *; }` is a blanket opt-out of shrinking AND obfuscation for the project's\n"
    "# largest model package, which is far more than \"keep the package name\" asks for. What actually\n"
    "# needs members kept is the enums, and the rule below already keeps those. `-keepnames` keeps\n"
    "# the class names and lets R8 drop what nothing reaches.\n"
    "-keepnames class com.android.geto.domain.model.**\n",
    "proguard: the model keep rule",
)

# ⚠ Asserted after the edit that replaced it, and on the exact rule — the file's new comment names
# the old form for explanation, which a bare substring search would find.
check(
    "-keep class com.android.geto.domain.model.** { *; }" not in proguard,
    "proguard: the blanket keep rule survived",
)

check(
    "-keepnames class com.android.geto.domain.model.**" in proguard,
    "proguard: the narrowed rule did not land",
)

# The enum rule is deliberately untouched: the proto mappers reach values()/valueOf() reflectively.
check(
    "-keep enum com.android.geto.domain.model.** {" in proguard,
    "proguard: the enum rule was disturbed",
)

writes[PROGUARD] = proguard

# ---------------------------------------------------------------- the module

check(not MODULE.exists(), "baselineprofile: the module directory already exists")

writes[MODULE / "build.gradle.kts"] = LICENCE + """
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
"""

writes[MODULE / "src/main/AndroidManifest.xml"] = """<?xml version="1.0" encoding="utf-8"?>
<!--
  ~ Copyright 2026 soul_99 (suIMD)
  ~
  ~ Licensed under the GNU General Public License v3.0. See LICENSE.
  -->
<manifest xmlns:tools="http://schemas.android.com/tools">

    <!--
      The generator drives the app from outside its own process, so it needs to see what is
      installed. Instrumentation-only: this manifest is never merged into the app.
    -->
    <uses-permission android:name="android.permission.QUERY_ALL_PACKAGES"
        tools:ignore="QueryAllPackagesPermission" />

</manifest>
"""

writes[MODULE / "src/main/kotlin/com/android/geto/baselineprofile/StartupBaselineProfile.kt"] = (
    LICENCE + """package com.android.geto.baselineprofile

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
"""
)

writes[MODULE / "README.md"] = """# `:baselineprofile`

Generates the baseline profile that `:app` ships. Added in r29.

## What it is for

A baseline profile is a list of classes and methods, shipped inside the APK, that ART compiles
ahead of time at install rather than interpreting on first run. On a Compose app the measured
effect is on **cold start and the first scroll of a list** — the two moments this app is slowest,
because that is when the whole Compose runtime is being touched for the first time.

## Running it

Needs a connected device or emulator. It is not part of `assemble` and never runs in CI here.

```
gradlew :app:generateReleaseBaselineProfile
```

That installs the app and this module's own APK, drives the startup path several times, and writes

```
app/src/release/generated/baselineProfiles/baseline-prof.txt
```

**Commit that file.** It is the thing that ships; this module only produces it.

## If it produces nothing

* The device must be rooted or a `userdebug` build for Macrobenchmark to read the profile back. A
  Google APIs emulator image (not Play Store) is the easiest way to get one.
* `minSdk` here is 28 because Macrobenchmark cannot drive anything older. The profile it writes
  still installs back to the app's own `minSdk` of 24 through `profileinstaller`.

## When to regenerate

When the startup path changes — a new first screen, a different splash, a change to what
`MainActivity` reads before its first frame. Not every round.
"""

# ---------------------------------------------------------------- write

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

for path, text in writes.items():
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(text, encoding="utf-8")

    print(f"wrote {path.relative_to(ROOT).as_posix()}")

print("ok")
