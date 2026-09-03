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
package com.android.geto.domain.framework

import com.android.geto.domain.model.InstalledAppData

interface PackageManagerWrapper {
    suspend fun getActivityIcon(componentName: String): ByteArray?

    /**
     * The launcher label of one activity, for a sentence that names the app.
     *
     * Null when the component is gone — uninstalled between the launch and the toast — and
     * the caller then says the sentence that names no app rather than one with a blank in
     * it. The label, not the package name: "Settings hidden for com.example.bank" is not
     * what somebody reads a toast for.
     */
    suspend fun getActivityLabel(componentName: String): String?

    /**
     * Every installed application, with its label and a small icon, sorted by label.
     *
     * Deliberately not limited to packages with a launcher entry: a Shizuku install
     * hidden by a stealth build has no launcher icon, and that is precisely the install
     * someone is trying to name in the picker this feeds.
     */
    suspend fun getInstalledApps(): List<InstalledAppData>

    /**
     * The package a "open this app" shortcut should target: [preferredPackage] if it is
     * installed and launchable, otherwise the first installed app whose label matches one
     * of [labels], in order. Null when nothing matches.
     *
     * Separate from [getInstalledApps] because it needs no icons. Resolving one package to
     * open should not cost a few hundred bitmaps.
     */
    suspend fun findLaunchablePackage(preferredPackage: String, labels: List<String>): String?

    /**
     * Whether [packageName] is installed at all — launchable or not.
     *
     * Not the same question as [findLaunchablePackage]: a Shizuku build hiding itself has
     * no launcher entry but is very much installed, and the difference decides whether the
     * manager's Shizuku switch is usable or dead.
     */
    suspend fun isInstalled(packageName: String): Boolean

    /**
     * Last-update time for every installed package, keyed by package name.
     *
     * Bulk rather than per-package: the launcher list is rebuilt from scratch on every
     * package add, remove or change, and one binder call per app turned that into
     * hundreds of round trips before a single icon appeared.
     */
    suspend fun getLastInstallTimes(): Map<String, Long>

    /**
     * Small icons for the named packages only; missing or undecodable packages are omitted.
     *
     * ⚠ **The counterpart of [getAppLabels], and it exists for the same reason.**
     * [getInstalledApps] would answer this too, by enumerating every package on the device and
     * rasterising an icon for each — seconds of work and megabytes of bitmaps to put pictures on
     * a dozen rows. The pickers that need this know exactly which packages they are asking about.
     */
    suspend fun getAppIcons(packageNames: Set<String>): Map<String, ByteArray>

    /** Installation identities for the requested packages; missing packages are omitted. */
    suspend fun getPackageIdentities(packageNames: Set<String>): Map<String, String>

    /**
     * Display labels for the named packages only; missing packages are omitted.
     *
     * The cheap way to put a human name on a handful of package names. [getInstalledApps]
     * answers the same question, but it enumerates every package on the device and rasterises
     * an icon for each — seconds of work to label a dozen rows that show no icons at all.
     */
    suspend fun getAppLabels(packageNames: Set<String>): Map<String, String>

    fun isSystem(flags: Int): Boolean

    /**
     * IMD's own package name.
     *
     * IMD+ has to name itself to the shell: the restricted-settings AppOp and the battery
     * exemption are both granted per package, and the package is the one this code is running
     * in. Read from the framework rather than written down anywhere, so a build flavour or a
     * rename cannot leave a stale copy behind that silently grants nothing.
     */
    fun ownPackageName(): String
}
