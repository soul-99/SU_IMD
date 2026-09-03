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
package com.android.geto.designsystem.theme

import androidx.compose.ui.graphics.Color

/**
 * The one red in the app, and the reason it lives here rather than beside any of its uses.
 *
 * The author chose it for the Support button, where it was a `private val` in
 * `SettingsScreen.kt`. It now also marks a revert that is still owed — on the settings
 * manager's unhide button and on the Favourites tab's button — and three copies of a hex
 * literal is how two of them come to differ by a shade nobody meant.
 *
 * **Fixed rather than themed, in both light and dark.** It is not a role in the colour scheme;
 * it is a flag, and a flag that changes shade with the theme stops reading as one. White
 * content clears AA contrast on it either way, which is why every use pairs it with white
 * rather than with `onError` or a scheme colour.
 */
val GetoRed = Color(0xFFB71C1C)
