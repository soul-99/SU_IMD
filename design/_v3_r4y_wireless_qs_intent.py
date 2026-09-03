#!/usr/bin/env python3
"""v3-r4y — the wireless debugging link tries Shizuku's route first.

    "here is the source code for shizuku it have a developer options button which directly opens
     wireless debugging page but ours fail on both my devices can we us it to know what it trigers
     so that we can use it for wireless debugging link button in settings manager as first option
     before fallback"

## What Shizuku actually does

`manager/src/main/java/moe/shizuku/manager/utils/SettingsPage.kt`, `Developer.WirelessDebugging`:

    Intent(TileService.ACTION_QS_TILE_PREFERENCES).apply {
        setPackage("com.android.settings")
        putExtra(
            Intent.EXTRA_COMPONENT_NAME,
            ComponentName(
                "com.android.settings",
                "com.android.settings.development.qstile.DevelopmentTiles\\$WirelessDebugging",
            ),
        )
    }

…with the highlighted Developer options page behind it in a `recoverCatching`.

## ⚠ Why this works where an explicit activity name does not

Both routes end at the same screen. The difference is **who resolves the name**.

Ours starts `com.android.settings.Settings$AdbWirelessSettingsActivity` directly, so the name has
to be exactly right on that build — one OEM rename and the start throws. Shizuku's asks the
Settings app to open *"the preferences screen belonging to this quick-settings tile"*, and the
tile class it names is part of the platform's development-tiles set, which OEMs leave alone far
more often than they leave the Settings activity aliases alone. The Settings app does the
resolving, on the device, with its own knowledge of where that screen lives.

So it goes **in front of** what we had rather than replacing it: three candidates now, tried in
order, and the loop that already existed asks each one by starting it.

## ⚠ Two things of Shizuku's are deliberately not copied

* **`FLAG_ACTIVITY_CLEAR_TASK`**, which it adds along with `NO_HISTORY` and
  `EXCLUDE_FROM_RECENTS`. Clearing the task is right for their standalone launcher and wrong
  here: this link is pressed from a dialog floating over somebody else's app, and clearing that
  task would take the app the user was in with it. Our loop's `FLAG_ACTIVITY_NEW_TASK` stays as
  it is, the same as every other row's.
* **Their Xiaomi branch**, which calls `HighlightWirelessDebugging.buildIntent(context)` and
  throws the result away before returning the tile intent anyway. As written it does nothing, so
  copying it would be copying a bug.

## ⚠ The author's "only while the setting is on" condition is kept

r4h's rule — *"switched off, that screen holds nothing but the switch the user has just come
from"* — is his, and it is about the destination rather than about how we get there. The new
candidate lands on the same screen, so it carries the same condition. **One `takeIf` to remove**
if he would rather it opened in both states, as Shizuku's does.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ROUTE = "feature/apps/src/main/kotlin/com/android/geto/feature/apps/manager/SettingsManagerRoute.kt"

EDITS: list[tuple[str, str]] = [
    (
        """private fun wirelessDebuggingPage(): Intent = Intent().setClassName(
    "com.android.settings",
    "com.android.settings.Settings\\$AdbWirelessSettingsActivity",
)""",
        """private fun wirelessDebuggingPage(): Intent = Intent().setClassName(
    "com.android.settings",
    "com.android.settings.Settings\\$AdbWirelessSettingsActivity",
)

/**
 * The same screen, reached the way Shizuku reaches it — and the way that works where ours did not.
 *
 * ⚠ **The difference is who resolves the name.** [wirelessDebuggingPage] starts a Settings
 * activity by its exact class, so one OEM rename and the start throws — which is what the author
 * saw on both of his devices. This asks the Settings app for *"the preferences screen belonging to
 * this quick-settings tile"* and names a class from the platform's own development-tiles set,
 * which survives OEM reshuffling far more often than the Settings activity aliases do. Settings
 * itself then finds the screen, on the device, with its own knowledge of where it lives.
 *
 * Taken from Shizuku 13.7.0 (thedjchi), `moe.shizuku.manager.utils.SettingsPage`, which the author
 * supplied precisely because its button works where this one did not.
 *
 * ⚠ **Its `FLAG_ACTIVITY_CLEAR_TASK` is not copied.** That is right for a standalone launcher and
 * wrong here: this link is pressed from a dialog floating over somebody else's app, and clearing
 * the task would take that app with it. [openTarget]'s own `FLAG_ACTIVITY_NEW_TASK` is what every
 * other row uses and is what this uses too.
 *
 * Still not public API, and still asked by starting it rather than by resolving it.
 */
