#!/usr/bin/env python3
"""
r30e — the author's pass over the new README.

Twelve edits, his, in the order he gave them. Each one is asserted before it is made, so a section
that has already moved fails loudly rather than being edited into the wrong place.

## The highlighted phrases

*"can we give solid colour background soft rectangle … if github supports it"* — it does, but only
through the tags its sanitiser allows: **inline CSS is stripped from a README**, so `style=` is not
an option and never will be. `<mark>` is on the allow-list and is the one tag that gives a solid
soft-cornered background while leaving the text in the page's own font. (`<code>` is the other
candidate and gives a grey rectangle, but it also forces monospace, which would make the two
phrases read as code rather than as emphasis.)

## What is removed, and what that costs

Six blocks go: the ADB grant instructions, the Screenshots strip, *Functions from the original
Geto*, the SUIMD.md pointer, the Geto attribution paragraph and the GPL closing note.

⚠ **The attribution survives, and this was checked rather than assumed.** GPL-3.0 asks that the
notices travel with the work, not that a particular paragraph sit in the README. After this edit
the page still carries *Supercharged fork of Geto* under the title, and still names
**Original Project: Geto by JackEblan** and **License: GPL-3.0** in Development & Contributions —
and `LICENSE`, `SUIMD.md § 4` and the in-app About screen are untouched. Both facts are asserted
below, so a later edit cannot quietly take the last of it out.

Computes the whole file in memory, asserts every match count, writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

README = ROOT / "README.md"

failures: list[str] = []


def check(condition: bool, message: str) -> bool:
    if not condition:
        failures.append(message)

    return condition


text = README.read_text(encoding="utf-8")


def swap(old: str, new: str, label: str) -> None:
    global text

    found = text.count(old)

    if not check(found == 1, f"{label}: found {found}x, expected 1"):
        return

    text = text.replace(old, new, 1)


def cut(old: str, label: str) -> None:
    swap(old, "", label)


# ---------------------------------------------------------------- 1. the two highlights

swap(
    "is a ***powerful settings/ services manager*** and ***settings/ services hider***",
    "is a ***<mark>powerful settings/ services manager</mark>*** and "
    "***<mark>settings/ services hider</mark>***",
    "the two highlighted phrases",
)

# ---------------------------------------------------------------- 2. 'and many more'

swap(
    "6. and many more (you need to manually configure them using Memory function of app, "
    "hint: use Settings observer to help yourself)",
    "6. and many more (per app configuration - hiding framework, hint: use Settings observer "
    "for help)",
    "the 'and many more' bracket",
)

# ---------------------------------------------------------------- 3. the settings manager lead

swap(
    "One dialog, opened from the Favourites tab, a homescreen shortcut or a Quick Settings tile "
    "- without IMD itself having to be open. IMD's settings manager allows you to:",
    "IMD's settings manager allows you to:",
    "the settings manager lead sentence",
)

# ---------------------------------------------------------------- 4. Automations, points only

swap(
    """1. **Auto unhide settings** - your settings come back on their own, without you having to remember: when you return to IMD, when the app you launched is closed, or at the end of the wait you set.
2. **Auto hide settings (IMD+ : needs background service)** - pick the apps you want protected and IMD hides your settings the moment one of them opens, whoever opened it. It closes the app, hides what you named, and opens it again, so the app starts having never seen the settings it objects to.
3. **IMD Intents (Tasker / MacroDroid integration, secured with auth keys)** - drive IMD from an automation app: open the settings manager, Revert to default, Revert using memory, or hide your configured settings and services. The auth key is random per install and refreshable, it is off until you turn it on, and it works even when IMD is not running.""",
    """1. **Auto unhide settings**
2. **Auto hide settings** (IMD+ : needs background service)
3. **IMD Intents** (Tasker / MacroDroid integration, secured with auth keys)""",
    "the Automations points",
)

# ---------------------------------------------------------------- 5. the fourth permission

swap(
    "* Post notifications (optional)\n",
    "* Post notifications (optional)\n"
    "* Other permissions (optional: only needed if you use automations like IMD+)\n",
    "the Other permissions bullet",
)

# ---------------------------------------------------------------- 6. the ADB grant block

cut(
    """
Grant the mandatory one once with a PC:

```
adb shell pm grant com.soul_99.suIMD android.permission.WRITE_SECURE_SETTINGS
```

