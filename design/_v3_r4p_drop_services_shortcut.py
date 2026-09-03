#!/usr/bin/env python3
"""v3-r4p — the long-press Settings manager shortcut goes.

    "also remove the settings manager shortcut from imd as we already settings a manger an icon
     on install"

Correct: `AndroidManifest.xml` declares `.activity.services.SettingsManagerLauncher`, an
activity-alias with `MAIN`/`LAUNCHER`, so installing IMD already puts a **Settings manager**
entry in the launcher with its own icon and label. The static shortcut in `shortcuts.xml` opened
the same `ServicesActivity` from a long press on IMD's own icon - a second door to a room that
now has its own.

## ⚠ What is deliberately left alone

* **The activity-alias.** It is the icon the author is keeping.
* **`ServicesActivity`'s `exported="true"`.** The tile, the IMD intent and any pinned shortcut a
  user has already made all reach it, and unexporting it would break those.
* **`@string/services_shortcut_label` and `@mipmap/ic_services`.** Both are still used, by the
  alias - `check20_resrefs` would call a removal of either a missing reference.
* **The revert shortcut.** Untouched, and asserted so: the two blocks are the same shape and a
  loose match would take the wrong one.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SHORTCUTS = "app/src/main/res/xml/shortcuts.xml"

MANIFEST = "app/src/main/AndroidManifest.xml"

OLD = """    <shortcut
        android:shortcutId="imd_services"
        android:enabled="true"
        android:icon="@mipmap/ic_services"
        android:shortcutShortLabel="@string/services_shortcut_label"
        android:shortcutLongLabel="@string/services_shortcut_label">
        <intent
            android:action="android.intent.action.VIEW"
            android:targetPackage="com.soul_99.suIMD"
            android:targetClass="com.android.geto.activity.services.ServicesActivity" />
    </shortcut>

    <shortcut
        android:shortcutId="imd_revert_to_default\""""

NEW = """    <shortcut
        android:shortcutId="imd_revert_to_default\""""

# The comment above the list explained why the shortcuts are static. It still applies to the
# one that is left, so it stays - but it said "it" of a pair, and now there is one.
OLD_NOTE = """      Static rather than dynamic: it never changes, so there is nothing for the app to
      keep in sync, and a static shortcut is present from install without the app having
      to have been opened first."""

NEW_NOTE = """      Static rather than dynamic: it never changes, so there is nothing for the app to
      keep in sync, and a static shortcut is present from install without the app having
      to have been opened first.

      ⚠ The Settings manager shortcut that used to sit above this one is gone, at the
      author's instruction: the SettingsManagerLauncher activity-alias in the manifest
      already puts a Settings manager entry in the launcher on install, so a long-press
      shortcut to the same ServicesActivity was a second door to the same room."""

# Must survive.
KEPT_MANIFEST = [
    '<activity-alias\n            android:name=".activity.services.SettingsManagerLauncher"',
    'android:icon="@mipmap/ic_services"',
    'android:label="@string/services_shortcut_label"',
]

KEPT_SHORTCUTS = [
    'android:shortcutId="imd_revert_to_default"',
    "com.android.geto.activity.revert.RevertActivity",
]

GONE = ['android:shortcutId="imd_services"', "activity.services.ServicesActivity"]


def main() -> int:
    shortcuts = ROOT / SHORTCUTS

    manifest = ROOT / MANIFEST

    for path in (shortcuts, manifest):
        if not path.is_file():
            print(f"REFUSED: missing {path.relative_to(ROOT)}")
            return 1

    text = shortcuts.read_text(encoding="utf-8")

    for old in (OLD, OLD_NOTE):
        found = text.count(old)

        if found != 1:
            head = old.strip().splitlines()[0][:70]

            print(f"REFUSED: {SHORTCUTS}\n  {head!r} matched {found} time(s), expected 1")
            return 1

    staged = text.replace(OLD, NEW, 1).replace(OLD_NOTE, NEW_NOTE, 1)

    # ⚠ Counted on the closing tag, not on "<shortcut" - which is also a prefix of the root
    # element "<shortcuts", so the first draft counted the document itself as a shortcut and
    # refused. The assertion was right; the token was not.
    if staged.count("</shortcut>") != 1:
        print(
            f"REFUSED: {SHORTCUTS}\n  {staged.count('</shortcut>')} shortcut(s) left, expected "
            f"exactly 1",
        )
        return 1

    if staged.count("    <shortcut\n") != 1:
        print(f"REFUSED: {SHORTCUTS}\n  the remaining shortcut does not open exactly once")
        return 1

    for token in KEPT_SHORTCUTS:
        if token not in staged:
            print(f"REFUSED: {SHORTCUTS}\n  the revert shortcut lost {token!r}")
            return 1

    for token in GONE:
        if token in staged:
            print(f"REFUSED: {SHORTCUTS}\n  {token!r} survives the removal")
            return 1

    # ⚠ Read, never written. The alias is the icon the author is keeping, and the label and
    # mipmap the removed shortcut used are still referenced from it.
    manifest_text = manifest.read_text(encoding="utf-8")

    for token in KEPT_MANIFEST:
        if token not in manifest_text:
            print(f"REFUSED: {MANIFEST}\n  {token.splitlines()[0]!r} is absent")
            return 1

    shortcuts.write_text(staged, encoding="utf-8")

    print(f"  ok        {SHORTCUTS}  :: Settings manager shortcut removed, revert kept")
    print(f"  ok        {MANIFEST}  :: SettingsManagerLauncher alias untouched")
    print("\nwrote 1 file(s), 2 edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
