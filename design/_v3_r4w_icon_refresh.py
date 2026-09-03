#!/usr/bin/env python3
"""v3-r4w — saving Icon style redraws every icon, pinned shortcuts included.

    "also make icons refresh everywhere after save, also can we refresh already added shortcut
     icons too?"

## ⚠ Re-reading the list was never going to be enough, and this is why

`DefaultLauncherAppsWrapper` keeps an `iconCache` keyed by **component name + the package's last
update time**. That key is exactly right for the thing it was built for — `onPackageChanged` fires
for routine events and re-rasterising a few hundred icons each time was the bug it fixed — and
exactly wrong here: changing the icon *style* changes no package's update time, so a rebuilt list
would have been served every one of its old pictures back out of that cache.

So the cache is cleared and the list rebuilt, together, on one signal.

## The signal

`IconStyleState` already held the boolean the two renderers read. It gains a revision counter that
`invalidate()` bumps, and three places listen:

* the **launcher apps** flow — All apps, Favourites, the settings manager: clears its cache and
  re-emits;
* the **installed apps** list in `MainActivityViewModel`, which the Shizuku package picker draws;
* the **pinned shortcuts**, below.

⚠ **`ApplyIconStyleUseCase` sets the boolean itself rather than waiting for `GetoApplication`'s
collector to do it.** Both write the same value, so this is not a second source of truth — it is
ordering. The redraw begins in the next line, and a redraw that overtook the collector would
re-render every icon in the old style and then sit there looking like the setting had not worked.

## ⚠ Refreshing a pinned shortcut is possible, with one honest limit

`ShortcutManagerCompat.updateShortcuts` accepts pinned shortcuts, and the ids IMD pins **are** the
component names, so each one can be re-rendered from its own app's icon and pushed back with the
labels the user gave it untouched.

The limit is the launcher. Some redraw a pinned shortcut as soon as it is updated; others hold
their own copy of the bitmap and only pick up a change when they are restarted, or when the home
screen is reloaded. Nothing this app can do reaches inside a launcher's cache. So the update is
sent for every shortcut, and where nothing appears to happen the answer is a launcher restart, not
a bug here.

⚠ **A shortcut whose icon cannot be read is skipped, not updated.** `getActivityIcon` returns null
for an app that has since been uninstalled, and passing that null through would replace a working
icon with a blank one — turning "your icons changed style" into "your shortcuts lost their
pictures".

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STATE = "domain/common/src/main/kotlin/com/android/geto/domain/common/IconStyleState.kt"

REFRESH_USE_CASE = "domain/use-case/src/main/kotlin/com/android/geto/domain/usecase/RefreshShortcutIconsUseCase.kt"

APPLY_USE_CASE = "domain/use-case/src/main/kotlin/com/android/geto/domain/usecase/ApplyIconStyleUseCase.kt"

LAUNCHER = "framework/launcher-apps/src/main/kotlin/com/android/geto/framework/launcherapps/DefaultLauncherAppsWrapper.kt"

MAIN_VM = "app/src/main/kotlin/com/android/geto/activity/main/MainActivityViewModel.kt"

VIEW_MODEL = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsViewModel.kt"

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

NEW_FILES = {
    REFRESH_USE_CASE: LICENCE + """package com.android.geto.domain.usecase

import com.android.geto.domain.common.dispatcher.Dispatcher
import com.android.geto.domain.common.dispatcher.GetoDispatchers
import com.android.geto.domain.framework.PackageManagerWrapper
import com.android.geto.domain.framework.ShortcutManagerCompatWrapper
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.withContext
import javax.inject.Inject

/**
 * Re-renders every pinned shortcut's icon and pushes it back to the launcher.
 *
 * ⚠ **The id of a shortcut IMD pins *is* the component name** — see `GetPinShortcutUseCase`,
 * which looks a shortcut up by exactly that. So each pinned shortcut can be re-rendered from its
 * own app's icon with nothing else stored, and `FLAG_MATCH_PINNED` returns only this app's
 * shortcuts, so there is no other kind of id to meet.
 *
 * ⚠ **The labels are carried over, not regenerated.** A user who renamed a shortcut when they
 * created it would otherwise find the app's own name back on it, which is a far more annoying
 * change than the one they asked for.
 *
 * ⚠ **A shortcut whose icon cannot be read is skipped.** `getActivityIcon` answers null for an
 * app that has been uninstalled since, and writing that null through would replace a working
 * picture with a blank one.
 *
 * Returns how many were updated, for the diagnostics log.
 *
 * ⚠ **What happens next is the launcher's business.** Some redraw a pinned shortcut the moment it
 * is updated; others hold their own copy of the bitmap until they are restarted. Nothing here
 * reaches inside a launcher's cache, so where nothing appears to change the answer is a launcher
 * restart rather than a second attempt.
 */
