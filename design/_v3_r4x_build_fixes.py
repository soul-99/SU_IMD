#!/usr/bin/env python3
"""v3-r4x — two build errors from r4v/r4w.

    "errors on build"

## ⚠ 1. `user_preferences.proto` never imported `icon_style.proto`

    IconStyleProto iconStyle = 72;

`protoc` resolves a type from another file only through an explicit `import`, and the nine other
enums in this message each have one. Without it the field is `"IconStyleProto" is not defined` and
the whole datastore module fails to generate — which takes `:data:datastore`, `:data:repository`
and everything above them with it, so the error the author saw was almost certainly a cascade from
this one line.

⚠ **`check11_proto` passed and did not catch it**, because it reads field numbers and names rather
than resolving types across files. Nothing here changes that; it is recorded so the next new enum
field is not written the same way. **A new enum field needs two edits, not one.**

## ⚠ 2. The `MainActivityViewModel` collector landed between a KDoc and the property it documents

`_v3_r4w_icon_refresh.py` anchored on `private val _installedAppsRevision = …` and inserted above
it — which is *inside* that property's doc comment block, so the KDoc now describes an `init` block
and `_installedAppsRevision` has none.

It also puts an `init` before three properties it reaches through `refreshInstalledApps`. That
happens to be safe — the collector body runs after construction — but "happens to be safe" is not
a thing to leave in a constructor. The block moves below every property it touches.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PROTO = "data/datastore-proto/src/main/proto/com/android/geto/data/datastore/proto/user_preferences.proto"

MAIN_VM = "app/src/main/kotlin/com/android/geto/activity/main/MainActivityViewModel.kt"

COLLECTOR = """    // ⚠ **The Shizuku picker's icons follow the Icon style too.** This list is cached until
    // something forces a re-read, so without this it would go on showing whichever style was in
    // force when it was first read — for the rest of the process's life.
    init {
        viewModelScope.launch {
            IconStyleState.revision.drop(1).collect {
                refreshInstalledApps(force = true)
            }
        }
    }

"""

EDITS: list[tuple[str, str, str]] = [
    (
        PROTO,
        'import "com/android/geto/data/datastore/proto/unhiding_framework.proto";',
        'import "com/android/geto/data/datastore/proto/unhiding_framework.proto";\n'
        'import "com/android/geto/data/datastore/proto/icon_style.proto";',
    ),
    # Lift the collector out from between the KDoc and its property...
    (
        MAIN_VM,
        COLLECTOR,
        "",
    ),
    # ...and put it back below everything it touches.
    (
        MAIN_VM,
        """    /** Guards against two enumerations running at once; only ever touched from the main thread. */
    private val installedAppsInFlight = MutableStateFlow(false)
""",
        """    /** Guards against two enumerations running at once; only ever touched from the main thread. */
    private val installedAppsInFlight = MutableStateFlow(false)

    /**
     * ⚠ **The Shizuku picker's icons follow the Icon style too.**
     *
     * This list is cached until something forces a re-read, so without this it would go on
     * showing whichever style was in force when it was first read — for the rest of the
     * process's life.
     *
     * ⚠ **Below every property it reaches**, and that is not tidiness. r4w put it above three of
     * them; the collector body happens to run after construction, so it happened to be safe,
     * which is not a property worth relying on in a constructor.
     */
    init {
        viewModelScope.launch {
            IconStyleState.revision.drop(1).collect {
                refreshInstalledApps(force = true)
            }
        }
    }
""",
    ),
]

AFTER = [
    (PROTO, 'import "com/android/geto/data/datastore/proto/icon_style.proto";', 1),
    (PROTO, "IconStyleProto iconStyle = 72;", 1),
    (MAIN_VM, "init {", 1),
    (MAIN_VM, "IconStyleState.revision.drop(1)", 1),
]


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

    for relative, token, expected in AFTER:
        found = staged[relative].count(token)

        if found != expected:
            print(f"REFUSED: {relative}\n  {token!r} occurs {found} time(s), expected {expected}")
            return 1

    # ⚠ **Every enum type this message names must be imported.** Written as a rule rather than as
    # one more line, so the next enum field cannot repeat this: the file that defines each type is
    # named after it in snake_case, which is the convention every one of them already follows.
    proto = staged[PROTO]

    enums = {
        "ThemeProto": "theme",
        "SortLauncherAppsActivityInfoProto": "sort_launcher_apps_activity_info",
        "SortOrderLauncherAppsActivityInfoProto": "sort_order_launcher_apps_activity_info",
        "SortFavouriteAppsProto": "sort_favourite_apps",
        "FavouriteAppsViewProto": "favourite_apps_view",
        "ShizukuForkModeProto": "shizuku_fork_mode",
        "NotificationFunctionProto": "notification_function",
        "HidingFrameworkProto": "hiding_framework",
        "UnhidingFrameworkProto": "unhiding_framework",
        "IconStyleProto": "icon_style",
    }

    for type_name, file_stem in enums.items():
        if type_name not in proto:
            continue

        statement = f'import "com/android/geto/data/datastore/proto/{file_stem}.proto";'

        if statement not in proto:
            print(f"REFUSED: {PROTO}\n  {type_name} is used with no import of {file_stem}.proto")
            return 1

        if not (ROOT / PROTO).parent.joinpath(f"{file_stem}.proto").is_file():
            print(f"REFUSED: {file_stem}.proto is imported but does not exist")
            return 1

    for relative, text in staged.items():
        (ROOT / relative).write_text(text, encoding="utf-8")

    print(f"  ok        {PROTO}  :: every enum it names is imported")
    print(f"  ok        {MAIN_VM}  :: the collector is below the properties it uses")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
