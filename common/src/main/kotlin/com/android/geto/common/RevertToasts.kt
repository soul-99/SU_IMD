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
 * Posted to the main looper rather than shown directly: half of these callers are broadcast
 * receivers and tile services running on a background thread, where Toast.makeText throws.
 *
 * The application context, not this one, so a toast outliving the activity that asked for it
 * cannot hold it in memory.
 */
private fun Context.showRevertToast(message: Int) {
    val application = applicationContext

    Handler(Looper.getMainLooper()).post {
        Toast.makeText(application, message, Toast.LENGTH_SHORT).show()
    }
}