class RefreshShortcutIconsUseCase @Inject constructor(
    private val shortcutManagerCompatWrapper: ShortcutManagerCompatWrapper,
    private val packageManagerWrapper: PackageManagerWrapper,
    @param:Dispatcher(GetoDispatchers.IO) private val ioDispatcher: CoroutineDispatcher,
) {
    suspend operator fun invoke(): Int = withContext(ioDispatcher) {
        var updated = 0

        for (shortcut in shortcutManagerCompatWrapper.getShortcuts()) {
            val icon = packageManagerWrapper.getActivityIcon(componentName = shortcut.id)
                ?: continue

            val wrote = shortcutManagerCompatWrapper.updateShortcuts(
                componentName = shortcut.id,
                icon = icon,
                id = shortcut.id,
                shortLabel = shortcut.shortLabel,
                longLabel = shortcut.longLabel,
            )

            if (wrote) updated += 1
        }

        updated
    }
}
""",
    APPLY_USE_CASE: LICENCE + """package com.android.geto.domain.usecase

import com.android.geto.domain.common.IconStyleState
import com.android.geto.domain.model.IconStyle
import com.android.geto.domain.repository.UserDataRepository
import javax.inject.Inject

/**
 * Saves the Icon style and makes every icon in the app — and on the home screen — catch up.
 *
 * ⚠ **The in-memory flag is set here rather than left to `GetoApplication`'s collector.** Both
 * write the same value from the same source, so this is not a second source of truth; it is
 * ordering. The redraw starts on the line after, and a redraw that overtook the collector would
 * re-render every icon in the *old* style and leave the setting looking broken.
 *
 * ⚠ **Then `invalidate()`, which is what makes a re-read produce different bytes.** The launcher
 * apps wrapper caches rendered icons under component-name-plus-package-update-time — a key that
 * is right for the package changes it was built for and blind to this one, since changing a style
 * changes no package's update time. The counter is the signal to drop that cache.
 */
