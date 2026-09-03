#!/usr/bin/env python3
"""
r30b — SUIMD.md section 2 catches up with the diagrams it introduces.

The pictures were rewritten in `tools/logics/build_logics.py` after a line-by-line audit. The
prose around them had drifted the same way and in some places says the opposite of what the code
does, so this corrects it, renames the two sections whose features were renamed, and adds **2.15
Auto unhide settings** for the diagram that did not exist before.

## What was actually wrong in the prose

* **2.1** — *"an overlay step that fails cancels the launch and leaves the device untouched"*. Only
  half true, and the wrong half is the reassuring one: a failed *Shizuku start* touches nothing, but
  a failed *AppOp write* happens after the start, and that start is **not** rolled back.
* **2.5** — *"cycling USB debugging is the one that always works, and the only one that warns you"*.
  Both clauses are dead. It is not a fallback (both transports drop unconditionally, right after the
  stop intent), and nothing warns: the notifier is `@Deprecated` with no consumer in the app.
* **2.7** — *"only the ones that were actually on are claimed"*. The claim also takes services
  already held by another profile, deliberately, so that profile's revert cannot bring one back
  in the middle of a hide.
* **2.8** — *"ten silent seconds"*. The budget is per fork: 8 s on Thedjchi, 40 s on Shevery.
* **2.9** — titled *"IMD services manager"*. The app calls it the **Settings manager** everywhere.
* **2.11** — titled *"Tasker / MacroDroid triggers"* and described as *"Experimental"*. It is
  **IMD intents**, and r30a removed the experimental tag at the author's instruction.
* **2.3 / 2.4** — titled for *"the Memory function"*, which v3 split into a **hiding framework**
  (Per app configuration) and an **unhiding framework** (Memory). The section titles now name the
  framework that actually reaches them.

⚠ **The intro's promise is kept rather than dropped.** It says these are current with each release;
it was not true, and the honest fix is to make it true and say when they were last checked, not to
soften the sentence.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SUIMD = ROOT / "SUIMD.md"
LOGICS = ROOT / "docs" / "logics"

failures: list[str] = []


def check(condition: bool, message: str) -> bool:
    if not condition:
        failures.append(message)

    return condition


def replace_once(text: str, old: str, new: str, label: str) -> str:
    found = text.count(old)

    if not check(found == 1, f"{label}: found {found}x, expected 1"):
        return text

    return text.replace(old, new, 1)


doc = SUIMD.read_text(encoding="utf-8")

# ---------------------------------------------------------------- the intro

doc = replace_once(
    doc,
    "These are kept current with each release - when a logic changes, the picture changes with it.\n"
    "\n"
    "Each picture is rendered from a mermaid definition in `tools/logics/`, so a change to a logic\n"
    "is a change to text rather than to a drawing.\n",
    "Each picture is rendered from a mermaid definition in `tools/logics/`, so a change to a logic\n"
    "is a change to text rather than to a drawing. **All fifteen were re-read against the code in\n"
    "r30**, which is when the last of the drift was taken out of them - the second Shizuku fork had\n"
    "reached thirty-two source files without appearing in a single drawing.\n"
    "\n"
    "Two colours carry meaning. A **red** box is where a run stops. A **green** box is a branch that\n"
    "exists only on the **Shevery** fork, which starts and stops its service in a completely\n"
    "different way from Thedjchi's and cannot manage Display over other apps on a launch at all.\n",
    "intro: the currency claim and the colour key",
)

# ---------------------------------------------------------------- 2.1

doc = replace_once(
    doc,
    "this one is wrong. Note where it can stop: an overlay step that fails cancels the launch and\n"
    "leaves the device untouched, because half-hidden is the worst outcome available - the app\n"
    "still detects whatever is left on, and your device has been changed anyway.\n",
    "this one is wrong. Note where it can stop: an overlay step that fails cancels the launch,\n"
    "because half-hidden is the worst outcome available - the app still detects whatever is left\n"
    "on, and your device has been changed anyway.\n"
    "\n"
    "⚠ **Two of those stops are not equal, and the diagram distinguishes them.** A Shizuku start\n"
    "that never succeeds has touched nothing. An AppOp write that is *refused* happens after that\n"
    "start, and the start is not rolled back - so on that path the service may be left running when\n"
    "it was not before. Only a failure later in the loop, with the grant gone, reverses the whole\n"
    "run.\n",
    "2.1: the overlay stop",
)

# ---------------------------------------------------------------- 2.3 / 2.4 titles

doc = replace_once(
    doc,
    "### 2.3 Per-app profile - the Memory function\n"
    "\n"
    "The precise tool: one profile per app, applied on launch. What it records is the point - the\n"
    "values your device really had, not the values the profile guessed it would have.\n",
    "### 2.3 Per app configuration - applying a profile\n"
    "\n"
    "The precise tool: one profile per app, applied on launch, and what reaches it is the **hiding\n"
    "framework** set to *Per app configuration*. What it records is the point - the values your\n"
    "device really had, not the values the profile guessed it would have - and it records them only\n"
    "where this app is the first to move a setting away from that value, so two apps cannot each\n"
    "claim to have found it in a different state.\n",
    "2.3: the title and blurb",
)

doc = replace_once(
    doc,
    "### 2.4 Revert using memory\n"
    "\n"
    "The counterpart, and the one place the app's memory is spent. Note the Shizuku branch: only an\n"
    "app that actually took a running service down puts it back, so the memory never cumulates\n"
    "across apps.\n",
    "### 2.4 Per app configuration - reverting a profile\n"
    "\n"
    "The counterpart, and the one place the app's memory is spent. Note the overlay branch: only the\n"
    "app that actually withdrew overlay access gives it back, so a second app that found it already\n"
    "withdrawn does not hand back something it never took.\n",
    "2.4: the title and blurb",
)

# ---------------------------------------------------------------- 2.5

doc = replace_once(
    doc,
    "fork's watchdog can restart the service mid-session, and starting the service turns ADB back on\n"
    "- which is exactly the state a locked-down app is looking for. The stop intent is the polite\n"
    "route; cycling USB debugging is the one that always works, and the only one that warns you.\n",
    "fork's watchdog can restart the service mid-session, and starting the service turns ADB back on\n"
    "- which is exactly the state a locked-down app is looking for.\n"
    "\n"
    "⚠ **The transports are not a fallback.** The stop intent goes first, and then USB and wireless\n"
    "debugging come down anyway - the service cannot outlive the transport it rides on, so this is\n"
    "the part that actually does the work. There is no confirmation poll: v3 removed it. And on\n"
    "**Shevery** nothing is sent at all, because that fork has no intents to send.\n",
    "2.5: the stop mechanism",
)

# ---------------------------------------------------------------- 2.7

doc = replace_once(
    doc,
    "Only the services you picked in IMD settings are ever touched, and only the ones that were\n"
    "actually on are claimed - so a revert can never switch on something you disabled yourself.\n",
    "Only the services you picked in IMD settings are ever touched - so a revert can never switch on\n"
    "something you disabled yourself.\n"
    "\n"
    "⚠ **The claim is wider than \"what was on\".** It also takes a service already held by another\n"
    "profile, on purpose: without that, the other profile's revert could switch one back on in the\n"
    "middle of a hide. And a device-wide revert releases *every* holder rather than only its own -\n"
    "scoping that is what caused the bug this behaviour was written to fix.\n",
    "2.7: what is claimed",
)

# ---------------------------------------------------------------- 2.8

doc = replace_once(
    doc,
    "A broadcast, not a command: the fork is free to ignore it, so this confirms rather than\n"
    "assumes. It is also why a launch that needs Shizuku shows a spinner - ten silent seconds\n"
    "reads as a hang.\n",
    "On **Thedjchi** a broadcast, not a command: the fork is free to ignore it, so this confirms\n"
    "rather than assumes. It is why a launch that needs Shizuku shows a spinner - eight silent\n"
    "seconds reads as a hang.\n"
    "\n"
    "⚠ **On Shevery there is no broadcast at all.** IMD switches the debugging transports on and\n"
    "waits up to forty seconds for that fork's own ErrorProtect watchdog to notice and start the\n"
    "service, then puts back exactly the transports it raised if nothing came up. It is the one\n"
    "start in the app that changes the device in order to ask, which is why it is the one that owes\n"
    "a rollback.\n",
    "2.8: the per-fork start",
)

# ---------------------------------------------------------------- 2.9

doc = replace_once(
    doc,
    "### 2.9 IMD services manager\n"
    "\n"
    "The dialog that opens without the app itself having to be open. Every row is read live and\n"
    "re-read twice a second, because all of these can be changed from outside this app.\n",
    "### 2.9 The Settings manager\n"
    "\n"
    "The dialog that opens without the app itself having to be open - through its own launcher icon,\n"
    "a Quick Settings tile, a homescreen shortcut, the Favourites tab, or an IMD intent. Every row\n"
    "is read live and re-read twice a second, because all of these can be changed from outside this\n"
    "app.\n"
    "\n"
    "Which rows appear is yours to choose, under *Setting manager toggles*, and their order follows\n"
    "the Shizuku fork. ⚠ **A fork that is not configured does not grey its row out - the row and the\n"
    "overlay row leave the card entirely**, which is the author's instruction and the opposite of\n"
    "what this diagram used to show.\n",
    "2.9: the title and blurb",
)

# ---------------------------------------------------------------- 2.11

doc = replace_once(
    doc,
    "### 2.11 Tasker / MacroDroid triggers\n"
    "\n"
    "Experimental, off by default, and refused until both the switch and the auth key agree.\n",
    "### 2.11 IMD intents\n"
    "\n"
    "Off by default, and every broadcast is refused - silently - until both the switch and the auth\n"
    "key agree. ⚠ **Opening the Settings manager is the exception**: it is an activity rather than a\n"
    "broadcast, it carries no auth key, and the integration switch cannot refuse it, because all it\n"
    "does is put a screen in front of you that you then operate by hand.\n",
    "2.11: the title and blurb",
)

# ---------------------------------------------------------------- the alt text
#
# ⚠ Renaming a heading does not rename the picture's alt text beside it, and the alt text is the
# half a screen reader reads. Caught by this script's own "old name survived" assertion, which is
# the whole reason it is scoped to a section rather than trusting the replacements above.

for old_alt, new_alt in (
    ("Flowchart: the IMD services manager", "Flowchart: the Settings manager"),
    ("Flowchart: Revert using memory", "Flowchart: reverting a per-app profile"),
    ("Flowchart: Tasker and MacroDroid triggers", "Flowchart: IMD intents"),
):
    doc = replace_once(doc, old_alt, new_alt, f"alt text: {old_alt}")

# ---------------------------------------------------------------- 2.15, and the section end

doc = replace_once(
    doc,
    '<p><img src="docs/logics/14-auto-hide.png" width="100%" alt="Flowchart: Auto-hide settings (IMD+)"></p>\n'
    "\n"
    "---\n",
    '<p><img src="docs/logics/14-auto-hide.png" width="100%" alt="Flowchart: Auto-hide settings (IMD+)"></p>\n'
    "\n"
    "### 2.15 Auto unhide settings\n"
    "\n"
    "The other half of the pair above, and the one that needs no notification tapped: it watches for\n"
    "the moment a hide has served its purpose and puts the device back on its own.\n"
    "\n"
    "There are three triggers - the app swiped away from recents, the app left alone for longer than\n"
    "a timer, and the screen locked for longer than a timer - and two conditions saying which kinds\n"
    "of hide they apply to. ⚠ **Which condition is read is inferred, not stored.** A hide that named\n"
    "an app leaves a watch entry, so it is an app-launch session; a hide from the tile names nothing\n"
    "and leaves none, so it is a tile session. That is also why the screen-lock trigger is the\n"
    "failsafe and cannot be switched off while the tile condition is on: a tile session has no app\n"
    "to watch, and screen lock is the only thing that could ever end it.\n"
    "\n"
    "Two things degrade rather than fail. Without the DUMP permission the swipe trigger simply never\n"
    "fires; without usage access the idle timer measures from the hide instead of from when you last\n"
    "used the app.\n"
    "\n"
    '<p><img src="docs/logics/15-auto-unhide.png" width="100%" alt="Flowchart: Auto unhide settings"></p>\n'
    "\n"
    "---\n",
    "2.15: the new section",
)

# ---------------------------------------------------------------- assertions

# ⚠ **Scoped to section 2, not the document.** Both of these phrases also appear in section 3, the
# version history, where they are a record of what a past release said and must not be touched -
# the same trap r30a hit with the EXPERIMENTAL tag. A whole-file search finds the history and
# reports the edit as having failed.
section_two = doc[doc.index("## 2. IMD app logics"):doc.index("## 3. Version history")]

check(
    "IMD services manager" not in section_two,
    "SUIMD 2: the old services-manager name survived",
)

check(
    "ten silent seconds" not in section_two,
    "SUIMD 2: the ten-second figure survived",
)

check(
    "Experimental, off by default" not in section_two,
    "SUIMD 2: the experimental description of IMD intents survived",
)

# ⚠ Every diagram in the folder must be shown, and every image shown must exist. Neither direction
# is implied by the other, and it is the second that would ship a broken image.
rendered = {p.stem for p in LOGICS.glob("*.png")}

referenced = set(re.findall(r'docs/logics/([0-9a-z-]+)\.png', doc))

check(
    len(rendered) == 15,
    f"docs/logics holds {len(rendered)} pictures, expected 15",
)

check(
    rendered == referenced,
    f"SUIMD shows {sorted(referenced - rendered)} that do not exist, "
    f"and omits {sorted(rendered - referenced)}",
)

for n in range(1, 16):
    heading = f"### 2.{n} "

    check(doc.count(heading) == 1, f"SUIMD: {heading.strip()} appears {doc.count(heading)}x")

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

SUIMD.write_text(doc, encoding="utf-8")

print(f"wrote {SUIMD.relative_to(ROOT).as_posix()}")

print("ok")
