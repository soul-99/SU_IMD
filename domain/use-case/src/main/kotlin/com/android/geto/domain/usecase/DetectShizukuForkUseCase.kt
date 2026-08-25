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
import com.android.geto.domain.model.ShizukuForkDefaults
import com.android.geto.domain.model.ShizukuForkMode
import com.android.geto.domain.repository.UserDataRepository
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withContext
import javax.inject.Inject

/**
 * Guesses which Shizuku family is installed, so the section is not blank on first run.
 *
 * Shizuku first, Shevery second, matching what someone is most likely to have. Whichever is
 * found also fills the package name and the start action, exactly as picking the family by
 * hand does - a selected radio button over three empty fields would look configured while
 * doing nothing.
 *
 * No marker flag is needed to make this run once. [ShizukuForkMode.Unset] is the state of an
 * install where nobody has chosen, nothing in the UI can return to it, and this only ever
 * writes when it finds that state - so a user's own choice is never overwritten, and neither
 * is a deliberate decision to leave it alone once something has been picked.
 *
 * Silence is a valid outcome. With neither app installed the mode stays Unset and the fields
 * stay empty, which is honest: a guess at that point would just be a package name the user
 * has to notice is wrong.
 */
class DetectShizukuForkUseCase @Inject constructor(
    private val userDataRepository: UserDataRepository,
    private val packageManagerWrapper: PackageManagerWrapper,
    @param:Dispatcher(GetoDispatchers.Default) private val defaultDispatcher: CoroutineDispatcher,
) {
    suspend operator fun invoke() = withContext(defaultDispatcher) {
        val userData = userDataRepository.userData.first()

        if (userData.shizukuForkMode != ShizukuForkMode.Unset) return@withContext

        val apps = packageManagerWrapper.getInstalledApps()

        val mode = when {
            apps.any { it.label.equals(ShizukuForkDefaults.SHIZUKU_LABEL, ignoreCase = true) } ->
                ShizukuForkMode.Thedjchi

            apps.any { it.label.equals(ShizukuForkDefaults.SHEVERY_LABEL, ignoreCase = true) } ->
                ShizukuForkMode.Other

            else -> return@withContext
        }

        val packageName = ShizukuForkDefaults.packageFor(mode = mode, apps = apps)

        val label = apps.firstOrNull { it.packageName == packageName }?.label.orEmpty()

        userDataRepository.updateShizukuForkMode(shizukuForkMode = mode)
        userDataRepository.updateShizukuPackageName(shizukuPackageName = packageName)
        userDataRepository.updateShizukuStartAction(
            shizukuStartAction = ShizukuForkDefaults.actionFor(mode = mode, selectedLabel = label),
        )
    }
}