class ApplyIconStyleUseCase @Inject constructor(
    private val userDataRepository: UserDataRepository,
    private val refreshShortcutIconsUseCase: RefreshShortcutIconsUseCase,
) {
    suspend operator fun invoke(iconStyle: IconStyle) {
        userDataRepository.updateIconStyle(iconStyle = iconStyle)

        IconStyleState.shapeLegacyIcons = iconStyle == IconStyle.SmartAdaptive

        IconStyleState.invalidate()

        refreshShortcutIconsUseCase()
    }
}
""",
}

EDITS: list[tuple[str, str, str]] = [
    (
        STATE,
        """object IconStyleState {
    @Volatile
    @JvmStatic
    var shapeLegacyIcons: Boolean = true
}""",
        """object IconStyleState {
    @Volatile
    @JvmStatic
    var shapeLegacyIcons: Boolean = true

    private val _revision = MutableStateFlow(0)

    /**
     * Bumped whenever the style changes, so anything holding rendered icons can drop them.
     *
     * ⚠ **A counter rather than the style itself.** What the listeners need to know is *"your
     * pictures are stale"*, and a flow of the style would say nothing at all if it were ever set
     * to the value it already had — while a counter is a fact about staleness that cannot be
     * conflated away.
     */
    val revision: StateFlow<Int> = _revision.asStateFlow()

    fun invalidate() {
        _revision.update { it + 1 }
    }
}""",
    ),
    # ---------------- The launcher list drops its cache and rebuilds ----------------
    (
        LAUNCHER,
        """        getActivityList()

        val callback = object : LauncherApps.Callback() {""",
        """        getActivityList()

        // ⚠ **The Icon style changed, so every cached picture is wrong.** The cache above is
        // keyed by component name and package update time — the right key for the package
        // events this flow was built to survive, and blind to this one, because changing a style
        // changes no package's update time. Clearing it is what makes the rebuild produce
        // different bytes rather than handing back the same ones.
        //
        // drop(1) discards the value every new collector is replayed: at this point it means
        // "nothing has changed yet", and acting on it would rebuild the list a second time for
        // no reason on every subscription.
        launch {
            IconStyleState.revision.drop(1).collect {
                iconCache.clear()

                getActivityList()
            }
        }

        val callback = object : LauncherApps.Callback() {""",
    ),
    # ---------------- The installed-apps list follows ----------------
    (
        MAIN_VM,
        "    private val _installedAppsRevision = MutableStateFlow(0)",
        """    // ⚠ **The Shizuku picker's icons follow the Icon style too.** This list is cached until
    // something forces a re-read, so without this it would go on showing whichever style was in
    // force when it was first read — for the rest of the process's life.
    init {
        viewModelScope.launch {
            IconStyleState.revision.drop(1).collect {
                refreshInstalledApps(force = true)
            }
        }
    }

    private val _installedAppsRevision = MutableStateFlow(0)""",
    ),
    # ---------------- Save goes through the use case ----------------
    (
        VIEW_MODEL,
        """    fun updateIconStyle(iconStyle: IconStyle) {
        viewModelScope.launch {
            userDataRepository.updateIconStyle(iconStyle = iconStyle)
        }
    }""",
        """    /**
     * Saves the Icon style and redraws everything that has already rendered an icon.
     *
     * Through a use case rather than written here, because "redraw everything" reaches three
     * places this ViewModel has no business knowing about — see [ApplyIconStyleUseCase].
     */
    fun updateIconStyle(iconStyle: IconStyle) {
        viewModelScope.launch {
            applyIconStyleUseCase(iconStyle = iconStyle)
        }
    }""",
    ),
]

IMPORTS = [
    (STATE, "import kotlinx.coroutines.flow.MutableStateFlow"),
    (STATE, "import kotlinx.coroutines.flow.StateFlow"),
    (STATE, "import kotlinx.coroutines.flow.asStateFlow"),
    (STATE, "import kotlinx.coroutines.flow.update"),
    (LAUNCHER, "import com.android.geto.domain.common.IconStyleState"),
    (LAUNCHER, "import kotlinx.coroutines.flow.drop"),
    (MAIN_VM, "import com.android.geto.domain.common.IconStyleState"),
    (MAIN_VM, "import kotlinx.coroutines.flow.drop"),
    (VIEW_MODEL, "import com.android.geto.domain.usecase.ApplyIconStyleUseCase"),
]

# The ViewModel's new dependency, injected beside the ones it already has.
INJECT_ANCHOR = "    private val userDataRepository: UserDataRepository,"

INJECT_NEW = """    private val userDataRepository: UserDataRepository,
    private val applyIconStyleUseCase: ApplyIconStyleUseCase,"""

AFTER = [
    (STATE, "fun invalidate()", 1),
    (STATE, "val revision: StateFlow<Int>", 1),
    (LAUNCHER, "IconStyleState.revision.drop(1)", 1),
    (LAUNCHER, "iconCache.clear()", 1),
    (MAIN_VM, "IconStyleState.revision.drop(1)", 1),
    (VIEW_MODEL, "applyIconStyleUseCase(iconStyle = iconStyle)", 1),
    (VIEW_MODEL, "private val applyIconStyleUseCase: ApplyIconStyleUseCase,", 1),
]


def add_import(text: str, statement: str) -> str:
    if statement in text:
        return text

    lines = text.splitlines(keepends=True)

    prefix = "import com.android.geto." if statement.startswith("import com.") else "import kotlinx."

    indices = [i for i, line in enumerate(lines) if line.startswith(prefix)]

    if not indices:
        indices = [i for i, line in enumerate(lines) if line.startswith("import ")]

    # ⚠ A file with no imports at all — IconStyleState is one. The block starts after the
    # package line, with a blank line between.
    if not indices:
        package = next(i for i, line in enumerate(lines) if line.startswith("package "))

        lines.insert(package + 1, "\n" + statement + "\n")

        return "".join(lines)

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

    if staged[VIEW_MODEL].count(INJECT_ANCHOR) != 1:
        print(f"REFUSED: {VIEW_MODEL}\n  the constructor's repository line was not unique")
        return 1

    staged[VIEW_MODEL] = staged[VIEW_MODEL].replace(INJECT_ANCHOR, INJECT_NEW, 1)

    for relative, statement in IMPORTS:
        staged[relative] = add_import(staged[relative], statement)

    for relative, token, expected in AFTER:
        found = staged[relative].count(token)

        if found != expected:
            print(f"REFUSED: {relative}\n  {token!r} occurs {found} time(s), expected {expected}")
            return 1

    # ⚠ Everything the new code leans on has to already be there. Asserted rather than assumed:
    # each of these missing is a build error on the author's machine, not here.
    for relative, token in (
        (LAUNCHER, "private val iconCache = ConcurrentHashMap<String, ByteArray>()"),
        (LAUNCHER, "import kotlinx.coroutines.launch"),
        (MAIN_VM, "fun refreshInstalledApps("),
        (MAIN_VM, "import androidx.lifecycle.viewModelScope"),
        (MAIN_VM, "import kotlinx.coroutines.launch"),
    ):
        if token not in staged[relative]:
            print(f"REFUSED: {relative}\n  {token!r} is absent")
            return 1

    for relative, content in NEW_FILES.items():
        (ROOT / relative).write_text(content, encoding="utf-8")

    for relative, text in staged.items():
        (ROOT / relative).write_text(text, encoding="utf-8")

    print(f"  ok        {STATE}  :: a revision anything holding icons can watch")
    print(f"  ok        {LAUNCHER}  :: the icon cache is dropped and the list rebuilt")
    print(f"  ok        {REFRESH_USE_CASE}  :: pinned shortcuts re-rendered, labels kept")
    print(f"\nwrote {len(NEW_FILES) + len(staged)} file(s), {len(EDITS) + 1} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
