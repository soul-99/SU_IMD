/*
 *
 *   Copyright 2026 soul_99 (suIMD)
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
package com.android.geto.designsystem.component

import androidx.compose.animation.AnimatedVisibilityScope
import androidx.compose.animation.ExperimentalAnimationApi
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.ui.Modifier
import androidx.compose.ui.input.pointer.PointerEventPass
import androidx.compose.ui.input.pointer.pointerInput

/**
 * Swallows touches while this destination's own transition is running.
 *
 * ⚠ **Both destinations are on screen for the length of a tab change**, and the one leaving is
 * still laid out and still hit-testable where its buttons used to be - so a tap landing as the
 * animation finishes reaches a control the user can barely see. The author's report:
 * *"previous page's buttons were they got pressed even though they are not visible on the
 * screen leading to wrong touches"*.
 *
 * ⚠ **The arriving destination is blocked too, on purpose.** A press aimed at a control that is
 * still sliding into place is aimed at where it *was*. Over a transition of a few hundred
 * milliseconds, refusing both is the only answer that cannot act on a stale position.
 *
 * ⚠ **[PointerEventPass.Initial], not the default.** The main pass runs after the children have
 * already been offered the event, which is too late to stop a button from taking it.
 *
 * ⚠ **The flag is read inside the loop rather than around the modifier.** Adding and removing
 * `pointerInput` as transitions start and stop would rebuild the pointer handler mid-gesture,
 * and a rebuilt handler loses whatever gesture was in progress.
 */
@OptIn(ExperimentalAnimationApi::class)
@Composable
fun Modifier.blockTouchesWhileAnimating(scope: AnimatedVisibilityScope): Modifier {
    val animating by rememberUpdatedState(scope.transition.isRunning)

    return pointerInput(Unit) {
        awaitPointerEventScope {
            while (true) {
                val event = awaitPointerEvent(PointerEventPass.Initial)

                if (animating) {
                    event.changes.forEach { it.consume() }
                }
            }
        }
    }
}
