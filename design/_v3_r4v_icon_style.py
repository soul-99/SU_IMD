#!/usr/bin/env python3
"""v3-r4v — Icon style, under User interface.

    "add a new option in user interface section called 'Icon style', on clicking a dialog box with
     save button, dialog box options toggles(select only one at a time type): 'Smart adaptive
     icons'(default, uses the framework we generated in the current version), 'System icons'
     (just gets the system icons from android launcher/system like we had before)"

His three labels go in verbatim.

## ⚠ Where the switch is read, and why it is a memory holder rather than an injection

Exactly two places shape an icon, and both are in `:framework`:

* `DefaultDrawableWrapper.toByteArray` — every icon the app draws;
* `ShortcutIconFactory.legacyBitmapIcon` — every icon a pinned shortcut carries.

Neither can reach the preferences. `framework:drawable` depends on `domain:common` alone, and
`framework:shortcut-manager` on `domain:common` and `domain:framework`; making either depend on
`domain:repository` points the module graph backwards for one boolean. Threading the answer down
instead means a parameter on `toByteArray`, which has five call sites in three modules, none of
which know a user preference either.

So it is `IconStyleState` in `domain:common`: one volatile boolean, written by `GetoApplication`
from the stored value and read where the shaping happens. **This is the pattern the app already
uses** — `AutoHideDetection` holds what the accessibility service needs for the same reason, that
the code which has to answer cannot wait on a datastore read.

⚠ **Default true, and that matters.** The holder is read before `GetoApplication` has collected
anything — the very first icon of a cold start can be decoded that early. `true` is *Smart
adaptive*, which is both the author's default and what the app did yesterday, so the race resolves
to the same picture either way.

## ⚠ What "System icons" restores, precisely

Not a different icon: the same drawable, unshaped. `isLegacy` stops being consulted, so a legacy
icon is drawn as the finished 48dp picture the system handed over, and a shortcut carries
`createWithBitmap` instead of `createWithAdaptiveBitmap`. Adaptive icons are untouched by either
setting — nothing was ever shaping those.

## ⚠ Already-decoded icons do not change until they are read again

The lists hold PNG bytes decoded when the list was last read; nothing here invalidates them. A
list refresh or an app restart picks up the new style. Worth saying out loud rather than leaving
the author to find it: if he wants the change to be visible immediately, the app list needs a
forced refresh on save, and that is a separate decision about which lists to disturb.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PROTO_DIR = "data/datastore-proto/src/main/proto/com/android/geto/data/datastore/proto"

ICON_PROTO = f"{PROTO_DIR}/icon_style.proto"

PREFS_PROTO = f"{PROTO_DIR}/user_preferences.proto"

MODEL = "domain/model/src/main/kotlin/com/android/geto/domain/model/IconStyle.kt"

USER_DATA = "domain/model/src/main/kotlin/com/android/geto/domain/model/UserData.kt"

STATE = "domain/common/src/main/kotlin/com/android/geto/domain/common/IconStyleState.kt"

MAPPER = "data/datastore/src/main/kotlin/com/android/geto/data/datastore/mapper/DataStoreMapper.kt"

SOURCE = "data/datastore/src/main/kotlin/com/android/geto/data/datastore/UserPreferencesDataSource.kt"

REPO_IFACE = "domain/repository/src/main/kotlin/com/android/geto/domain/repository/UserDataRepository.kt"

REPO_IMPL = "data/repository/src/main/kotlin/com/android/geto/data/repository/DefaultUserDataRepository.kt"

APPLICATION = "app/src/main/kotlin/com/android/geto/GetoApplication.kt"

DRAWABLE = "framework/drawable/src/main/kotlin/com/android/geto/framework/drawable/DefaultDrawableWrapper.kt"

SHORTCUT = "framework/shortcut-manager/src/main/kotlin/com/android/geto/framework/shortcutmanager/ShortcutIconFactory.kt"

TESTS = "tools/host-tests/DomainLogicTests.kt"

LICENCE = """/*
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
"""

NEW_FILES: dict[str, str] = {
    ICON_PROTO: LICENCE + """
syntax = "proto3";

option java_package = "com.android.geto.data.datastore.proto";
option java_multiple_files = true;

// How an app icon is drawn. Zero is the default for a field nobody has written,
// so Smart adaptive has to be zero - it is both the author's default and what
// every install did before this option existed.
enum IconStyleProto {
  IconStyleSmartAdaptive = 0;
  IconStyleSystem = 1;
}
""",
    MODEL: LICENCE + """package com.android.geto.domain.model

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
""",
    STATE: LICENCE + """package com.android.geto.domain.common

/**
 * Whether legacy icons are shaped, held in memory for the two places that draw them.
 *
 * ⚠ **A holder rather than an injection, deliberately.** The two readers are
 * `DefaultDrawableWrapper` and `ShortcutIconFactory`, both in `:framework`, and neither can reach
 * the preferences: `framework:drawable` depends on `domain:common` alone, and pointing it at
 * `domain:repository` would turn the module graph around for one boolean. Threading it down
 * instead means a parameter on `toByteArray`, whose five call sites know nothing about user
 * preferences either.
 *
 * The app already solves this exact problem this way — see `AutoHideDetection`, which holds what
 * the accessibility service needs because the code that has to answer cannot wait on a datastore
 * read.
 *
 * ⚠ **`true` before anything has been collected, and that is not an arbitrary default.** The
 * first icon of a cold start can be decoded before `GetoApplication` has read the preference.
 * `true` is Smart adaptive, which is both the stored default and what every version before this
 * one did, so the race resolves to the same picture whichever way it goes.
 */