or, with no PC, tap **Use Shizuku** on the first-run screen and it runs that command for you. The screen also shows the command with a copy button and re-checks itself when you come back, so you never have to type it twice. The grant survives reboots but not a reinstall.
""",
    "the ADB grant block",
)

# ---------------------------------------------------------------- 7. the Screenshots strip

start = text.find("## Screenshots\n")

end = text.find("## Changelog\n")

if check(start != -1 and end > start, "the Screenshots section is not where it was"):
    text = text[:start] + text[end:]

# ---------------------------------------------------------------- 8. Functions from Geto

start = text.find("## Functions from the original Geto\n")

end = text.find("## Support the project", start if start != -1 else 0)

if check(start != -1 and end > start, "the Functions-from-Geto section is not where it was"):
    text = text[:start] + text[end:]

# ---------------------------------------------------------------- 9. the signature

# Two lines, right aligned, exactly as the app's own Support dialog signs off:
# `support_signature_dash` + `support_signature_name`, then `support_signature_real_name`.
swap(
    "\\- **soul_99** (Dr. Utkarsh Rajput)\n",
    '<p align="right">\n'
    "  <b>- soul_99</b><br>\n"
    "  (Dr. Utkarsh Rajput)\n"
    "</p>\n",
    "the signature",
)

# ---------------------------------------------------------------- 10. Rafay's bracket

swap(
    "[RafayGhafoor](https://github.com/RafayGhafoor) (Muhammad Rafay Awan)",
    "[RafayGhafoor](https://github.com/RafayGhafoor) (Display over other apps initial framework)",
    "Rafay's bracket",
)

# ---------------------------------------------------------------- 11. read these first

swap(
    """View [SUIMD.md](SUIMD.md), which documents how to use the app, how each of its logics works, and what was changed and why with each version - including the bugs found in the original and the reasoning behind each fix.

This app is a fork of **[Geto](https://github.com/JackEblan/Geto)** by **Jack Eblan**, licensed GPL-3.0. All of the original design and the great majority of the code are his; the additions above are the difference. Full credit for the app this is built on goes to him.
""",
    """Before you change anything, read **[SUIMD.md](SUIMD.md)** first. It documents how the app works, how each of its logics runs, and what was changed from the original Geto and why - including the bugs found in it and the reasoning behind each fix. Almost everything that looks odd in this code is answered there.

Then read **[CONTRIBUTING.md](CONTRIBUTING.md)** before you open a pull request.
""",
    "the read-these-first paragraph",
)

# ---------------------------------------------------------------- 12. the GPL closing note

cut(
    """&nbsp;

The source is all here under the GPL-3.0. Use it freely for your own purposes - build it, change it, fork it, keep the changes to yourself or pass them on. That is what it is for.

""",
    "the GPL closing note",
)

# ---------------------------------------------------------------- assertions

# ⚠ The attribution, which is what the removed paragraph was carrying. It is not optional and it is
# not a matter of taste, so it is checked rather than trusted to the edits above.
for required in (
    "<sub>Supercharged fork of [Geto](https://github.com/JackEblan/Geto)</sub>",
    "**Original Project:** [Geto](https://github.com/JackEblan/Geto) by [JackEblan](https://github.com/JackEblan)",
    "GNU General Public License v3.0",
):
    check(required in text, f"attribution: {required[:48]!r} is gone from the README")

for path in ("LICENSE", "SUIMD.md", "CONTRIBUTING.md"):
    check((ROOT / path).exists(), f"{path} does not exist, and the README now links to it")

# What he asked to be gone, gone.
for removed in (
    "## Screenshots",
    "## Functions from the original Geto",
    "adb shell pm grant",
    "Use Shizuku** on the first-run screen",
    "One dialog, opened from the Favourites tab",
    "Muhammad Rafay Awan",
    "Use it freely for your own purposes",
    "you need to manually configure them using Memory function",
):
    check(removed not in text, f"still present: {removed!r}")

# The highlights, and nothing stray left behind by them.
check(text.count("<mark>") == 2 and text.count("</mark>") == 2, "the <mark> tags do not pair")

check("****" not in text, "a four-asterisk run appeared")

check(text.count("***") == 6, f"{text.count('***')} '***' markers, expected 6")

# The Automations points keep their brackets and lose their prose - one line each, nothing after.
for point in (
    "1. **Auto unhide settings**\n",
    "2. **Auto hide settings** (IMD+ : needs background service)\n",
    "3. **IMD Intents** (Tasker / MacroDroid integration, secured with auth keys)\n",
):
    check(point in text, f"automations: {point.strip()!r} is not on its own line")

# Headings still in the order he set, with the two removed ones gone from it.
ORDER = [
    "# IMD - It's My Device",
    "#### How this works flowchart",
    "## Settings manager",
    "## Automations",
    "## About Permissions",
    "## Security Concerns",
    "## Changelog",
    "## Support the project",
    "## Development & Contributions",
    "## About this project",
]

position = -1

for marker in ORDER:
    found = text.find(marker)

    if not check(found != -1, f"readme: {marker!r} is missing"):
        continue

    check(found > position, f"readme: {marker!r} is out of order")

    position = found

# Cutting whole blocks is how a file grows blank lines. Not one triple newline may survive.
while "\n\n\n" in text:
    text = text.replace("\n\n\n", "\n\n")

check(text.endswith("*Long live free and open source software!*\n"), "the last line moved")

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

before = len(README.read_text(encoding="utf-8").splitlines())

README.write_text(text, encoding="utf-8")

print(f"README.md {before} -> {len(text.splitlines())} lines")

print("ok")
