#!/usr/bin/env python3
"""
r30k — v3 stops being unreleased: it gets a date, and SUIMD.md gets its version-history entry.

The author: *"please remove not yet released from documentation, like changelog"*.

## The two are one edit

`CHANGELOG.md` said **v3 - not yet released**, and `SUIMD.md § 3` had no v3 section at all. Those
were the same fact written twice, which is why r30d asserted them against each other. Dating one
without writing the other would leave the release checklist's step 2 undone and that assertion
lying, so both move here.

⚠ **The date is the author's own release day, not the day the code was written.** The rounds ran
across late August and early September; the release is dated the day it is tagged, exactly as
v2.4's entry is dated 28 August rather than spread across the week that produced it.

## The § 3 entry

Written in the section's own voice and to its own shape — a lead paragraph saying what the release
*is*, then **Added** / **Changed** / **Fixed** / **Broke**, with the reasoning kept rather than
summarised away. `CHANGELOG.md` is where v3 is told to users; this is where it is told to whoever
next has to change the code, so the two say different things about the same release on purpose.

**Broke** carries the four failed builds from r29 verbatim in kind: the section's preamble promises
that anything under it was found by the author testing on his own device, and three of these were
found by him and one by aapt2 refusing the resource table.

Computes both documents in memory, asserts, writes nothing if any assertion fails.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CHANGELOG = ROOT / "CHANGELOG.md"
SUIMD = ROOT / "SUIMD.md"
APP = ROOT / "app/build.gradle.kts"

DATE = "3 September 2026"
VERSION_CODE = 17

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


ENTRY = f"""### v3 - {DATE} · versionCode {VERSION_CODE}

The release where IMD stops needing to be told. Every version before this one hid settings because
somebody pressed something - a tile, a shortcut, a row in the app - and put them back the same way.
v3 adds the other half at both ends: **auto unhide settings** ends a hide without a press, and
**auto hide settings (IMD+)**, begun in v2.4, is now reliable enough to be one of three automations
rather than an experiment.

It is also the release that stopped treating hiding and unhiding as one setting, which is the
change most of the rest of this entry follows from.

**Added - Auto unhide settings**

A hide now ends on its own. The watcher takes one of three signals - the app you launched being
closed, the screen locking, or your returning to IMD - and reverts when it sees one, with a silent
ongoing notification saying it is running and going away when everything is back.

- **The notification cannot be swiped off.** It is the only visible sign that the device is not as
  you left it; a user who dismisses it and forgets has no way of knowing. It comes back while the
  session is live.
- **It ticks every 5 seconds while the screen is on and every 30 while it is off.** The revert
  wants to be prompt, and a poll in a pocket wants to be cheap; those are different numbers, so it
  is two.
- ⚠ **A session kind the user has switched off settles rather than waiting.** The gate was right
  from the start but its disallowed branch answered "not settled", so the service stayed up and
  reached the same line every fifteen seconds for the whole hidden window. Answering "settled" is
  correct because the answer cannot change: the kind is fixed the moment the hide names an app or
  does not.

**Added - hiding and unhiding are two frameworks**

*Hiding-unhiding mechanism* is gone, replaced by a **hiding framework** (IMD defaults, or per app
configuration) and an **unhiding framework** (revert to default, or memory function), both at the
top of Advanced and each row reading *using X*.

- ⚠ **This is the fix for a bug, not only a preference.** Hiding device-wide on the memory function
  used to apply the *configured defaults* on the way back rather than restoring what the device
  actually was - so on a new install, every tile hide put back something nobody had chosen. The
  device-wide hide now records real state, and the revert is carried out by **the framework that
  did the hide**, not by whichever one is selected when the revert runs.
- Existing setups migrate without being asked: *revert to default* becomes IMD defaults + revert to
  default, *memory* becomes per app configuration + memory function. New installs start on IMD
  defaults + memory function.
- A revert now also restores anything a per-app profile hid that is not one of the six default
  targets, before the defaults are applied.

**Added - recovering from a force close**

If IMD is force-stopped while settings are still hidden, the next launch offers to restore them
first or to ignore every outstanding revert - on all six ways in: the apps list, favourites, the
per-app screen, a pinned shortcut, IMD+, and opening IMD itself. A spinner covers the restore, one
per window.

