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
package com.android.geto.designsystem.icon

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.filled.ArrowForward
import androidx.compose.material.icons.automirrored.filled.Sort
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Android
import androidx.compose.material.icons.filled.AppShortcut
import androidx.compose.material.icons.filled.Apps
import androidx.compose.material.icons.filled.ArrowDownward
import androidx.compose.material.icons.filled.ArrowUpward
import androidx.compose.material.icons.filled.ExpandLess
import androidx.compose.material.icons.filled.ExpandMore
import androidx.compose.material.icons.filled.Link
import androidx.compose.material.icons.filled.OpenInNew
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Remove
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.SettingsBackupRestore
import androidx.compose.material.icons.filled.SettingsSuggest
import androidx.compose.material.icons.filled.Star
import androidx.compose.material.icons.filled.StarBorder
import androidx.compose.material.icons.filled.Tune
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material.icons.filled.VisibilityOff
import androidx.compose.material.icons.outlined.Info

object GetoIcons {
    val Apps = Icons.Default.Apps
    val Settings = Icons.Default.Settings
    val Android = Icons.Default.Android
    val Back = Icons.AutoMirrored.Filled.ArrowBack
    val Refresh = Icons.Default.Refresh
    val Shortcut = Icons.Default.AppShortcut
    val SettingsSuggest = Icons.Default.SettingsSuggest
    val Add = Icons.Default.Add
    val ArrowForward = Icons.AutoMirrored.Filled.ArrowForward
    val Search = Icons.Default.Search
    val Sort = Icons.AutoMirrored.Filled.Sort

    // suIMD additions
    val Star = Icons.Default.Star
    val StarBorder = Icons.Default.StarBorder
    val ExpandMore = Icons.Default.ExpandMore
    val ExpandLess = Icons.Default.ExpandLess
    val ArrowUpward = Icons.Default.ArrowUpward
    val ArrowDownward = Icons.Default.ArrowDownward
    val Remove = Icons.Default.Remove
    val Link = Icons.Default.Link
    val Tune = Icons.Default.Tune
    val Restore = Icons.Default.SettingsBackupRestore
    val OpenInNew = Icons.Default.OpenInNew
    val Visible = Icons.Default.Visibility
    val Hidden = Icons.Default.VisibilityOff

    /** Outlined rather than filled: it sits beside a label, not on a button. */
    val Info = Icons.Outlined.Info
}
