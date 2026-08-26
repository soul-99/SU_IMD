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
    /**
     * Whether this run tried to give overlay access back and could not.
     *
     * Carried here rather than left to the caller to read back out of stored preferences,
     * because the caller lives in the broadcast-receiver module and reaching for the
     * repository from there would drag the whole data layer across a module boundary for one
     * boolean. It is also narrower than `DisplayOverOtherApps in failed`, which is equally
     * true of a failed *hide* - and a failed hide needs no notification, because nothing was
     * taken away that has to be given back.
     */
    val overlayRestoreFailed: Boolean = false,
) {
    val isSuccess: Boolean get() = failed.isEmpty()

    /** Everything was already where it should be, so the press was a no-op. */
    val isNoOp: Boolean get() = changed.isEmpty() && failed.isEmpty()
}
