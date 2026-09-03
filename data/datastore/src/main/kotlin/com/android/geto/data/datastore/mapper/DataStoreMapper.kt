/*
 *
 *   Copyright 2023 Einstein Blanco
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
package com.android.geto.data.datastore.mapper

import com.android.geto.data.datastore.proto.FavouriteAppsViewProto
import com.android.geto.data.datastore.proto.HidingFrameworkProto
import com.android.geto.data.datastore.proto.IconStyleProto
import com.android.geto.data.datastore.proto.NotificationFunctionProto
import com.android.geto.data.datastore.proto.ShizukuForkModeProto
import com.android.geto.data.datastore.proto.SortFavouriteAppsProto
import com.android.geto.data.datastore.proto.SortLauncherAppsActivityInfoProto
import com.android.geto.data.datastore.proto.SortOrderLauncherAppsActivityInfoProto
import com.android.geto.data.datastore.proto.ThemeProto
import com.android.geto.data.datastore.proto.UnhidingFrameworkProto
import com.android.geto.domain.model.FavouriteAppsView
import com.android.geto.domain.model.HidingFramework
import com.android.geto.domain.model.IconStyle
import com.android.geto.domain.model.NotificationFunction
import com.android.geto.domain.model.ShizukuForkMode
import com.android.geto.domain.model.SortFavouriteApps
import com.android.geto.domain.model.SortLauncherAppsActivityInfo
import com.android.geto.domain.model.SortOrderLauncherAppsActivityInfo
import com.android.geto.domain.model.Theme
import com.android.geto.domain.model.UnhidingFramework

internal fun ThemeProto.asTheme(): Theme = when (this) {
    ThemeProto.THEME_UNSPECIFIED,
    ThemeProto.THEME_FOLLOW_SYSTEM,
    ThemeProto.UNRECOGNIZED,
    -> {
        Theme.FOLLOW_SYSTEM
    }

    ThemeProto.THEME_LIGHT -> {
        Theme.LIGHT
    }

    ThemeProto.THEME_DARK -> {
        Theme.DARK
    }
}

internal fun SortLauncherAppsActivityInfoProto.asSortLauncherAppsActivityInfo(): SortLauncherAppsActivityInfo = when (this) {
    SortLauncherAppsActivityInfoProto.SortName -> {
        SortLauncherAppsActivityInfo.Name
    }

    SortLauncherAppsActivityInfoProto.SortUpdateTime -> {
        SortLauncherAppsActivityInfo.UpdateTime
    }

    SortLauncherAppsActivityInfoProto.SortInstallTime -> {
        SortLauncherAppsActivityInfo.InstallTime
    }

    SortLauncherAppsActivityInfoProto.UNRECOGNIZED -> {
        SortLauncherAppsActivityInfo.Name
    }
}

internal fun SortOrderLauncherAppsActivityInfoProto.asSortOrderLauncherAppsActivityInfo(): SortOrderLauncherAppsActivityInfo = when (this) {
    SortOrderLauncherAppsActivityInfoProto.SortOrderAscending -> {
        SortOrderLauncherAppsActivityInfo.Ascending
    }

    SortOrderLauncherAppsActivityInfoProto.SortOrderDescending -> {
        SortOrderLauncherAppsActivityInfo.Descending
    }

    SortOrderLauncherAppsActivityInfoProto.UNRECOGNIZED -> {
        SortOrderLauncherAppsActivityInfo.Ascending
    }
}

internal fun SortLauncherAppsActivityInfo.asSortLauncherAppsActivityInfoProto(): SortLauncherAppsActivityInfoProto = when (this) {
    SortLauncherAppsActivityInfo.Name -> {
        SortLauncherAppsActivityInfoProto.SortName
    }

    SortLauncherAppsActivityInfo.UpdateTime -> {
        SortLauncherAppsActivityInfoProto.SortUpdateTime
    }

    SortLauncherAppsActivityInfo.InstallTime -> {
        SortLauncherAppsActivityInfoProto.SortInstallTime
    }
}

internal fun SortOrderLauncherAppsActivityInfo.asSortOrderLauncherAppsActivityInfoProto(): SortOrderLauncherAppsActivityInfoProto = when (this) {
    SortOrderLauncherAppsActivityInfo.Ascending -> {
        SortOrderLauncherAppsActivityInfoProto.SortOrderAscending
    }

    SortOrderLauncherAppsActivityInfo.Descending -> {
        SortOrderLauncherAppsActivityInfoProto.SortOrderDescending
    }
}

internal fun Theme.asThemeProto(): ThemeProto = when (this) {
    Theme.FOLLOW_SYSTEM -> {
        ThemeProto.THEME_FOLLOW_SYSTEM
    }

    Theme.LIGHT -> {
        ThemeProto.THEME_LIGHT
    }

    Theme.DARK -> {
        ThemeProto.THEME_DARK
    }
}

internal fun SortFavouriteAppsProto.asSortFavouriteApps(): SortFavouriteApps = when (this) {
    SortFavouriteAppsProto.FavouriteSortCustom -> {
        SortFavouriteApps.Custom
    }

    SortFavouriteAppsProto.FavouriteSortAlphabetical -> {
        SortFavouriteApps.Alphabetical
    }

    SortFavouriteAppsProto.UNRECOGNIZED -> {
        SortFavouriteApps.Custom
    }
}

internal fun SortFavouriteApps.asSortFavouriteAppsProto(): SortFavouriteAppsProto = when (this) {
    SortFavouriteApps.Custom -> {
        SortFavouriteAppsProto.FavouriteSortCustom
    }

    SortFavouriteApps.Alphabetical -> {
        SortFavouriteAppsProto.FavouriteSortAlphabetical
    }
}

internal fun IconStyleProto.asIconStyle(): IconStyle = when (this) {
    IconStyleProto.IconStyleSmartAdaptive -> IconStyle.SmartAdaptive

    IconStyleProto.IconStyleSystem -> IconStyle.System

    // A value written by a newer build. Falling back to the default is the same answer an
    // install that has never written the field gets, which is the only honest one.
    IconStyleProto.UNRECOGNIZED -> IconStyle.SmartAdaptive
}

internal fun IconStyle.asIconStyleProto(): IconStyleProto = when (this) {
    IconStyle.SmartAdaptive -> IconStyleProto.IconStyleSmartAdaptive

    IconStyle.System -> IconStyleProto.IconStyleSystem
}

internal fun FavouriteAppsViewProto.asFavouriteAppsView(): FavouriteAppsView = when (this) {
    FavouriteAppsViewProto.FavouriteViewList -> {
        FavouriteAppsView.List
    }

    FavouriteAppsViewProto.FavouriteViewGrid -> {
        FavouriteAppsView.Grid
    }

    FavouriteAppsViewProto.UNRECOGNIZED -> {
        FavouriteAppsView.List
    }
}

internal fun FavouriteAppsView.asFavouriteAppsViewProto(): FavouriteAppsViewProto = when (this) {
    FavouriteAppsView.List -> {
        FavouriteAppsViewProto.FavouriteViewList
    }

    FavouriteAppsView.Grid -> {
        FavouriteAppsViewProto.FavouriteViewGrid
    }
}

internal fun ShizukuForkModeProto.asShizukuForkMode(): ShizukuForkMode = when (this) {
    ShizukuForkModeProto.ShizukuForkThedjchi -> {
        ShizukuForkMode.Thedjchi
    }

    ShizukuForkModeProto.ShizukuForkOther -> {
        ShizukuForkMode.Other
    }

    // Nothing stored yet - a fresh install, or a build that predates the setting - reads as
    // thedjchi, which is the family this app recommends and the one its defaults are written
    // for. It used to read as Unset, leaving the picker on neither option and the fields
    // hidden until something was chosen; starting on the recommended family means a new
    // install arrives with the package already detected and one less step to get wrong.
    //
    // Safe to default because it commits nothing on its own: isShizukuConfigured still wants
    // a package, a start action and - for this family - an auth key, so a Shizuku that has
    // not really been set up is still correctly reported as unconfigured.
    ShizukuForkModeProto.ShizukuForkUnset,
    ShizukuForkModeProto.UNRECOGNIZED,
    -> {
        ShizukuForkMode.Thedjchi
    }
}

internal fun ShizukuForkMode.asShizukuForkModeProto(): ShizukuForkModeProto = when (this) {
    ShizukuForkMode.Unset -> {
        ShizukuForkModeProto.ShizukuForkUnset
    }

    ShizukuForkMode.Thedjchi -> {
        ShizukuForkModeProto.ShizukuForkThedjchi
    }

    ShizukuForkMode.Other -> {
        ShizukuForkModeProto.ShizukuForkOther
    }
}

internal fun NotificationFunctionProto.asNotificationFunction(): NotificationFunction = when (this) {
    NotificationFunctionProto.NotificationFunctionRevertToDefault -> {
        NotificationFunction.RevertToDefault
    }

    NotificationFunctionProto.NotificationFunctionMemory -> {
        NotificationFunction.Memory
    }

    // Never chosen, or written by a build this one does not know about. Both mean the same
    // thing here — no decision has been recorded — and the recommendation answers it.
    NotificationFunctionProto.NotificationFunctionUnset,
    NotificationFunctionProto.UNRECOGNIZED,
    -> {
        NotificationFunction.Default
    }
}

internal fun NotificationFunction.asNotificationFunctionProto(): NotificationFunctionProto = when (this) {
    NotificationFunction.Memory -> {
        NotificationFunctionProto.NotificationFunctionMemory
    }

    NotificationFunction.RevertToDefault -> {
        NotificationFunctionProto.NotificationFunctionRevertToDefault
    }
}

internal fun HidingFrameworkProto.asHidingFramework(): HidingFramework = when (this) {
    HidingFrameworkProto.HidingFrameworkImdDefaults -> {
        HidingFramework.ImdDefaults
    }

    HidingFrameworkProto.HidingFrameworkPerApp -> {
        HidingFramework.PerApp
    }

    // Never chosen, or written by a build this one does not know about. Both mean no decision
    // has been recorded, and the recommendation answers it — the same shape as
    // NotificationFunctionProto above.
    HidingFrameworkProto.HidingFrameworkUnset,
    HidingFrameworkProto.UNRECOGNIZED,
    -> {
        HidingFramework.Default
    }
}

internal fun HidingFramework.asHidingFrameworkProto(): HidingFrameworkProto = when (this) {
    HidingFramework.ImdDefaults -> {
        HidingFrameworkProto.HidingFrameworkImdDefaults
    }

    HidingFramework.PerApp -> {
        HidingFrameworkProto.HidingFrameworkPerApp
    }
}

internal fun UnhidingFrameworkProto.asUnhidingFramework(): UnhidingFramework = when (this) {
    UnhidingFrameworkProto.UnhidingFrameworkMemory -> {
        UnhidingFramework.Memory
    }

    UnhidingFrameworkProto.UnhidingFrameworkRevertToDefault -> {
        UnhidingFramework.RevertToDefault
    }

    UnhidingFrameworkProto.UnhidingFrameworkUnset,
    UnhidingFrameworkProto.UNRECOGNIZED,
    -> {
        UnhidingFramework.Default
    }
}

internal fun UnhidingFramework.asUnhidingFrameworkProto(): UnhidingFrameworkProto = when (this) {
    UnhidingFramework.Memory -> {
        UnhidingFrameworkProto.UnhidingFrameworkMemory
    }

    UnhidingFramework.RevertToDefault -> {
        UnhidingFrameworkProto.UnhidingFrameworkRevertToDefault
    }
}
