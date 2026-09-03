#!/usr/bin/env python3
"""v3-r4n item 7 — IMD's own detector comes back after IMD updates itself.

The author:

    "if i am right when app are updated their accessibility service is turned off???, if yes can
     we make it that if after app update IMD+ was on before update it re enabled?"

**The premise is right**, with a caveat that was put to him: a package replace disables the
replaced app's own accessibility service on most Android versions, and a few OEM builds preserve
it across a same-signature update. Harmless either way — enabling a service that is already
enabled is a no-op, which `EnableAutoHideServiceUseCase` says first thing.

## The marker: option (b), the author's choice

Asked whether to write a separate "was on before" flag (a) or read the IMD+ switch (b), he chose
**(b)**. The reasoning, checked in the code before asking:

* `UserData.autoHideEnabled` is documented as *"Their answer, and nothing more"* — it is already
  the persisted record of what the user asked for;
* nothing outside the user's own toggle clears it. A hide takes the detector away by recording a
  hold under `AccessibilityServicePlan.AUTO_HIDE_HOLD` and leaves the switch alone;
* the live requirement is read separately, from `serviceState.accessibilityRunning`, so the
  system disabling the service changes the *requirement* and never the stored answer.

A second flag would therefore be a second copy of one fact. It would also not protect the one
case where a marker looks useful — a user who switches the detector off by hand in Android's
settings and leaves IMD+ on — because it is only cleared when IMD+ is switched off.

## Why the receiver does not check anything else

`ACTION_MY_PACKAGE_REPLACED` is delivered to this app alone, and only for its own replacement.
The use case is idempotent and reports rather than throws: already running is success, a refused
write is an ordinary outcome, and the Android 13+ AppOp path is attempted through Shizuku and
allowed to fail. So the receiver's whole job is *"did the user ask for IMD+"*.

⚠ **`goAsync`, like every other receiver here.** Without it the process is cached as soon as
`onReceive` returns, and this run writes a secure setting and then polls for a bind for up to
two and a half seconds.

⚠ **Not exported.** A manifest receiver for this action is exempt from the background-launch
restrictions, and the action can only be sent by the system.

Asserts the file does not already exist, that the manifest anchor matches exactly once, and that
the receiver and its declaration agree on the class name. Writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RECEIVER = "broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/PackageReplacedBroadcastReceiver.kt"
MANIFEST = "broadcast-receiver/src/main/AndroidManifest.xml"

CLASS = "com.android.geto.broadcastreceiver.PackageReplacedBroadcastReceiver"

NEW_FILE = '''/*
 *
 *   Copyright 2026 soul_99 (suIMD)
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

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import com.android.geto.common.ApplicationScope
import com.android.geto.domain.repository.UserDataRepository
import com.android.geto.domain.usecase.EnableAutoHideServiceUseCase
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * Puts IMD's own accessibility service — the IMD+ detector — back after IMD has been updated.
 *
 * Android disables an app's accessibility service when the app is replaced, on most versions.
 * IMD+ then reads as switched off for a reason the user had no part in and no way to see: the
 * switch on the settings page is drawn from the live service state, so the feature simply stops
 * working the next time the app is updated.
 *
 * ⚠ **[UserData.autoHideEnabled] is the "was on before" record, and there is deliberately no
 * second flag.** It is the user's stored answer and nothing else writes it: a hide takes the
 * detector away by recording a hold under [AccessibilityServicePlan.AUTO_HIDE_HOLD] and leaves
 * the switch alone, and the live requirement is read from the service state rather than from
 * here. A separate marker would be a second copy of one fact, free to drift from it — and it
 * would not protect the case it looks like it protects, a detector switched off by hand in
 * Android's settings, because that is not what would clear it either.
 *
 * ⚠ **[EnableAutoHideServiceUseCase] is idempotent and never throws.** Already running is
 * success; a refused write and a dead Shizuku binder are ordinary outcomes it reports rather
 * than raising. So there is nothing for this receiver to check beyond the user's answer, and
 * nothing it can usefully do about a failure — the settings page will show the requirement
 * unmet, exactly as it does today.
 *
 * ⚠ **`goAsync`, for the same reason as every other receiver in this package**: without it the
 * process can be cached the moment `onReceive` returns, and the enable writes a secure setting
 * and then waits up to two and a half seconds for the service to bind.
 */
@AndroidEntryPoint
class PackageReplacedBroadcastReceiver : BroadcastReceiver() {

    @Inject
    @ApplicationScope
    lateinit var appScope: CoroutineScope

    @Inject
    lateinit var userDataRepository: UserDataRepository

    @Inject
    lateinit var enableAutoHideServiceUseCase: EnableAutoHideServiceUseCase

    override fun onReceive(context: Context?, intent: Intent?) {
        // The manifest filter already narrows this to one action, and the system is the only
        // sender of it. Checked anyway, because a receiver that acts on whatever it is handed
        // is one refactor away from acting on something else.
        if (intent?.action != Intent.ACTION_MY_PACKAGE_REPLACED) return

        val pendingResult = goAsync()

        appScope.launch {
            try {
                if (userDataRepository.userData.first().autoHideEnabled) {
                    enableAutoHideServiceUseCase()
                }
            } finally {
                pendingResult.finish()
            }
        }
    }
}
'''

OLD_MANIFEST = """        <receiver
            android:name="com.android.geto.broadcastreceiver.OverlayRestoreRetryBroadcastReceiver"
            android:exported="false">
            <intent-filter>
                <action android:name="ACTION_RETRY_OVERLAY_RESTORE" />
            </intent-filter>
        </receiver>"""

NEW_MANIFEST = OLD_MANIFEST + """

        <!--
          Android switches an app's own accessibility service off when the app is replaced, so
          IMD+ would stop working after every update of IMD until somebody noticed. Not
          exported: MY_PACKAGE_REPLACED is delivered to this app alone and only the system
          sends it. A manifest receiver for it is exempt from the background-launch
          restrictions, which is why this is declared here rather than registered at runtime -
          there is nothing running to register it at the moment it fires.
        -->
        <receiver
            android:name="com.android.geto.broadcastreceiver.PackageReplacedBroadcastReceiver"
            android:exported="false">
            <intent-filter>
                <action android:name="android.intent.action.MY_PACKAGE_REPLACED" />
            </intent-filter>
        </receiver>"""


def main() -> int:
    receiver_path = ROOT / RECEIVER
    manifest_path = ROOT / MANIFEST

    if receiver_path.exists():
        print(f"REFUSED: {RECEIVER} already exists")
        return 1

    if not manifest_path.is_file():
        print(f"REFUSED: missing {MANIFEST}")
        return 1

    manifest = manifest_path.read_text(encoding="utf-8")

    found = manifest.count(OLD_MANIFEST)

    if found != 1:
        print(f"REFUSED: {MANIFEST}\n  the anchor matched {found} time(s), expected exactly 1")
        return 1

    if CLASS in manifest:
        print(f"REFUSED: {MANIFEST} already declares {CLASS}")
        return 1

    staged_manifest = manifest.replace(OLD_MANIFEST, NEW_MANIFEST, 1)

    # ⚠ **The declaration and the class must agree**, and `check6_manifest` only checks the
    # app module. A typo here is a receiver that never fires and nothing that says so.
    package, _, simple = CLASS.rpartition(".")

    if f"package {package}" not in NEW_FILE:
        print("REFUSED: the receiver's package does not match its manifest name")
        return 1

    if f"class {simple} : BroadcastReceiver()" not in NEW_FILE:
        print("REFUSED: the receiver's class name does not match its manifest name")
        return 1

    if staged_manifest.count(CLASS) != 1:
        print(f"REFUSED: {MANIFEST} declares {CLASS} more than once")
        return 1

    # ⚠ **Position, not presence.** The new receiver has to sit inside <application>, and the
    # anchor it follows is inside it — asserted rather than assumed, because a manifest with a
    # receiver outside <application> fails to build with a message that names neither.
    app_open = staged_manifest.index("<application>")
    app_close = staged_manifest.index("</application>")
    declared = staged_manifest.index(CLASS)

    if not app_open < declared < app_close:
        print("REFUSED: the receiver is declared outside <application>")
        return 1

    # Every symbol the receiver imports must be reachable from this module. The three that are
    # not already used in the package are what would break the build.
    for symbol, where in (
        ("EnableAutoHideServiceUseCase", "domain/use-case/src/main/kotlin/com/android/geto/domain/usecase/EnableAutoHideServiceUseCase.kt"),
        ("UserDataRepository", "domain/repository/src/main/kotlin/com/android/geto/domain/repository/UserDataRepository.kt"),
    ):
        if not (ROOT / where).is_file():
            print(f"REFUSED: {symbol} is not where the import says it is")
            return 1

    # And the field it reads has to exist, spelled as the property access it is.
    user_data = (ROOT / "domain/model/src/main/kotlin/com/android/geto/domain/model/UserData.kt").read_text(
        encoding="utf-8",
    )

    if "val autoHideEnabled: Boolean," not in user_data:
        print("REFUSED: UserData has no autoHideEnabled field")
        return 1

    receiver_path.write_text(NEW_FILE, encoding="utf-8")
    manifest_path.write_text(staged_manifest, encoding="utf-8")

    print(f"  ok        {RECEIVER}  :: new")
    print(f"  ok        {MANIFEST}  :: MY_PACKAGE_REPLACED, not exported")
    print("\nwrote 1 file(s), 1 edit(s) + 1 new file")

    return 0


if __name__ == "__main__":
    sys.exit(main())
