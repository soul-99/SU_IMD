#!/usr/bin/env python3
"""v3-r4y — the icons really do change now. r4w's refresh was blocked twice over.

    "the icons do not refresh on changing icon style, please try to refresh icons after icon
     style change for all apps tab. fav tab, homescreen shortcuts"

r4w cleared the icon cache and rebuilt the list, which was necessary and — I now see — not close
to sufficient. **Two more caches stood in front of the screen, and either one alone would have
swallowed the whole thing.**

## ⚠ 1. The list rebuilt, compared *equal*, and was thrown away

`LauncherAppsActivityInfo` deliberately leaves the icon out of `equals`, with a comment saying
why: the icon is *"a rendered PNG derived entirely from componentName and lastUpdateTime, both of
which are compared, so comparing it adds nothing"*.

That sentence was true when it was written and **r4v made it false.** The icon is now derived from
those two *and the Icon style*. So a list rebuilt in the other style is `equal` to the old one,
and the `distinctUntilChanged()` at the end of `getActivityListFlow()` dropped the emission. The
new bytes never left the wrapper.

## ⚠ 2. Coil was keyed on the same two fields, and would have served the old bitmap anyway

`AppIcon` sets an explicit `memoryCacheKey` of `componentName + "@" + lastUpdateTime` — added to
stop every icon re-decoding on scroll, which was the right fix for that problem and pins exactly
the wrong thing here. Even if a new list had arrived, every row would have drawn the cached
picture.

## The fix: the model carries which style rendered it

`iconRevision` joins `lastUpdateTime` in the model, in `equals`, in the wrapper's own cache key
and in Coil's. **It is the same idea as `lastUpdateTime`, for the other thing that changes an
icon** — a package update, or the user changing the style. Both now say "this picture is from a
different world", in every cache that had to be told.

⚠ **Not a new invalidation mechanism.** `IconStyleState.revision` already existed and already
worked; what was missing was carrying its value into the three comparisons that decide whether a
picture is stale.

## And the picker's list, for the same reason

`MainActivityViewModel._installedApps` is a `MutableStateFlow`, which conflates on `equals`, and
`InstalledAppData.equals` compares package name and label only — so a re-read produced no
emission there either. Cleared before the refresh, so the new list cannot compare equal to
nothing.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MODEL = "domain/model/src/main/kotlin/com/android/geto/domain/model/LauncherAppsActivityInfo.kt"

LAUNCHER = "framework/launcher-apps/src/main/kotlin/com/android/geto/framework/launcherapps/DefaultLauncherAppsWrapper.kt"

ICON = "feature/apps/src/main/kotlin/com/android/geto/feature/apps/AppIcon.kt"

MAIN_VM = "app/src/main/kotlin/com/android/geto/activity/main/MainActivityViewModel.kt"

EDITS: list[tuple[str, str, str]] = [
    # ---------------- 1. The model says which style rendered it ----------------
    (
        MODEL,
        """/**
 * The icon is deliberately left out of [equals] and [hashCode].
 *
 * It is a rendered PNG derived entirely from [componentName] and [lastUpdateTime], both of
 * which are compared, so comparing it adds nothing. It used to be compared with
 * `contentEquals`, which meant the `distinctUntilChanged` on the launcher list walked a
 * few hundred byte arrays element by element every time any package on the device changed.
 */""",
        """/**
 * The icon is deliberately left out of [equals] and [hashCode].
 *
 * It is a rendered PNG derived entirely from [componentName], [lastUpdateTime] **and
 * [iconRevision]**, all of which are compared, so comparing the bytes adds nothing. It used to be
 * compared with `contentEquals`, which meant the `distinctUntilChanged` on the launcher list
 * walked a few hundred byte arrays element by element every time any package on the device
 * changed.
 *
 * ⚠ **[iconRevision] is in that sentence because r4v made the old version of it false.** Until
 * then the icon really was a function of the component and the update time; the Icon style setting
 * made it a function of three things, and this class went on comparing two. A list re-rendered in
 * the other style was `equal` to the old one and the `distinctUntilChanged` dropped it, so the new
 * pictures never reached the screen at all.
 */""",
    ),
    (
        MODEL,
        """    val activityIcon: ByteArray?,
    val activityLabel: String,
    val firstInstallTime: Long,
    val lastUpdateTime: Long,
    val isSystem: Boolean,
) {""",
        """    val activityIcon: ByteArray?,
    val activityLabel: String,
    val firstInstallTime: Long,
    val lastUpdateTime: Long,
    val isSystem: Boolean,
    /**
     * Which Icon style rendered [activityIcon] — `IconStyleState.revision` at the time.
     *
     * The companion of [lastUpdateTime]: that says *"the app changed its picture"*, this says
     * *"the user changed how pictures are drawn"*. Both make the same icon stale, and every cache
     * between here and the screen keys on both.
     */
    val iconRevision: Int = 0,
) {""",
    ),
    (
        MODEL,
        """            lastUpdateTime == other.lastUpdateTime &&
            isSystem == other.isSystem
    }""",
        """            lastUpdateTime == other.lastUpdateTime &&
            isSystem == other.isSystem &&
            iconRevision == other.iconRevision
    }""",
    ),
    (
        MODEL,
        """        result = 31 * result + isSystem.hashCode()
        return result
    }""",
        """        result = 31 * result + isSystem.hashCode()
        result = 31 * result + iconRevision
        return result
    }""",
    ),
    # ---------------- 2. The wrapper fills it in, and keys its own cache on it ----------------
    (
        LAUNCHER,
        """    /** Component plus update time: a reinstall or an update is what changes an icon. */
    private fun LauncherActivityInfo.iconKey(lastUpdateTimes: Map<String, Long>): String =
        componentName.flattenToString() + "@" + (lastUpdateTimes[applicationInfo.packageName] ?: 0L)""",
        """    /**
     * Component, update time **and Icon style**: those are the three things that change an icon.
     *
     * ⚠ The style was missing until r4y, and the collector below cleared the whole cache to work
     * around it. The clear stays — it frees the bytes of a style nobody is looking at any more —
     * but this is what makes the key correct rather than merely emptied at the right moment.
     */
    private fun LauncherActivityInfo.iconKey(lastUpdateTimes: Map<String, Long>): String =
        componentName.flattenToString() + "@" +
            (lastUpdateTimes[applicationInfo.packageName] ?: 0L) + "@" +
            IconStyleState.revision.value""",
    ),
    (
        LAUNCHER,
        """        lastUpdateTime = lastUpdateTimes[applicationInfo.packageName] ?: 0L,
        isSystem = packageManagerWrapper.isSystem(flags = applicationInfo.flags),
    )""",
        """        lastUpdateTime = lastUpdateTimes[applicationInfo.packageName] ?: 0L,
        isSystem = packageManagerWrapper.isSystem(flags = applicationInfo.flags),
        // Read at render time, so the value travels with the picture it describes.
        iconRevision = IconStyleState.revision.value,
    )""",
    ),
    # ---------------- 3. Coil is keyed on it too ----------------
    (
        ICON,
        """ * The icon arrives as PNG bytes. Handing those straight to `AsyncImage` gives Coil nothing
 * stable to key its memory cache on, so every icon was decoded again each time its row
 * scrolled back into view — the single biggest source of jank in these lists. An explicit
 * [ImageRequest.Builder.memoryCacheKey] fixes that: the key is the component plus the
 * package's update time, so an app that updates gets a fresh decode and nothing else does.""",
        """ * The icon arrives as PNG bytes. Handing those straight to `AsyncImage` gives Coil nothing
 * stable to key its memory cache on, so every icon was decoded again each time its row
 * scrolled back into view — the single biggest source of jank in these lists. An explicit
 * [ImageRequest.Builder.memoryCacheKey] fixes that: the key is the component plus the
 * package's update time, so an app that updates gets a fresh decode and nothing else does.
 *
 * ⚠ **And the icon revision, since r4y.** Those two fields were the whole of what could change a
 * picture until the Icon style setting existed; afterwards this key pinned the old bitmap in
 * front of every new one, and a list that had genuinely been re-rendered drew as though nothing
 * had happened.""",
    ),
    (
        ICON,
        """    val request = remember(
        launcherAppsActivityInfo.componentName,
        launcherAppsActivityInfo.lastUpdateTime,
    ) {
        ImageRequest.Builder(context)
            .data(launcherAppsActivityInfo.activityIcon)
            .memoryCacheKey(
                launcherAppsActivityInfo.componentName + "@" +
                    launcherAppsActivityInfo.lastUpdateTime,
            )""",
        """    val request = remember(
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
            )""",
    ),
    # ---------------- 4. The picker's own conflation ----------------
    (
        MAIN_VM,
        """        viewModelScope.launch {
            IconStyleState.revision.drop(1).collect {
                refreshInstalledApps(force = true)
            }
        }""",
        """        viewModelScope.launch {
            IconStyleState.revision.drop(1).collect {
                // ⚠ **Cleared first, and that is the whole of why this did nothing.** A
                // MutableStateFlow conflates on `equals`, and `InstalledAppData.equals` compares
                // the package name and label only — so a list re-read in the other style was
                // equal to the one already there and never emitted. Emptying it first means the
                // re-read cannot compare equal to what it replaces.
                _installedApps.update { emptyList() }

                refreshInstalledApps(force = true)
            }
        }""",
    ),
]

