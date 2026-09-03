# Contributing to IMD

Thanks for wanting to help. This document is what a contributor needs to know before opening
a pull request — how to build the project, how it is laid out, and the handful of rules that
are not obvious from reading the code.

Two things make this project different from a normal Android app, and most of what follows
comes back to one of them:

1. **It holds `WRITE_SECURE_SETTINGS`.** Everything here switches real settings off and on
   somebody's device, usually with no screen in front of them. A bug in this app does not
   crash a screen — it leaves debugging enabled on a phone whose owner thinks it is off.
2. **It is a GPL-3.0 fork of [Geto](https://github.com/JackEblan/Geto), distributed through
   F-Droid.** The licence and the build both have obligations, and both are easy to break by
   accident.

By taking part you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

---

## Before you write anything

- **Bugs and features go through issues first.** The
  [templates](.github/ISSUE_TEMPLATE) exist so a report has the version, the device and the
  steps in it. For anything larger than a fix, open an issue and let it be discussed before
  you spend an evening on it — this app has strong opinions about defaults and about what it
  is allowed to change, and it is better to find out before the code is written.
- **Check what the app already does.** [SUIMD.md](SUIMD.md) section 2 draws every decision
  the app makes about a setting as a flowchart, and section 3 is the full version history.
  A surprising amount of "this looks wrong" turns out to be deliberate and explained there.
- **Small, focused pull requests.** One change per PR. A PR that fixes a bug and reformats
  four files cannot be reviewed for the bug.

---

## Building

| | |
|---|---|
| JDK | **21** (pinned in `gradle/gradle-daemon-jvm.properties`) |
| Gradle | 9.3.1, via the wrapper — do not install your own |
| AGP / Kotlin | 9.1.0 / 2.3.20 |
| compileSdk / minSdk | 36 / 24 |

```bash
./gradlew :app:assembleDebug
```

That is exactly what CI runs on every push and pull request
(`.github/workflows/Build-SU_IMD.yml`), so if it passes locally it will pass there.

**Release builds need a key you supply yourself.** No keystore ships with this source. Drop a
`keystore.properties` beside `settings.gradle.kts` (it is gitignored) or use *Build → Generate
Signed App Bundle / APK*. Keep the same key for every build you install: Android only accepts
an update signed by the key that signed what is already there, and uninstalling loses the
`WRITE_SECURE_SETTINGS` grant, which means setting the whole thing up again.

**To actually test the app** you need that grant:

```bash
adb shell pm grant com.soul_99.suIMD android.permission.WRITE_SECURE_SETTINGS
```

Most of the interesting behaviour also wants a Shizuku fork installed and configured. Note
that the Play Store build of Shizuku is the one build none of this works with — see the
warning at the top of the Shizuku section in Settings.

---

## How the code is laid out

28 Gradle modules, in four layers. The rule that matters is the **direction of dependency**:

```
app ──────────────► feature:* ──────────► domain:use-case ──────► domain:model
                        │                       │
                        └──► ui, design-system  └──► domain:repository, domain:framework
                                                          ▲
                            data:*, framework:*, service ──┘
```

- **`domain:model`** — pure Kotlin. No Android, no coroutines-on-a-dispatcher, no injection.
  This is where the rules live: what a default is, what "configured" means, what a revert is
  allowed to put back. It is a plain JVM library on purpose, which is what makes the host
  tests below possible.
- **`domain:use-case`** — one class per thing the app does. Business logic, expressed against
  the interfaces in `domain:repository` and `domain:framework`, never against Android types.
- **`domain:framework` / `framework:*`** — an interface per platform capability
  (`PackageManagerWrapper`, `ShizukuWrapper`, `SecureSettingsWrapper`, …) and its
  Android implementation. **New platform calls go behind a wrapper**, so a use case stays
  testable and so there is one place to look when a call misbehaves on one OEM.
- **`data:*`** — Room, and the Proto DataStore that holds every preference.
- **`feature:*`, `ui`, `design-system`** — Compose. `design-system` holds anything reusable
  (`GetoIcons`, `DialogContainer`, `emphasised`); features hold screens.

If you are unsure where something belongs, ask this: *would this still be true on a device
that is not Android?* If yes, it belongs in `domain:model`.

---

## Style

Formatting is **ktlint via spotless**, applied through an init script:

```bash
./gradlew --init-script gradle/init.gradle.kts spotlessApply
```

Rules are in [`.editorconfig`](.editorconfig) — trailing commas on, Composable function
names exempt from the naming rule.

Beyond formatting, match the file you are editing. Two conventions are worth stating because
they are unusual and they are enforced in review:

**Licence headers are maintained by hand.** Spotless's header enforcement is deliberately
switched off (the reasoning is in `gradle/init.gradle.kts`), because it replaces headers
rather than adding to them and would strip the fork's modification notice. **Copy the header
from the file next to yours.** A file this fork wrote or changed carries both lines:

```kotlin
/*
 *
 *   Copyright 2023 Einstein Blanco
 *   Modifications Copyright 2026 soul_99 (suIMD)
 *
 *   Licensed under the GNU General Public License v3.0 (the "License");
 ...
```

**Comments say *why*, not *what*.** The code says what it does. A comment earns its place by
recording the reason a thing is the way it is — the bug it prevents, the alternative that was
tried and failed, the ordering that is load-bearing. If a comment would be obvious from the
line below it, delete it.

---

## Strings and translations

Every user-visible string lives in a `strings.xml`. **There are eleven locales** — English
plus `ar`, `b+pt+BR`, `b+zh+Hans`, `de`, `es`, `fr`, `hi`, `ja`, `ko`, `ru` — and a string
added to one has to be added to all of them.

```bash
python3 tools/check_translations.py
```

That checks the mechanical things a reader of the language would not have to check: every
name present, no invented names, format specifiers surviving intact, XML valid. Run it before
you push.

Three traps that have each cost a build:

- **`emphasised(text, names)`** bolds a substring by searching for it. The name string has to
  appear **verbatim** inside the sentence in *every* locale. A translation that inflects the
  word — "службу" where the name says "служба" — silently loses its bolding.
- **aapt strips leading and trailing whitespace** from an unquoted string. Separators and
  spacing belong in the Kotlin that joins the strings, not in the resource.
- **Apostrophes must be escaped** as `\'` in XML — an unescaped one is an aapt error, not a
  typo. French is full of them, and so is English (`IMD app\'s`).

---

## Tests and checks

There is no device-free way to run the Compose or Android layers, but the rules that matter
most are in `domain:model`, which is plain Kotlin — so they can be:

```bash
bash tools/host-tests/run.sh        # needs kotlinc on PATH
```

This compiles `domain:model` together with `tools/host-tests/DomainLogicTests.kt` and runs a
few hundred assertions about defaults, encoding round-trips, the overlay master switch, fork
behaviour and the settings-to-hide fallbacks.

**If you change domain logic, add an assertion.** If you change a default, expect several
existing ones to fail — read them before you edit them, because each one is written down for
a reason that is usually in the comment above it.

---

## Things that need extra care

These are the review sticking points. None of them is negotiable, and most exist because
something once went wrong.

**Nothing may reach the network.** The app has no `INTERNET` permission and never will. No
analytics, no crash reporting, no update check, no dependency that phones home. F-Droid
builds this from source; a dependency that is not FOSS, or that fetches anything at build
time, cannot ship.

**A revert may only put back what this app took away.** Restoring is replayed from a recorded
debt — never granted afresh. An app installed later under a package name IMD once held is not
the app it took the permission from, and does not inherit it.

**Half-hidden is the worst outcome on the way in.** If hiding fails, the launch is abandoned
and the device is left alone: the target app still detects whatever remained switched on and
refuses to run, and the user is now looking at a dialog with their settings off for an app
that never opened. On the way *out* the rule inverts — restoring four of five is strictly
better than none, so a revert reports failures and keeps going.

**A default must never change under an existing install.** Changing what a fresh install
starts with is fine. Letting that reach an install that has been behaving the old way is not.
The pattern is a one-shot migration keyed on a marker field, guarded by
`setupNoticeVersion != 0` for "this install existed before today" — see
`MigrateRevertDefaultsUseCase`, which does this for both default configurations.

**Anything shown as filled in must actually be stored.** A field that displays a derived
default while storage holds a blank produces the worst kind of bug report: everything looks
configured and the app insists it is not. If the UI shows it, write it.

**Proto field numbers are never reused.** Add new fields at the next free number; retire old
ones with `reserved`. A reused number reads one install's old data as another field's value.

**The exported surface stays shut by default.** The Tasker/MacroDroid receiver needs both a
master switch and a matching per-install auth key before it will act. Anything new that can
be triggered from outside the app needs the same, and needs saying out loud in the PR.

---

## What else to update with your change

A change to behaviour is not finished when it compiles:

- **[README.md](README.md)** — if a user-facing feature changed.
- **[SUIMD.md](SUIMD.md)** — section 3 gets a version-history entry; section 2's flowcharts
  are regenerated from `tools/logics/` whenever a logic changes, so the picture and the code
  never disagree.
- **In-app help** — the setup page strings (`help_*` in `feature/settings`) are the first
  thing a new install reads. If your change alters what somebody has to set up, it belongs
  there too, in all eleven locales.
- **`fastlane/metadata/android/en-US/changelogs/<versionCode>.txt`** — the release note
  F-Droid shows. The file is named after the `versionCode`, not the version name.

---

## Commits and pull requests

- Write commit messages for somebody reading the log a year from now: what changed and why,
  not "fixes".
- This repository is what F-Droid builds from, so keep commit subjects about the app —
  release-facing, not workflow chatter.
- Branch from `master`. CI builds every pull request; a red build will not be merged.
- Tags are `vX.Y` (`v2.0`, `v2.1`), matching the GitHub release title.
- Bumping a release means: `versionCode` **and** `versionName` in `app/build.gradle.kts`, a
  new changelog file named after the new `versionCode`, the SUIMD.md history entry, and the
  logic flowcharts if anything they draw has moved.

---

## Licence

This project is licensed under the **GNU General Public License v3.0**. Contributions are
accepted under the same licence — by opening a pull request you agree that your work is
licensed under GPL-3.0.

Every file you add carries the header described above. Full attribution, the notice of
modification GPL-3.0 §5(a) requires, third-party notices and the trademark position are set
out in [SUIMD.md](SUIMD.md) section 4.