private fun wirelessDebuggingTilePage(): Intent {
    val settings = "com.android.settings"

    return Intent(TileService.ACTION_QS_TILE_PREFERENCES)
        .setPackage(settings)
        .putExtra(
            Intent.EXTRA_COMPONENT_NAME,
            ComponentName(
                settings,
                "$settings.development.qstile.DevelopmentTiles\\$WirelessDebugging",
            ),
        )
}""",
    ),
    (
        """        ManualRevertTarget.WirelessDebugging -> listOfNotNull(
            wirelessDebuggingPage().takeIf { wirelessDebuggingOn },
            developerOptionsAt(key = WIRELESS_DEBUGGING_KEY),
        )""",
        """        // ⚠ **Three candidates since r4y, and the new one is first.** Shizuku's tile-preferences
        // route asks the Settings app to find this screen instead of naming its activity, which
        // is why its button works on devices where ours fell through to Developer options — the
        // author's report, and his source. See wirelessDebuggingTilePage.
        //
        // ⚠ **Both routes keep the author's r4h condition**: with the setting off that screen
        // holds nothing but the switch he has just come from, so the highlighted Developer
        // options page is the better landing. One `takeIf` each if that should change.
        ManualRevertTarget.WirelessDebugging -> listOfNotNull(
            wirelessDebuggingTilePage().takeIf { wirelessDebuggingOn },
            wirelessDebuggingPage().takeIf { wirelessDebuggingOn },
            developerOptionsAt(key = WIRELESS_DEBUGGING_KEY),
        )""",
    ),
]

IMPORTS = [
    "import android.content.ComponentName",
    "import android.service.quicksettings.TileService",
]

AFTER = [
    ("private fun wirelessDebuggingTilePage(): Intent {", 1),
    ("TileService.ACTION_QS_TILE_PREFERENCES", 1),
    ("Intent.EXTRA_COMPONENT_NAME", 1),
    ("wirelessDebuggingTilePage().takeIf { wirelessDebuggingOn },", 1),
    ("wirelessDebuggingPage().takeIf { wirelessDebuggingOn },", 1),
    # The fallback that was always last is still last, and still ungated.
    ("developerOptionsAt(key = WIRELESS_DEBUGGING_KEY),", 1),
    # ⚠ Not copied from Shizuku, and this is what says so rather than the comment alone.
    # ⚠ Spelled with the `Intent.` only code carries: the bare names appear in the KDoc this
    # same script writes, which is the comment trap in its usual form.
    ("Intent.FLAG_ACTIVITY_CLEAR_TASK", 0),
    ("Intent.FLAG_ACTIVITY_NO_HISTORY", 0),
    ("Intent.FLAG_ACTIVITY_EXCLUDE_FROM_RECENTS", 0),
]


def add_import(text: str, statement: str) -> str:
    if statement in text:
        return text

    lines = text.splitlines(keepends=True)

    indices = [i for i, line in enumerate(lines) if line.startswith("import android")]

    if not indices:
        raise SystemExit(f"REFUSED: nowhere to put {statement!r}")

    target = next((i for i in indices if lines[i] > statement + "\n"), indices[-1] + 1)

    lines.insert(target, statement + "\n")

    return "".join(lines)


def main() -> int:
    path = ROOT / ROUTE

    if not path.is_file():
        print(f"REFUSED: missing {ROUTE}")
        return 1

    text = path.read_text(encoding="utf-8")

    for old, new in EDITS:
        found = text.count(old)

        if found != 1:
            print(f"REFUSED: {ROUTE}\n  {old.strip().splitlines()[0][:70]!r} matched {found} time(s)")
            return 1

        text = text.replace(old, new, 1)

    for statement in IMPORTS:
        text = add_import(text, statement)

    for token, expected in AFTER:
        found = text.count(token)

        if found != expected:
            print(f"REFUSED: {ROUTE}\n  {token!r} occurs {found} time(s), expected {expected}")
            return 1

    # ⚠ **The loop that makes a candidate list mean anything must still be there.** Without it
    # only the first entry would ever be tried, and the two behind it would be decoration.
    for token in (
        "for (candidate in candidates)",
        "startActivity(candidate.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))",
    ):
        if token not in text:
            print(f"REFUSED: {ROUTE}\n  {token!r} is absent; the fallback chain is not tried")
            return 1

    # `TileService` arrived in API 24 and minSdk is 24, so no version guard is needed. Read out
    # of the manifest-level config rather than assumed.
    gradle = (ROOT / "build-logic/convention/src/main/kotlin/com/android/geto/Android.kt").read_text(
        encoding="utf-8",
    )

    if "minSdk = 24" not in gradle:
        print("REFUSED: minSdk is not 24; TileService needs a version guard")
        return 1

    path.write_text(text, encoding="utf-8")

    print(f"  ok        {ROUTE}  :: Shizuku's tile-preferences route, first of three")
    print(f"\nwrote 1 file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
