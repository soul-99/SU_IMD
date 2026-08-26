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
package com.android.geto.broadcastreceiver

import android.content.Context
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.usecase.GetOverlayRestoreFailedUseCase
import com.android.geto.domain.usecase.SetManualTargetUseCase
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.OVERLAY_RESTORE_NOTIFICATION_ID
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Puts overlay access back, and keeps asking until it works.
 *
 * Both ends of the retry loop live here: [retry] is the notification's button, and [report]
 * is what a failed revert calls to raise the notification in the first place. Keeping the
 * posting in one place is what guarantees the repost after a failed retry says exactly the
 * same thing as the first one, which matters because the instruction in it is the fix.
 *
 * Nothing here starts Shizuku. The whole reason this notification exists is that starting it
 * automatically already failed once; the text asks the user to start it by hand, and retrying
 * the start on their behalf would spend another ten seconds arriving at the same place.
 */
@Singleton
class OverlayRestoreRunner @Inject constructor(
    @param:ApplicationContext private val context: Context,
    private val setManualTargetUseCase: SetManualTargetUseCase,
    private val getOverlayRestoreFailedUseCase: GetOverlayRestoreFailedUseCase,
    private val notificationManagerWrapper: AndroidNotificationManagerWrapper,
) {
    /** The restore itself. True when every held package got its access back. */
    suspend fun retry(): Boolean {
        val restored = setManualTargetUseCase(
            target = ManualRevertTarget.DisplayOverOtherApps,
            enabled = true,
        )

        if (restored) {
            notificationManagerWrapper.cancel(OVERLAY_RESTORE_NOTIFICATION_ID)
        } else {
            report()
        }

        return restored
    }

    /**
     * Raise the notification if, and only if, overlay access is still owed after a failed
     * attempt. Returns whether it did, so the caller can say the same thing in a toast.
     */
    suspend fun reportIfFailed(): Boolean {
        val failed = getOverlayRestoreFailedUseCase()

        if (failed) report()

        return failed
    }

    /** Raise, or re-raise, the notification. Posting under the same id replaces it. */
    fun report() {
        notificationManagerWrapper.notify(
            id = OVERLAY_RESTORE_NOTIFICATION_ID,
            notification = buildOverlayRestoreFailedNotification(context = context),
        )
    }
}
