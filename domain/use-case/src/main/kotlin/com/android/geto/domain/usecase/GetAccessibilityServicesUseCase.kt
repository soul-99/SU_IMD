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

import com.android.geto.domain.framework.AccessibilityServicesWrapper
import com.android.geto.domain.framework.PackageManagerWrapper
import com.android.geto.domain.model.AccessibilityServiceData
import com.android.geto.domain.model.accessibilityServicesForPicker
import com.android.geto.domain.repository.UserDataRepository
import kotlinx.coroutines.flow.first
import javax.inject.Inject

class GetAccessibilityServicesUseCase @Inject constructor(
    private val accessibilityServicesWrapper: AccessibilityServicesWrapper,
    private val packageManagerWrapper: PackageManagerWrapper,
    private val userDataRepository: UserDataRepository,
) {
    /**
     * Enabled services first, then alphabetical, so the useful ones are at the top.
     *
     * Narrowed to what the picker should show since v3 — see [accessibilityServicesForPicker]
     * for why that is "enabled, **or** held by IMD, **or** selected" rather than the literal
     * "enabled". The third was added after the author found the overlay picker dropping his
     * selection; this list had the same hole and had simply not been caught in it.
     */
    suspend operator fun invoke(): List<AccessibilityServiceData> {
        val userData = userDataRepository.userData.first()

        // IMD's own detector needs no special case here: while IMD+ is on it is either bound,
        // and so enabled, or a hide has taken it down, and so held. The only state it is
        // neither in is IMD+ switched on with the detector never granted — where not listing
        // it is the more honest answer anyway, because it is not running.
        val services = accessibilityServicesForPicker(
            services = accessibilityServicesWrapper.getAccessibilityServices(),
            heldAccessibilityServices = userData.heldAccessibilityServices,
            managedAccessibilityServices = userData.managedAccessibilityServices,
        ).sortedWith(
            compareByDescending<AccessibilityServiceData> { it.enabled }
                .thenBy(String.CASE_INSENSITIVE_ORDER) { it.label },
        )

        // ⚠ **Read after the filter, not before it.** The picker shows a fraction of the
        // installed services, and asking for an icon per row of a list nobody will see is the
        // waste `GetOverlayPackagesUseCase` records having made once already.
        //
        // Several services can share one app, so the set is smaller again than the list.
        val icons = runCatching {
            packageManagerWrapper.getAppIcons(services.map { it.packageName }.toSet())
        }.getOrDefault(emptyMap())

        return services.map { service -> service.copy(icon = icons[service.packageName]) }
    }
}
