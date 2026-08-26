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
 * One app that can display over other apps, for the picker.
 *
 * The counterpart of [AccessibilityServiceData], and the same rules apply: only
 * [packageName] is ever persisted, and the label is resolved fresh every time so a renamed
 * or updated app never leaves a stale entry in the list.
 *
 * [allowed] is the live AppOp. It is false only for a package IMD is currently holding
 * down - those stay in the list precisely because they would otherwise vanish from it for
 * as long as the hiding is in force, which is when someone is most likely to open it.
 */
data class OverlayPackageData(
    val packageName: String,
    val label: String,
    val allowed: Boolean,
)
