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
 * **A blank start action is the one honest sign that nothing here has been configured.** The
 * fork mode cannot say it any more, since an unset one now reads as the recommended family;
 * and neither can the package name, which the preferences layer fills in with stock Shizuku's
 * when nothing is stored. The start action is the only one of the three that stays empty until
 * something actually writes it - which is why it, alone, is what this asks about.
 *
 * That matters more than it looks. [isShizukuConfigured] wants a start action, so an install
 * where this never ran reports itself as unconfigured however full the fields look - which is
 * the "you need to configure Shizuku first" a fresh install used to meet with every field
 * apparently filled in.
 *
 * No marker flag is needed to make this run once: it only ever writes when it finds that
 * state, so a user's own answer is never overwritten. With neither app installed the package
 * is left alone - a guess at that point would just be a name the user has to notice is wrong -
 * but the start action for the current family is still written, because a field the app shows
 * has to be a field the app has actually stored.
 */
class DetectShizukuForkUseCase @Inject constructor(
    private val userDataRepository: UserDataRepository,
    private val packageManagerWrapper: PackageManagerWrapper,
    @param:Dispatcher(GetoDispatchers.Default) private val defaultDispatcher: CoroutineDispatcher,
) {
    suspend operator fun invoke() = withContext(defaultDispatcher) {
        val userData = userDataRepository.userData.first()

        // Somebody has been here. See the note above for why this one field is the question.
        if (userData.shizukuStartAction.isNotBlank()) return@withContext

        val apps = packageManagerWrapper.getInstalledApps()

        val detected = when {
            apps.any { it.label.equals(ShizukuForkDefaults.SHIZUKU_LABEL, ignoreCase = true) } ->
                ShizukuForkMode.Thedjchi

            apps.any { it.label.equals(ShizukuForkDefaults.SHEVERY_LABEL, ignoreCase = true) } ->
                ShizukuForkMode.Other

            else -> null
        }

        // Nothing found: keep whichever family the install already reads as, and fill in only
        // the action. Safe to write the detected one when there is one, because getting here
        // at all means no start action is stored - and choosing a family in Settings always
        // writes one, so no deliberate choice can be sitting behind this.
        val mode = detected ?: userData.shizukuForkMode

        if (detected != null) {
            userDataRepository.updateShizukuForkMode(shizukuForkMode = mode)
        }

        val packageName = ShizukuForkDefaults.packageFor(mode = mode, apps = apps)

        if (packageName.isNotBlank()) {
            userDataRepository.updateShizukuPackageName(shizukuPackageName = packageName)
        }

        val label = apps.firstOrNull { it.packageName == packageName }?.label.orEmpty()

        val startAction = ShizukuForkDefaults.actionFor(mode = mode, selectedLabel = label)

        if (startAction.isNotBlank()) {
            userDataRepository.updateShizukuStartAction(shizukuStartAction = startAction)
        }
    }
}
