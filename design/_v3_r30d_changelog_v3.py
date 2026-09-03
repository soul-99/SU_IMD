#!/usr/bin/env python3
"""
r30d — v3 goes to the top of CHANGELOG.md.

The author: *"build changelog upto v3"*.

## Where this came from

Not from memory. The v3 rounds are documented across nine handovers plus the round notes, and all
of it was read back and filtered to one question: **would somebody using the app notice this?**
Everything that only a person reading the source would notice — module direction, recomposition
counts, script assertions, host-test totals, the checkers — is out. What is left is grouped New /
Improved / Fixed like every other entry in this file, and cut to one line each.

⚠ **No date and no version code, when this round ran.** The tree still said
`versionCode 16 / versionName 2.4` and `SUIMD.md § 3` had no v3 section, so the entry said
"not yet released" rather than inventing a day, and the date cross-check below had to know about
that one case. r30j gave v3 its number and r30k its date and its `SUIMD.md` entry; the exception
is gone.

⚠ **Two things are deliberately not claimed.** The baseline profile added in r29 was wired up but
never generated on a device, so there is no startup-speed line here. And Arabic still renders
numbers as ٠١٢ despite the strings using Western digits — an open bug, not an improvement, and it
belongs in the release notes only once it is settled.

Computes the whole file in memory, asserts, writes nothing if any assertion fails.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CHANGELOG = ROOT / "CHANGELOG.md"

failures: list[str] = []


def check(condition: bool, message: str) -> bool:
    if not condition:
        failures.append(message)

    return condition


ENTRY = """## v3 - not yet released

The largest release since the fork, and the one that stops IMD being a thing you drive by hand.

**New**

- **Hiding and unhiding are now two separate choices.** *Hiding framework* (IMD defaults or Per app
  configuration) and *Unhiding framework* (Revert to default or Memory function) replace the single
  *Hiding-unhiding mechanism*, so you can hide from one device-wide list and still have your own
  settings put back exactly as they were. Existing setups are migrated for you.
- **If IMD is force-closed while your settings are still hidden**, the next launch offers to
  restore them first - from any of the six ways in, with a spinner while it works.
- **A popup when the Write Secure Settings permission has been lost**, on every route that can hide:
  the tile, both in-app launches, the pinned shortcut, IMD+, the settings manager and IMD intents.
  Anything that run had already hidden is undone.
- **All on / All off** in the settings manager, for switching every usable row at once.
- **Manage Shizuku**, a master switch that takes the Shizuku and Display-over-other-apps rows out of
  the manager entirely on a device that has no Shizuku.
- **Restore wireless debugging also** - a checkbox under Wireless debugging, for the memory
  framework.
- A **countdown while the Shizuku service starts**, so a wait no longer looks like a hang.
- A **Back button in the setup flow**, and eleven settings rows that open a page now carry an icon.
- A new IMD intents action, **Unhide settings and services**.
- The settings manager shows a **red line while a revert is still outstanding**, and a grey IMD
  button that opens IMD's own settings.

**Improved**

- **Ten languages are now essentially complete** - about 1,500 strings written across Hindi,
  Arabic, Portuguese (BR), Simplified Chinese, German, Spanish, French, Japanese, Korean and
  Russian. The in-app *where to find this setting* trails now name each row exactly as that
  language's own Android settings screen labels it, and Arabic reads right to left properly.
- **The settings manager was rebuilt**: a frosted window, Material 3 switches with a hand-drawn
  tick, the whole row tappable rather than just the switch, one width rule shared with every other
  dialog, and rows locked with a reason while a hide or revert is running.
- **Auto unhide is quicker and quieter** - it checks every 5 seconds while the screen is on and
  every 30 while it is off, and its notification cannot be lost by a swipe.
- **The Hide settings tile keeps the shade open** for the whole operation so you can see it work,
  says *Unhiding settings…* during a revert, and is correct the next time you open the shade even
  if the hide happened somewhere else.
- **Every hide and unhide ends with a toast that names what actually happened**, and the failure
  toasts that said nothing useful are gone.
- **Renames**: *IMD services manager* is now **IMD Settings Manager**, the first-run screen reads
  **IMD - It's My Device**, IMD+ is **IMD+ (needs background service)** rather than EXPERIMENTAL,
  and **IMD intents** has dropped its EXPERIMENTAL tag.
- Both pickers refresh when you come back from Android's settings without closing, and list only
  what is relevant instead of everything installed.
