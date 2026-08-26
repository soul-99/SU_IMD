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
import android.os.Handler
import android.os.Looper
import android.widget.Toast

/**
 * The two reverts announce themselves, because from the outside they look identical — the
 * screen does not change, and the settings they touch are not on screen.
 *
 * Which one ran matters: one puts back what a single app switched off, the other puts the
 * whole device into the configured default. Saying which happened is the difference between
 * a user trusting the button and pressing it twice to see if it worked.
 *
 * There are six places these fire from — a tile, a notification, a shortcut, two buttons and
 * a dialog — several of which have no UI of their own to show a snackbar in. A toast is the
 * one thing that works from all of them.
 */
fun Context.showRevertToDefaultToast() = showRevertToast(R.string.revert_to_default_toast)

fun Context.showRevertFromMemoryToast() = showRevertToast(R.string.revert_from_memory_toast)

/**
 * The same two, for a revert nobody pressed a button for.
 *
 * Worded apart from the manual pair on purpose. A revert the user asked for needs only to
 * confirm it ran; one that happened because they came back to the app has to say why the
 * device just changed, or it reads as the app doing something at random.
 */
fun Context.showAutoRevertToDefaultToast() =
    showRevertToast(R.string.auto_revert_to_default_toast)

fun Context.showAutoRevertFromMemoryToast() =
    showRevertToast(R.string.auto_revert_from_memory_toast)

/**
 * And the three ways a revert can end without having finished.
 *
 * Only Shizuku and overlay access get a message, because they are the only two that depend on
 * something outside this app and so the only two a user cannot simply fix from the services
 * manager. A failed settings write is already visible there as a switch in the wrong position.
 *
 * Fired after the "Revert to default" toast rather than instead of it: the first says what ran,
 * this says what did not land, and losing the first would make a revert that half worked look
 * like a revert that never started.
 */
fun Context.showRevertShizukuFailedToast() =
    showRevertToast(R.string.revert_failed_shizuku_toast, long = true)

fun Context.showRevertOverlayFailedToast() =
    showRevertToast(R.string.revert_failed_overlay_toast, long = true)

fun Context.showRevertShizukuAndOverlayFailedToast() =
    showRevertToast(R.string.revert_failed_shizuku_and_overlay_toast, long = true)

/**
 * The one the Tasker integration adds: "Settings hidden", for the hide trigger.
 *
 * Hiding from a launch needs no toast - the app it hides for opens a beat later and is the
 * confirmation. Hiding from a macro opens nothing, so without a word the trigger looks like it
 * did nothing, which is the same reason the shortcut path grew its own feedback.
 */
fun Context.showSettingsHiddenToast() = showRevertToast(R.string.settings_hidden_toast)

/**
 * Posted to the main looper rather than shown directly: half of these callers are broadcast
 * receivers and tile services running on a background thread, where Toast.makeText throws.
 *
 * The application context, not this one, so a toast outliving the activity that asked for it
 * cannot hold it in memory.
 */
private fun Context.showRevertToast(message: Int, long: Boolean = false) {
    val application = applicationContext

    // LENGTH_LONG for the failures. They are a sentence and a half naming two things and
    // where to fix them, and the short duration is about two seconds - enough to notice a
    // toast, not enough to read one. Android allows no third option: the duration is a flag,
    // not a number, and anything longer than this needs a dialog or the notification, both of
    // which the failures already have.
    val duration = if (long) Toast.LENGTH_LONG else Toast.LENGTH_SHORT

    Handler(Looper.getMainLooper()).post {
        Toast.makeText(application, message, duration).show()
    }
}
