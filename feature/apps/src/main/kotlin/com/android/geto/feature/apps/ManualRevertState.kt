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
package com.android.geto.feature.apps

import com.android.geto.domain.model.ManualRevertResult

/**
 * A manual revert can sit for a second and a half waiting for adbd, so the dialog needs
 * to know it is in flight and stop taking further presses.
 */
data class ManualRevertState(
    val busy: Boolean = false,
    val result: ManualRevertResult? = null,
    /** How many were asked for, so a partial result can be reported as "3 of 5". */
    val requested: Int = 0,
)
