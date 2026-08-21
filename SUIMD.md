# IMD — SU IMD, Shut up! it’s my device

A fork of [Geto](https://github.com/JackEblan/Geto) by Jack Eblan, modified by
soul_99 (Dr. Utkarsh Rajput). GPL-3.0, same as the original.

- Package name: `com.soul_99.suIMD`
- Launcher label: **IMD** (full form **SU IMD — Shut up! it’s my device**)
- Installs alongside stock Geto — different package, so both can coexist.

Internal Kotlin packages are still `com.android.geto.*`. Only the `applicationId` and the
app label changed, which keeps the diff against upstream small and reviewable. Nothing
about that is visible on the device.

---

## Building

This project is Kotlin + Compose + Hilt + Room + Protobuf DataStore, so it needs Gradle,
the Android SDK, and Google's Maven. Two ways to get an APK.

### Option A — GitHub Actions (no Android Studio needed)

1. Create a repository (private is fine) and push this source to it.
2. `.github/workflows/Build-SU_IMD.yml` runs on every push to `master`/`main`, and can also
   be triggered by hand from the Actions tab ("Build SU_IMD APK" → Run workflow).
3. When it finishes, download the **SU_IMD-debug-apk** artifact from the run page. Inside is
   `SU_IMD-debug-<sha>.apk`.

The workflow installs JDK 21 (the project pins `toolchainVersion=21` in
`gradle/gradle-daemon-jvm.properties`), raises the Gradle heap for CI, and runs
`:app:assembleDebug`. Upstream's spotless and instrumentation-test jobs were removed —
they need an emulator and a formatter run that would fail the build for cosmetic reasons.

### Option B — Android Studio

Open the project, let it sync, Build → Build APK. Output lands in
`app/build/outputs/apk/debug/`.

**If the Gradle download times out.** `services.gradle.org` is unreachable or very slow
from some networks, and Android Studio reports:

```
Could not install Gradle distribution from 'https://services.gradle.org/distributions/gradle-9.3.1-bin.zip'.
Reason: java.net.SocketTimeoutException: Connect timed out
```

`gradle/wrapper/gradle-wrapper.properties` already points at Gradle's own GitHub mirror
instead, with the published SHA-256 so Gradle verifies the download before unpacking:

```
distributionUrl=https\://github.com/gradle/gradle-distributions/releases/download/v9.3.1/gradle-9.3.1-bin.zip
distributionSha256Sum=b266d5ff6b90eada6dc3b20cb090e3731302e553a27c5d3e4df1f0d76beaff06
```

If that is slow too, download the zip in a browser (browsers resume; the JVM's HTTP client
does not) and point the wrapper at the local copy — Windows path, note the forward slashes
and the escaped colon:

```
distributionUrl=file\:///C\:/Users/you/Downloads/gradle-9.3.1-bin.zip
```

Then File → Sync Project with Gradle Files.

Getting past the wrapper is only the first download. The sync that follows pulls several
hundred megabytes of AndroidX, Compose, Hilt and Room from `dl.google.com` and
`repo1.maven.org`. `gradle.properties` raises the HTTP timeouts from Gradle's 30 second
defaults to help with that, but if your link is the problem rather than
`services.gradle.org` specifically, Option A does all of this on GitHub's runners instead.

### Signing

**No signing key ships with this source, and none should ever be committed.**

Debug builds use Android Studio's own debug key, which is generated per machine. Release
builds are signed either through **Build → Generate Signed App Bundle / APK**, or by
putting a `keystore.properties` next to `settings.gradle.kts`:

```
storeFile=C:/path/to/your.jks
storePassword=...
keyAlias=...
keyPassword=...
```

That file and `*.jks` are both gitignored.

**Use the same key for every build you install.** Android only accepts an update signed by
the key that signed what is already on the device, so switching keys means uninstalling
first — and an uninstall loses the `WRITE_SECURE_SETTINGS` grant, which then has to be
granted again over ADB or Shizuku. Back the keystore up somewhere outside the repository;
losing it means every future build has to be installed fresh.

---

## First run

The app opens on a two-page setup screen. The first page cannot be passed until both
permissions are in place. It is gated on the live system state, not on a "seen the intro" flag — the ADB grant
happens outside the app and can be lost to a reinstall, and a stored flag would leave the
app looking functional while every settings write silently failed.

1. **Secure settings access.** The screen shows the exact command with a copy button and
   re-checks itself every time you come back to the app:

   ```
   adb shell pm grant com.soul_99.suIMD android.permission.WRITE_SECURE_SETTINGS
   ```

   With a PC: enable USB debugging and run it. Without a PC: tap **Use Shizuku** and the
   app runs that command through Shizuku itself. No root either way. See section 9.

   `WRITE_SECURE_SETTINGS` is `signature|privileged|development`; the development flag is
   what lets `pm grant` hand it to a sideloaded app.

2. **Notifications.** Applying settings posts an ongoing notification whose Revert action is
   how your device gets put back. Without it, changes stay applied — which is why setup
   treats it as mandatory rather than optional.

The second page is informational: it names the two things that have to be configured by
hand, because neither can be done from a wizard — the Shizuku values have to be read out of
the Shizuku app, and which accessibility services to manage is a personal choice. Both are
silent when left unset, which is exactly the sort of thing that gets diagnosed as "the app
is broken" months later, so the page exists to say so up front.

Then, in the app's own Settings:

3. **Shizuku restart** (Settings → Shizuku). Open **Advanced** first — the toggle stays
   greyed out until all three fields are filled, and tapping it before then just says
   *Please fill advanced section* and opens Advanced for you.

   In Shizuku, open **View intents**, and copy across:

   | Shizuku shows | Paste into |
   | --- | --- |
   | Action | **Service start intent (action)** |
   | Package | **Package name** |
   | Extras → `auth:` | **Authentication key (extras > auth:)** |

   Then turn on **Restart Shizuku service**. Reading the values off the Shizuku screen
   rather than deriving them means a stealth-renamed install works with no special case.

4. **Accessibility services** (Settings → Accessibility → *Accessibility services to hide*):
   tick the services you want switched off when a "Hide Accessibility Services" app setting
   is applied. Nothing is hidden until you tick something.

---

## What changed

### 1. Shizuku comes back after a revert

**Problem.** Reverting *hide developer options* / *USB debugging* / *wireless debugging*
turns the flags back on, but the Shizuku service died when they went off and does not
restart itself.

**Fix.** A revert that sets `development_settings_enabled`, `adb_enabled` or
`adb_wifi_enabled` back to `1` fires Shizuku's start broadcast: an explicit broadcast with
action `<shizuku-package>.START` carrying the string extra `auth`. This is the intent API
in [thedjchi's Shizuku fork](https://github.com/thedjchi/Shizuku/releases); upstream RikkaApps
Shizuku does not listen for it, and the app tells you so rather than silently doing nothing.

Details worth knowing:

- There is a **1.5 second pause** before the broadcast. Writing `adb_wifi_enabled=1` does
  not make adbd listening instantly — it has to restart and re-advertise over mDNS, and a
  start attempt that lands before that just fails.
- The whole revert (settings write, accessibility restore, Shizuku poke) runs under
  `NonCancellable`, and `RevertSettingsBroadcastReceiver` now uses `goAsync()`. Without
  those, backing out of the settings screen mid-revert silently skipped the restart, and a
  revert triggered from the notification raced the low-memory killer.
- `QUERY_ALL_PACKAGES` is declared. A stealth-renamed Shizuku is not discoverable through
  a static `<queries>` entry, and without visibility the broadcast is dropped rather than
  delivered. This app is sideloaded, not shipped through Play.

### 2. Accessibility services actually stop

**Problem.** Geto's "Hide Accessibility Services" template wrote **Global**
`accessibility_enabled=0`. That key lives in **Secure**, not Global, and even in the right
table it only flips a flag — services listed in `Settings.Secure.enabled_accessibility_services`
keep running. The app also had no idea which services existed.

**Fix.**

- The template now targets `SECURE`.
- Settings lists every installed accessibility service, marks which are currently on, and
  lets you tick the ones suIMD should manage. Services suIMD has switched off stay in the
  list so you can still find them; services left behind in the system value by an
  uninstalled app show up too, so you can clear them out.
- On apply, the ticked services are removed from `enabled_accessibility_services`. On
  revert, exactly the ones this app removed go back.

The rules being enforced, and why:

- **Surgical edits only.** The enabled-services string is never saved and restored
  wholesale. If you switch some other service on while the banking app is open, a blind
  restore would delete it; if you switch one off, a blind restore would resurrect it.
- **Nothing is re-enabled that was already off.** A managed service that was off when the
  app launched is not claimed, so reverting will not switch on something you had disabled
  yourself.
- **Holds are per target app.** Two apps hiding overlapping sets used to share one global
  record: reverting app A switched services back on while app B was still open, and B's own
  revert then found nothing to do. Each app now records its own hold, and a service comes
  back only once no app is still holding it.
- **The record is written before the system setting.** A stale record is harmless — the
  revert finds the service already enabled and skips it. A service switched off with no
  record could never be switched back on.
- **One writer for `accessibility_enabled`.** When suIMD owns the services list for an app,
  the raw `accessibility_enabled` row is skipped and the flag is derived from the resulting
  list. Two writers left the flag contradicting the list it describes.

### 3. Three tabs

**Favourites** (the new landing tab) · **All Apps** · **Settings**.

- A star sits at the right of every row in All Apps, and at the bottom-right of a per-app
  settings screen — immediately left of the launch arrow.
- Favourites shows the app name only. All Apps keeps the package name underneath, where it
  is what tells two similarly-named apps apart.
- Favourites options (the slider icon next to the search box):
  - **Sort** — Custom or A–Z. Custom is the order you added them; **Reorder** opens a
    move-up/move-down list. (Move buttons rather than drag: long press is already bound to
    launch-or-modify on this tab, and a drag handle competing with that gesture is how you
    get accidental launches.)
  - **View** — List or Grid.
  - **Default tap** — *Tap launches* (long press modifies) or *Tap modifies* (long press
    launches).
- Uninstall an app and it disappears from Favourites rather than leaving a dead tile. Its
  saved entry is kept, though, so an app that is merely unavailable right now — unmounted
  SD card, paused work profile — comes back rather than being quietly deleted.

### 4. Launching a favourite applies its settings

A tap on the Favourites tab runs the same three steps a pinned shortcut does — apply the
app's configured settings, post the ongoing notification with the Revert action, then open
the app. Opening it without applying them would silently defeat the point of it being
there.

An app with nothing configured is simply opened; there is no point refusing to launch it
over a configuration you never made.

### 5. Shortcut icons match the original app icon

Upstream rendered the target app's icon to a PNG and pinned it with
`IconCompat.createWithBitmap`, which tells the launcher "this is a finished picture, do not
touch it". The launcher then cannot apply its own mask or the standard adaptive inset, so
the shortcut ends up a different shape and size from the icon next to it.

The shortcut now hands over a **full-bleed adaptive bitmap**: the adaptive drawable's
background and foreground layers drawn unmasked onto a square, passed as
`createWithAdaptiveBitmap`, so the launcher applies its own mask and inset exactly as it
does for the real app. Legacy non-adaptive icons still go through as plain bitmaps.

The obvious approach — pointing the shortcut at the target app's own icon *resource* —
looks perfect and is not allowed: `ShortcutService.injectValidateIconResPackage` rejects any
resource icon whose package is not the shortcut owner's, and throws from the system server
on both pin and update. That is written down in the source so nobody tries it again.

### 6. About and the footer

Settings ends with an **About** section of three lines:

- *App created by* **soul_99** — tapping the name opens a dialog with **View GitHub**
  ([soul-99](https://github.com/soul-99)) and the email address, which opens a mail app.
- *Fork of* **Geto app** — links to [JackEblan/Geto](https://github.com/JackEblan/Geto).
- **GNU General Public License v3.0** — links to the licence text.

Below it, greyed out, the logo and *"Long live free and open source software!"*

### 7. Re-enable settings/services, from the Favourites tab

**Problem.** The ongoing notification is the only way back. Swipe it away — or have the
launcher or a battery optimiser cull it — and the device is stuck: once developer options
are hidden there is no system screen left to switch them back on from, and the app that
hid them had no way to undo it either.

**Fix.** A button in the bottom-right corner of the Favourites tab opens
**Re-enable settings/services**: developer settings, USB debugging, wireless debugging,
accessibility services and Shizuku, each with a tick box, and one Re-enable button that
does all the ticked ones and closes.

- Every row also carries its own small, understated button that does just that one thing
  and leaves the ticked set alone — for retrying one stubborn item without disturbing a
  selection you want to keep. That one does *not* close the dialog.
- The ticked set is persisted, so it survives closing the dialog, the app, and the device.
  An empty stored set is read as "all of them" rather than "none": with nothing ticked the
  Revert button does nothing, so the distinction is not worth keeping.
- Each target is written unconditionally rather than looked up against some app's stored
  profile. This is not a revert of a particular app — the user has said what they want back.
- Accessibility services switches on everything picked in Settings, plus anything still
  held for any target app, **whatever state they were last in** — this is a re-enable, not
  a release. A release only puts back what there is a record of switching off, and the
  reason someone opens this dialog is usually that the record is gone. The write happens
  even when there is nothing to add, because `accessibility_enabled` can be left at 0 by
  an interrupted apply and the wrapper derives that flag from the list.
- Shizuku ignores the "Restart Shizuku service" toggle. That toggle governs the *automatic*
  restart on revert; pressing this is an explicit instruction. It still needs the auth key.
- The 1.5 second pause before the Shizuku broadcast only happens when this same run has
  just switched a transport back on. Asking Shizuku to start when nothing else changed is
  immediate.
- The whole thing runs under `NonCancellable`. Closing the dialog mid-revert must not leave
  it half done.
- The result is reported per target. A partial result says "restored 3 of 5" rather than
  rounding up to "done" — being told everything is back while Shizuku is still down is
  worse than being told nothing.

### 8. App icon

The launcher icon is the gear-and-key mark as vector geometry. The scripts that produce it
live in `design/`, so it is sharp at every density and there is no bitmap to re-trace if it
ever needs changing. The two halves are built differently, on purpose:

- **The key is constructed.** It is rounded rectangles, so it is written as rounded
  rectangles: shaft, two teeth, the bow, the hole, and the six small concave fillets where
  those meet. The bow and the hole are rounded rectangles with fully rounded ends, *not*
  ellipses — the source's bow has a dead-straight right edge for fifty-odd rows, which no
  ellipse has. That model fits the measured outline to 0.16px rms; the best superellipse
  manages 0.85px.
- **The gear is measured.** It is drawn art rather than a textbook gear, and every attempt
  to model it — tangent lobe circles, superellipse, `cos(6θ)` lobes — was visibly wrong
  along the tooth flanks, by up to 26px in a 300px radius. `design/trace.py` samples the
  real outline at sub-pixel precision every quarter degree, averages the six rotational
  copies, mirrors about the tooth axis, and fits one 60° sector with eight cubic Béziers
  which `gen.py` rotates six times. Cutting the sector at a notch minimum, where symmetry
  forces the tangent perpendicular to the radius, makes the six copies join smoothly for
  free.

`design/verify.py` re-renders the whole thing in the source PNG's own coordinates and diffs
it against the original: 0.25% of the frame differs by more than a sixth of a channel, and
all of that is anti-aliasing plus the ~1.5px of six-fold asymmetry in the source artwork
itself — which the icon deliberately does not reproduce.

The gear is sized against upstream Geto rather than against the adaptive safe zone, so the
two sit together on a home screen without one looking oversized: Geto's gear measures 36.20
units across the 108-unit viewport, and this one is set 10% above that.

Shipped as a proper adaptive icon — `ic_launcher_foreground` on a solid background, with
`ic_launcher_monochrome` (the gear silhouette) for themed icons on Android 13+. Legacy
`mipmap` PNGs are generated at all five densities for pre-26 launchers.

### 9. Getting the permission without a computer

The first-run screen offers **Copy command** and **Use Shizuku** side by side, because
which one is easier depends entirely on whether there is a PC within reach. Use Shizuku
asks Shizuku for its own permission, then has it run
`pm grant <package> android.permission.WRITE_SECURE_SETTINGS`.

- It goes through the binder Shizuku publishes, never through its package name, so a
  renamed or hidden install works identically. The app declares `rikka.shizuku.ShizukuProvider`
  under its *own* authority and Shizuku pushes the binder in; nothing here queries for
  Shizuku, launches it, or names it.
- `pm grant` rather than a direct `IPermissionManager` call: the framework moved permission
  APIs off `IPackageManager` in API 30 and gave `grantRuntimePermission` a fourth argument
  in API 35, so a direct binder call needs a branch per platform. One command string works
  unchanged across all of them.
- `Shizuku.newProcess` is private and deprecated as of API 13.1.5, so it is reached by
  reflection with a matching keep rule in `proguard-rules.pro`. If it ever disappears, the
  call returns false and the ADB command on the same screen still works.
- The screen re-reads the real permission state after the grant rather than trusting the
  result, and says which of "not running", "refused" and "could not run it" happened.

### 10. Reverting to what the setting really was

**Problem** (present in upstream). Revert writes the *Value on revert* the user typed when
the profile was written. That is a prediction, not an observation. Hide developer options
on a device where they were already off, revert, and they come **on** — and developer
options being off is precisely the state in which there is no settings screen left to
switch them back off from.

**Fix.** `ApplyAppSettingsUseCase` reads the current value of every setting it is about to
write and records it against that app, before writing anything and under `NonCancellable`.
`RevertAppSettingsUseCase` writes those values back instead of the configured ones, and
drops the record only once the writes have succeeded — a record left behind after a failed
revert is what lets a retry still get it right.

- The record is per target app, in the same preferences file as the accessibility holds,
  encoded by `SettingSnapshot`. Values are arbitrary strings, so the separators are ASCII
  control characters rather than anything a settings value might contain.
- "Never set" and "set to empty" are different, and are stored differently: reverting to
  *unset* is not something the settings API can express, so a setting that had no value
  falls back to the configured one rather than writing an empty string.
- A profile with no record — applied by an older build, or whose record was lost — falls
  back to the configured value and behaves exactly as it used to.
- **The Re-enable control does not consult this.** It is an explicit "switch these on",
  used when the record is most likely gone; deferring to a previous state there would
  defeat the point of the button.

### 11. Icons: what was tried, and reverted

An intermediate version rendered every icon in the app from its adaptive layers and masked
them all to one squircle so the lists would match. It was worse, and it is worth recording
why so it is not tried again:

- Adaptive foregrounds are drawn on a 108-unit canvas of which a launcher only ever shows
  the middle 72. Painting the whole canvas into the tile renders every logo at two thirds
  of the size the launcher shows it — which is why most icons came out visibly small.
- `LauncherActivityInfo.getIcon` already returns whatever treatment the OEM launcher
  applies. On devices that mask it, the result was a second mask over the first.
- Legacy icons go through `ShortcutIconFactory`'s bitmap fallback, so masking here quietly
  made **pinned shortcuts** wrong too — the one thing that was already right.

Matching a launcher exactly means reproducing per-OEM behaviour that is not queryable, so
the icon pipeline takes what the system gives it and passes it through untouched. That is
already the right answer for shaping: `LauncherActivityInfo.getIcon` returns the badged,
density-correct icon, and drawing an `AdaptiveIconDrawable` applies the device's own mask —
so the shape in the list is the shape the launcher uses, for free.

One real bug did come out of it. Every icon was rasterised at *its own* intrinsic size,
capped at 192px. A legacy icon whose intrinsic size is 48px was therefore rendered at 48px
and then scaled up into a 50dp slot — four times the pixels it had on a high-density
screen, which is why some icons read as small and soft next to their neighbours. Every icon
is now rendered at the same 192px square. The search field kept
its Material search-bar shape around a `BasicTextField` — see *Other fixes* for why
Material3's own `SearchBar` is unusable here.

### 12. The Favourites tab opens without a spinner

It was fed by the same flow as All Apps, so it could not show three starred apps until
every launcher entry on the device had been enumerated and every icon rendered — a spinner
on every cold start, for a list the user can see is tiny. It now resolves each favourite
directly through `getActivityList(packageName, user)`: a handful of lookups instead of a
few hundred, sharing the same rendered-icon cache as the full list.

### 13. A one-time tip

Shown once past setup, gated on a stored flag rather than on "setup just finished" so that
it also reaches anyone upgrading into this version. It says the one thing that otherwise
gets learned the hard way: developer options do not have to stay on for Shizuku, because
Shizuku enables USB debugging itself with its own `WRITE_SECURE_SETTINGS` — so the obvious
setup, leaving developer options on so Shizuku works, fights every profile that hides them.

### 14. Speed

- **The star reacts on the tap.** It used to be driven straight from the persisted value,
  so it waited for a DataStore serialise → write → fsync → re-emit round trip before
  changing. It now flips locally and lets the persisted value take over when the write
  lands, so a failed write still corrects itself.
- **Starring an app no longer re-sorts every app on the device.** The All Apps list combined
  the launcher list with the whole of `UserData`, and favourites live in `UserData` — so
  every star tap re-filtered and re-sorted the full list. Ordering now depends on a
  three-field projection with `distinctUntilChanged`, and only search re-runs on the rest.
- **One binder call instead of one per app.** Building the list called
  `getPackageInfo` per installed app to read its install time. It now reads them all in a
  single `getInstalledPackages` query.
- **Icons are rasterised at 192px** instead of their intrinsic size, which for an
  xxxhdpi adaptive icon meant keeping a 432px bitmap in memory per installed app.
- **Shizuku fields are committed on a pause**, half a second after the last keystroke,
  rather than writing the whole preferences proto on every character.
- **Icons are rendered once, not on every package event.** The launcher list is rebuilt
  whenever any package is added, removed, changed, or becomes (un)available, and
  `onPackageChanged` fires for routine things — so a few hundred icons were being loaded,
  drawn, masked and PNG-encoded because one of them changed. They are now cached by
  component and update time, and the cache is replaced wholesale each rebuild so
  uninstalled apps cannot accumulate.
- **Coil is given a stable memory-cache key.** The icon arrives as a byte array, which Coil
  cannot key on, so every icon was decoded again each time its row scrolled back into
  view. This was the single biggest source of scroll jank.
- **The launcher list no longer compares icon bytes.** `LauncherAppsActivityInfo.equals`
  ran `contentEquals` over every icon, which the `distinctUntilChanged` on the list then
  did a few hundred times per package event. The icon is derived from fields that are
  already compared, so it is simply left out.
- **Favourites ordering is driven by a two-field projection**, the same fix already made
  for All Apps — otherwise ticking a box in the Re-enable dialog re-ordered the list.
- Dead code removed along the way: the `isShizukuInstalled` probe and its ViewModel state
  (the fields say what to talk to now), the unused sort-order string, and the unfavourite
  plumbing on the Favourites tab now that the star is gone from it.

---

## Other fixes made along the way

These were found while working on the above and are not upstream behaviour:

- **The search box could not be typed into.** `SearchBar(state, inputField)` is only the
  collapsed half of Material3's expressive search API — it suppresses the soft keyboard and
  expects an `ExpandedFullScreenSearchBar` to be rendering results elsewhere. Upstream had
  no second half, so tapping the field focused it, opened no keyboard, and never collapsed
  again. Both app lists now use an ordinary text field that filters in place.
- **Tapping Revert on a notification could revert the wrong app.** Every revert
  `PendingIntent` used request code `0`, and `PendingIntent` identity ignores extras — so
  applying a second app rewrote the first notification's extras. Now keyed by notification
  id.
- **Unticking a setting did nothing.** Apply and revert wrote every row regardless of its
  checkbox. They now write only ticked rows.
- **A failed write skipped the remaining settings.** The `all { }` short-circuited, leaving
  earlier writes committed and later ones silently skipped. Every setting is now attempted
  before the result is reported.
- **The revert button went dead** after one tap when all rows were unticked — the result
  state was never reset, so the flow stopped emitting.
- **Tapping Revert could revert the wrong app.** Every revert `PendingIntent` used request
  code `0`, and `PendingIntent` identity ignores extras, so applying a second app rewrote
  the first notification's component name. Now keyed by notification id, in one shared
  builder rather than three copies.
- Tap-to-launch no longer crashes on an app uninstalled between the list emission and the
  tap.

---

## Verifying without a device

Google's Maven is unreachable from the environment this was written in, so the project
could not be compiled here. What was done instead:

- **`tools/host-tests/run.sh`** — 113 assertions over the pure logic in `:domain:model`,
  which is a plain JVM library with no dependencies and so runs on a desktop JVM. Covers
  the accessibility hold/release arithmetic (including the two-app interleaved scenario in
  both revert orders), the app-list ordering and search, the favourites ordering, the
  manual-revert target encoding, and the setting-key predicates. Needs `kotlinc` on PATH.
- The **whole domain layer** — `:domain:model`, `:domain:common`, `:domain:framework`,
  `:domain:repository`, `:domain:use-case` — type-checked with `kotlinc` against hand-written
  stubs carrying the real `kotlinx.coroutines` signatures. Clean.
- Both new framework modules type-checked against a real AOSP `android.jar` (API 36), so
  the `Settings.Secure`, `ComponentName`, `AccessibilityManager` and `PackageManager` calls
  are known to resolve.
- The Compose link APIs used in Settings (`LinkAnnotation.Url`, `LinkAnnotation.Clickable`,
  `TextLinkStyles`, `withLink`) checked against `ui-text`'s published `api/current.txt`
  rather than from memory.
- `.proto` files compiled with a real `protoc`, and every field accessor used in
  `UserPreferencesDataSource` diffed against the generated Java and Kotlin.
- Whole-repo static audits: resource references, string format arities, import resolution,
  cross-module dependency reachability, call-site arity, Hilt binding completeness.

None of that is a substitute for a compile. Expect to fix a stray import or two on the
first CI run.

## Known limitations

- The Shizuku restart is fire-and-forget. There is no in-app confirmation that Shizuku came
  back — check Shizuku itself.
- The 1.5 second pause before the start broadcast is a fixed guess, not a poll.
- A setting unticked *between* applying and reverting is skipped on revert, so it stays at
  its launch value. Revert first, then untick.
