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
package com.android.geto.feature.apps

import com.android.geto.domain.model.AppSettingsResult
import com.android.geto.domain.model.HidingFramework

/**
 * The outcome of applying a favourite's settings, on its way to the UI so it can post the
 * revert notification and open the app.
 *
 * ⚠ **It carried the launched app's icon and the unhiding framework until r3**, both solely
 * to fill arguments on `postAppliedSettingsNotification`. That function now takes neither:
 * every launch posts the one generic revert notification, so there is no icon to draw and no
 * branch to choose. The icon was a rasterised bitmap fetched over binder on every launch.
 *
 * Not a data class, still: the state is cleared to null after handling, so nothing compares
 * two of these, and structural equality would only mislead the next reader into thinking
 * something does.
 */
class FavouriteAppLaunch(
    val componentName: String,
    val result: AppSettingsResult,
    /**
     * The **hiding** half, and the app's label, for the completion toast.
     *
     * Which sentence the toast uses is a hiding question — "Settings hidden for X" means the
     * hide read X's own profile, which is what Per app configuration does. Read at the same
     * moment as everything else here, so a framework changed between the hide and the toast
     * cannot have the toast describe a hide that did not run.
     *
     * [appName] is null when the component has gone between the launch and this record, and
     * the toast then says the sentence that names no app rather than one with a blank in it.
     */
    val hidingFramework: HidingFramework,
    val appName: String?,
)
