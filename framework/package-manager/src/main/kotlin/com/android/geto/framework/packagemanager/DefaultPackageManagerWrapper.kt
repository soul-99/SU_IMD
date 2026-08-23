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
package com.android.geto.framework.packagemanager

import android.content.ComponentName
import android.content.Context
import android.content.pm.ApplicationInfo
import android.content.pm.PackageManager
import android.os.Build
import com.android.geto.domain.common.dispatcher.Dispatcher
import com.android.geto.domain.common.dispatcher.GetoDispatchers
import com.android.geto.domain.framework.PackageManagerWrapper
import com.android.geto.domain.model.InstalledAppData
import com.android.geto.framework.drawable.AndroidDrawableWrapper
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.withContext
import javax.inject.Inject

internal class DefaultPackageManagerWrapper @Inject constructor(
    private val androidDrawableWrapper: AndroidDrawableWrapper,
    @param:ApplicationContext private val context: Context,
    @param:Dispatcher(GetoDispatchers.IO) private val ioDispatcher: CoroutineDispatcher,
) : PackageManagerWrapper {
    private val packageManager = context.packageManager

    private companion object {
        /** Comfortably covers a 40dp picker row at xxxhdpi. */
        const val PICKER_ICON_SIZE = 96
    }

    override suspend fun getActivityIcon(componentName: String): ByteArray? = withContext(ioDispatcher) {
        try {
            ComponentName.unflattenFromString(componentName)?.let {
                androidDrawableWrapper.toByteArray(
                    drawable = packageManager.getActivityIcon(it),
                )
            }
        } catch (_: PackageManager.NameNotFoundException) {
            null
        }
    }

    override suspend fun getInstalledApps(): List<InstalledAppData> = withContext(ioDispatcher) {
        val applications = try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                packageManager.getInstalledApplications(
                    PackageManager.ApplicationInfoFlags.of(0),
                )
            } else {
                @Suppress("DEPRECATION")
                packageManager.getInstalledApplications(0)
            }
        } catch (_: RuntimeException) {
            // Same binder transaction limit as getLastInstallTimes: an empty picker the
            // user can still type into beats no Settings screen at all.
            emptyList()
        }

        applications.map { applicationInfo ->
            InstalledAppData(
                packageName = applicationInfo.packageName,
                label = runCatching {
                    packageManager.getApplicationLabel(applicationInfo).toString()
                }.getOrDefault(applicationInfo.packageName),
                // PICKER_ICON_SIZE rather than the default: this list can run to several
                // hundred entries, and rasterising each at 192px costs seconds and
                // megabytes for rows drawn at 40dp.
                icon = runCatching {
                    androidDrawableWrapper.toByteArray(
                        drawable = packageManager.getApplicationIcon(applicationInfo),
                        size = PICKER_ICON_SIZE,
                    )
                }.getOrNull(),
            )
        }.sortedWith(compareBy(String.CASE_INSENSITIVE_ORDER) { it.label })
    }

    override suspend fun findLaunchablePackage(
        preferredPackage: String,
        labels: List<String>,
    ): String? = withContext(ioDispatcher) {
        if (preferredPackage.isNotBlank() && isLaunchable(preferredPackage)) {
            return@withContext preferredPackage
        }

        val applications = try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                packageManager.getInstalledApplications(
                    PackageManager.ApplicationInfoFlags.of(0),
                )
            } else {
                @Suppress("DEPRECATION")
                packageManager.getInstalledApplications(0)
            }
        } catch (_: RuntimeException) {
            emptyList()
        }

        // Ordered by the caller's preference, not by whatever order the package manager
        // happens to return, so "Shizuku, then Shevery" means exactly that.
        labels.firstNotNullOfOrNull { label ->
            applications.firstOrNull { applicationInfo ->
                isLaunchable(applicationInfo.packageName) &&
                    runCatching {
                        packageManager.getApplicationLabel(applicationInfo).toString()
                    }.getOrDefault("").trim().equals(label, ignoreCase = true)
            }?.packageName
        }
    }

    override suspend fun isInstalled(packageName: String): Boolean = withContext(ioDispatcher) {
        if (packageName.isBlank()) return@withContext false

        runCatching {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                packageManager.getPackageInfo(packageName, PackageManager.PackageInfoFlags.of(0))
            } else {
                @Suppress("DEPRECATION")
                packageManager.getPackageInfo(packageName, 0)
            }

            true
        }.getOrDefault(false)
    }

    private fun isLaunchable(packageName: String): Boolean = runCatching {
        packageManager.getLaunchIntentForPackage(packageName) != null
    }.getOrDefault(false)

    override suspend fun getLastInstallTimes(): Map<String, Long> = withContext(ioDispatcher) {
        val packages = try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                packageManager.getInstalledPackages(PackageManager.PackageInfoFlags.of(0))
            } else {
                @Suppress("DEPRECATION")
                packageManager.getInstalledPackages(0)
            }
        } catch (_: RuntimeException) {
            // A very large package list can blow the binder transaction limit on some
            // devices. Sorting by update time then falls back to "unknown", which is far
            // better than failing to show the app list at all.
            emptyList()
        }

        packages.associate { it.packageName to it.lastUpdateTime }
    }

    override fun isSystem(flags: Int): Boolean = (flags and (ApplicationInfo.FLAG_SYSTEM or ApplicationInfo.FLAG_UPDATED_SYSTEM_APP)) != 0
}
