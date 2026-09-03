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
 * Which settings a launch hides.
 *
 * Half of what [NotificationFunction] used to decide on its own. v3 splits that one choice in
 * two because it was always two questions wearing one switch: *what gets hidden* and *how it
 * comes back* are independent, and welding them together meant a user who wanted per-app
 * hiding had to accept memory reverting with it, and the reverse.
 *
 * * [ImdDefaults] hides one configured list, the same for every app. Nothing has to be set up
 *   per app, and the tile, the shortcut and the intents hide exactly what a launch does.
 * * [PerApp] hides a profile belonging to the app being launched. The device-wide list is
 *   still there and still used — but only by the Hide settings QS toggle and the IMD
 *   intents, which name no app and so have no profile to read.
 *
 * ⚠ **This does not decide what a revert does.** That is [UnhidingFramework], and the four
 * combinations are all reachable. Two of them no released version has ever run: see
 * `MigrateFrameworksUseCase` for which one an upgrading install lands in, and
 * `ApplySettingsToHideUseCase` for the device-wide memory record that
 * [ImdDefaults] + [UnhidingFramework.Memory] needs.
 */
enum class HidingFramework {
    /** One list for every app. */
    ImdDefaults,

    /** A profile per app, set by long-pressing an app icon in IMD. */
    PerApp,
    ;

    companion object {
        /**
         * What an install that has never opened the picker gets.
         *
         * [ImdDefaults], because it is the one that works with nothing configured per app —
         * a fresh install has no profiles, and [PerApp] on a device with none of them would
         * hide nothing at all for every app the user launched.
         */
        val Default: HidingFramework = ImdDefaults
    }
}
