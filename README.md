# IMD - It's My Device

<sub>Supercharged fork of [Geto](https://github.com/JackEblan/Geto)</sub>

<p>
  <img src="fastlane/metadata/android/en-US/images/phoneScreenshots/01_poster.png" width="100%" alt="Poster: IMD - It's My Device. A settings/services manager that shows the live status of your settings, and a hider that turns them off and back on around a restrictive app. Lists the supported settings, the three automations, and five screenshots of the app">
</p>

<a href="https://apps.obtainium.imranr.dev/redirect.html?r=obtainium%3A%2F%2Fadd%2Fhttps%3A%2F%2Fgithub.com%2Fsoul-99%2FSU_IMD">
  <img src="https://raw.githubusercontent.com/ImranR98/Obtainium/main/assets/graphics/badge_obtainium.png" alt="Get it on Obtainium" height="54">
</a>
<a href="https://github.com/soul-99/SU_IMD/releases">
  <img src="https://raw.githubusercontent.com/Kunzisoft/Github-badge/main/get-it-on-github.png" alt="Get it on GitHub" height="54">
</a>

IMD (It's My Device) is a ***<mark>powerful settings/ services manager</mark>*** and ***<mark>settings/ services hider</mark>*** (automated disable-enable settings) for restrictive apps (banking, payments...etc). It supports the following settings / services :

1. Developer settings
2. ADB / Debugging
3. Accessibility services
4. Display over other apps (needs active Shizuku service)
5. Shizuku service
6. and many more (per app configuration - hiding framework, hint: use Settings observer for help)

#### How this works flowchart

```mermaid
flowchart TD
    A["User opens app from IMD / IMD generated app shortcut"]
    B["IMD actually disables these settings<br/><i><u>no app's security policy is broken</u></i>"]
    C["Use your app normally"]
    D["Use Revert function<br/><i>(accessible via: notification / quick toggle / Quick settings tile / homescreen shortcut / IMD settings manager)</i>"]
    E["IMD enables the disabled settings"]
    A --> B
    B --> C
    C --> D
    D --> E
```

## Settings manager

<p>
  <img src="fastlane/metadata/android/en-US/images/phoneScreenshots/02_settings_manager.png" width="230" alt="The Settings Manager window over a homescreen: All off / All on, then Developer settings, USB debugging, Wireless debugging, Shizuku service, Accessibility services and Display over other apps, each with a switch and a link out to Android's own page, and Hide settings / Revert to default at the bottom">
  <img src="fastlane/metadata/android/en-US/images/phoneScreenshots/03_qs_toggles.png" width="230" alt="The Quick Settings shade with three IMD tiles: Settings hidden, Settings manager and Revert to default">
</p>

IMD's settings manager allows you to:

1. View the ***live status*** of your settings/ services
2. Quickly toggle them on-off

## Automations

<p>
  <img src="fastlane/metadata/android/en-US/images/phoneScreenshots/08_how_auto_unhide_works.png" width="200" alt="The 'How auto unhide works' page: seven numbered steps from IMD hiding your settings to the notification going away once everything is back">
  <img src="fastlane/metadata/android/en-US/images/phoneScreenshots/09_how_imd_plus_works.png" width="200" alt="The 'How IMD+ works' page: nine numbered steps from opening a watched app to IMD's own accessibility service coming back and IMD+ being armed again">
  <img src="fastlane/metadata/android/en-US/images/phoneScreenshots/10_imd_intents.png" width="200" alt="The IMD intents screen, showing the per-install auth key with a refresh, and the type, package, class and action of each intent with a copy button on every value">
</p>

1. **Auto unhide settings**
2. **Auto hide settings** (IMD+ : needs background service)
3. **IMD Intents** (Tasker / MacroDroid integration, secured with auth keys)

## About Permissions

* `WRITE_SECURE_SETTINGS` (one time grant via adb shell or Shizuku) (MANDATORY, needed to change settings state)
* Shizuku service (optional) (needed to hide Display over other apps permissions - an appops permission)
* Post notifications (optional)
* Other permissions (optional: only needed if you use automations like IMD+)

## Security Concerns

* No internet access or unnecessary continuous background services (so almost zero battery / system resource use).
* Does not tamper with any apps on the device.
* The parts of this app that change settings cannot be triggered by another app, so only you can change them.
* No ads, analytics, trackers or accounts of any kind. The app has no network permission at all - which is also why it cannot check for its own updates, and why Obtainium is how you find out there is one.

- **Package:** `com.soul_99.suIMD` - installs alongside stock Geto, both can coexist
- **Requires:** Android 7.0 (API 24) or newer. **No root.**
- **Licence:** GPL-3.0

## Changelog

Every release and what changed in it: **[CHANGELOG.md](CHANGELOG.md)**

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

<p align="right">
  <b>- soul_99</b><br>
  (Dr. Utkarsh Rajput)
</p>

## Development & Contributions

- **Created by:** [soul_99](https://github.com/soul-99/) (Dr. Utkarsh Rajput)
- **Contributions:** [RafayGhafoor](https://github.com/RafayGhafoor) (Display over other apps initial framework)
- **Original Project:** [Geto](https://github.com/JackEblan/Geto) by [JackEblan](https://github.com/JackEblan)
- **License:** IMD is licensed under the GNU General Public License v3.0, same as the original. See the [license](https://github.com/JackEblan/Geto/blob/master/LICENSE) for more information.

Before you change anything, read **[SUIMD.md](SUIMD.md)** first. It documents how the app works, how each of its logics runs, and what was changed from the original Geto and why - including the bugs found in it and the reasoning behind each fix. Almost everything that looks odd in this code is answered there.

Then read **[CONTRIBUTING.md](CONTRIBUTING.md)** before you open a pull request.

## About this project

I'm a full time radiology resident doctor, software is just a part time hobby.

This app exists because I wanted it to exist for myself, I have made multiple revisions after testing every build, fixing bugs and adding features, making the app what it is now - **on par with my expectations.**

Please know that due to my profession, it might take me some time for me to reply to queries, fix bugs and add new features in future builds, so please be patient.

But I do plan to maintain this app for the near future, until someone else makes a better app for the same purpose.

&nbsp;

Namaste 🙏 & Thanks !

---

*Long live free and open source software!*
