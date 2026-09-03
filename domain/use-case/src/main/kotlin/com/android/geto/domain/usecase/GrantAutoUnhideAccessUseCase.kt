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

import com.android.geto.domain.framework.PackageManagerWrapper
import com.android.geto.domain.framework.ShizukuWrapper
import com.android.geto.domain.model.ShizukuGrant
import javax.inject.Inject

/**
 * Grants auto unhide's two shell-only permissions to IMD itself, through Shizuku.
 *
 * **The point of doing it here is that it only has to work once.** Both permissions survive
 * until the app is reinstalled, so after this the detection never asks Shizuku for anything
 * again — which is what makes auto unhide possible at all, given that Shizuku is very often
 * down for the whole window auto unhide has to watch, and is itself one of the things IMD
 * hides.
 *
 * The `adb` route in the dialog beside these buttons does exactly the same thing from a
 * computer, for anyone who never sets Shizuku up.
 */
class GrantAutoUnhideAccessUseCase @Inject constructor(
    private val shizukuWrapper: ShizukuWrapper,
    private val packageManagerWrapper: PackageManagerWrapper,
) {
    /**
     * `pm grant android.permission.DUMP`.
     *
     * Returns the grant's own three outcomes rather than a boolean, because "Shizuku is not
     * running" and "Shizuku refused" send the user to different places, and neither is the
     * same as the command having failed.
     */
    suspend fun grantDumpPermission(): ShizukuGrant =
        shizukuWrapper.grantDumpPermission(packageName = packageManagerWrapper.ownPackageName())

    /**
     * The usage-access AppOp.
     *
     * A boolean because there is a perfectly good second route for this one — the settings
     * list Android provides — and the button beside it is always available. Nothing here needs
     * to explain a failure that the user can simply walk around.
     */
    suspend fun grantUsageAccess(): Boolean =
        shizukuWrapper.allowUsageAccess(packageName = packageManagerWrapper.ownPackageName())

    /** The command to run from a computer instead, shown verbatim so it can be copied. */
    fun adbCommand(): String =
        "adb shell pm grant ${packageManagerWrapper.ownPackageName()} android.permission.DUMP"
}