- **Dynamic (wallpaper) colours and progressive blur are both on by default.**
- **Scrolling the Settings page is smoother**, and the blurred header is cheaper to draw.
- Settings screens open on more devices - IMD now tries a list of destinations rather than one.
- A revert is carried out by the framework that did the hide, not by whichever one is set now.
- On a Shevery install the manager rows are named for Shevery, and a failed start says Shevery.
- The About page now reads **Supercharged fork of Geto**, with a *Long live FOSS !* footer and a
  *view Project on GitHub* button beside Share.

**Fixed**

- **The IMD+ open-and-close loop.** When a hide could not complete, IMD+ killed and relaunched the
  app over and over. It now tries once, then waits 1 minute, then 5, then 30; a success clears the
  wait.
- **A device-wide hide on the Memory function applied the configured defaults instead of putting
  back what was actually there** - on a new install that was every tile hide. Fixed on the
  notification, the IMD+ and the Favourites paths.
- **Revert to default was only restoring three of its six targets.**
- **Auto unhide reverts were being cut short** - the settings were written but the notification
  never cleared and no toast appeared.
- A hide started from the tile with the quick-settings trigger on and the screen-lock trigger off
  could never be reverted, and its service never stopped.
- A device-wide memory revert restored whatever was true at the very first hide, for ever.
- A failed hide from a pinned shortcut was completely silent; IMD+ swallowed the same failure, and
  the settings manager's row was a dead switch.
- Accessibility services and Display over other apps could be stuck off in the manager and do
  nothing when switched on by hand.
- The force-close popup could be dismissed by a back press, which ran the destructive answer.
- A Shevery wait no longer dies when its dialog is dismissed, and a Shizuku row that is still
  starting no longer opens the *unavailable* dialog.
- Creating a shortcut by long press no longer hangs silently - a Retry appears after 8 seconds.
- Legacy-style app icons no longer show a faint hairline along two edges, and three separate bugs
  with the switch tick are gone.

"""

text = CHANGELOG.read_text(encoding="utf-8")

check("## v3" not in text, "changelog: a v3 entry already exists")

check("\n## v2.4 - 28 August 2026\n" in text, "changelog: the v2.4 heading is not where it was")

updated = text.replace("## v2.4 - 28 August 2026", ENTRY + "## v2.4 - 28 August 2026", 1)

check(
    updated.count("## v2.4 - 28 August 2026") == 1,
    "changelog: v2.4 was duplicated",
)

# v3 goes above v2.4 and below the preamble, and nowhere else. Newest first is the file's only rule.
check(
    updated.index("## v3 - not yet released") < updated.index("## v2.4 - 28 August 2026"),
    "changelog: v3 is not above v2.4",
)

check(
    updated.index("# Changelog") < updated.index("## v3 - not yet released"),
    "changelog: v3 landed above the title",
)

# ⚠ The date cross-check from r30c, re-run here so a prepend cannot slip past it — with the one
# allowance this entry needs, spelled out rather than left as a hole.
suimd = (ROOT / "SUIMD.md").read_text(encoding="utf-8")

for version, date in re.findall(r"\n## (v[\d.]+) - ([^\n]+)\n", updated):
    if version == "v3":
        check(
            date == "not yet released" and f"### v3 - " not in suimd,
            "changelog: v3 is dated, or SUIMD.md has gained a v3 section - reconcile them",
        )

        continue

    check(
        f"### {version} - {date} ·" in suimd or f"### {version} - {date}\n" in suimd,
        f"changelog: {version} is dated {date}, which is not what SUIMD.md says",
    )

# Every entry in the file carries at least one of the three groups, and v3 carries all three.
for group in ("**New**", "**Improved**", "**Fixed**"):
    check(
        group in ENTRY,
        f"changelog: v3 has no {group} group",
    )

# The tag went in r30a. A document written after it must not put it back as anything but the name
# of the thing that was removed.
check(
    ENTRY.count("EXPERIMENTAL") == 2,
    f"changelog: {ENTRY.count('EXPERIMENTAL')} EXPERIMENTAL, expected 2 (both saying it is gone)",
)

# ⚠ Neither of these may be claimed - see the module docstring.
for claim in ("baseline profile", "starts faster", "startup"):
    check(
        claim not in ENTRY.lower(),
        f"changelog: v3 claims {claim!r}, which was never measured on a device",
    )

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

CHANGELOG.write_text(updated, encoding="utf-8")

print(f"CHANGELOG.md {len(text.splitlines())} -> {len(updated.splitlines())} lines")

print("ok")
