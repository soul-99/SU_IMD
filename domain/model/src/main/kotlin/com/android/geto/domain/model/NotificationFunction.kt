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
 * What the notification posted after launching an app is for.
 *
 * The two are genuinely different products, not a display option, which is why this is a
 * mode rather than a checkbox:
 *
 * * [Memory] is per-app. Each launch records what the device was really set to beforehand
 *   and posts its own notification, so reverting puts back exactly what that app changed
 *   and leaves everything else alone. Several apps launched in a row means several
 *   notifications, each undoing its own share.
 * * [RevertToDefault] is per-device. There is one notification at a time and one button on
 *   it, and pressing it drives every configured target to the state chosen in settings,
 *   regardless of which app was launched or what it changed.
 *
 * A device where the user keeps developer options on all the time wants the first. A device
 * where the user keeps them off and only turns them on deliberately wants the second, and
 * finds a pile of per-app notifications to be noise.
 */
enum class NotificationFunction {
    /** What every version before this one did, and still the right answer for some devices. */
    Memory,

    RevertToDefault,
    ;

    companion object {
        /**
         * What an install that has never opened the picker gets.
         *
         * [RevertToDefault] rather than the older behaviour, because the failure modes are
         * not symmetric. The memory function's weak point is that its notification is the
         * only way back, and a notification can be swiped away, culled by a launcher or
         * lost to a battery optimiser — leaving developer options switched off with nothing
         * on screen to undo it. "Revert to default" has one button that always does the
         * same thing, and the tile and shortcut reach it without a notification at all.
         *
         * The cost is that it restores a configured state rather than exactly what one app
         * changed, which is why setup now points people at that configuration.
         */
        val Default: NotificationFunction = RevertToDefault
    }
}
