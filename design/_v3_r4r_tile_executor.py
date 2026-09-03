#!/usr/bin/env python3
"""v3-r4r — the Add toggle request gets a real executor.

`StatusBarManager.requestAddTileService` takes an `Executor` and a `Consumer<Int>`. The first
draft passed `{}` for both, which compiles - Kotlin lets a single-parameter lambda omit its
parameter - but an `Executor` written as `{}` is one that receives a `Runnable` and never runs it.
The callback would simply never fire.

⚠ **It happens to be harmless here and is still wrong.** The callback does nothing on purpose:
every outcome is already in front of the user, because the system puts up its own confirmation and
the tile either appears in their quick settings or does not. But an executor that silently drops
its work is the kind of thing that is copied to somewhere it matters.

`context.mainExecutor` is API 28 and this whole function is behind an API 33 guard, so there is
nothing to check for.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PAGE = "app/src/main/kotlin/com/android/geto/onboarding/SetupCompletePage.kt"

OLD = """            statusBar.requestAddTileService(
                component(context),
                label,
                Icon.createWithResource(context, icon),
                {},
                {},
            )"""

NEW = """            statusBar.requestAddTileService(
                component(context),
                label,
                Icon.createWithResource(context, icon),
                // ⚠ A real executor. Written as `{}` this compiles - Kotlin lets a
                // single-parameter lambda omit its parameter - and is an Executor that takes a
                // Runnable and never runs it, so the callback below could never fire. Harmless
                // while that callback does nothing, and exactly the kind of thing that gets
                // copied somewhere it matters.
                context.mainExecutor,
                // Deliberately empty: the system puts up its own confirmation, and the tile
                // either appears in the user's quick settings or does not. A message here would
                // be the app narrating something they just watched.
                {},
            )"""


def main() -> int:
    path = ROOT / PAGE

    if not path.is_file():
        print(f"REFUSED: missing {PAGE}")
        return 1

    text = path.read_text(encoding="utf-8")

    found = text.count(OLD)

    if found != 1:
        print(f"REFUSED: {PAGE}\n  the request matched {found} time(s), expected 1")
        return 1

    staged = text.replace(OLD, NEW, 1)

    # The API 33 guard that makes mainExecutor (API 28) safe must still be above it.
    if "Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU" not in staged:
        print(f"REFUSED: {PAGE}\n  the API guard is gone")
        return 1

    if staged.count("context.mainExecutor") != 1:
        print(f"REFUSED: {PAGE}\n  expected exactly one executor")
        return 1

    path.write_text(staged, encoding="utf-8")

    print(f"  ok        {PAGE}  :: context.mainExecutor, empty callback")
    print("\nwrote 1 file(s), 1 edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
