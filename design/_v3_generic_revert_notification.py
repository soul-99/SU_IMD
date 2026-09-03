#!/usr/bin/env python3
"""
r3 — one revert notification, generic, for every launch; the per-app route removed.

The author's instruction, after device-testing r2b3d and being asked which notification a
first launch should carry: *"do one thing no need to send app icon notifications and make it
easy and uniform, IMD send only generic revert notifications from now"*, and then *"remove it
but do it carefully not to break anything else's functioning"*.

⚠ **This reverses G1.** The kickoff's §0.1 asked for the opposite — the first launch carrying
the launched app's icon — and the author changed his mind when the trade was put to him. What
is built here is the later instruction.

### What goes

`postAppliedSettingsNotification` branched on the **unhiding** framework: `Memory` posted a
per-app notification keyed on `componentName.hashCode()` whose button was
`RevertSettingsBroadcastReceiver` (that one app's record, and nothing else), `RevertToDefault`
posted the shared generic one. Now every launch posts the shared one, under the one fixed id,
and the whole per-app route goes with it:

  AppliedSettingsNotification.kt      deleted — the builder and its `launchedAppIcon` helper
  RevertSettingsBroadcastReceiver.kt  deleted — the per-app revert button
  AndroidManifest.xml                 the receiver's declaration and its intent filter
  NotificationRepostBroadcastReceiver its per-app rebuild branch
  GetoApplication                     REVERT_MEMORY_CHANNEL_ID created -> deleted

⚠ **It also fixes a live bug, which is why the uniform answer is the safe one.** Under
**IMD defaults + Memory — what every new install gets** — a launch hid the *device-wide* list
and then posted the *per-app* notification, whose button is
`revertAppSettingsUseCase(componentName)`. That use case opens with
`getAppSettingsByComponentName`, so with no per-app profile it returned `EmptyAppSettings` and
wrote nothing: the tap cancelled the notification and reverted nothing at all, leaving the
device hidden with the only way back gone. It is the fourth instance of handover_3 §2.3's
pattern — a call that is the way back from *this* hide driving the named function's machinery
instead of the framework's. The generic notification's button is
`settingsHiddenRunner.unhide()`, which follows the framework and is right in all four
combinations, so posting it everywhere closes this by construction.

⚠ **The trampoline keeps `ACTION_REVERT_SETTINGS` as a migration shim.** An install upgrading
from r2b3d can have a per-app notification standing in the shade, and its PendingIntent still
names that action. Dropped, a tap would clear the notification and revert nothing — exactly
the bug above, handed to an upgrading user. Routed to the framework-following unhide instead,
it does what the notification it came from promised.

⚠ **The two `cancel(componentName.hashCode())` calls stay**, in `AutoRevertRunner` and
`AutoUnhideWatcher`. Nothing posts under those ids any more, but a notification left standing
by the previous build does, and these are what clear it. Their comments are corrected to say
so rather than left describing a route that no longer exists.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

POST = ("broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/"
        "PostAppliedSettingsNotification.kt")
EFFECT = "feature/apps/src/main/kotlin/com/android/geto/feature/apps/AppLaunchEffect.kt"
APP_SETTINGS = ("feature/app-settings/src/main/kotlin/com/android/geto/feature/appsettings/"
                "AppSettingsScreen.kt")
SHORTCUT = "app/src/main/kotlin/com/android/geto/activity/shortcut/ShortcutActivity.kt"
TRAMPOLINE = ("broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/"
              "RevertTrampolineActivity.kt")
REPOST = ("broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/"
          "NotificationRepostBroadcastReceiver.kt")
MANIFEST = "broadcast-receiver/src/main/AndroidManifest.xml"
APPLICATION = "app/src/main/kotlin/com/android/geto/GetoApplication.kt"
WRAPPER = ("framework/notification-manager/src/main/kotlin/com/android/geto/framework/"
           "notificationmanager/AndroidNotificationManagerWrapper.kt")
AUTO_REVERT = ("broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/"
               "AutoRevertRunner.kt")
WATCHER = ("broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/"
           "AutoUnhideWatcher.kt")
AUTO_HIDE = ("broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/"
             "AutoHideRunner.kt")
REVERT_NOTIFICATION = ("broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/"
                       "RevertToDefaultNotification.kt")

DELETIONS = [
    ("broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/"
     "AppliedSettingsNotification.kt"),
    ("broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/"
     "RevertSettingsBroadcastReceiver.kt"),
]

# The whole file, because every line of the old one was about the branch that is going.
POST_NEW = '''/*
 *
 *   Copyright 2023 Einstein Blanco
 *   Modifications Copyright 2026 soul_99 (suIMD)
 *
 *   Licensed under the GNU General Public License v3.0 (the "License");
 *   you may not use this file except in compliance with the License.
 *   You may obtain a copy of the License at
 *
 *       https://www.gnu.org/licenses/gpl-3.0
 *
 *   Unless required by applicable law or agreed to in writing, software
 *   distributed under the License is distributed on an "AS IS" BASIS,
 *   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *   See the License for the specific language governing permissions and
 *   limitations under the License.
 *
 */
package com.android.geto.broadcastreceiver

import android.content.Context
import com.android.geto.common.AutoUnhideWatch
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.REVERT_TO_DEFAULT_NOTIFICATION_ID

/**
 * Posts the notification that offers the way back from a launch.
 *
 * **One notification, one id, whatever the two frameworks say** — the author's instruction in
 * r3, replacing a branch that posted a per-app notification under the memory function and the
 * generic one otherwise.
 *
 * Its button is the framework-following unhide rather than the named `Revert to default`
 * function — see `RevertToDefaultBroadcastReceiver`, which is what makes one notification
 * correct in all four combinations. Under the memory function it puts back what the hide
 * measured; under Revert to default it drives the configured list. That is handover_3 §2.3's
 * rule: a notification is the way back from *this* hide, so it follows the framework.
 *
 * ⚠ **The old per-app branch was wrong under IMD defaults + Memory**, which is what every new
 * install gets. The hide there is the device-wide list, but the notification it posted offered
 * a per-app revert — and `RevertAppSettingsUseCase` opens on `getAppSettingsByComponentName`,
 * so with no profile for that app the tap cancelled the notification and wrote nothing. The
 * uniform answer closes that by construction rather than by another branch.
 *
 * The fixed id is also what makes the "one notification only" rule work: a second launch lands
 * on the same id and replaces the first, rather than leaving a row of offers behind it.
 *
 * A free function taking the wrapper rather than a class holding it, because all the callers
 * already have the wrapper to hand — two of them as a composition local — and plumbing an
 * injected object into a composable to save one argument is not a trade worth making.
 */
fun postAppliedSettingsNotification(
    context: Context,
    notificationManager: AndroidNotificationManagerWrapper,
) {
    // ⚠ **The cascade, and it still earns its place.** This launch arrived into a window
    // something else had already hidden, so there is one shared debt — and IMD+'s own
    // notification, which is posted under an id of its own by a different builder, is standing
    // beside this one offering to undo its share of it. `cancelAll` sweeps it, and the post
    // below replaces the lot.
    //
    // ⚠ **A state, not an event, and that is `AutoUnhideWatch.collapsed`'s job.** The launch
    // sites derive it from the persisted records *before* they apply anything, so a process
    // death does not break a chain: the next launch reads the records, finds a debt
    // outstanding, and collapses again.
    if (AutoUnhideWatch.collapsed) notificationManager.cancelAll()

    notificationManager.notify(
        id = REVERT_TO_DEFAULT_NOTIFICATION_ID,
        notification = buildRevertToDefaultNotification(context = context),
    )
}
'''

EDITS: list[tuple[str, list[tuple[str, str, int]]]] = [
    (EFFECT, [
        (
            """                    postAppliedSettingsNotification(
                        context = context,
                        notificationManager = notificationManager,
                        unhidingFramework = launch.unhidingFramework,
                        componentName = launch.componentName,
                        icon = launch.icon,
                    )
