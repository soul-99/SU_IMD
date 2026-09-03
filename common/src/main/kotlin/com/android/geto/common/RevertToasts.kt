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
 * The v3 toast set: **one** said as the work starts, nine said when it has finished.
 *
 * Every one of them is `Toast.LENGTH_SHORT`, here and in the module-local toasts elsewhere in
 * the app that call `Toast.makeText` directly. `design/_v3_toast_length.py` asserts there is no
 * `LENGTH_LONG` left anywhere.
 *
 * ⚠ **The completion toasts name the framework that acted, and that is the whole point of
 * them.** After the split "the settings came back" is no longer one sentence: they may have
 * been driven to the configured defaults or restored to what was actually there, for the
 * device or for one app, and a user who cannot tell which cannot tell whether the app did what
 * they asked.
 *
 * ⚠ **One progress toast, and it is IMD+'s hide.** The author's rule, and the reason it is
 * this one: it is the only work nobody asked for. IMD+ force-stops the app the user has just
 * tapped, so without a word the app they opened simply vanishes. Every other route was pressed
 * — a tile, a button, a notification — and the user is already looking at the thing they
 * pressed, so a progress toast there says nothing and queues in front of the completion toast,
 * which is the one carrying the answer. Two toasts for one press also read as two things
 * happening.
 *
 * ⚠ **Only the hiding ones say IMD+, and that is the author's rule stated outright.** The
 * prefix marks work the user did not ask for, and an unhide is always asked for — a
 * notification button, a tile, a swipe-away, a phone put down — whichever framework hid the
 * settings. Both prefixes respect the Hiding and Unhiding frameworks; the prefix says who
 * started the work, not which framework ran.
 *
 * ⚠ **There are no failure toasts any more.** Every case the old three covered already raises
 * a notification — `OverlayRestoreRunner.report()` for overlay access,
 * `buildShizukuRevertFailedNotification` for Shizuku, and the overlay one names Shizuku as the
 * cause when both fail — so removing them lost no news, only a duplicate of it. A revert that
 * did not finish therefore says **nothing** rather than borrowing the completion toast: the
 * notification is the honest report, and "Settings restored" over a half-done revert is not.
 */
fun Context.showAutoHidingToast() = showRevertToast(R.string.toast_auto_hiding)

fun Context.showHiddenToast(appName: String? = null, autoHide: Boolean = false) {
    if (appName == null) {
        showRevertToast(
            if (autoHide) R.string.toast_auto_done_hidden else R.string.toast_done_hidden,
        )

        return
    }

    showRevertToast(
        if (autoHide) R.string.toast_auto_done_hidden_for else R.string.toast_done_hidden_for,
        argument = appName,
    )
}

/**
 * The way back from a hide, whatever set it in motion and whichever framework drove it.
 *
 * [appName] is the per-app memory revert's app, and null is not a missing value — it is the
 * device-wide memory record, which names no app because no app owns it. The two sentences
 * differ by a bracket for exactly that reason.
 *
 * ⚠ **"Restored", not "reverted", and [showRevertedToDefaultToast] is the exception that
 * defines it.** The author's rule: a hide is undone, so the settings are *restored* — even on
 * the `RevertToDefault` unhiding framework, where the destination happens to be the configured
 * list. Only the named `Revert to default` function, run on purpose from somewhere that is not
 * an unhide, still says reverted. Same work underneath; two different things to say about it.
 */
fun Context.showRestoredToast(fromMemory: Boolean, appName: String? = null) {
    if (!fromMemory) {
        showRevertToast(R.string.toast_done_restored_defaults)

        return
    }

    if (appName == null) {
        showRevertToast(R.string.toast_done_restored_memory)

        return
    }

    showRevertToast(R.string.toast_done_restored_memory_for, argument = appName)
}

/**
 * The named `Revert to default` function, invoked on purpose.
 *
 * Three routes reach this and the author named all three: the settings manager's button, the
 * Revert to default Quick Settings tile (and the launcher shortcut, which shares its activity),
 * and Tasker's `ACTION_REVERT_TO_DEFAULT`. What they have in common is that nobody was undoing
 * a hide — they asked for the device to be put into the state they nominated as normal, which
 * is a thing you revert to rather than restore.
 */
fun Context.showRevertedToDefaultToast() = showRevertToast(R.string.toast_done_reverted_defaults)

/**
 * The Favourites button when there is no debt to settle.
 *
 * Only that button says this, and only because it is the one unhide route that refuses to fall
 * back. The Hide settings tile in the same position reverts to default instead, on the grounds
 * that a tile which did nothing reads as broken; this button is pressed from a screen that can
 * answer in words, so it answers.
 */
fun Context.showNothingToRestoreToast() = showRevertToast(R.string.toast_nothing_to_restore)

/**
 * Posted to the main looper rather than shown directly: half of these callers are broadcast
 * receivers and tile services running on a background thread, where Toast.makeText throws.
 *
 * The application context, not this one, so a toast outliving the activity that asked for it
 * cannot hold it in memory.
 */
private fun Context.showRevertToast(
    message: Int,
    argument: String? = null,
) {
    val application = applicationContext

    // Resolved on the application context, not by handing the format to Toast: an argument
    // has to be substituted before the string reaches makeText, and getString(id, arg) is the
    // one form that survives a locale whose translation reorders the placeholder.
    val text = if (argument == null) {
        application.getString(message)
    } else {
        application.getString(message, argument)
    }

    Handler(Looper.getMainLooper()).post {
        Toast.makeText(application, text, Toast.LENGTH_SHORT).show()
    }
}
