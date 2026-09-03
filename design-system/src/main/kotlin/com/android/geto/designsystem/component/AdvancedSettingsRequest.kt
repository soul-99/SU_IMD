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
package com.android.geto.designsystem.component

import androidx.compose.runtime.compositionLocalOf

/**
 * How many times something has asked for Settings with Advanced expanded this session.
 *
 * A count for the same reason [LocalRevertConfigurationRequest] is one — see there for the
 * full argument. In practice this one arrives at most once per launch, since the only thing
 * that sends it re-launches the app to do so, but a flag would still be the wrong shape: it
 * would describe a state where what is being carried is an event.
 */
val LocalAdvancedSettingsRequest = compositionLocalOf { 0 }
