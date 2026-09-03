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
import androidx.compose.ui.unit.dp
import androidx.compose.ui.graphics.vector.path
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.Color
import androidx.compose.material.icons.automirrored.rounded.ArrowBack
import androidx.compose.material.icons.automirrored.rounded.ArrowForward
import androidx.compose.material.icons.automirrored.rounded.Sort
import androidx.compose.material.icons.automirrored.outlined.HelpOutline
import androidx.compose.material.icons.rounded.Add
import androidx.compose.material.icons.rounded.Android
import androidx.compose.material.icons.rounded.AppShortcut
import androidx.compose.material.icons.rounded.Check
import androidx.compose.material.icons.rounded.ContentCopy
import androidx.compose.material.icons.rounded.Apps
import androidx.compose.material.icons.rounded.ArrowDownward
import androidx.compose.material.icons.rounded.ArrowUpward
import androidx.compose.material.icons.rounded.Email
import androidx.compose.material.icons.rounded.ExpandLess
import androidx.compose.material.icons.rounded.ExpandMore
import androidx.compose.material.icons.rounded.Link
import androidx.compose.material.icons.rounded.Share
import androidx.compose.material.icons.automirrored.rounded.OpenInNew
import androidx.compose.material.icons.rounded.Refresh
import androidx.compose.material.icons.rounded.Remove
import androidx.compose.material.icons.rounded.Search
import androidx.compose.material.icons.rounded.Settings
import androidx.compose.material.icons.rounded.SettingsBackupRestore
import androidx.compose.material.icons.rounded.SettingsSuggest
import androidx.compose.material.icons.rounded.Tune
import androidx.compose.material.icons.rounded.Visibility
import androidx.compose.material.icons.rounded.VisibilityOff
import androidx.compose.material.icons.outlined.Info
import androidx.compose.material.icons.outlined.Troubleshoot

/**
 * Every icon the app draws, in one place.
 *
 * ⚠ **Material's *Rounded* set, not the default Filled one — the author's r12 instruction to make
 * them *"less sharp edge icons"*.** Rounded is the same drawings with their corners and terminals
 * softened, so nothing here changes meaning; the magnifier in the search field and the sort and
 * tune glyphs beside it simply stop having points on them.
 *
 * ⚠ **Three keep their own set.** [Info], [Help] and [Diagnostics] are outlines chosen for being
 * outlines - they sit beside labels rather than on buttons - and Material has no rounded *outlined*
 * variant to move them to. Converting them would have quietly filled them in.
 */
object GetoIcons {
    val Apps = Icons.Rounded.Apps
    val AppGrid = GetoAppGrid
    val Settings = Icons.Rounded.Settings
    val Android = Icons.Rounded.Android
    val Back = Icons.AutoMirrored.Rounded.ArrowBack
    val Refresh = Icons.Rounded.Refresh
    val Copy = Icons.Rounded.ContentCopy
    val Share = Icons.Rounded.Share
    val Shortcut = Icons.Rounded.AppShortcut
    val SettingsSuggest = Icons.Rounded.SettingsSuggest
    val Add = Icons.Rounded.Add
    val ArrowForward = Icons.AutoMirrored.Rounded.ArrowForward
    val Search = Icons.Rounded.Search
    val Sort = Icons.AutoMirrored.Rounded.Sort

    // suIMD additions

    /**
     * The app's star, rounded — r10, and it is deliberately not Material's.
     *
     * The author asked for a star that is *"less pointy"* and *"curvy"*, and asked for it
     * *"everywhere"* rather than in the Favourites tab alone. Both members of the pair moved
     * together for that reason: the tab, the empty tab's backdrop and the ★/☆ on every app row
     * are one shape now. See design/_v3_rounded_star.py for the geometry.
     */
    val Star = GetoStarFilled
    val StarBorder = GetoStarHollow
    val ExpandMore = Icons.Rounded.ExpandMore
    val ExpandLess = Icons.Rounded.ExpandLess
    val ArrowUpward = Icons.Rounded.ArrowUpward
    val ArrowDownward = Icons.Rounded.ArrowDownward
    val Remove = Icons.Rounded.Remove

    /** The tick inside GetoCheckbox. */
    val Check = Icons.Rounded.Check

    /** Beside the author dialog's email row, saying what the row opens. */
    val Email = Icons.Rounded.Email
    val Tune = Icons.Rounded.Tune
    val Restore = Icons.Rounded.SettingsBackupRestore
    val OpenInNew = Icons.AutoMirrored.Rounded.OpenInNew

    /** In front of a heading that is itself the link, so the icon and the words are one target. */
    val Link = Icons.Rounded.Link

    /** The circle-and-question-mark that marks the readme button. */
    val Help = Icons.AutoMirrored.Outlined.HelpOutline

    /** A magnifier over a pulse line — the diagnostics button. */
    val Diagnostics = Icons.Outlined.Troubleshoot
    val Visible = Icons.Rounded.Visibility
    val Hidden = Icons.Rounded.VisibilityOff

    /** Outlined rather than filled: it sits beside a label, not on a button. */
    val Info = Icons.Outlined.Info
}

/**
 * The author's nine-square app grid — the All Apps tab, and the App drawer shortcuts row.
 *
 * ⚠ **Built here rather than as a drawable, because it has two homes with different tints.** The
 * settings row wants `colorScheme.outline` like the rest of that set; the tab bar tints by selected
 * state and would be illegible in grey. `TopLevelDestination.icon` is typed `ImageVector`, so this
 * is the one form both can take — `rememberVectorPainter` carries it to the row. One definition,
 * two tints.
 *
 * ⚠ **Nine rounded rectangles, drawn as paths.** `ImageVector` has no rounded-rect primitive, so
 * each cell is four lines and four quarter-arcs. The numbers are the template's: a 4.9 cell on a
 * 6.3 pitch from 3.2, which fills a 24 box with even gutters.
 */
private val GetoAppGrid: ImageVector = ImageVector.Builder(
    name = "AppGrid",
    defaultWidth = 24.dp,
    defaultHeight = 24.dp,
    viewportWidth = 24f,
    viewportHeight = 24f,
).apply {
    fun cell(x: Float, y: Float) {
        path(fill = SolidColor(Color.White)) {
            val side = 4.9f

            val radius = 1.35f

            moveTo(x + radius, y)

            lineTo(x + side - radius, y)

            quadTo(x + side, y, x + side, y + radius)

            lineTo(x + side, y + side - radius)

            quadTo(x + side, y + side, x + side - radius, y + side)

            lineTo(x + radius, y + side)

            quadTo(x, y + side, x, y + side - radius)

            lineTo(x, y + radius)

            quadTo(x, y, x + radius, y)

            close()
        }
    }

    cell(x = 3.2f, y = 3.2f)
    cell(x = 9.5f, y = 3.2f)
    cell(x = 15.8f, y = 3.2f)
    cell(x = 3.2f, y = 9.5f)
    cell(x = 9.5f, y = 9.5f)
    cell(x = 15.8f, y = 9.5f)
    cell(x = 3.2f, y = 15.8f)
    cell(x = 9.5f, y = 15.8f)
    cell(x = 15.8f, y = 15.8f)
}.build()
