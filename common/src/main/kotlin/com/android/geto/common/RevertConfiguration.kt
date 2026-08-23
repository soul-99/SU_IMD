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
package com.android.geto.common

import android.content.Context
import android.content.Intent

/**
 * Asks the app to open on Settings with the revert configuration in front.
 *
 * Set on the launch intent rather than expressed as a route, because the request comes
 * from outside the navigation graph — from the manager dialog, which the Quick Settings
 * tile and the launcher shortcut both show without the app running at all.
 */
const val EXTRA_OPEN_REVERT_CONFIGURATION = "com.android.geto.OPEN_REVERT_CONFIGURATION"

/**
 * Opens the app on the revert configuration, whether or not it is already running.
 *
 * Found through the package manager rather than by naming the activity: this is called
 * from feature modules, and the activity lives in the app module, which depends on them
 * and not the other way round.
 *
 * CLEAR_TOP with SINGLE_TOP is what makes an app that is already open honour this rather
 * than simply coming to the front on whatever tab it was left on — the running instance
 * is handed the intent instead of a new one being stacked on top of it.
 */
fun Context.openRevertConfiguration() {
    val intent = packageManager.getLaunchIntentForPackage(packageName) ?: return

    intent.addFlags(
        Intent.FLAG_ACTIVITY_NEW_TASK or
            Intent.FLAG_ACTIVITY_CLEAR_TOP or
            Intent.FLAG_ACTIVITY_SINGLE_TOP,
    )

    intent.putExtra(EXTRA_OPEN_REVERT_CONFIGURATION, true)

    startActivity(intent)
}
