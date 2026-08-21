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
package com.android.geto.domain.model

/**
 * One accessibility service installed on the device.
 *
 * [id] is the flattened component name ("pkg/com.example.MyService") exactly as it
 * appears in Settings.Secure.enabled_accessibility_services, and is the only value
 * ever persisted. Labels are resolved fresh each time so a renamed or updated app
 * never leaves a stale entry behind.
 */
data class AccessibilityServiceData(
    val id: String,
    val packageName: String,
    val label: String,
    val enabled: Boolean,
)
