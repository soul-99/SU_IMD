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
     * Every installed application, with its label and a small icon, sorted by label.
     *
     * Deliberately not limited to packages with a launcher entry: a Shizuku install
     * hidden by a stealth build has no launcher icon, and that is precisely the install
     * someone is trying to name in the picker this feeds.
     */
    suspend fun getInstalledApps(): List<InstalledAppData>

    /**
     * Last-update time for every installed package, keyed by package name.
     *
     * Bulk rather than per-package: the launcher list is rebuilt from scratch on every
     * package add, remove or change, and one binder call per app turned that into
     * hundreds of round trips before a single icon appeared.
     */
    suspend fun getLastInstallTimes(): Map<String, Long>

    fun isSystem(flags: Int): Boolean
}