""",
            """                    postAppliedSettingsNotification(
                        context = context,
                        notificationManager = notificationManager,
                    )
""",
            1,
        ),
    ]),
    (APP_SETTINGS, [
        (
            """                postAppliedSettingsNotification(
                    context = context,
                    notificationManager = androidNotificationManagerWrapper,
                    unhidingFramework = unhidingFramework,
                    componentName = appSettingsRouteData.componentName,
                    icon = activityIcon,
                )
""",
            """                postAppliedSettingsNotification(
                    context = context,
                    notificationManager = androidNotificationManagerWrapper,
                )
""",
            1,
        ),
    ]),
    (SHORTCUT, [
        (
            """                        postAppliedSettingsNotification(
                            context = this@ShortcutActivity,
                            notificationManager = androidNotificationManagerWrapper,
                            unhidingFramework = shortcutActivityUiState.unhidingFramework,
                            componentName = componentName,
                            icon = shortcutActivityUiState.applicationIcon,
                        )
""",
            """                        postAppliedSettingsNotification(
                            context = this@ShortcutActivity,
                            notificationManager = androidNotificationManagerWrapper,
                        )
""",
            1,
        ),
    ]),
    (TRAMPOLINE, [
        (
            """        val receiver: Class<*> = when (action) {
            ACTION_REVERT_SETTINGS -> RevertSettingsBroadcastReceiver::class.java
            ACTION_REVERT_TO_DEFAULT -> RevertToDefaultBroadcastReceiver::class.java
            ACTION_AUTO_HIDE_REVERT -> AutoHideRevertBroadcastReceiver::class.java
            else -> return null
        }
