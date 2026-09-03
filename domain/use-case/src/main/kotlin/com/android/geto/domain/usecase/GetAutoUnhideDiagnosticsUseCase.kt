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
import com.android.geto.domain.repository.UserDataRepository
import kotlinx.coroutines.flow.first
import javax.inject.Inject

/**
 * ⚠ **TEMPORARY — r12 only. Delete this, its dialog, its row and its three strings in r13**,
 * the way the diag1 build's log was deleted in r3.
 *
 * It exists to answer one question that cannot be answered from here: **does this device
 * actually kill an app when it is swiped out of recents?** AOSP does, and reports it as
 * `REASON_USER_REQUESTED` with the description "remove task" — but OEM skins vary, and an app
 * holding a foreground service survives the swipe on any of them. If the answer turns out to
 * be no on the author's device, the swipe trigger is not viable there and the two backup
 * triggers carry the feature.
 *
 * It reports rather than concludes. The fields worth seeing are whichever ones turn out to be
 * wrong, so the raw numbers go out unformatted — `reason=10` means more to somebody comparing
 * it against the documentation than "the user closed it" would.
 *
 * Reads the **IMD+ watch list** for which packages to ask about, because that list already
 * exists and is already full of the apps this is being tested with. Nothing new to configure.
 */
class GetAutoUnhideDiagnosticsUseCase @Inject constructor(
    private val appSessionWrapper: AppSessionWrapper,
    private val userDataRepository: UserDataRepository,
) {
    suspend operator fun invoke(buildInfo: String): String {
        val userData = userDataRepository.userData.first()

        val lines = mutableListOf<String>()

        lines += "--- auto unhide probe ---"

        lines += buildInfo

        lines += "exitReasonsSupported=${appSessionWrapper.exitReasonsSupported}"

        lines += "dumpPermission=${appSessionWrapper.hasDumpPermission()}"

        lines += "usageAccess=${appSessionWrapper.hasUsageAccess()}"

        val packages = userData.autoHidePackages

        if (packages.isEmpty()) {
            lines += ""

            lines += "No apps in the IMD+ watch list. Add the app you are testing with to"

            lines += "IMD+ > Apps to watch, then open this again."
        }

        packages.forEach { packageName ->
            lines += ""

            lines += "[$packageName] exit records:"

            lines += appSessionWrapper.describeExits(packageName = packageName)
        }

        lines += ""

        lines += "usage events, last 5 minutes:"

        lines += appSessionWrapper.describeEvents(
            sinceMillis = System.currentTimeMillis() - USAGE_EVENT_WINDOW_MILLIS,
        )

        return lines.joinToString(separator = "\n")
    }
}

/** Long enough to cover opening an app, pressing home, waiting, and swiping it away. */
private const val USAGE_EVENT_WINDOW_MILLIS = 5 * 60 * 1000L
