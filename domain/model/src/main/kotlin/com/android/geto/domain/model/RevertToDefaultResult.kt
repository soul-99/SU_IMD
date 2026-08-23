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
 * Per-target outcome of one "Revert to default" run.
 *
 * Split three ways rather than reported as a bare success flag because "nothing needed
 * doing" and "everything failed" both leave the device unchanged, and only one of them is a
 * problem worth telling anyone about.
 */
data class RevertToDefaultResult(
    val changed: Set<ManualRevertTarget> = emptySet(),
    val failed: Set<ManualRevertTarget> = emptySet(),
    val unchanged: Set<ManualRevertTarget> = emptySet(),
) {
    val isSuccess: Boolean get() = failed.isEmpty()

    /** Everything was already where it should be, so the press was a no-op. */
    val isNoOp: Boolean get() = changed.isEmpty() && failed.isEmpty()
}
