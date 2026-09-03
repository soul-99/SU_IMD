/*
 *
 *   Copyright 2026 soul_99 (suIMD)
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
 * How IMD draws an app icon.
 *
 * Only ever affects a **legacy** (non-adaptive) icon. An adaptive one arrives already shaped by
 * the launcher and has never been touched by either setting, so the choice below is really
 * "shape the ones nothing has shaped, or leave them as the system handed them over".
 */
enum class IconStyle {
    /**
     * The default. A legacy icon is trimmed and given the device's own icon mask, so it matches
     * the adaptive icons beside it — see `LegacyIconShaping`.
     */
    SmartAdaptive,

    /** What the app did before v3: whatever the system returns, drawn unchanged. */
    System,
}
