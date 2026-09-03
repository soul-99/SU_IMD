#!/usr/bin/env python3
r"""
r30i — the F-Droid listing text, and a proof that none of it is mine.

## What went wrong the first time

The first version of this script put a sentence into `full_description` that the author had
**explicitly told me to delete** from the README one round earlier — *"It opens from the Favourites
tab, a homescreen shortcut or a Quick Settings tile, without IMD itself having to be open…"*. It
came back in a slightly different shape, which is worse than copying it: it looks like his.

⚠ **The fix is not care, it is a check.** Below, every content line of `full_description` has to be
found in `README.md` after both are reduced to plain text. If a sentence is not his, the script
refuses to write. That is what `check_prose` does, and it is the only reason to trust this file.

The three things it cannot check, and how they are handled instead:

* **The section headings** — `How this works`, `Settings manager`, `Automations`,
  `About Permissions`, `Security Concerns`. Each is asserted to be a heading in the README.
* **The flowchart.** F-Droid renders no images, so the mermaid diagram becomes its five node
  labels, **verbatim, `<br>` and `<u>` and all** — not a paraphrase of them.
* **`<b>` for `***…***` and `<mark>`.** F-Droid takes a small HTML subset and no markdown.

## The app name

The author asked for *"IMD - It's My Device (supercharged fork of Geto) Settings manager/ hide
settings from apps"* — 89 characters, against F-Droid's 50-character cap on a title.

⚠ **It is not truncated; it is split at its own seam.** F-Droid has exactly two fields for a name
and a line under it, and his string is exactly a name and a line under it:

* `title.txt` — `IMD - It's My Device (supercharged fork of Geto)` (48 of 50)
* `short_description.txt` — `Settings manager/ hide settings from apps` (41 of 80)

Every word of his, in the order he wrote it, stacked on the page the way the page stacks them.

Computes all three in memory, proves them against the README, writes nothing if anything fails.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

METADATA = ROOT / "fastlane/metadata/android/en-US"

README = ROOT / "README.md"

LIMITS = {"title": 50, "short_description": 80, "full_description": 4000}

ALLOWED_TAGS = {"b", "i", "u", "br", "ul", "ol", "li", "a", "p"}

# Asserted to be README headings, not prose. Everything else must survive the proof.
HEADINGS = ["How this works", "Settings manager", "Automations", "About Permissions", "Security Concerns"]

# ⚠ **The only non-heading line allowed through the proof, and it carries no words.** The author
# asked for the arrow the app's own "How auto unhide works" page draws between its steps. It is
# structure, like a bullet, so it has nothing to be proved against.
#
# ⚠ **The indent is twenty U+00A0, not twenty spaces, and that is the whole trick.** He wrote the
# line as `'                    ↓'`. Ordinary leading spaces collapse to nothing the moment the
# description is rendered as HTML, which is why the first attempt left the arrow at the margin.
#
# `&nbsp;` is the obvious fix and the wrong one: it depends on the renderer resolving the entity,
# and one that does not prints the six characters `&nbsp;` on the page. A **literal non-breaking
# space** needs no parsing at all — it is simply a character HTML does not treat as collapsible
# whitespace, so it survives in F-Droid's client and on f-droid.org alike.
#
# Twenty of them, exactly as many as he typed.
PAD = "\u00a0" * 20

ARROW = "↓"

INDENTED_ARROW = PAD + ARROW

failures: list[str] = []


def check(condition: bool, message: str) -> bool:
    if not condition:
        failures.append(message)

    return condition


def plain(text: str) -> str:
    """Both documents reduced to the same thing: words, and nothing that marks them up.

    Applied to the README *and* to each line of the description, so a bullet dash, an asterisk
    pair, a backtick or a tag disappears from both sides at once and cannot make two identical
    sentences look different.
    """
    text = re.sub(r"<br\s*/?>", " ", text)

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", text)

    text = re.sub(r"</?[a-zA-Z][^>]*>", "", text)

    text = text.replace("`", "").replace("*", "").replace("#", "").replace("-", " ")

    # ⚠ **Quotes and brackets go too, because the flowchart's words live inside `A["…"]`.** Without
    # this, five sentences that are the author's word for word read as mine.
    text = text.replace('"', "").replace("[", "").replace("]", "")

    # A leading number is list structure, exactly like a bullet, and the same sentence is numbered
    # in one document and not in the other.
    text = re.sub(r"^\s*\d+\.\s+", "", text)

    return re.sub(r"\s+", " ", text).strip()


TITLE = "IMD - It's My Device (supercharged fork of Geto)"

SHORT = "Settings manager/ hide settings from apps"

FULL = f"""IMD (It's My Device) is a powerful <b>settings/ services manager</b> and <b>settings/ services hider</b> (automated disable-enable settings) for restrictive apps (banking, payments...etc). It supports the following settings / services :

1. Developer settings
2. ADB / Debugging
3. Accessibility services
4. Display over other apps (needs active Shizuku service)
5. Shizuku service
6. and many more (per app configuration - hiding framework, hint: use Settings observer for help)

<b>How this works</b>

1. User opens app from IMD / IMD generated app shortcut
{INDENTED_ARROW}
2. IMD actually disables these settings<br><u>no app's security policy is broken</u>
{INDENTED_ARROW}
3. Use your app normally
{INDENTED_ARROW}
4. Use Revert function<br><i>(accessible via: notification / quick toggle / Quick settings tile / homescreen shortcut / IMD settings manager)</i>
{INDENTED_ARROW}
5. IMD enables the disabled settings

<b>Settings manager</b>

IMD's settings manager allows you to:

1. View the <b>live status</b> of your settings/ services
2. Quickly toggle them on-off

<b>Automations</b>

1. <b>Auto unhide settings</b>
2. <b>Auto hide settings</b> (IMD+ : needs background service)
3. <b>IMD Intents</b> (Tasker / MacroDroid integration, secured with auth keys)

<b>About Permissions</b>

* WRITE_SECURE_SETTINGS (one time grant via adb shell or Shizuku) (MANDATORY, needed to change settings state)
* Shizuku service (optional) (needed to hide Display over other apps permissions - an appops permission)
* Post notifications (optional)
* Other permissions (optional: only needed if you use automations like IMD+)

<b>Security Concerns</b>

* No internet access or unnecessary continuous background services (so almost zero battery / system resource use).
* Does not tamper with any apps on the device.
* The parts of this app that change settings cannot be triggered by another app, so only you can change them.
* No ads, analytics, trackers or accounts of any kind. The app has no network permission at all - which is also why it cannot check for its own updates, and why Obtainium is how you find out there is one.

<b>Package:</b> com.soul_99.suIMD - installs alongside stock Geto, both can coexist
<b>Requires:</b> Android 7.0 (API 24) or newer. No root.
<b>Licence:</b> GPL-3.0

Supercharged fork of Geto (https://github.com/JackEblan/Geto)
"""

DRAFTS = {"title": TITLE, "short_description": SHORT, "full_description": FULL}

readme = README.read_text(encoding="utf-8")

approved = plain(readme)

# ---------------------------------------------------------------- the proof

for line in FULL.splitlines():
    if not line.strip():
        continue

    reduced = plain(line)

    if reduced == ARROW:
        continue

    if reduced in HEADINGS:
        # A heading is structure, not prose - but it still has to be one of his.
        # A prefix, not an exact match, for one reason named here: the README's heading is
        # "How this works flowchart" and there is no flowchart on an F-Droid page. Dropping the
        # last word is the whole licence this takes.
        check(
            any(
                plain(candidate).startswith(reduced)
                for candidate in re.findall(r"^#{2,4} .+$", readme, re.M)
            ),
            f"heading {reduced!r} is not a heading in the README",
        )

        continue

    check(
        reduced in approved,
        f"NOT THE AUTHOR'S: {reduced!r}",
    )

# The reverse direction is not asserted: the listing is a subset of the README by design (it
# carries no Changelog, no Development section, no screenshots strip of its own).

# The title and summary are his sentence, split. Together they must reconstruct it exactly.
check(
    f"{TITLE} {SHORT}"
    == "IMD - It's My Device (supercharged fork of Geto) Settings manager/ hide settings from apps",
    f"title + short_description do not reconstruct the author's app name: {TITLE + ' ' + SHORT!r}",
)

# ---------------------------------------------------------------- the limits and the markup

for name, text in DRAFTS.items():
    length = len(text.rstrip("\n"))

    check(length <= LIMITS[name], f"{name}: {length} characters, over F-Droid's {LIMITS[name]}")

    check(text.strip() != "", f"{name}: empty")

for tag in re.findall(r"</?([a-zA-Z]+)[^>]*>", FULL):
    check(tag.lower() in ALLOWED_TAGS, f"full_description: <{tag}> is not in F-Droid's subset")

for tag in ("b", "i", "u"):
    opens = len(re.findall(rf"<{tag}>", FULL))

    closes = len(re.findall(rf"</{tag}>", FULL))

    check(opens == closes, f"full_description: {opens} <{tag}> against {closes} </{tag}>")

for marker in ("**", "***", "##", "](", "<mark>"):
    check(marker not in FULL, f"full_description: markdown {marker!r} survived the port")

# ⚠ **Settled in r30j.** Step 4 of the flowchart used to say "IMD services manager", the name the
# app dropped in v3 - carried here verbatim because it was the author's text, and reported to him
# rather than corrected on his behalf. He chose to fix it, so the README's mermaid block moved and
# this line moved with it. The old name may not come back through either document.
check(
    "IMD services manager" not in FULL,
    "full_description: the pre-v3 name is back in the flowchart's step 4",
)

check("EXPERIMENTAL" not in FULL, "full_description: EXPERIMENTAL is stale wording")

# Four arrows for five steps, and every one of them between two of those steps - not stranded
# somewhere else in the document.
steps = FULL.split("<b>How this works</b>")[1].split("<b>Settings manager</b>")[0]

check(steps.count(ARROW) == 4, f"how this works: {steps.count(ARROW)} arrows, expected 4")

check(FULL.count(ARROW) == 4, f"full_description: {FULL.count(ARROW)} arrows outside the steps")

# \u26a0 Every arrow carries the padding, and the padding is non-breaking. An ordinary space here
# looks identical in an editor and collapses to nothing on the page - which is exactly the bug this
# replaced, and the only way it could come back.
check(
    FULL.count(INDENTED_ARROW) == 4,
    f"full_description: {FULL.count(INDENTED_ARROW)} indented arrows, expected 4",
)

check(
    re.search(r"[ \t]\u2193", FULL) is None,
    "full_description: an arrow is padded with ordinary spaces, which collapse when rendered",
)

check(
    re.findall(r"^(?:\d\.|\u00a0*\u2193)", steps.strip(), re.M)
    == ["1.", INDENTED_ARROW, "2.", INDENTED_ARROW, "3.", INDENTED_ARROW, "4.", INDENTED_ARROW, "5."],
    "how this works: the steps and arrows do not alternate",
)

# ---------------------------------------------------------------- write

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

for name, text in DRAFTS.items():
    path = METADATA / f"{name}.txt"

    before = len(path.read_text(encoding="utf-8").rstrip("\n"))

    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")

    print(f"{name:20s} {before:5d} -> {len(text.rstrip(chr(10))):5d} chars  (limit {LIMITS[name]})")

print(f"\nevery prose line proved against README.md")

print("ok")
