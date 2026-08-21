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
package com.android.geto.domain.usecase

import com.android.geto.domain.common.dispatcher.Dispatcher
import com.android.geto.domain.common.dispatcher.GetoDispatchers
import com.android.geto.domain.framework.LauncherAppsWrapper
import com.android.geto.domain.model.AppListOrder
import com.android.geto.domain.model.AppListOrdering
import com.android.geto.domain.model.LauncherAppsActivityInfoData
import com.android.geto.domain.repository.UserDataRepository
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.flowOn
import kotlinx.coroutines.flow.map
import javax.inject.Inject

class GetLauncherAppsActivityInfosUseCase @Inject constructor(
    private val launcherAppsWrapper: LauncherAppsWrapper,
    private val userDataRepository: UserDataRepository,
    @param:Dispatcher(GetoDispatchers.Default) private val defaultDispatcher: CoroutineDispatcher,
) {
    operator fun invoke(textFlow: Flow<String?>): Flow<LauncherAppsActivityInfoData> {
        val userData = userDataRepository.userData

        // Sorting depends on only three of UserData's fields, so it is driven by a
        // distinct-until-changed projection of those. Favourites live on UserData as well,
        // and without this split every star tap re-sorted every installed app.
        //
        // DataStore keeps its value in memory and shares it between collectors, so reading
        // userData twice here costs one extra map, not a second disk read.
        val orderedApps = combine(
            launcherAppsWrapper.getActivityListFlow(),
            userData.map { AppListOrder(userData = it) }.distinctUntilChanged(),
            AppListOrdering::arrange,
        )

        return combine(textFlow, orderedApps, userData) { text, apps, data ->
            LauncherAppsActivityInfoData(
                launcherAppsActivityInfos = AppListOrdering.search(apps = apps, text = text),
                userData = data,
            )
        }.flowOn(defaultDispatcher)
    }
}