""",
            """        val receiver: Class<*> = when (action) {
            // ⚠ **A migration shim, not a live route.** Nothing posts a per-app revert
            // notification any more - r3 made every launch post the one generic notification -
            // but an install upgrading from r2b3d can have one standing in the shade, and its
            // PendingIntent still names this action. Sent to the framework-following unhide
            // rather than dropped, so a tap does what the notification it came from promised
            // instead of clearing itself and reverting nothing. It can go once nobody can
            // still be holding one.
            ACTION_REVERT_SETTINGS -> RevertToDefaultBroadcastReceiver::class.java
            ACTION_REVERT_TO_DEFAULT -> RevertToDefaultBroadcastReceiver::class.java
            ACTION_AUTO_HIDE_REVERT -> AutoHideRevertBroadcastReceiver::class.java
            else -> return null
        }
""",
            1,
        ),
        (
            """            // The two that can name a target. A per-app revert always does; an IMD+ revert does
            // only when the memory function was in force, and then the extra is the app whose
            // page it applied. "Revert to default" is about the whole device and carries
            // nothing. Copying a null extra is harmless - the receiver reads it as "no app",
            // which is exactly what an IMD+ run in the other mode means.
            if (action == ACTION_REVERT_SETTINGS || action == ACTION_AUTO_HIDE_REVERT) {
""",
            """            // The one action that can name a target. An IMD+ revert does so only when the
            // memory function was in force, and then the extra is the app whose page it
            // applied. Every other revert here is about the whole device and carries nothing.
            // Copying a null extra is harmless - the receiver reads it as "no app", which is
            // exactly what an IMD+ run in the other mode means.
            if (action == ACTION_AUTO_HIDE_REVERT) {
""",
            1,
        ),
    ]),
    (REPOST, [
        (
            """ * Which notification to rebuild is decided by the id it was posted under, which the intent
 * carries. The device-wide one has a fixed id of its own; every other id is a component
 * name's hash code, and the component name comes along so the rebuilt notification reverts
 * the same app the swiped one would have.
""",
            """ * Which notification to rebuild is decided by the id it was posted under, which the intent
 * carries, and since r3 every id this app posts under is one of the three named below. IMD+'s
 * carries a component name with it, so the notification that comes back reverts the same app
 * the swiped one would have.
""",
            1,
        ),
        (
            """        } else {
            val componentName =
                intent.getStringExtra(NOTIFICATION_EXTRA_COMPONENT_NAME) ?: return

            // No bytes to hand over: the icon the original was posted with was rasterised
            // by whoever posted it, and a bitmap is not worth carrying through a
            // PendingIntent extra. The builder asks the system for it instead, from the
            // component name that *is* carried - so the notification that comes back looks
            // like the one that was swiped away rather than a blank-faced copy of it.
            buildAppliedSettingsNotification(
                context = context,
                notificationId = notificationId,
                componentName = componentName,
                icon = null,
            )
        }
""",
            """        } else {
            // ⚠ **Every id this app posts under is named above.** Until r3 anything else was a
            // per-app revert notification keyed on `componentName.hashCode()`, and that route
            // is gone - so an unrecognised id can now only be one left standing by a build
            // before this one. A swipe there is taken at face value and it stays gone; the
            // generic notification the new build posts is what offers the way back.
            return
        }
