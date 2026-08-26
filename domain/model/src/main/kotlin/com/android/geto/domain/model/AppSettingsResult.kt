/*
 *
 *   Copyright 2023 Einstein Blanco
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

enum class AppSettingsResult {
    Success,
    Failure,

    /**
     * Hiding "Display over other apps" needs a running Shizuku service, and it could not be
     * reached. Kept apart from [Failure] because it is the one failure with a specific,
     * actionable cause: every other failure is a settings write that did not take, whereas
     * this one is answered by granting IMD permission in Shizuku or fixing the fork
     * configuration, and the user cannot guess that from "could not apply settings".
     */
    OverlayFailure,
    NoPermission,
    InvalidValues,
    EmptyAppSettings,
    DisabledAppSettings,
}
