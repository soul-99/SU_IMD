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
import com.android.geto.domain.model.isShizukuConfigured
import com.android.geto.domain.repository.UserDataRepository
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withContext
import javax.inject.Inject

/**
 * Switches 'Manage Shizuku' on for an install that was already using Shizuku, once.
 *
 * The author's rule: off for new installs, on for anyone updating from a lower version. There
 * is no "is this an upgrade" bit in the store to read, so the question actually asked is
 * whether Shizuku is **configured** — a fork, a package name, a start action, and an auth key
 * where the fork needs one.
 *
 * ⚠ **That is not a workaround, it is the same question.** An install carrying a complete
 * Shizuku configuration is one that has been using Shizuku, which is exactly who the author
 * wants switched on. A fresh install has none of it. And an upgrader who never configured
 * Shizuku would have been forced off anyway by the rule that the switch cannot stand on with a
 * blank field below it, so both readings give the same answer for them.
 *
 * ⚠ **The marker is written whether or not anything changed**, like [MigrateFrameworksUseCase]
 * — somebody who migrates on and then deliberately switches it off must not have that undone
 * by the next launch. Once per install, not once per version.
 */
class MigrateManageShizukuUseCase @Inject constructor(
    private val userDataRepository: UserDataRepository,
    @param:Dispatcher(GetoDispatchers.Default) private val defaultDispatcher: CoroutineDispatcher,
) {
    suspend operator fun invoke() = withContext(defaultDispatcher) {
        val userData = userDataRepository.userData.first()

        if (userData.manageShizukuMigratedV3) return@withContext

        userDataRepository.updateManageShizukuMigratedV3(done = true)

        // Only ever switched on here. An install with nothing configured is left at the
        // proto3 default, which is the off this migration exists to leave alone.
        if (userData.isShizukuConfigured) {
            userDataRepository.updateManageShizuku(enabled = true)
        }
    }
}