""",
            1,
        ),
    ]),
    (MANIFEST, [
        (
            """        <receiver
            android:name="com.android.geto.broadcastreceiver.RevertSettingsBroadcastReceiver"
            android:exported="false">
            <intent-filter>
                <action android:name="ACTION_REVERT_SETTINGS" />
            </intent-filter>
        </receiver>

""",
            "",
            1,
        ),
    ]),
    (APPLICATION, [
        (
            """            // One channel per revert mechanism, so either ongoing notification can be
            // silenced or sorted on its own. Both are registered whichever mechanism is in
            // use: a channel is invisible in Android's settings until something has been
            // posted to it, and creating one lazily would mean the first post of each
            // arriving before its channel existed.
            notificationManagerWrapper.createNotificationChannel(
                channelId = AndroidNotificationManagerWrapper.REVERT_TO_DEFAULT_CHANNEL_ID,
                name = getString(notificationR.string.revert_to_default),
                importance = NotificationManager.IMPORTANCE_DEFAULT,
            )

            notificationManagerWrapper.createNotificationChannel(
                channelId = AndroidNotificationManagerWrapper.REVERT_MEMORY_CHANNEL_ID,
                name = getString(notificationR.string.revert_using_memory),
                importance = NotificationManager.IMPORTANCE_DEFAULT,
            )
""",
            """            // The channel for the one ongoing notification a hide leaves behind, so it can
            // be silenced or sorted without touching anything else. Registered whichever
            // framework is in use: a channel is invisible in Android's settings until
            // something has been posted to it, and creating one lazily would mean the first
            // post arriving before its channel existed.
            notificationManagerWrapper.createNotificationChannel(
                channelId = AndroidNotificationManagerWrapper.REVERT_TO_DEFAULT_CHANNEL_ID,
                name = getString(notificationR.string.revert_to_default),
                importance = NotificationManager.IMPORTANCE_DEFAULT,
            )

            // ⚠ **The per-app revert channel, deleted rather than merely left uncreated.** r3
            // replaced the per-app notification with the single generic one, so nothing posts
            // here any more - but a device that ever saw one carries this channel in Android's
            // settings, and an entry that can never hold a notification again is worse than no
            // entry at all. Same treatment as AUTO_UNHIDE_CHANNEL_ID_LOW below, for the same
            // reason.
            notificationManagerWrapper.deleteNotificationChannel(
                channelId = AndroidNotificationManagerWrapper.REVERT_MEMORY_CHANNEL_ID,
            )
