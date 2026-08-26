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
 * Which apps the memory function still has something outstanding for.
 *
 * The union of the two records a per-app launch leaves behind: the pre-launch snapshot it
 * saved so it could put the settings back, and any accessibility services it is holding down
 * under that app's own component name. The device-wide holder is deliberately excluded - it
 * belongs to the manager and the "Settings to hide" launch, not to any one app's memory, and
 * a "revert every app" sweep must not touch it.
 *
 * A component appearing in either record is enough: a profile that only hid debugging settings
 * has a snapshot but no accessibility hold, and one that only managed accessibility may have a
 * hold recorded before its snapshot write landed.
 */
fun memoryHeldComponents(
    settingStateBefore: Map<String, Map<String, String?>>,
    heldAccessibilityServices: Map<String, List<String>>,
): Set<String> = settingStateBefore.keys +
    heldAccessibilityServices.keys.filterNot { it == AccessibilityServicePlan.DEVICE_WIDE_HOLD }
