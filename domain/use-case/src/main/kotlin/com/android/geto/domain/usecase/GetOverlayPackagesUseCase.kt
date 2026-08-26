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
import com.android.geto.domain.framework.PackageManagerWrapper
import com.android.geto.domain.framework.ShizukuWrapper
import com.android.geto.domain.model.OverlayPackageData
import com.android.geto.domain.repository.UserDataRepository
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withContext
import javax.inject.Inject

/**
 * The apps that can display over other apps, for the picker to choose from.
 *
 * **Null means the question could not be asked**, not that the answer is empty. Reading
 * overlay AppOps needs a running Shizuku service, and the two outcomes have to stay apart:
 * an empty list is a device where nothing holds the permission, and null is a device where
 * IMD cannot see. The picker opens on the first and refuses to open on the second, because
 * a list that silently reads as empty would invite the user to conclude they have nothing
 * to select.
 *
 * Packages IMD is currently holding down are included even though the live AppOp says they
 * are not allowed. They are only off because of this app, and leaving them out would empty
 * the list for exactly as long as the hiding is in force.
 */
class GetOverlayPackagesUseCase @Inject constructor(
    private val shizukuWrapper: ShizukuWrapper,
    private val packageManagerWrapper: PackageManagerWrapper,
    private val userDataRepository: UserDataRepository,
    @param:Dispatcher(GetoDispatchers.IO) private val ioDispatcher: CoroutineDispatcher,
) {
    suspend operator fun invoke(): List<OverlayPackageData>? = withContext(ioDispatcher) {
        val allowed = runCatching {
            shizukuWrapper.getAllowedOverlayPackages()
        }.getOrNull() ?: return@withContext null

        val userData = userDataRepository.userData.first()

        val held = userData.heldOverlayPackages.values.flatten().toSet()

        val labels = runCatching {
            packageManagerWrapper.getInstalledApps().associate { it.packageName to it.label }
        }.getOrDefault(emptyMap())

        (allowed + held)
            .map { packageName ->
                OverlayPackageData(
                    packageName = packageName,
                    // A package with no entry in the installed list is one that has gone
                    // since; showing its name is more useful than dropping the row, because
                    // it may still be sitting in the selection waiting to be unticked.
                    label = labels[packageName] ?: packageName,
                    allowed = packageName in allowed,
                )
            }
            // Selected-but-currently-held first, then alphabetically: the rows that are off
            // because of this app are the ones someone opening this list came to find.
            .sortedWith(compareBy({ it.allowed }, { it.label.lowercase() }))
    }
}