""",
            1,
        ),
    ]),
    (WRAPPER, [
        (
            """         * Both are registered whether or not the mechanism that posts them is the one in
         * use - a channel with nothing posted to it is invisible in settings until it has
         * something, and registering on demand would mean the first post of each arrives
         * before its channel exists.
         */
        const val REVERT_TO_DEFAULT_CHANNEL_ID = "imd_revert_to_default_channel"
        const val REVERT_MEMORY_CHANNEL_ID = "imd_revert_memory_channel"
""",
            """         * ⚠ **Only the first of the two is registered now.** r3 replaced the per-app
         * revert notification with the single generic one, so the second has nothing left to
         * post to it and `GetoApplication` deletes it on start rather than creating it. The
         * one that remains is registered whichever framework is in use - a channel with
         * nothing posted to it is invisible in settings until it has something, and
         * registering on demand would mean the first post arriving before its channel exists.
         */
        const val REVERT_TO_DEFAULT_CHANNEL_ID = "imd_revert_to_default_channel"

        /**
         * ⚠ **Kept only so that it can be deleted.** Nothing posts to it since r3. A device
         * that saw a per-app revert notification before the upgrade still carries this channel
         * in Android's settings, where it would sit for ever with nothing able to use it, so
         * `GetoApplication` deletes it on start exactly as it does [AUTO_UNHIDE_CHANNEL_ID_LOW].
         */
        const val REVERT_MEMORY_CHANNEL_ID = "imd_revert_memory_channel"
""",
            1,
        ),
        (
            """        const val ACTION_REVERT_SETTINGS = "ACTION_REVERT_SETTINGS"
""",
            """        /**
         * ⚠ **Legacy, and reachable only from a notification posted by a build before r3.**
         * Nothing creates a PendingIntent with it any more; `RevertTrampolineActivity` maps it
         * to the framework-following unhide so that a per-app notification still standing in
         * an upgrading install's shade does what it promised when it is tapped.
         */
        const val ACTION_REVERT_SETTINGS = "ACTION_REVERT_SETTINGS"
