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
 * under that app's own component name.
 *
 * **The two holders that are not apps are excluded.** The device-wide one belongs to the
 * manager and the "Settings to hide" launch, and IMD+'s belongs to IMD's own detector — neither
 * is any app's memory, neither can be reverted by naming a component, and a "revert every app"
 * sweep must not go looking for an app called `__auto_hide_own_detector__`. Counting either
 * would also make [UserData.memoryHoldsSettings] read true for a device with nothing of the
 * user's hidden at all, which is what the Quick Settings tile and the IMD+ switch both read.
 *
 * A component appearing in either record is enough: a profile that only hid debugging settings
 * has a snapshot but no accessibility hold, and one that only managed accessibility may have a
 * hold recorded before its snapshot write landed.
 *
 * ⚠ **The filter is applied to both maps, and until v3 it was applied to only one.** Nothing
 * wrote an internal holder into `settingStateBefore`, so the omission cost nothing and could
 * not be seen. v3's device-wide memory record writes exactly that key — see
 * `ApplySettingsToHideUseCase` — and without this filter `RevertAllMemoryUseCase` would sweep
 * it as if it were an app and call the per-app revert with a component name no launcher has
 * ever heard of. The doc above always claimed both were excluded; now they are.
 */
fun memoryHeldComponents(
    settingStateBefore: Map<String, Map<String, String?>>,
    heldAccessibilityServices: Map<String, List<String>>,
): Set<String> = (settingStateBefore.keys + heldAccessibilityServices.keys)
    .filterNot { it in AccessibilityServicePlan.INTERNAL_HOLDS }
    .toSet()

/**
 * Whether the memory function is still holding anything down.
 *
 * Derived rather than stored, and that is the point: the records it reads are written by a
 * launch and removed by the revert of that same launch, so this answer cannot disagree with
 * what is actually outstanding. A stored flag could, and the one place it would show is the
 * Quick Settings tile — the surface most likely to be looked at long after the launch, with
 * the app not running.
 */
val UserData.memoryHoldsSettings: Boolean
    get() = memoryHeldComponents(
        settingStateBefore = settingStateBefore,
        heldAccessibilityServices = heldAccessibilityServices,
    ).isNotEmpty()

/**
 * Whether anything IMD did is currently hiding settings — by either mechanism.
 *
 * What the "Hide settings" tile shows, and what decides which reverts a press of it
 * has to run. The two halves are kept apart deliberately: they are undone by different
 * reverts, and a device can genuinely owe both at once — the tile hides device-wide whichever
 * mechanism is chosen, so a memory-function user who presses the tile and then launches an app
 * from IMD has one debt of each kind outstanding.
 */
val UserData.settingsHidden: Boolean
    get() = settingsHiddenDeviceWide || memoryHoldsSettings
