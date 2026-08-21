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
package com.android.geto.domain.model

/**
 * The icon is deliberately left out of [equals] and [hashCode].
 *
 * It is a rendered PNG derived entirely from [componentName] and [lastUpdateTime], both of
 * which are compared, so comparing it adds nothing. It used to be compared with
 * `contentEquals`, which meant the `distinctUntilChanged` on the launcher list walked a
 * few hundred byte arrays element by element every time any package on the device changed.
 */
data class LauncherAppsActivityInfo(
    val componentName: String,
    val packageName: String,
    val activityIcon: ByteArray?,
    val activityLabel: String,
    val firstInstallTime: Long,
    val lastUpdateTime: Long,
    val isSystem: Boolean,
) {
    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (other !is LauncherAppsActivityInfo) return false

        return componentName == other.componentName &&
            packageName == other.packageName &&
            activityLabel == other.activityLabel &&
            firstInstallTime == other.firstInstallTime &&
            lastUpdateTime == other.lastUpdateTime &&
            isSystem == other.isSystem
    }

    override fun hashCode(): Int {
        var result = componentName.hashCode()
        result = 31 * result + packageName.hashCode()
        result = 31 * result + activityLabel.hashCode()
        result = 31 * result + firstInstallTime.hashCode()
        result = 31 * result + lastUpdateTime.hashCode()
        result = 31 * result + isSystem.hashCode()
        return result
    }
}
