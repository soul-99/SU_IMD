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

/** Asks the app to open on Settings with the Advanced section already expanded. */
const val EXTRA_OPEN_ADVANCED_SETTINGS = "com.android.geto.OPEN_ADVANCED_SETTINGS"

/**
 * Starts the app over, and puts the user back where they were.
 *
 * CLEAR_TASK rather than the CLEAR_TOP of [openRevertConfiguration], because this is a
 * re-launch and not a navigation: every screen behind it is discarded and the activity is
 * built again from nothing. Changing which mechanism hides and unhides settings changes what
 * several screens are looking at, and a running instance would keep showing what it read
 * before the change - most visibly the per-app rows, which mean different things under the
 * two mechanisms.
 *
 * The process itself is not killed. Nothing in this app holds the mechanism in a static or a
 * singleton — every reader takes it from stored preferences — so a fresh activity is a fresh
 * read of everything, and killing the process would only make the app take a second longer to
 * come back.
 *
 * Found through the package manager rather than by naming the activity, because this is
 * called from a feature module and the activity lives in the app module, which depends on it
 * and not the other way round.
 */
/**
 * Brings IMD to the front, on whatever it was last showing.
 *
 * ⚠ **No extra, and that is the whole of it.** [EXTRA_OPEN_ADVANCED_SETTINGS] is what makes
 * `HomeScreen` navigate to the Settings tab; without it the app simply comes back - the author's
 * *"open imd app instead of imd app settings page"*.
 *
 * ⚠ **`CLEAR_TOP` with `SINGLE_TOP`, never `CLEAR_TASK`.** A cleared task means the activity is
 * destroyed and rebuilt, which has nothing to animate *from* and is exactly the *"no animation so
 * it looks wierd"* this replaces. Raised from inside the app the running activity is handed the
 * intent and stays as it was, so the manager dialog's own dismissal is the transition; raised
 * from the tile or the pinned shortcut it is an ordinary activity start with the system's
 * ordinary transition.
 *
 * A second function rather than a flag on [relaunchToAdvancedSettings], so the caller that
 * genuinely needs a rebuilt activity - a change of hiding-unhiding mechanism - cannot lose it by
 * accident.
 */
fun Context.openImdApp() {
    val intent = packageManager.getLaunchIntentForPackage(packageName) ?: return

    intent.addFlags(
        Intent.FLAG_ACTIVITY_NEW_TASK or
            Intent.FLAG_ACTIVITY_CLEAR_TOP or
            Intent.FLAG_ACTIVITY_SINGLE_TOP,
    )

    startActivity(intent)
}

fun Context.relaunchToAdvancedSettings() {
    val intent = packageManager.getLaunchIntentForPackage(packageName) ?: return

    intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK)

    intent.putExtra(EXTRA_OPEN_ADVANCED_SETTINGS, true)

    startActivity(intent)
}
