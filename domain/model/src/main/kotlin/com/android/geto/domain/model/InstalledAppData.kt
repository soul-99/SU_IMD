/*
 *
 *   Copyright 2023 Einstein Blanco
 *   Modifications Copyright 2026 soul_99 (suIMD)
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
 * One installed package, for the Shizuku package-name picker.
 *
 * Every installed application is listed, not only those with a launcher icon: a Shizuku
 * install hidden by a stealth build has no icon in the launcher, and that is exactly the
 * install someone needs to pick here.
 *
 * [icon] is null when the package has none or it could not be decoded, which the picker
 * draws as a blank slot rather than dropping the row — a package with an unreadable icon
 * is still a package you may need to select.
 */
data class InstalledAppData(
    val packageName: String,
    val label: String,
    val icon: ByteArray?,
) {
    // ByteArray uses identity equality, which would make every re-read of the app list
    // look like a change and re-render the whole picker. The package name identifies the
    // row; nothing else needs comparing.
    override fun equals(other: Any?): Boolean = this === other ||
        (other is InstalledAppData && packageName == other.packageName && label == other.label)

    override fun hashCode(): Int = 31 * packageName.hashCode() + label.hashCode()
}