object IconStyleState {
    @Volatile
    @JvmStatic
    var shapeLegacyIcons: Boolean = true
}
""",
}

EDITS: list[tuple[str, str, str]] = [
    # ---------------- The stored value ----------------
    (
        PREFS_PROTO,
        "  bool sortFavouriteAppsSet = 71;",
        """  bool sortFavouriteAppsSet = 71;

  // How app icons are drawn - see IconStyleProto. No "…Set" companion is needed
  // beside it, unlike the two above: the default this app wants *is* the proto
  // default, so an install that has never written it reads correctly.
  IconStyleProto iconStyle = 72;""",
    ),
    (
        USER_DATA,
        "    val favouriteAppsView: FavouriteAppsView,",
        "    val favouriteAppsView: FavouriteAppsView,\n    val iconStyle: IconStyle,",
    ),
    (
        MAPPER,
        "internal fun FavouriteAppsViewProto.asFavouriteAppsView(): FavouriteAppsView = when (this) {",
        """internal fun IconStyleProto.asIconStyle(): IconStyle = when (this) {
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

internal fun FavouriteAppsViewProto.asFavouriteAppsView(): FavouriteAppsView = when (this) {""",
    ),
    (
        SOURCE,
        """            favouriteAppsView = if (it.favouriteAppsViewSet) {""",
        """            iconStyle = it.iconStyle.asIconStyle(),
            favouriteAppsView = if (it.favouriteAppsViewSet) {""",
    ),
    (
        SOURCE,
        "    suspend fun updateFavouriteAppsView(favouriteAppsView: FavouriteAppsView) {",
        """    suspend fun updateIconStyle(iconStyle: IconStyle) {
        userPreferences.updateData {
            it.copy {
                this.iconStyle = iconStyle.asIconStyleProto()
            }
        }
    }

    suspend fun updateFavouriteAppsView(favouriteAppsView: FavouriteAppsView) {""",
    ),
    (
        REPO_IFACE,
        "    suspend fun updateFavouriteAppsView(favouriteAppsView: FavouriteAppsView)",
        "    suspend fun updateIconStyle(iconStyle: IconStyle)\n\n"
        "    suspend fun updateFavouriteAppsView(favouriteAppsView: FavouriteAppsView)",
    ),
    # ---------------- The two places that shape ----------------
    (
        DRAWABLE,
        """        val shaped = if (LegacyIconShaping.isLegacy(drawable)) {""",
        """        // ⚠ **The user's Icon style, read from memory** — see IconStyleState for why it is
        // held rather than injected. False is "System icons": the drawable is handed over
        // exactly as the system gave it, which is what this app did before v3.
        val shaped = if (IconStyleState.shapeLegacyIcons && LegacyIconShaping.isLegacy(drawable)) {""",
    ),
    (
        SHORTCUT,
        """        // Below API 26 there is no adaptive icon to match, so the finished picture is still the
        // honest answer there.
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) {
            return IconCompat.createWithBitmap(bitmap)
        }""",
        """        // Below API 26 there is no adaptive icon to match, so the finished picture is still the
        // honest answer there.
        //
        // ⚠ **And when the user has chosen System icons**, which is what that choice means on
        // this path: hand the launcher a finished picture and let it sit unshaped, exactly as
        // every build before v3 did. See IconStyleState.
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O || !IconStyleState.shapeLegacyIcons) {
            return IconCompat.createWithBitmap(bitmap)
        }""",
    ),
    # ---------------- Kept up to date ----------------
    (
        APPLICATION,
        """        // Auto-hide settings (IMD+) starts listening here, and only here.""",
        """        // ⚠ **The Icon style, into the memory holder the two renderers read.** They are in
        // `:framework` and cannot reach the preferences — see IconStyleState. One collector
        // rather than a read at each icon: a few hundred icons are decoded per list.
        appScope.launch {
            userDataRepository.userData
                .map { it.iconStyle }
                .distinctUntilChanged()
                .collect { style ->
                    IconStyleState.shapeLegacyIcons = style == IconStyle.SmartAdaptive
                }
        }

        // Auto-hide settings (IMD+) starts listening here, and only here.""",
    ),
    # ---------------- The host tests' UserData ----------------
    (
        TESTS,
        "    autoUnhideOnScreenLock = false,",
        "    autoUnhideOnScreenLock = false,\n    iconStyle = IconStyle.SmartAdaptive,",
    ),
]

IMPORTS = [
    (USER_DATA, None),
    (MAPPER, "import com.android.geto.data.datastore.proto.IconStyleProto"),
    (MAPPER, "import com.android.geto.domain.model.IconStyle"),
    (SOURCE, "import com.android.geto.data.datastore.mapper.asIconStyle"),
    (SOURCE, "import com.android.geto.data.datastore.mapper.asIconStyleProto"),
    (SOURCE, "import com.android.geto.domain.model.IconStyle"),
    (REPO_IFACE, "import com.android.geto.domain.model.IconStyle"),
    (APPLICATION, "import com.android.geto.domain.common.IconStyleState"),
    (APPLICATION, "import com.android.geto.domain.model.IconStyle"),
    (DRAWABLE, "import com.android.geto.domain.common.IconStyleState"),
    (SHORTCUT, "import com.android.geto.domain.common.IconStyleState"),
    (TESTS, "import com.android.geto.domain.model.IconStyle"),
]

AFTER = [
    (PREFS_PROTO, "IconStyleProto iconStyle = 72;", 1),
    (USER_DATA, "val iconStyle: IconStyle,", 1),
    (MAPPER, "fun IconStyleProto.asIconStyle()", 1),
    (MAPPER, "fun IconStyle.asIconStyleProto()", 1),
    (SOURCE, "suspend fun updateIconStyle(", 1),
    (REPO_IFACE, "suspend fun updateIconStyle(", 1),
    (DRAWABLE, "IconStyleState.shapeLegacyIcons &&", 1),
    (SHORTCUT, "!IconStyleState.shapeLegacyIcons", 1),
    (APPLICATION, "IconStyleState.shapeLegacyIcons =", 1),
    (TESTS, "iconStyle = IconStyle.SmartAdaptive,", 1),
]


def add_import(text: str, statement: str) -> str:
    if statement is None or statement in text:
        return text

    lines = text.splitlines(keepends=True)

    indices = [i for i, line in enumerate(lines) if line.startswith("import com.android.geto.")]

    if not indices:
        indices = [i for i, line in enumerate(lines) if line.startswith("import ")]

    if not indices:
        raise SystemExit(f"REFUSED: nowhere to put {statement!r}")

    target = next((i for i in indices if lines[i] > statement + "\n"), indices[-1] + 1)

    lines.insert(target, statement + "\n")

    return "".join(lines)


def main() -> int:
    for relative in NEW_FILES:
        if (ROOT / relative).exists():
            print(f"REFUSED: {relative} already exists")
            return 1

    staged: dict[str, str] = {}

    for relative, old, new in EDITS:
        path = ROOT / relative

        if not path.is_file():
            print(f"REFUSED: missing {relative}")
            return 1

        text = staged.get(relative, path.read_text(encoding="utf-8"))

        found = text.count(old)

        if found != 1:
            print(f"REFUSED: {relative}\n  {old.strip().splitlines()[0][:70]!r} matched {found} time(s)")
            return 1

        staged[relative] = text.replace(old, new, 1)

    for relative, statement in IMPORTS:
        staged[relative] = add_import(staged[relative], statement)

    for relative, token, expected in AFTER:
        found = staged[relative].count(token)

        if found != expected:
            print(f"REFUSED: {relative}\n  {token!r} occurs {found} time(s), expected {expected}")
            return 1

    # ⚠ **72 must be free.** A reused proto field number reads another value's bytes as this one,
    # which is a data-loss bug no static check would find. Read out of the file, not assumed.
    proto = staged[PREFS_PROTO]

    if proto.count(" = 72;") != 1:
        print(f"REFUSED: {PREFS_PROTO}\n  field number 72 is not used exactly once")
        return 1

    if " = 73;" in proto:
        print(f"REFUSED: {PREFS_PROTO}\n  a field already numbered above 72; pick the next free one")
        return 1

    # `map` and `distinctUntilChanged` are what the new collector uses; both are already in
    # GetoApplication for the auto unhide watcher beside it.
    for token in ("import kotlinx.coroutines.flow.map", "import kotlinx.coroutines.flow.distinctUntilChanged"):
        if token not in staged[APPLICATION]:
            print(f"REFUSED: {APPLICATION}\n  {token!r} is absent")
            return 1

    for relative, content in NEW_FILES.items():
        (ROOT / relative).parent.mkdir(parents=True, exist_ok=True)

        (ROOT / relative).write_text(content, encoding="utf-8")

    for relative, text in staged.items():
        (ROOT / relative).write_text(text, encoding="utf-8")

    print(f"  ok        {ICON_PROTO}  :: Smart adaptive is the proto default")
    print(f"  ok        {STATE}  :: one volatile boolean, read where icons are shaped")
    print("  ok        both renderers honour it; GetoApplication keeps it current")
    print(f"\nwrote {len(NEW_FILES) + len(staged)} file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
