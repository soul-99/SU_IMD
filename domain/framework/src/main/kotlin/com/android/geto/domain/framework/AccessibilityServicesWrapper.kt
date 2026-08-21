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
package com.android.geto.domain.framework

import com.android.geto.domain.model.AccessibilityServiceData

interface AccessibilityServicesWrapper {
    /**
     * Every accessibility service installed on the device, each flagged with whether
     * it is currently enabled. Includes disabled ones on purpose: a service suIMD has
     * switched off must stay visible in the picker, otherwise it would disappear from
     * the very screen used to manage it.
     */
    suspend fun getAccessibilityServices(): List<AccessibilityServiceData>

    /**
     * The flattened component names currently listed in
     * Settings.Secure.enabled_accessibility_services.
     */
    suspend fun getEnabledAccessibilityServices(): List<String>

    /**
     * Overwrites Settings.Secure.enabled_accessibility_services with exactly [components]
     * and keeps Settings.Secure.accessibility_enabled consistent with it. Returns false
     * if the write was refused.
     */
    suspend fun setEnabledAccessibilityServices(components: List<String>): Boolean
}
