# Changelog

What changed in each release, newest first, in terms of what it does for you.

The full technical history - every bug found in the original Geto, what caused it and the reasoning
behind each fix - is in [SUIMD.md § 3](SUIMD.md).

## v3 - 3 September 2026

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
- **The dark theme's green is calmer** - the switches and buttons no longer read as a
  highlighter, which was most obvious with six of them stacked in the settings manager.
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
