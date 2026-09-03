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
package com.android.geto.domain.common

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update

/**
 * Whether legacy icons are shaped, held in memory for the two places that draw them.
 *
 * ⚠ **A holder rather than an injection, deliberately.** The two readers are
 * `DefaultDrawableWrapper` and `ShortcutIconFactory`, both in `:framework`, and neither can reach
 * the preferences: `framework:drawable` depends on `domain:common` alone, and pointing it at
 * `domain:repository` would turn the module graph around for one boolean. Threading it down
 * instead means a parameter on `toByteArray`, whose five call sites know nothing about user
 * preferences either.
 *
 * The app already solves this exact problem this way — see `AutoHideDetection`, which holds what
 * the accessibility service needs because the code that has to answer cannot wait on a datastore
 * read.
 *
 * ⚠ **`true` before anything has been collected, and that is not an arbitrary default.** The
 * first icon of a cold start can be decoded before `GetoApplication` has read the preference.
 * `true` is Smart adaptive, which is both the stored default and what every version before this
 * one did, so the race resolves to the same picture whichever way it goes.
 */
object IconStyleState {
    @Volatile
    @JvmStatic
    var shapeLegacyIcons: Boolean = true

    private val _revision = MutableStateFlow(0)

    /**
     * Bumped whenever the style changes, so anything holding rendered icons can drop them.
     *
     * ⚠ **A counter rather than the style itself.** What the listeners need to know is *"your
     * pictures are stale"*, and a flow of the style would say nothing at all if it were ever set
     * to the value it already had — while a counter is a fact about staleness that cannot be
     * conflated away.
     */
    val revision: StateFlow<Int> = _revision.asStateFlow()

    fun invalidate() {
        _revision.update { it + 1 }
    }
}
