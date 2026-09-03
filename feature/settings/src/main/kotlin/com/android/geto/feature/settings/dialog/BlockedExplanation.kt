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
package com.android.geto.feature.settings.dialog

/**
 * Why a greyed control in one of the two configuration dialogs refuses, in the words the
 * pop-up should say.
 *
 * ⚠ **Replaces `List<String>?`, which carried two questions in one value.** Both dialogs used
 * to keep a nullable list of location trees and pick the sentence from whether it was empty:
 * empty meant "Shevery, and the thing is unsupported rather than unconfigured". That worked
 * while exactly one row had nothing to point at. r4n gives the Shizuku row the same shape on
 * the same fork and a *different* sentence — managing the service, not Display over other
 * apps — so the trick stops being able to tell them apart.
 *
 * [paths] empty is now only what it looks like: nothing to point at. Which sentence to use is
 * [message], said out loud by whoever raised it.
 */
internal data class BlockedExplanation(
    val message: String,
    val paths: List<String> = emptyList(),
)
