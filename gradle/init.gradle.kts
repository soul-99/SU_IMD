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
                // WARNING, read before running spotlessApply on this fork.
                //
                // licenseHeaderFile REPLACES the header it finds. spotless/copyright.kt
                // holds the original notice only, so applying it strips the
                // "Modifications Copyright 2026 soul_99 (suIMD)" line from the 98 files
                // that carry it - which is the notice GPL-3.0 section 5(a) asks a modified
                // work to keep.
                //
                // Adding that line to the copyright files is not a straight fix either:
                // spotless applies one header to every file, so untouched upstream files
                // would then claim a modification that never happened.
                //
                // Until that is decided, format without the header step:
                //   ./gradlew -I gradle/init.gradle.kts spotlessApply
                // is NOT safe as written. Run ktlint directly, or comment this line out
                // for the run.
                licenseHeaderFile(rootProject.file("spotless/copyright.kt"))
            }
            format("kts") {
                target("**/*.kts")
                targetExclude("**/build/**/*.kts")
                // Look for the first line that doesn't have a block comment (assumed to be the license)
                licenseHeaderFile(rootProject.file("spotless/copyright.kts"), "(^(?![\\/ ]\\*).*$)")
            }
            format("xml") {
                target("**/*.xml")
                targetExclude("**/build/**/*.xml")
                // Look for the first XML tag that isn't a comment (<!--) or the xml declaration (<?xml)
                licenseHeaderFile(rootProject.file("spotless/copyright.xml"), "(<[^!?])")
            }
        }
    }
}