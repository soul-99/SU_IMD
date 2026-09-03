#!/usr/bin/env python3
"""
v3-r4m — the "is anything still hidden, and if not take the offer down" question gets an owner.

    "same notification non dismissal also occuring for IMD+"

`_v3_revert_offer_cleared.py` put the question on `SettingsHiddenRunner` and fixed four routes.
The fifth is IMD+'s own revert, and it **cannot** call it: `SettingsHiddenRunner` already
injects `AutoHideRunner`, so injecting it back would be a Hilt dependency cycle - a runtime
failure the sandbox cannot see, since neither module compiles here.

So the question moves into a class of its own that depends on neither runner.

⚠ **`AutoHideRunner.revert(componentName)` returns early**, before the hand-over to
`RevertToDefaultRunner` that sweeps the shade on the device-wide branch. It cancels
`AUTO_HIDE_NOTIFICATION_ID` and nothing else, so the shared offer under
`REVERT_TO_DEFAULT_NOTIFICATION_ID` - posted by whatever launch put the settings down - was
left standing over a device IMD+ had just restored. The early return is why the device-wide
branch never showed this.

Every edit asserts its anchor matches exactly once. Nothing is written if any file fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BR = "broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver"

OWNER = f"{BR}/RevertOfferNotification.kt"
RUNNER = f"{BR}/SettingsHiddenRunner.kt"
AUTO_HIDE = f"{BR}/AutoHideRunner.kt"

OWNER_SOURCE = '''/*
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

import com.android.geto.domain.usecase.GetSettingsHiddenUseCase
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper
import javax.inject.Inject
import javax.inject.Singleton

/**
 * The offer to undo a hide, and the one question worth asking before taking it down.
 *
 * ⚠ **One notification serves every hide since r3**, under
 * [AndroidNotificationManagerWrapper.REVERT_TO_DEFAULT_NOTIFICATION_ID]. Before that each app
 * had its own, keyed on its component name's hash - and five revert routes were still
 * cancelling that hash, which nothing has posted under since. They restored the device and
 * left the offer standing over it. The author reported it twice, from auto unhide and from
 * IMD+.
 *
 * ⚠ **A class of its own rather than a method on [SettingsHiddenRunner], and the reason is a
 * dependency cycle the sandbox cannot see.** That runner already injects [AutoHideRunner], so
 * IMD+'s own revert - the fifth route, and the one that returns early before the sweep - could
 * not have asked it without Hilt refusing to build the graph. Nothing here depends on either
 * runner, so everything can reach it.
 *
 * ⚠ **Conditional, and it has to stay that way.** One shared notification means cancelling it
 * while a second app is still hidden would take away that app's only way back from the shade.
 * The records are asked rather than the revert that just ran, because a memory sweep and a
 * single profile revert both end here and only the records know whether anything is left.
 *
 * `cancelAll` rather than the one id: an install upgrading from before r3 can still have
 * per-app notifications keyed on hashes this cannot compute, and they describe a device that
 * no longer exists either. A foreground service's own notification survives it, which is what
 * keeps the auto unhide watcher's own notification out of this.
 */
@Singleton
class RevertOfferNotification @Inject constructor(
    private val getSettingsHiddenUseCase: GetSettingsHiddenUseCase,
    private val notificationManagerWrapper: AndroidNotificationManagerWrapper,
) {
    /** Returns whether it cleared, so a caller that also wants to settle can reuse the answer. */
    suspend fun clearIfSettled(): Boolean {
        val hidden = getSettingsHiddenUseCase()

        if (hidden.deviceWide || hidden.memory) return false

        notificationManagerWrapper.cancelAll()

        return true
    }
}
'''

# --- the runner's copy becomes a delegation --------------------------------------------

RUNNER_OLD = """    suspend fun clearRevertOfferIfSettled(): Boolean {
        val hidden = getSettingsHiddenUseCase()

        if (hidden.deviceWide || hidden.memory) return false

        notificationManagerWrapper.cancelAll()

        return true
    }"""

RUNNER_NEW = """    suspend fun clearRevertOfferIfSettled(): Boolean =
        revertOfferNotification.clearIfSettled()"""

RUNNER_CTOR_OLD = "    private val settingsWorkTracker: SettingsWorkTracker,\n) {"

RUNNER_CTOR_NEW = (
    "    private val settingsWorkTracker: SettingsWorkTracker,\n"
    "    private val revertOfferNotification: RevertOfferNotification,\n"
    ") {"
)

# --- IMD+'s early-returning per-app branch ------------------------------------------------

AUTO_HIDE_OLD = """            if (!overlayRestoreRunner.reportIfFailed()) {
                context.showRestoredToast(
                    fromMemory = true,
                    appName = packageManagerWrapper.getActivityLabel(
                        componentName = componentName,
                    ),
                )
            }

            return@track"""

AUTO_HIDE_NEW = """            // ⚠ **The shared offer, which this branch never took down.** The cancel at
            // the top of this function names AUTO_HIDE_NOTIFICATION_ID - IMD+'s own - and
            // this branch returns below, before the hand-over to RevertToDefaultRunner that
            // sweeps the shade on the device-wide path. So a launch's "tap to revert" offer,
            // posted under the one fixed id every hide shares, sat over a device IMD+ had
            // just restored. The author's second report.
            //
            // Conditional inside: another app may still be hidden, and one notification now
            // serves them all.
            revertOfferNotification.clearIfSettled()

            if (!overlayRestoreRunner.reportIfFailed()) {
                context.showRestoredToast(
                    fromMemory = true,
                    appName = packageManagerWrapper.getActivityLabel(
                        componentName = componentName,
                    ),
                )
            }

            return@track"""

AUTO_HIDE_CTOR_OLD = "    private val overlayRestoreRunner: OverlayRestoreRunner,\n) {"

AUTO_HIDE_CTOR_NEW = (
    "    private val overlayRestoreRunner: OverlayRestoreRunner,\n"
    "    private val revertOfferNotification: RevertOfferNotification,\n"
    ") {"
)

EDITS = [
    (RUNNER, "clearRevertOfferIfSettled delegates", RUNNER_OLD, RUNNER_NEW),
    (RUNNER, "SettingsHiddenRunner constructor", RUNNER_CTOR_OLD, RUNNER_CTOR_NEW),
    (AUTO_HIDE, "the IMD+ per-app branch", AUTO_HIDE_OLD, AUTO_HIDE_NEW),
    (AUTO_HIDE, "AutoHideRunner constructor", AUTO_HIDE_CTOR_OLD, AUTO_HIDE_CTOR_NEW),
]


def main() -> int:
    owner = ROOT / OWNER

    if owner.exists():
        print(f"REFUSED: {OWNER} already exists — has this run before?")
        return 1

    staged: dict[Path, str] = {}

    for rel, name, old, new in EDITS:
        path = ROOT / rel

        if not path.is_file():
            print(f"REFUSED: missing {rel}")
            return 1

        text = staged.get(path) or path.read_text(encoding="utf-8")

        found = text.count(old)

        if found != 1:
            print(f"REFUSED: {rel}\n  {name} matched {found} time(s), expected exactly 1")
            return 1

        staged[path] = text.replace(old, new, 1)

    # ⚠ The cycle this whole script exists to avoid: nothing the new class depends on may
    # depend back on it, and neither runner may appear in its constructor.
    for forbidden in ("SettingsHiddenRunner", "AutoHideRunner", "RevertToDefaultRunner"):
        if forbidden in OWNER_SOURCE.split("class RevertOfferNotification")[1]:
            print(f"REFUSED: RevertOfferNotification's body names {forbidden}")
            return 1

    # Assert POSITION: the new call must land inside the componentName branch, above its
    # `return@track` and above the device-wide code that follows it.
    auto_hide = staged[ROOT / AUTO_HIDE]

    at_branch = auto_hide.index("        if (componentName != null) {")
    at_call = auto_hide.index("            revertOfferNotification.clearIfSettled()")
    at_return = auto_hide.index("            return@track", at_branch)
    at_after = auto_hide.index("        userDataRepository.updateAutoHideRunning(running = false)")

    if not at_branch < at_call < at_return < at_after:
        print(
            "REFUSED: placement wrong — "
            f"branch@{at_branch} call@{at_call} return@{at_return} after@{at_after}"
        )
        return 1

    # The runner keeps its own two dependencies; they are used elsewhere in the file and a
    # delegation that left them unused would be a warning the sandbox never sees.
    runner = staged[ROOT / RUNNER]

    for kept in ("getSettingsHiddenUseCase(", "notificationManagerWrapper.cancelAll()"):
        if kept not in runner:
            print(f"REFUSED: SettingsHiddenRunner no longer uses {kept}")
            return 1

    for path, text in staged.items():
        over = [
            (n, len(line))
            for n, line in enumerate(text.split("\n"), 1)
            if len(line) > 120 and not line.lstrip().startswith("import ")
        ]

        was = {line for line in path.read_text(encoding="utf-8").split("\n") if len(line) > 120}

        gained = [(n, w) for n, w in over if text.split("\n")[n - 1] not in was]

        if gained:
            print(f"REFUSED: {path.relative_to(ROOT)} would gain lines over 120: {gained}")
            return 1

    over_owner = [
        (n, len(line))
        for n, line in enumerate(OWNER_SOURCE.split("\n"), 1)
        if len(line) > 120 and not line.lstrip().startswith("import ")
    ]

    if over_owner:
        print(f"REFUSED: {OWNER} would carry lines over 120: {over_owner}")
        return 1

    owner.write_text(OWNER_SOURCE, encoding="utf-8")

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")

    print(f"  + new     {OWNER}")
    print(f"  ok        {RUNNER}  :: delegates, no cycle")
    print(f"  ok        {AUTO_HIDE}  :: the IMD+ per-app branch")
    print(f"\nwrote {len(staged) + 1} file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
