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

import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import android.net.Uri

/**
 * The project's own links, and the two ways out to them.
 *
 * Shared rather than repeated because both the one-time note and the Settings screen offer
 * the same three destinations, and a URL that drifts between two copies is a link that
 * quietly stops working in one of them.
 */
object ProjectLinks {
    const val REPOSITORY = "https://github.com/soul-99/SU_IMD"

    const val RELEASES = "$REPOSITORY/releases"

    /** The section the version line points at: what changed, per version. */
    const val CHANGELOG = "$REPOSITORY#added-in-this-fork"

    /**
     * Obtainium's documented "add app" deep link: it opens Obtainium's Add App page with
     * the repository URL already filled in, leaving the actual add to the user.
     */
    const val OBTAINIUM_ADD = "obtainium://add/$REPOSITORY"

    /**
     * The maintainer's documented fallback for places that cannot handle a custom scheme.
     * Used here for the other case it happens to cover: Obtainium not being installed, when
     * this lands on a page that explains what it is rather than on an error.
     */
    const val OBTAINIUM_FALLBACK =
        "https://apps.obtainium.imranr.dev/redirect.html?r=$OBTAINIUM_ADD"
}

/**
 * Opens [uri], doing nothing if no app on the device can.
 *
 * A missing browser is not worth crashing over, and it is the only realistic reason one of
 * these fails.
 */
fun Context.openProjectUri(uri: String) {
    runCatching {
        startActivity(
            Intent(Intent.ACTION_VIEW, Uri.parse(uri)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK),
        )
    }.onFailure {
        if (it !is ActivityNotFoundException && it !is SecurityException) throw it
    }
}

/**
 * Opens the system share sheet with [message] followed by the repository link.
 *
 * The link is appended here rather than left to the caller so every share carries the same
 * URL, the one in [ProjectLinks]; a share message with the address typed into it by hand is
 * the one that goes out pointing at last year's repo. Does nothing if no app can share, which
 * on a device with no messaging or mail app is the only way it fails.
 */
fun Context.shareProject(message: String) {
    val send = Intent(Intent.ACTION_SEND).apply {
        type = "text/plain"
        putExtra(Intent.EXTRA_TEXT, "$message\n${ProjectLinks.REPOSITORY}")
    }

    runCatching {
        startActivity(
            Intent.createChooser(send, null).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK),
        )
    }.onFailure {
        if (it !is ActivityNotFoundException && it !is SecurityException) throw it
    }
}

/**
 * Hands this app's repository to Obtainium, falling back to the web redirect when
 * Obtainium is not installed.
 *
 * Returns false when neither could be opened, so a caller can say something rather than
 * appearing to have done nothing.
 */
fun Context.openObtainium(): Boolean {
    val opened = runCatching {
        startActivity(
            Intent(Intent.ACTION_VIEW, Uri.parse(ProjectLinks.OBTAINIUM_ADD))
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK),
        )

        true
    }.getOrDefault(false)

    if (opened) return true

    return runCatching {
        startActivity(
            Intent(Intent.ACTION_VIEW, Uri.parse(ProjectLinks.OBTAINIUM_FALLBACK))
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK),
        )

        true
    }.getOrDefault(false)
}
