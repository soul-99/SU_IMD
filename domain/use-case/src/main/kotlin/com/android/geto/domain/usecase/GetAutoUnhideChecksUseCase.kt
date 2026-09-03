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

import com.android.geto.domain.framework.AppSessionWrapper
import com.android.geto.domain.model.AutoUnhideChecks
import javax.inject.Inject

/**
 * Whether auto unhide can actually see what it needs to see, asked of Android rather than of
 * storage.
 *
 * Both permissions behind this are granted by shell — through Shizuku or over adb — which
 * means they arrive without IMD being told, and can be taken away the same way. Nothing about
 * them can be cached across a session and still be true.
 */
class GetAutoUnhideChecksUseCase @Inject constructor(
    private val appSessionWrapper: AppSessionWrapper,
) {
    suspend operator fun invoke(): AutoUnhideChecks = AutoUnhideChecks(
        dumpPermission = appSessionWrapper.hasDumpPermission(),
        usageAccess = appSessionWrapper.hasUsageAccess(),
        exitReasonsSupported = appSessionWrapper.exitReasonsSupported,
    )
}
