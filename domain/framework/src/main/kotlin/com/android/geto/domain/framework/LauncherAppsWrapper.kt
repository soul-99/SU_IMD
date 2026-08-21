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
package com.android.geto.domain.framework

import com.android.geto.domain.model.LauncherAppsActivityInfo
import kotlinx.coroutines.flow.Flow

interface LauncherAppsWrapper {
    fun getActivityListFlow(): Flow<List<LauncherAppsActivityInfo>>

    /**
     * Resolves only the components named by [componentNames], re-emitting whenever the set
     * changes or a package on the device does.
     *
     * The Favourites tab used to be fed by [getActivityListFlow], which means it could not
     * show three apps until every launcher entry on the device had been enumerated and
     * every icon rendered. On a cold start that is a spinner for a second or more, for a
     * list the user can see is tiny. This resolves each favourite directly instead — a
     * handful of lookups rather than a few hundred.
     */
    fun getActivityInfosFlow(componentNames: Flow<List<String>>): Flow<List<LauncherAppsActivityInfo>>
}
