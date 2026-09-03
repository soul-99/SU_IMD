#!/usr/bin/env python3
"""
r30c — the new README, and CHANGELOG.md carved out of it.

The author gave the README's running order outright, so this script follows it and nothing else:

    heading → muted subheading → poster → install buttons → what it is and the settings list →
    "How this works" flowchart → settings manager → Automations → permissions and security →
    support the project → development and contributions

and *"we will remove changelog from readme instead make a heading named 'Changelog' which opens
changelog.md"*.

## What is his and what is mine

His sentences go in verbatim. Three deliberate departures, all listed back to him rather than
made quietly:

* **"restrictve" → "restrictive"** and **"Macrodroid" → "MacroDroid"**, the app's own spelling.
* **The asterisks are balanced.** He wrote `****powerful settings/ services manager***` — four
  leading and three trailing — three times. Four is not a markdown marker, so as typed it renders
  a stray `*` before bold-italic text. Read as `***…***`, bold-italic, which is what three of the
  four asterisks already say.
* **One lead line under each of the four Automations / settings-manager points.** A bare
  "Auto unhide settings" names a feature to somebody who already knows it and to nobody else.

## The screenshots

Every `<img>` here points at a file that exists today; the poster and the three Automations shots
are the ones he is replacing, and each carries a `TODO` comment on the line above so the slot is
findable. ⚠ **Asserted, not assumed** — every path referenced by either document is checked
against the tree before anything is written, so a rename cannot leave a broken image behind.

## The changelog

Everything under **Functions → Added in this fork** leaves the README and becomes `CHANGELOG.md`,
summarised to *"the points that actually user care about"*: the per-release under-the-hood notes
and the internal reasoning go, the dates come in from SUIMD.md §3, and the fix that stopped the
app running at all on Android 12 stays because it is the one entry a user might still be looking
for. **From the original Geto** is not a changelog and stays in the README.

Computes both documents in memory, asserts every reference, writes nothing if any assertion fails.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

README = ROOT / "README.md"
CHANGELOG = ROOT / "CHANGELOG.md"
SUIMD = ROOT / "SUIMD.md"

SHOTS = "fastlane/metadata/android/en-US/images/phoneScreenshots"

failures: list[str] = []


def check(condition: bool, message: str) -> bool:
    if not condition:
        failures.append(message)

    return condition


# ---------------------------------------------------------------- the flowchart

# ⚠ Lifted from the old README unchanged. It is the only diagram in either document that is aimed
# at somebody deciding whether to install the app; the fifteen in docs/logics are aimed at somebody
# reading the code, and SUIMD.md is where those belong.
FLOWCHART = """```mermaid
flowchart TD
    A["User opens app from IMD / IMD generated app shortcut"]
    B["IMD actually disables these settings<br/><i><u>no app's security policy is broken</u></i>"]
    C["Use your app normally"]
    D["Use Revert function<br/><i>(accessible via: notification / quick toggle / Quick settings tile / homescreen shortcut / IMD services manager)</i>"]
    E["IMD enables the disabled settings"]
    A --> B
    B --> C
    C --> D
    D --> E
```"""

# ---------------------------------------------------------------- README

README_TEXT = f"""# IMD - It's My Device

