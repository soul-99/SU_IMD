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

import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.Dp
import coil.compose.AsyncImage
import coil.request.ImageRequest
import com.android.geto.domain.model.LauncherAppsActivityInfo

/**
 * One app icon, rendered by the drawable wrapper.
 *
 * ⚠ Not necessarily masked. An icon the system already shaped is passed through untouched; only
 * a legacy one is given the platform's icon mask - see `LegacyIconShaping`. This line used to
 * say every icon was masked to a squircle, which stopped being true when that masking was
 * reverted and was still saying it a round later.
 *
 * The icon arrives as PNG bytes. Handing those straight to `AsyncImage` gives Coil nothing
 * stable to key its memory cache on, so every icon was decoded again each time its row
 * scrolled back into view — the single biggest source of jank in these lists. An explicit
 * [ImageRequest.Builder.memoryCacheKey] fixes that: the key is the component plus the
 * package's update time, so an app that updates gets a fresh decode and nothing else does.
 *
 * ⚠ **And the icon revision, since r4y.** Those two fields were the whole of what could change a
 * picture until the Icon style setting existed; afterwards this key pinned the old bitmap in
 * front of every new one, and a list that had genuinely been re-rendered drew as though nothing
 * had happened.
 *
 * The crossfade is off because these are cache hits; fading in an icon that was already
 * decoded just draws attention to the scroll.
 */
@Composable
internal fun AppIcon(
    modifier: Modifier = Modifier,
    launcherAppsActivityInfo: LauncherAppsActivityInfo,
    size: Dp,
) {
    val context = LocalContext.current

    val request = remember(
        launcherAppsActivityInfo.componentName,
        launcherAppsActivityInfo.lastUpdateTime,
        launcherAppsActivityInfo.iconRevision,
    ) {
        ImageRequest.Builder(context)
            .data(launcherAppsActivityInfo.activityIcon)
            .memoryCacheKey(
                launcherAppsActivityInfo.componentName + "@" +
                    launcherAppsActivityInfo.lastUpdateTime + "@" +
                    launcherAppsActivityInfo.iconRevision,
            )
            .crossfade(false)
            .build()
    }

    AsyncImage(
        modifier = modifier.size(size),
        model = request,
        contentDescription = null,
    )
}
