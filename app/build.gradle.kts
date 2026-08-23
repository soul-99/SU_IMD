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

import java.util.Properties

plugins {
    alias(libs.plugins.com.android.geto.application)
    alias(libs.plugins.com.android.geto.hilt)
    alias(libs.plugins.kotlin.serialization)
}

android {
    namespace = "com.android.geto"

    // No key ships with this source. Release builds are signed either through
    // Build > Generate Signed App Bundle / APK in Android Studio, or by dropping a
    // keystore.properties next to settings.gradle.kts:
    //
    //     storeFile=C:/path/to/your.jks
    //     storePassword=...
    //     keyAlias=...
    //     keyPassword=...
    //
    // That file is gitignored. Keep the same key for every build you install: Android
    // will only accept an update signed by the key that signed what is already there, and
    // an uninstall loses the WRITE_SECURE_SETTINGS grant.
    val keystoreProperties = rootProject.file("keystore.properties")

    signingConfigs {
        if (keystoreProperties.exists()) {
            create("release") {
                val properties = Properties().apply {
                    keystoreProperties.inputStream().use(::load)
                }

                storeFile = file(properties.getProperty("storeFile"))
                storePassword = properties.getProperty("storePassword")
                keyAlias = properties.getProperty("keyAlias")
                keyPassword = properties.getProperty("keyPassword")
            }
        }
    }

    defaultConfig {
        applicationId = "com.soul_99.suIMD"
        versionCode = 8
        versionName = "1.6.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"

        vectorDrawables {
            useSupportLibrary = true
        }
    }

    // Debug builds are left on Android Studio's own debug key, which is generated per
    // machine — a debug build from another computer will not install over this one.
    buildTypes {
        release {
            signingConfig = signingConfigs.findByName("release")

            isMinifyEnabled = true
            isShrinkResources = true

            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro",
            )
        }
    }
}

dependencies {
    implementation(projects.broadcastReceiver)
    implementation(projects.common)
    implementation(projects.designSystem)
    implementation(projects.data.repository)
    implementation(projects.domain.common)
    implementation(projects.domain.framework)
    implementation(projects.domain.model)
    implementation(projects.domain.repository)
    implementation(projects.domain.useCase)

    implementation(projects.feature.apps)
    implementation(projects.feature.appSettings)
    implementation(projects.feature.home)
    implementation(projects.feature.settings)

    implementation(projects.framework.accessibility)
    implementation(projects.framework.assetManager)
    implementation(projects.framework.drawable)
    implementation(projects.framework.launcherApps)
    implementation(projects.framework.notificationManager)
    implementation(projects.framework.packageManager)
    implementation(projects.framework.secureSettings)
    implementation(projects.framework.shizuku)
    implementation(projects.framework.shortcutManager)
    implementation(projects.ui)

    implementation(libs.androidx.activity.ktx)
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.core.splashscreen)
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.androidx.lifecycle.viewmodel.ktx)
    implementation(libs.androidx.lifecycle.runtime.compose)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.navigation.compose)
    implementation(libs.kotlinx.serialization.json)

    androidTestImplementation(libs.androidx.test.core.ktx)
    androidTestImplementation(libs.androidx.test.runner)
    androidTestImplementation(libs.androidx.test.rules)
    androidTestImplementation(libs.androidx.test.ext.junit.ktx)
}
