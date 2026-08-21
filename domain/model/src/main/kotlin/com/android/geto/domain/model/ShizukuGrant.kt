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
 * Outcome of asking Shizuku to hand this app WRITE_SECURE_SETTINGS.
 *
 * Four cases rather than a boolean because each needs a different sentence from the setup
 * screen: install or start Shizuku, allow the prompt, or something else went wrong.
 */
enum class ShizukuGrant {
    /** No Shizuku binder. Not installed, or installed and not started. */
    NotRunning,

    /** Shizuku is there but refused this app, or the user dismissed the prompt. */
    PermissionDenied,

    /** Shizuku ran the command and it did not take. */
    Failed,

    Granted,
}
