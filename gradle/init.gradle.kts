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

val ktlintVersion = "1.8.0"

initscript {
    val spotlessVersion = "8.1.0"

    repositories {
        mavenCentral()
    }

    dependencies {
        classpath("com.diffplug.spotless:spotless-plugin-gradle:$spotlessVersion")
    }
}

rootProject {
    subprojects {
        apply<com.diffplug.gradle.spotless.SpotlessPlugin>()
        extensions.configure<com.diffplug.gradle.spotless.SpotlessExtension> {
            kotlin {
                target("**/*.kt")
                targetExclude("**/build/**/*.kt")
                ktlint(ktlintVersion).editorConfigOverride(
                    mapOf(
                        "android" to "true",
                    ),
                )
                // Header enforcement is deliberately off on this fork.
                //
                // licenseHeaderFile REPLACES the header it finds with the contents of the
                // file it is given, and spotless/copyright.kt holds the original notice
                // only. Left on, spotlessApply would strip
                // "Modifications Copyright 2026 soul_99 (suIMD)" from every file that
                // carries it - the notice GPL-3.0 section 5(a) asks a modified work to keep.
                //
                // Putting that line into copyright.kt is not the fix either: spotless
                // applies one header to every file, so the files this fork never touched
                // would start claiming a modification that never happened.
                //
                // So spotless formats, and headers are maintained by hand. New files copy
                // the header from the file beside them. The licence position itself is
                // unaffected and is set out in full in SUIMD.md section 3.
            }
            format("kts") {
                target("**/*.kts")
                targetExclude("**/build/**/*.kts")
                // Header enforcement off, for the reason given above.
            }
            format("xml") {
                target("**/*.xml")
                targetExclude("**/build/**/*.xml")
                // Header enforcement off, for the reason given above.
            }
        }
    }
}