#!/usr/bin/env python3
"""r4b — a second launcher icon, so installing IMD puts 'Settings manager' beside it.

The author: *"when IMD app is installed it install two apps in android app launcher one for IMD
and one for Settings manager."*

### An `activity-alias`, not a second activity

`ServicesActivity` already exists, is already exported, already carries
`@string/services_shortcut_label` and already draws `SettingsManagerRoute`. What it lacks is a
`MAIN` / `LAUNCHER` filter — and adding one to the activity itself would give the QS tile and the
pinned shortcut a launcher entry as a side effect of what they are, rather than as a decision.

An alias is the platform's own answer to "the same screen, a second door": it is a manifest entry
with its own label, icon and filter, pointing at an activity that stays exactly as it was. It can
also be enabled or disabled at runtime later, which a hard-coded second launcher activity cannot.

⚠ **Declared after its target.** The platform resolves `targetActivity` against what it has
already read, so an alias above its activity does not build.

⚠ **No new artwork, and that is deliberate.** `@mipmap/ic_services` is a complete adaptive icon —
foreground and monochrome — and is already what the launcher shows for the pinned Settings
manager shortcut. Reusing it means the new icon is one the user has already seen standing for
this screen, and it means this change needs no template: the author's rule about showing anything
visual first is about **new** artwork, and there is none here.

⚠ **The alias inherits `excludeFromRecents` and `taskAffinity=""` from its target.** Both are
right for a launcher entry onto a dialog: it opens in a task of its own and does not linger in
recents after it is dismissed, which is how the tile and the shortcut already behave.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MANIFEST = "app/src/main/AndroidManifest.xml"

ALIAS = """
        <!--
          The second launcher icon, at the author's instruction: installing IMD puts two entries
          in the launcher, one for the app and one for the Settings manager.

          An activity-alias rather than a second activity, because ServicesActivity is already
          exactly this screen and already exported for the tile and the pinned shortcut. The
          alias adds a door with its own label and icon and changes nothing about the room.

          ⚠ Declared after its target: targetActivity is resolved against what the platform has
          already read, so an alias above its activity does not build.

          The icon is the one the pinned Settings manager shortcut already uses, so the launcher
          entry looks like the thing it opens rather than like a second copy of IMD.
        -->
        <activity-alias
            android:name=".activity.services.SettingsManagerLauncher"
            android:exported="true"
            android:icon="@mipmap/ic_services"
            android:label="@string/services_shortcut_label"
            android:targetActivity=".activity.services.ServicesActivity">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />

                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity-alias>
"""

EDITS: list[tuple[str, list[tuple[str, str, int]]]] = [
    (MANIFEST, [
        (
            """        <activity
            android:name=".activity.services.ServicesActivity"
            android:exported="true"
            android:excludeFromRecents="true"
            android:label="@string/services_shortcut_label"
            android:launchMode="singleTop"
            android:taskAffinity=""
            android:theme="@style/Theme.Geto.Services" />
""",
            """        <activity
            android:name=".activity.services.ServicesActivity"
            android:exported="true"
            android:excludeFromRecents="true"
            android:label="@string/services_shortcut_label"
            android:launchMode="singleTop"
            android:taskAffinity=""
            android:theme="@style/Theme.Geto.Services" />
""" + ALIAS,
            1,
        ),
    ]),
]


def main() -> int:
    staged: dict[Path, str] = {}
    problems: list[str] = []

    for rel, subs in EDITS:
        path = ROOT / rel

        if not path.exists():
            problems.append(f"{rel}: missing")

            continue

        text = path.read_text(encoding="utf-8")

        for old, new, expected in subs:
            found = text.count(old)

            if found != expected:
                problems.append(
                    f"{rel}: expected {expected} of "
                    f"{old.strip().splitlines()[0][:58]!r}, found {found}",
                )

                continue

            text = text.replace(old, new, expected)

        staged[path] = text

    manifest = staged.get(ROOT / MANIFEST, "")

    # Exactly two launcher entries now, and the alias must sit below its target.
    if manifest.count("android.intent.category.LAUNCHER") != 2:
        problems.append(f"{MANIFEST}: expected exactly two LAUNCHER categories")

    target = manifest.find('android:name=".activity.services.ServicesActivity"')
    alias = manifest.find('android:name=".activity.services.SettingsManagerLauncher"')

    if target < 0 or alias < 0 or alias < target:
        problems.append(f"{MANIFEST}: the alias is not declared after its target activity")

    # The icon has to exist, or the launcher entry is a build failure rather than a plain one.
    icons = list((ROOT / "app/src/main/res").glob("mipmap-*/ic_services.xml"))

    if not icons:
        problems.append("app/src/main/res: @mipmap/ic_services is missing")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")
        print(f"  wrote {path.relative_to(ROOT)}")

    print("ok - a second launcher entry for the Settings manager, reusing its own icon")

    return 0


if __name__ == "__main__":
    sys.exit(main())
