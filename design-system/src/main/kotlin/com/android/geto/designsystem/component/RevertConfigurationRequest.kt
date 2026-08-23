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
package com.android.geto.designsystem.component

import androidx.compose.runtime.compositionLocalOf

/**
 * How many times the manager dialog has asked for the revert configuration this session.
 *
 * A count rather than a flag, and that is the whole point: a flag can only describe a state,
 * and "please open the configuration" is an event. Set once and left true it says nothing on
 * the second press; reset after use it races with whatever is reading it. A number that only
 * goes up gives every request a distinct value, so keying an effect on it re-fires each time
 * and never fires twice for one request.
 *
 * Carried as a composition local rather than as a navigation argument because the graph is
 * built once: the lambda a `composable<T> { }` captures is fixed at that moment, so a value
 * threaded through the builder would deliver the first request and every later one would be
 * dropped — which is exactly the bug this replaces.
 *
 * Lives in the design system only because that is what both the app module that provides it
 * and the feature modules that read it can see.
 */
val LocalRevertConfigurationRequest = compositionLocalOf { 0 }