⚠ **The dialog cannot be dismissed by a back press or a tap beside it.** Both used to run the
destructive answer, which discarded real holds - the one dialog in the app where the cheapest
gesture was the irreversible one.

**Added - the permission is reported when it goes**

Losing `WRITE_SECURE_SETTINGS` used to be silent on a shortcut hide, swallowed by IMD+, and a dead
switch in the settings manager. It is now a popup on every route that can hide - both in-app
launches, the tile, the pinned shortcut, IMD+, the manager, and a notification for IMD intents -
and anything that run had already hidden is undone.

⚠ **A popup rather than IMD coming to the foreground.** The failure happens while you are in
another app; dragging IMD over it to deliver the news is worse than the news.

**Changed - the settings manager**

Renamed **IMD Settings Manager**, and rebuilt around it: a frosted window, Material 3 switches with
a hand-drawn tick, the whole row tappable rather than only the switch, **All on / All off**, a red
line while a revert is outstanding, external-link icons on the rows that have an Android page, a
**Manage Shizuku** master switch that removes the Shizuku and overlay rows on a device without it,
and a countdown while the Shizuku service starts - 8 seconds on Thedjchi, 40 on Shevery.

Rows are locked while any hide or revert runs, with a line above them saying which. They were
pressable during an IMD+ run, a shortcut launch or a notification revert, which let a user write
into the middle of a write.

**Changed - the words**

*IMD services manager* → **IMD Settings Manager** (tile and shortcut: *Settings manager*); the
first-run screen reads **IMD - It's My Device**; IMD+ is **(needs background service)** rather than
EXPERIMENTAL; **IMD intents** dropped its EXPERIMENTAL tag; and the About page says **Supercharged
fork of** rather than *Fork of*.

**Changed - the other ten languages**

About 1,500 strings written across Hindi, Arabic, Portuguese (BR), Simplified Chinese, German,
Spanish, French, Japanese, Korean and Russian, taking each locale from roughly 80% to essentially
complete.

⚠ **The in-app "where to find this" trails are assembled, not translated.** Each row is named
exactly as that language's own Android settings screen names it, and the trail is built from those
names - Arabic with the right-to-left arrow and the app name second. A translated *sentence*
describing a path is not a path.

⚠ **The six Shizuku setup step lines stay in English on purpose.** They are read against Shizuku's
own settings screen, which is English-only.

**Changed - the look and the cost**

Dynamic (wallpaper) colour and progressive blur are both on by default; anyone who had turned
either off gets it back once and their next choice sticks. The dark theme's `primary` moved from
`#B3E675` to `#8FAE6E` - the old one was a yellow-green at high lightness *and* high chroma, which
is the definition of a highlighter, and six switch tracks stacked in one dialog was where it showed.
The settings manager's two buttons and the Favourites manager button moved onto that same `primary`;
there had been three greens.

Scrolling the settings page no longer re-runs the whole body every frame, and the blurred header's
effect graph is cached rather than rebuilt per draw.

**Fixed**

- **The IMD+ open-and-close loop.** A hide that could not complete left IMD+ killing and relaunching
  the app forever. It now tries once, then waits 1 minute, then 5, then 30; a success clears the
  wait, and switching IMD+ off and on clears it immediately.
- **Revert to default restored three of its six targets.**
- **Auto unhide reverts were cut short** - the settings were written, the notification never cleared
  and no toast appeared.
- A device-wide memory revert restored whatever was true at the *first* hide, for ever; the record
  is now cleared by the revert that used it.
- A hide from the tile with the quick-settings trigger on and the screen-lock trigger off could
  never be reverted, and its service never stopped.
- Accessibility services and *Display over other apps* could be stuck off in the manager, doing
  nothing when switched on by hand, when IMD held no record.
- The tile could show a stale label, get stuck after a hide, or flash the wrong label on the way
  through a revert; it is now told about hides and reverts that happen outside the shade.
- A Shevery wait died when its dialog was dismissed; a Shizuku row that was still starting opened
  the *unavailable* dialog.
- Settings screens open on more devices - IMD tries a list of candidate destinations rather than one.
- Creating a shortcut by long press no longer hangs silently; a Retry appears after 8 seconds.
- Legacy-style app icons showed a hairline along their bottom and right edges - a float `RectF`
  whose half-pixel edges the rasteriser rounded inward on exactly two sides.
- Three separate bugs with the switch tick, all one cause.