""",
            1,
        ),
    ]),
    (REVERT_NOTIFICATION, [
        (
            """/**
 * The single notification posted after a launch when the notification function is set to
 * "Revert to default".
 *
 * Deliberately says nothing about which app was launched. In this mode the button does not
 * undo that app — it drives the whole device to the configured default — so naming an app
 * or showing its icon would describe something the button does not do. The revert icon is
 * there instead, and it is the same drawing as the tile and the shortcut, so all three
 * routes to the same action look like the same action.
 *
 * Posted under [REVERT_TO_DEFAULT_NOTIFICATION_ID], which is what makes this mode's "one
 * notification only" rule work: launching a second app replaces this notification rather
 * than adding another.
""",
            """/**
 * The notification posted after a hide — every hide, since r3.
 *
 * ⚠ **Deliberately says nothing about which app was launched, and that is now the author's
 * rule for every route rather than for one mode.** He was offered the launched app's icon on
 * the first notification of a chain and chose the opposite: *"no need to send app icon
 * notifications and make it easy and uniform, IMD send only generic revert notifications from
 * now"*. The revert icon is there instead, and it is the same drawing as the tile and the
 * shortcut, so all three routes to the same action look like the same action.
 *
 * Its button is the framework-following unhide rather than the named `Revert to default`
 * function — see `RevertToDefaultBroadcastReceiver` — so one notification is honest under all
 * four framework combinations: it puts back what the hide did, whatever the hide did.
 *
 * Posted under [REVERT_TO_DEFAULT_NOTIFICATION_ID], which is what makes the "one notification
 * only" rule work: launching a second app replaces this notification rather than adding
 * another.
""",
            1,
        ),
    ]),
    (AUTO_REVERT, [
        (
            """                // The per-app notification is posted under the component name's hash code,
                // and it now offers to undo a device that has already been put back.
                notificationManagerWrapper.cancel(componentName.hashCode())
""",
            """                // ⚠ **For a notification left standing by a build before r3.** Nothing
                // posts under a component name's hash code any more, but an upgrading
                // install can still have one in its shade, offering to undo a device that
                // has just been put back. Cancelling an id nothing holds costs nothing.
                notificationManagerWrapper.cancel(componentName.hashCode())
""",
            1,
        ),
    ]),
    (WATCHER, [
        (
            """        revertAppSettingsUseCase(componentName = componentName)

        notificationManagerWrapper.cancel(componentName.hashCode())
""",
            """        revertAppSettingsUseCase(componentName = componentName)

        // ⚠ **For a notification left standing by a build before r3**, as in AutoRevertRunner:
        // nothing posts under a component name's hash code since the per-app route went, and
        // cancelling an id nothing holds costs nothing.
        notificationManagerWrapper.cancel(componentName.hashCode())
""",
            1,
        ),
    ]),
    (AUTO_HIDE, [
        (
            """            // profile, so this is the only place its outcome is ever reported, and the ordinary
            // memory revert in RevertSettingsBroadcastReceiver has always done exactly this.
""",
            """            // profile, so this is the only place its outcome is ever reported on this route.
            // The ordinary memory sweep asks the same question in SettingsHiddenRunner.unhide.
""",
            1,
        ),
    ]),
]


def main() -> int:
    staged: dict[Path, str] = {}
    problems: list[str] = []

    for rel, subs in EDITS:
        path = ROOT / rel

        if not path.exists():
            problems.append(f"{rel}: missing")

            continue

        text = path.read_text(encoding="utf-8")

        for old, new, expected in subs:
            found = text.count(old)

            if found != expected:
                problems.append(
                    f"{rel}: expected {expected} of "
                    f"{old.strip().splitlines()[0][:58]!r}, found {found}",
                )

                continue

            text = text.replace(old, new, expected)

        staged[path] = text

    # The rewritten file, guarded on what the old one actually said rather than written over
    # it blind - if the branch is not there to remove, this script is running on the wrong tree.
    post_path = ROOT / POST
    post_old = post_path.read_text(encoding="utf-8") if post_path.exists() else ""

    for anchor in (
        "    when (unhidingFramework) {",
        "        UnhidingFramework.Memory -> {",
        "            val notificationId = componentName.hashCode()",
        "                notification = buildAppliedSettingsNotification(",
    ):
        if post_old.count(anchor) != 1:
            problems.append(f"{POST}: no single {anchor.strip()[:48]!r} to replace")

    staged[post_path] = POST_NEW

    for rel in DELETIONS:
        if not (ROOT / rel).exists():
            problems.append(f"{rel}: already gone, nothing to delete")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    # Nothing may still name the two files that are about to go, anywhere in the tree.
    dead = ("buildAppliedSettingsNotification", "RevertSettingsBroadcastReceiver")

    for path in sorted(ROOT.rglob("*.kt")) + sorted(ROOT.rglob("AndroidManifest.xml")):
        if any(part in ("build", "design", "out") for part in path.parts):
            continue

        if path.relative_to(ROOT).as_posix() in DELETIONS:
            continue

        text = staged.get(path)

        if text is None:
            text = path.read_text(encoding="utf-8")

        for name in dead:
            if name in text:
                problems.append(f"{path.relative_to(ROOT)}: still names {name}")

    # The 120-char guard, on the lines this script adds and no others - the file's own
    # pre-existing long lines are not this edit's business.
    for path, text in staged.items():
        before = set(path.read_text(encoding="utf-8").splitlines())

        for line in text.splitlines():
            if line not in before and len(line) > 120:
                problems.append(
                    f"{path.relative_to(ROOT)}: added line of {len(line)} chars: "
                    f"{line.strip()[:58]!r}",
                )

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")
        print(f"  wrote {path.relative_to(ROOT)}")

    for rel in DELETIONS:
        (ROOT / rel).unlink()
        print(f"  deleted {rel}")

    print("ok - one generic revert notification, per-app route removed")

    return 0


if __name__ == "__main__":
    sys.exit(main())
