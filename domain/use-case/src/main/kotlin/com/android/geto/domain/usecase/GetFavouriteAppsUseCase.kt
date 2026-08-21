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
import com.android.geto.domain.model.FavouriteAppsData
import com.android.geto.domain.model.FavouriteAppsOrder
import com.android.geto.domain.model.FavouriteAppsOrdering
import com.android.geto.domain.repository.UserDataRepository
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.flowOn
import kotlinx.coroutines.flow.map
import javax.inject.Inject

class GetFavouriteAppsUseCase @Inject constructor(
    private val launcherAppsWrapper: LauncherAppsWrapper,
    private val userDataRepository: UserDataRepository,
    @param:Dispatcher(GetoDispatchers.Default) private val defaultDispatcher: CoroutineDispatcher,
) {
    operator fun invoke(textFlow: Flow<String?>): Flow<FavouriteAppsData> {
        val userData = userDataRepository.userData

        // Ordering is driven by a two-field projection rather than the whole of UserData,
        // so writing an unrelated preference does not re-run it. DataStore shares its
        // value between collectors, so reading userData twice here is one extra map, not
        // a second read from disk.
        val order = userData.map { FavouriteAppsOrder(userData = it) }.distinctUntilChanged()

        // Only the favourites are resolved, not every launcher entry on the device. This
        // is what stops the tab showing a spinner on every cold start while a few hundred
        // unrelated icons are rendered.
        val ordered = combine(
            launcherAppsWrapper.getActivityInfosFlow(
                componentNames = order.map { it.favouriteComponentNames },
            ),
            order,
        ) { installed, order ->
            FavouriteAppsOrdering.order(
                favouriteComponentNames = order.favouriteComponentNames,
                installed = installed,
                sortFavouriteApps = order.sort,
            )
        }

        return combine(textFlow, ordered, userData) { text, apps, data ->
            FavouriteAppsData(
                launcherAppsActivityInfos = FavouriteAppsOrdering.filter(apps = apps, text = text),
                allFavouriteApps = apps,
                userData = data,
            )
        }.flowOn(defaultDispatcher)
    }
}