**Broke**

Four builds failed on the author's machine during r29, and each one is a lesson worth keeping:

- **`androidx.baselineprofile:1.5.0` does not exist.** The version was guessed and shipped flagged
  but unverified. 1.4.1 is stable and **1.5.0-rc02** heads the 1.5 line; the RC is pinned
  deliberately, because the 1.5 notes say it no longer needs `newDsl=false` under AGP 9.
- **A child project may not name a version for a plugin already on the root classpath.** build-logic
  puts AGP there as a plain dependency, so `com.android.test` must be applied by bare id - which
  every one of the other twenty-nine modules already did, evidence that was in the repo and unread.
- **aapt2 refused the whole resource table** over `values-fr.xml`: `Services d\\\\'accessibilité`.
  ElementTree resolves XML entities but knows nothing of Android's backslash escapes, so a value
  read back out of an already-translated file still carried its `\\'` and the writer escaped it
  twice. Fixed at the read/write asymmetry, and `check_escapes()` in `tools/check_translations.py`
  now reads the raw file, because every existing check went through ElementTree and none of them
  could see it.

⚠ **The baseline profile has never been generated.** The module and the wiring are here and
`assembleRelease` succeeds without a profile, so the APK simply ships without one. It needs one run
on a device - see `baselineprofile/README.md` - and the output committed.

⚠ **Arabic still renders `%1$d` as ٠١٢.** `Resources.getString` formats against the config locale
and `ar` carries the `arab` numbering system, so the digits are substituted after the string is
built. Fixing it is a change at each call site, touching strings that have already shipped.

"""

# ---------------------------------------------------------------- CHANGELOG.md

changelog = CHANGELOG.read_text(encoding="utf-8")

changelog = replace_once(
    changelog,
    "## v3 - not yet released",
    f"## v3 - {DATE}",
    "changelog: the v3 heading",
)

check("not yet released" not in changelog, "changelog: the marker survives somewhere")

writes[CHANGELOG] = changelog

# ---------------------------------------------------------------- SUIMD.md § 3

suimd = SUIMD.read_text(encoding="utf-8")

check("### v3 " not in suimd, "suimd: a v3 entry already exists")

check(
    suimd.count("### v2.4 - 28 August 2026 · versionCode 16") == 1,
    "suimd: the v2.4 heading is not where it was",
)

suimd = replace_once(
    suimd,
    "### v2.4 - 28 August 2026 · versionCode 16",
    ENTRY + "### v2.4 - 28 August 2026 · versionCode 16",
    "suimd: the v3 entry",
)

# Newest first is the section's only rule, and § 3 must still open on the preamble.
check(
    suimd.index("## 3. Version history")
    < suimd.index(f"### v3 - {DATE}")
    < suimd.index("### v2.4 - 28 August 2026"),
    "suimd: v3 is not between the preamble and v2.4",
)

check(
    suimd.index(f"### v3 - {DATE}") < suimd.index("## 4. Licence and attribution"),
    "suimd: v3 landed outside section 3",
)

writes[SUIMD] = suimd

# ---------------------------------------------------------------- the three must agree

app = APP.read_text(encoding="utf-8")

check(f"versionCode = {VERSION_CODE}" in app, f"app: versionCode is not {VERSION_CODE}")

check('versionName = "3"' in app, "app: versionName is not 3")

check(
    (ROOT / f"fastlane/metadata/android/en-US/changelogs/{VERSION_CODE}.txt").exists(),
    f"fastlane: changelogs/{VERSION_CODE}.txt is missing",
)

# ⚠ r30d's coupling, re-run here. Every dated heading in CHANGELOG.md must match SUIMD.md to the
# day - and v3 is now dated, so it is checked like every other release rather than excepted.
for version, date in re.findall(r"\n## (v[\d.]+) - ([^\n]+)\n", changelog):
    check(
        f"### {version} - {date} ·" in suimd or f"### {version} - {date}\n" in suimd,
        f"changelog: {version} is dated {date}, which is not what SUIMD.md says",
    )

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

for path, text in writes.items():
    path.write_text(text, encoding="utf-8")

print(f"CHANGELOG.md  v3 - not yet released  ->  v3 - {DATE}")

print(f"SUIMD.md      + {len(ENTRY.splitlines())} lines: v3 - {DATE} · versionCode {VERSION_CODE}")

print("ok")
