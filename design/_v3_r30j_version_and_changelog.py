#!/usr/bin/env python3
"""
r30j — v3 gets its number, its F-Droid changelog, and the flowchart loses a stale name.

Three things the author settled in one exchange:

1. **`versionCode 17` / `versionName "3"`.** History: v2.0 = 14, v2.2 = 15, v2.4 = 16, and there
   was never a v2.1 or a v2.3.
2. **`changelogs/17.txt`** — named after the *versionCode*, not the version name, and capped at
   **500 characters**, which is F-Droid's limit and the reason this is asserted rather than eyed.
3. **The flowchart's step 4 said "IMD services manager"** — the name the app stopped using in v3.
   It was in the README's mermaid block, so it was also in the rendered picture and, since r30i,
   on the F-Droid page. One word fixes all three.

⚠ **The changelog file is not the CHANGELOG.md entry.** `CHANGELOG.md` has room to say what v3 did;
this has 500 characters and one job — telling somebody with the update notification open whether
they care. So it is six lines, and the biggest one leads.

⚠ **`CHANGELOG.md` said "not yet released" when this round ran, deliberately** - a version bumped
in the tree is not a version tagged. r30k dated it and wrote the `SUIMD.md` entry that goes with
it, so the coupling assertion below now checks v3 like every other release rather than excepting
it.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

APP = ROOT / "app/build.gradle.kts"
README = ROOT / "README.md"
CHANGELOGS = ROOT / "fastlane/metadata/android/en-US/changelogs"

VERSION_CODE = 17
VERSION_NAME = "3"

FDROID_LIMIT = 500

failures: list[str] = []

writes: dict[Path, str] = {}


def check(condition: bool, message: str) -> bool:
    if not condition:
        failures.append(message)

    return condition


def replace_once(text: str, old: str, new: str, label: str) -> str:
    found = text.count(old)

    if not check(found == 1, f"{label}: found {found}x, expected 1"):
        return text

    return text.replace(old, new, 1)


# ---------------------------------------------------------------- the version

app = APP.read_text(encoding="utf-8")

app = replace_once(app, "versionCode = 16", f"versionCode = {VERSION_CODE}", "versionCode")

app = replace_once(app, 'versionName = "2.4"', f'versionName = "{VERSION_NAME}"', "versionName")

# ⚠ The two must move together. A code bumped without a name ships as "2.4" to every user who
# reads the About screen, and a name bumped without a code cannot be installed as an update.
check(
    f"versionCode = {VERSION_CODE}" in app and f'versionName = "{VERSION_NAME}"' in app,
    "app: the version did not land",
)

check("2.4" not in app, "app: 2.4 survives somewhere in the build file")

writes[APP] = app

# ---------------------------------------------------------------- the flowchart's step 4

readme = README.read_text(encoding="utf-8")

check(
    readme.count("IMD services manager") == 1,
    f"readme: {readme.count('IMD services manager')} 'IMD services manager', expected 1",
)

readme = replace_once(
    readme,
    "homescreen shortcut / IMD services manager)",
    "homescreen shortcut / IMD settings manager)",
    "readme: the flowchart's step 4",
)

check("IMD services manager" not in readme, "readme: the old name survived")

check(
    readme.count("IMD settings manager") == 1,
    "readme: the new name did not land exactly once",
)

writes[README] = readme

# ---------------------------------------------------------------- the F-Droid changelog

ENTRY = """v3

* New: Auto unhide settings - your settings come back on their own when you close the app, lock the screen, or return to IMD.
* Hiding and unhiding are now two separate choices, so a device-wide hide can put back exactly what was there.
* Force-closed with settings still hidden? The next launch offers to restore them.
* You are now told when the Write Secure Settings permission is lost, whichever way you hid.
* Ten languages essentially complete.
* Settings manager rebuilt, plus many fixes.
"""

target = CHANGELOGS / f"{VERSION_CODE}.txt"

check(not target.exists(), f"{target.name} already exists")

check(
    (CHANGELOGS / "16.txt").exists(),
    "changelogs/16.txt is missing — is this the right directory?",
)

length = len(ENTRY.rstrip("\n"))

check(length <= FDROID_LIMIT, f"{target.name}: {length} characters, over F-Droid's {FDROID_LIMIT}")

check(ENTRY.startswith(f"v{VERSION_NAME}\n"), "the changelog does not open with the version name")

# Every other file in this directory opens with its version name. Consistency is the whole reason
# a user can read two of these in a row.
for existing in sorted(CHANGELOGS.glob("*.txt")):
    first = existing.read_text(encoding="utf-8").splitlines()[0].strip()

    check(
        first.startswith("v"),
        f"{existing.name} opens with {first!r} — the convention has drifted",
    )

writes[target] = ENTRY

# ---------------------------------------------------------------- write

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

for path, text in writes.items():
    path.write_text(text, encoding="utf-8")

print(f"version      16 / 2.4  ->  {VERSION_CODE} / {VERSION_NAME}")

print(f"changelog    {target.relative_to(ROOT).as_posix()}  ({length} of {FDROID_LIMIT} chars)")

print("flowchart    'IMD services manager' -> 'IMD settings manager'")

print("\n⚠ re-run design/_v3_r30i_fdroid_description.py — its copy of step 4 is now stale, and its")

print("  own proof against README.md will refuse to write until it is updated.")

print("\nok")