IMPORTS = [
    (LAUNCHER, "import com.android.geto.domain.common.IconStyleState"),
]

AFTER = [
    (MODEL, "val iconRevision: Int = 0,", 1),
    (MODEL, "iconRevision == other.iconRevision", 1),
    (MODEL, "result = 31 * result + iconRevision", 1),
    (LAUNCHER, "IconStyleState.revision.value", 2),
    (LAUNCHER, "iconRevision = IconStyleState.revision.value,", 1),
    (ICON, "launcherAppsActivityInfo.iconRevision", 2),
    (MAIN_VM, "_installedApps.update { emptyList() }", 1),
]


def add_import(text: str, statement: str) -> str:
    if statement in text:
        return text

    lines = text.splitlines(keepends=True)

    indices = [i for i, line in enumerate(lines) if line.startswith("import com.android.geto.")]

    target = next((i for i in indices if lines[i] > statement + "\n"), indices[-1] + 1)

    lines.insert(target, statement + "\n")

    return "".join(lines)


def main() -> int:
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

    # ⚠ **Both construction paths must set it**, or the favourites tab would keep the old
    # pictures while All apps changed. The wrapper builds the model in one helper used by both,
    # which is what makes one edit enough — asserted rather than trusted.
    # ⚠ Spelled with the `= ` in front: the bare name is a substring of
    # `toLauncherAppsActivityInfo(`, so counting it found the helper's two call sites as well.
    if staged[LAUNCHER].count("= LauncherAppsActivityInfo(") != 1:
        print(f"REFUSED: {LAUNCHER}\n  the model is built in more than one place")
        return 1

    if staged[LAUNCHER].count("toLauncherAppsActivityInfo(") != 3:
        print(f"REFUSED: {LAUNCHER}\n  expected one helper and two callers")
        return 1

    # And the helper really is what both the list and the favourites resolution call.
    if "info.toLauncherAppsActivityInfo(" not in staged[LAUNCHER]:
        print(f"REFUSED: {LAUNCHER}\n  the favourites path does not go through the helper")
        return 1

    for relative, text in staged.items():
        (ROOT / relative).write_text(text, encoding="utf-8")

    print(f"  ok        {MODEL}  :: the model carries which style rendered it")
    print(f"  ok        {LAUNCHER}  :: both caches key on it; one helper serves both tabs")
    print(f"  ok        {ICON}  :: Coil's key includes it")
    print(f"  ok        {MAIN_VM}  :: the picker's StateFlow cannot conflate the change away")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