<sub>Supercharged fork of [Geto](https://github.com/JackEblan/Geto)</sub>

<!-- TODO r30: replace with the new poster -->
<p>
  <img src="{SHOTS}/01_poster.png" width="100%" alt="Poster: what IMD does, with screenshots of the IMD services manager, the Quick Settings tiles, the Favourites tab, creating a shortcut and the revert notification">
</p>

<a href="https://apps.obtainium.imranr.dev/redirect.html?r=obtainium%3A%2F%2Fadd%2Fhttps%3A%2F%2Fgithub.com%2Fsoul-99%2FSU_IMD">
  <img src="https://raw.githubusercontent.com/ImranR98/Obtainium/main/assets/graphics/badge_obtainium.png" alt="Get it on Obtainium" height="54">
</a>
<a href="https://github.com/soul-99/SU_IMD/releases">
  <img src="https://raw.githubusercontent.com/Kunzisoft/Github-badge/main/get-it-on-github.png" alt="Get it on GitHub" height="54">
</a>

IMD (It's My Device) is a ***powerful settings/ services manager*** and ***settings/ services hider*** (automated disable-enable settings) for restrictive apps (banking, payments...etc). It supports the following settings / services :

1. Developer settings
2. ADB / Debugging
3. Accessibility services
4. Display over other apps (needs active Shizuku service)
5. Shizuku service
6. and many more (you need to manually configure them using Memory function of app, hint: use Settings observer to help yourself)

#### How this works flowchart

{FLOWCHART}

## Settings manager

<p>
  <img src="{SHOTS}/02_services_manager.png" width="240" alt="The IMD services manager dialog over a homescreen, listing Developer settings, USB debugging, Wireless debugging, Accessibility services, Shizuku service and Display over other apps, each with a switch, and a Revert to default button at the bottom">
</p>

One dialog, opened from the Favourites tab, a homescreen shortcut or a Quick Settings tile - without IMD itself having to be open. IMD's settings manager allows you to:

1. View the ***live status*** of your settings/ services
2. Quickly toggle them on-off

## Automations

<!-- TODO r30: replace the three below with the new Automations screenshots -->
<p>
  <img src="{SHOTS}/06_revert_notification.png" width="200" alt="The ongoing revert notification, which puts the hidden settings back on a tap">
  <img src="{SHOTS}/10_settings_advanced.png" width="200" alt="The Advanced settings screen, where Auto-hide settings and IMD intents are configured">
  <img src="{SHOTS}/11_settings_tasker.png" width="200" alt="The IMD intents screen, showing the per-install auth key and the intents to copy into an automation app">
</p>

1. **Auto unhide settings** - your settings come back on their own, without you having to remember: when you return to IMD, when the app you launched is closed, or at the end of the wait you set.
2. **Auto hide settings (IMD+ : needs background service)** - pick the apps you want protected and IMD hides your settings the moment one of them opens, whoever opened it. It closes the app, hides what you named, and opens it again, so the app starts having never seen the settings it objects to.
3. **IMD Intents (Tasker / MacroDroid integration, secured with auth keys)** - drive IMD from an automation app: open the settings manager, Revert to default, Revert using memory, or hide your configured settings and services. The auth key is random per install and refreshable, it is off until you turn it on, and it works even when IMD is not running.

## About Permissions

* `WRITE_SECURE_SETTINGS` (one time grant via adb shell or Shizuku) (MANDATORY, needed to change settings state)
* Shizuku service (optional) (needed to hide Display over other apps permissions - an appops permission)
* Post notifications (optional)

Grant the mandatory one once with a PC:

```
adb shell pm grant com.soul_99.suIMD android.permission.WRITE_SECURE_SETTINGS
```

or, with no PC, tap **Use Shizuku** on the first-run screen and it runs that command for you. The screen also shows the command with a copy button and re-checks itself when you come back, so you never have to type it twice. The grant survives reboots but not a reinstall.

## Security Concerns

* No internet access or unnecessary continuous background services (so almost zero battery / system resource use).
* Does not tamper with any apps on the device.
* The parts of this app that change settings cannot be triggered by another app, so only you can change them.
* No ads, analytics, trackers or accounts of any kind. The app has no network permission at all - which is also why it cannot check for its own updates, and why Obtainium is how you find out there is one.

- **Package:** `com.soul_99.suIMD` - installs alongside stock Geto, both can coexist
- **Requires:** Android 7.0 (API 24) or newer. **No root.**
- **Licence:** GPL-3.0

## Screenshots

<p>
  <img src="{SHOTS}/02_services_manager.png" width="160" alt="IMD services manager">
  <img src="{SHOTS}/03_qs_toggles.png" width="160" alt="Quick Settings tiles">
  <img src="{SHOTS}/04_favourites.png" width="160" alt="Favourites tab">
  <img src="{SHOTS}/05_add_shortcut.png" width="160" alt="Create a shortcut">
  <img src="{SHOTS}/06_revert_notification.png" width="160" alt="Revert notification">
  <img src="{SHOTS}/07_settings_ui.png" width="160" alt="Settings">
  <img src="{SHOTS}/08_settings_defaults.png" width="160" alt="Default IMD settings">
  <img src="{SHOTS}/09_shizuku_config.png" width="160" alt="Shizuku configuration">
  <img src="{SHOTS}/10_settings_advanced.png" width="160" alt="Advanced settings">
  <img src="{SHOTS}/11_settings_tasker.png" width="160" alt="IMD intents">
</p>

## Changelog

Every release and what changed in it: **[CHANGELOG.md](CHANGELOG.md)**

## Functions from the original Geto

- Per-app profiles of Android **system**, **secure** and **global** settings (if using memory function as notification function).
- A searchable, sortable list of every installed apps.
- A browsable copy of the device settings.
- Launch app from inside IMD or shortcut with its profile applied, and an ongoing notification carrying the **Revert** action.
- A settings-observer foreground service.

## Support the project 🫶 (for free)

I created this app in my busy schedule of full-time medical residency.

Initially it was born out of my personal needs, but after positive community feedback, I decided to share it with the FOSS community.

I want it to be taken over by more capable developers in future, as my profession does not allow me to maintain it all year round.

**<u>You can do these for free, if you want to support this project and keep it alive.</u>**

1. **Share this project/app to community. This is most helpful and will help to keep the project alive.**
   (I don't need any credit or mentions) [Share the repo »](https://github.com/soul-99/SU_IMD)
2. ⭐ Star [the GitHub repo](https://github.com/soul-99/SU_IMD) to increase its visibility.
3. [Report](https://github.com/soul-99/SU_IMD/issues/) bugs in the main repo.
4. [Join](https://www.reddit.com/r/SU_IMD/) discussions.
5. Contribute to the code or docs, if you are a developer.

\\- **soul_99** (Dr. Utkarsh Rajput)

## Development & Contributions

- **Created by:** [soul_99](https://github.com/soul-99/) (Dr. Utkarsh Rajput)
- **Contributions:** [RafayGhafoor](https://github.com/RafayGhafoor) (Muhammad Rafay Awan)
- **Original Project:** [Geto](https://github.com/JackEblan/Geto) by [JackEblan](https://github.com/JackEblan)
- **License:** IMD is licensed under the GNU General Public License v3.0, same as the original. See the [license](https://github.com/JackEblan/Geto/blob/master/LICENSE) for more information.

View [SUIMD.md](SUIMD.md), which documents how to use the app, how each of its logics works, and what was changed and why with each version - including the bugs found in the original and the reasoning behind each fix.

This app is a fork of **[Geto](https://github.com/JackEblan/Geto)** by **Jack Eblan**, licensed GPL-3.0. All of the original design and the great majority of the code are his; the additions above are the difference. Full credit for the app this is built on goes to him.

## About this project

I'm a full time radiology resident doctor, software is just a part time hobby.

This app exists because I wanted it to exist for myself, I have made multiple revisions after testing every build, fixing bugs and adding features, making the app what it is now - **on par with my expectations.**

Please know that due to my profession, it might take me some time for me to reply to queries, fix bugs and add new features in future builds, so please be patient.

But I do plan to maintain this app for the near future, until someone else makes a better app for the same purpose.

&nbsp;

The source is all here under the GPL-3.0. Use it freely for your own purposes - build it, change it, fork it, keep the changes to yourself or pass them on. That is what it is for.

&nbsp;

Namaste 🙏 & Thanks !

---

*Long live free and open source software!*
"""

# ---------------------------------------------------------------- CHANGELOG

CHANGELOG_TEXT = """# Changelog

What changed in each release, newest first, in terms of what it does for you.

The full technical history - every bug found in the original Geto, what caused it and the reasoning
behind each fix - is in [SUIMD.md § 3](SUIMD.md).

## v2.4 - 28 August 2026

**New**

- **Auto-hide settings (IMD+)** - the first thing in IMD that acts without you pressing anything.
  Pick the apps you want protected; when one of them opens, IMD closes it, hides whatever
  *Settings to hide/ disable* names, and opens it again - so the app starts having never seen the
  settings it objects to. A notification puts everything back on a tap. For advanced users, and it
  says so on the row.
- Its detector asks Android for one thing only: **which app came to the front**. It cannot read
  screen content - the configuration does not request that capability, so the system never grants
  it.

**Improved**

- **IMD's own accessibility service is now switched off by every hide**, whichever route hid the
  settings, and restored on the revert.
- **IMD+ will not start while a revert is still outstanding.**
- Every dialog is capped and centred on a large screen and fills the width on a phone.
- The settings manager's accessibility switch no longer moves IMD's own detector in either
  direction.
- A new **Revert to default** icon that still reads at Quick Settings size.

## v2.2 - 27 August 2026

**Fixed**

- **The app could not start at all on Android 12 or below.** Since v1.6.5 every device from
  Android 7 to Android 12 crashed before a line of it ran. Fixed, and reported by a user on
  Android 11 - nothing they did caused it.

**New**

- **A "Hide settings" Quick Settings tile** - the first tile that shows a state instead of firing
  an action. It reads *Settings visible* or *Settings hidden*: one press hides, the next unhides,
  and it follows a revert you run from anywhere else.
- **Stop the Shizuku service as part of hiding** - device-wide or per app.
- **The Shevery fork** of Shizuku is supported alongside thedjchi's.
- **Nothing is hidden or unhidden on a fresh install** until you say what. A launch with nothing
  ticked is refused and tells you where to configure it.

**Improved**

- **The revert notification is ongoing, says one line, and reverts when you tap it.** No button to
  find, and swiping it away puts it back - so the way home cannot be lost by accident.
- Each revert mechanism has its own notification channel, so you can silence one without losing
  the other.
- **Notification function** is now **Hiding-unhiding mechanism**.
- Launching a second app no longer redoes work that is already done - repeat launches no longer
  spend twenty seconds starting and stopping Shizuku for nothing.
- The settings template dialog stays open while you add rows, and a second app's revert no longer
  undoes the first app's hide.

## v2.0 - 25 August 2026

**New**

- **Hide "Display over other apps"** - for banking apps that refuse to run while another app can
  draw over them. Needs Shizuku, only the apps you pick are touched, and Revert gives the
  permission back. _(contribution by [RafayGhafoor](https://github.com/RafayGhafoor))_
- **Auto Revert on returning** (off by default) - puts your settings back automatically when you
  return to IMD after launching an app from it.
- **Tasker / MacroDroid integration** - drive IMD from an automation app with a per-install auth
  key. Off by default, and works even when IMD is not running.
- **Settings observer log** - the observer now records which settings an app changed, with
  View log / Clear log in Settings.
- **Support the project 🫶 (for free)** in About - a short note and free ways to help.

**Improved**

- A revert always restores everything it can, and a notification reports anything it could not.
- If "Display over other apps" cannot be hidden on launch, nothing else is changed - the app
  simply does not open.
- Only the apps and services you selected are ever touched.
- The notification's **Revert** button clears it and closes the shade the instant it is pressed.
- The IMD services manager shortcut can be created by any launcher again.

## v1.6.8 - 24 August 2026

- Shortcuts can no longer be used by third party apps.
- Updated Shizuku configuration dialog.

## v1.6.7 - 24 August 2026

- The notification's revert button now names the mechanism it will run: **Revert to default** or
  **Revert using memory**.
- The **UI** settings section is now called **User interface**.

## v1.6.6 - 24 August 2026

- The default **Settings to unhide on revert** changed, for security reasons.

## v1.6.5 - 24 August 2026

- Ten more languages, in testing: Portuguese (Brazilian), Spanish, Simplified Chinese, French,
  German, Russian, Hindi, Arabic, Korean and Japanese.

## v1.6 - 23 August 2026

- Default configuration for both **Settings to hide** and **Settings to unhide**.
- Short press opens the app, long press creates a shortcut.
- **IMD services manager**: long pressing *Revert to default* opens its configuration, and the
  Accessibility services toggle greys out when no services are selected.
- **Settings reorganised**: *App functions* is now *Default IMD settings*, and holds both
  *Settings to hide* and *Settings to unhide on Revert*.
- Shortcut labels are filled in with the app's own name.

## v1.5 - 22-23 August 2026

_Several builds between v1.1 and v1.5, listed together._

- **The IMD services manager** - one dialog showing the live state of every setting and service,
  including Shizuku, with a switch on each.
- **Revert to default** - a second revert that puts everything back to a universal state you
  configure, rather than to what each app found. The older one is now the *memory function*.
- Both of them get **Quick Settings tiles**, **homescreen shortcuts** and **Favourites tab
  buttons**.
- **A detailed readme inside the app**, to help you set it up.
- An in-app link to add the app to Obtainium.
- Redesigned settings page, Material Design update and newer icons.

## v1.1 - 22 August 2026

- Better Shizuku integration, with the default values filled in for you.
- Support for Shizuku forks that accept start-service intents (the original RikkaApps fork does
  not).

## v1.0 - 21 August 2026

The first IMD release. What the fork added to Geto:

- Shizuku service restart.
- A working accessibility services flag, with per-service enable/disable.
- The previous state of a setting actually read back, with **setting memory**.
- A **Favourites** tab, and a re-enable settings/services button in it.
- Shortcut icons matching the Android adaptive icon.
- A first-run screen that can grant the permission through Shizuku.
- A Material Design search box.
"""

# ---------------------------------------------------------------- assertions

readme_old = README.read_text(encoding="utf-8")

check(not CHANGELOG.exists(), "CHANGELOG.md already exists")

# Every picture either document points at must be in the tree. A README whose images 404 is the
# first thing anybody sees of the project.
for document, label in ((README_TEXT, "readme"), (CHANGELOG_TEXT, "changelog")):
    for reference in re.findall(r'src="([^"]+)"', document):
        if reference.startswith("http"):
            continue

        check((ROOT / reference).exists(), f"{label}: {reference} does not exist")

# Local links, same reasoning.
for document, label in ((README_TEXT, "readme"), (CHANGELOG_TEXT, "changelog")):
    for target in re.findall(r"\]\(([^)#]+?)(?:#[^)]*)?\)", document):
        if target.startswith(("http", "#")):
            continue

        check((ROOT / target).exists() or target == "CHANGELOG.md", f"{label}: {target} is missing")

# ⚠ The running order is his, so it is asserted rather than trusted to the writing above. Each of
# these must appear once, in this sequence.
ORDER = [
    "# IMD - It's My Device",
    "<sub>Supercharged fork of",
    "01_poster.png",
    "badge_obtainium.png",
    "#### How this works flowchart",
    "## Settings manager",
    "## Automations",
    "## About Permissions",
    "## Security Concerns",
    "## Changelog",
    "## Support the project",
    "## Development & Contributions",
]

position = -1

for marker in ORDER:
    found = README_TEXT.find(marker)

    if not check(found != -1, f"readme: {marker!r} is missing"):
        continue

    check(found > position, f"readme: {marker!r} is out of order")

    position = found

# The changelog carries every release the old README listed, and the release list is taken from
# SUIMD.md rather than from my memory of it.
suimd = SUIMD.read_text(encoding="utf-8")

for version in ("v2.4", "v2.2", "v2.0", "v1.6.8", "v1.6.7", "v1.6.6", "v1.6.5", "v1.6", "v1.5", "v1.1", "v1.0"):
    check(
        f"\n## {version} - " in CHANGELOG_TEXT,
        f"changelog: {version} has no heading",
    )

    check(
        f"\n### {version} - " in suimd,
        f"changelog: {version} is not a release in SUIMD.md",
    )

# ⚠ Every dated heading must agree with SUIMD.md to the day. Two documents carrying the same dates
# separately is exactly how they come to disagree.
for version, date in re.findall(r"\n## (v[\d.]+) - ([^\n]+)\n", CHANGELOG_TEXT):
    check(
        f"### {version} - {date} ·" in suimd or f"### {version} - {date}\n" in suimd,
        f"changelog: {version} is dated {date}, which is not what SUIMD.md says",
    )

# The changelog leaves the README, and nothing that was only in the changelog may be lost with it.
check("### Added in this fork" not in README_TEXT, "readme: the changelog is still in it")

check(
    "#### v2.4" not in README_TEXT and "#### v1.0" not in README_TEXT,
    "readme: a version block survived",
)

check(
    "from the original Geto" in README_TEXT,
    "readme: the original-Geto function list was dropped - it is not a changelog",
)

# The tag went in r30a; it must not come back through a document written after it.
check("EXPERIMENTAL" not in README_TEXT, "readme: EXPERIMENTAL is back")

check(
    "EXPERIMENTAL" not in CHANGELOG_TEXT,
    "changelog: EXPERIMENTAL - the v2.2 entry is a record and stays in SUIMD.md, not here",
)

# The asterisk markers, balanced. Four leading asterisks is the thing this is guarding against, and
# it renders as a stray '*' rather than as an error, so nothing else would catch it.
check(
    README_TEXT.count("***") == 6 and "****" not in README_TEXT,
    f"readme: {README_TEXT.count('***')} '***' markers, expected 6, and no '****'",
)

for phrase in (
    "powerful settings/ services manager",
    "settings/ services hider",
    "live status",
):
    check(
        f"***{phrase}***" in README_TEXT,
        f"readme: {phrase!r} is not bold-italic",
    )

# His four feature points, verbatim apart from the spelling of MacroDroid.
for point in (
    "Auto unhide settings",
    "Auto hide settings (IMD+ : needs background service)",
    "IMD Intents (Tasker / MacroDroid integration, secured with auth keys)",
    "View the ***live status*** of your settings/ services",
    "Quickly toggle them on-off",
):
    check(point in README_TEXT, f"readme: {point!r} is missing")

check(
    README_TEXT.count("Macrodroid") == 0,
    "readme: 'Macrodroid' - the app spells it MacroDroid",
)

# The slots he is filling later must be findable.
check(
    README_TEXT.count("<!-- TODO r30:") == 2,
    f"readme: {README_TEXT.count('<!-- TODO r30:')} TODO markers, expected 2",
)

# ---------------------------------------------------------------- write

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

README.write_text(README_TEXT, encoding="utf-8")

CHANGELOG.write_text(CHANGELOG_TEXT, encoding="utf-8")

print(f"README.md    {len(readme_old.splitlines())} lines -> {len(README_TEXT.splitlines())}")

print(f"CHANGELOG.md {len(CHANGELOG_TEXT.splitlines())} lines (new)")

print("ok")
