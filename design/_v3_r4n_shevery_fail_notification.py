#!/usr/bin/env python3
"""v3-r4n — the manager's 40 s Shevery timeout raises the author's notification.

His spec, for a Shevery start from the IMD services manager that does not come up:

    "from IMD services manager put both toggles to where they were shevery start attempt and
     display a popup alerting notification 'Failed to start Shevery, please click here to start
     it manually.' on clicking it will open the current shevery/shizuku app."

Half of that is already built: `SettingsManagerViewModel.setSheveryService` waits the 40 s,
holds both toggles for the duration and re-reads the states in its `finally`, so they land back
where the device actually is. The missing half is the notification — a timeout surfaces only as
an inline `RowFailureDialog` in the manager, with generic Shizuku wording, and it opens an
explanatory dialog rather than the fork's app.

## One notification for both forks, and that is the author's own rule

Posted under `SHIZUKU_FALLBACK_NOTIFICATION_ID`, the id its Thedjchi sibling
`buildShizukuRevertFailedNotification` already uses. Spec item 5: *"only keep one notification
for this shizuku revert failure at anytime"*. A Shevery start failure and a Shizuku restart
failure are the same news about the same row, so the second replaces the first rather than
stacking beside it.

⚠ **The DOOA restore-failure notification is still left alone**, on its own id. That is the
decision the author confirmed this round — *"thats logical shizuku failure notification should
not touch DOOA failure one bcz thats important for user"* — and it is why this posts under a
specific id rather than sweeping.

## Where it is raised from

`SheveryStartFailureNotification`, a `@Singleton` in `broadcast-receiver` beside
`RevertOfferNotification`, injected into the manager's ViewModel.

⚠ **No Hilt cycle.** It depends on `AndroidNotificationManagerWrapper`, `UserDataRepository` and
the application `Context` — three leaves. The r4m trap was a helper placed on a class that was
already a dependency of its caller; this is the opposite direction, and the ViewModel already
injects two other classes from this module.

## The string

`shevery_start_failed`, the author's sentence verbatim, beside `shizuku_revert_failed` in
`framework/notification-manager`. English only; translations are frozen, so it joins
`check_translations.py`'s `DEFERRED` set.

Asserts every anchor matches exactly once, that the new notification reuses its sibling's launch
derivation and id, and that the DOOA notification's id is not touched. Writes nothing if any
assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

NOTIFICATION = "broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/ShizukuFallbackNotification.kt"
NOTIFIER = "broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/SheveryStartFailureNotification.kt"
VM = "feature/apps/src/main/kotlin/com/android/geto/feature/apps/manager/SettingsManagerViewModel.kt"
STRINGS = "framework/notification-manager/src/main/res/values/strings.xml"
CHECK = "tools/check_translations.py"

NEW_NOTIFIER = '''/*
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

import android.content.Context
import com.android.geto.domain.repository.UserDataRepository
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.first
import javax.inject.Inject
import javax.inject.Singleton

/**
 * The alerting notification a Shevery start raises when the forty seconds run out.
 *
 * The author's instruction for the services manager: *"display a popup alerting notification
 * 'Failed to start Shevery, please click here to start it manually.' on clicking it will open
 * the current shevery/shizuku app."*
 *
 * ⚠ **Its own class rather than a method on the ViewModel**, because the ViewModel lives in
 * `feature/apps` and the notification wrapper does not reach it. The same shape
 * [RevertOfferNotification] has, and for the same reason: a question that needs the
 * notification manager, asked from a module that only has the runner.
 *
 * ⚠ **Posted under the id its Thedjchi sibling uses.** A Shevery start that failed and a
 * Shizuku restart that failed are the same news about the same row, and the author's rule in
 * spec item 5 is that only one of them stands at a time. The Display-over-other-apps
 * restore-failure notification keeps its own id and is deliberately never touched — his
 * decision this round, because that one carries a Try again the user may still need.
 */
@Singleton
class SheveryStartFailureNotification @Inject constructor(
    @param:ApplicationContext private val context: Context,
    private val userDataRepository: UserDataRepository,
    private val notificationManagerWrapper: AndroidNotificationManagerWrapper,
) {
    suspend fun warnStartFailed() {
        notificationManagerWrapper.notify(
            id = AndroidNotificationManagerWrapper.SHIZUKU_FALLBACK_NOTIFICATION_ID,
            notification = buildSheveryStartFailedNotification(
                context = context,
                shizukuPackage = userDataRepository.userData.first().shizukuPackageName,
            ),
        )
    }
}
'''

EDITS: list[tuple[str, str, str, str]] = []


def edit(rel: str, name: str, old: str, new: str) -> None:
    EDITS.append((rel, name, old, new))


edit(
    STRINGS,
    "the author's sentence",
    """    <string name="shizuku_revert_failed">Failed to start Shizuku service, please click here to start manually</string>""",
    """    <string name="shizuku_revert_failed">Failed to start Shizuku service, please click here to start manually</string>
    <string name="shevery_start_failed">Failed to start Shevery, please click here to start it manually.</string>""",
)

edit(
    CHECK,
    "the DEFERRED set",
    """    # r4n: the Shizuku row's fork sentence, beside dooa_thedjchi_only.""",
    """    # r4n: the manager's Shevery start-failure notification.
    "shevery_start_failed",
    # r4n: the Shizuku row's fork sentence, beside dooa_thedjchi_only.""",
)

edit(
    NOTIFICATION,
    "the Shevery builder",
    """fun buildShizukuRevertFailedNotification(
    context: Context,
    shizukuPackage: String,
): Notification {""",
    """fun buildSheveryStartFailedNotification(
    context: Context,
    shizukuPackage: String,
): Notification = buildForkStartFailedNotification(
    context = context,
    shizukuPackage = shizukuPackage,
    text = context.getString(R.string.shevery_start_failed),
)

fun buildShizukuRevertFailedNotification(
    context: Context,
    shizukuPackage: String,
): Notification = buildForkStartFailedNotification(
    context = context,
    shizukuPackage = shizukuPackage,
    text = context.getString(R.string.shizuku_revert_failed),
)

/**
 * The shape both fork-failure notifications share: the fork's own app on a tap, an OK that
 * dismisses, and nothing else.
 *
 * ⚠ **One builder, two sentences.** They differ only in wording — a Shevery start that never
 * came up and a Shizuku restart that failed are the same news about the same row — and they
 * post under the same id so that only one of them stands at a time. Written once rather than
 * twice so a change to the tap behaviour cannot land on one and miss the other.
 */
private fun buildForkStartFailedNotification(
    context: Context,
    shizukuPackage: String,
    text: String,
): Notification {""",
)

edit(
    NOTIFICATION,
    "the shared body's text",
    """    val text = context.getString(R.string.shizuku_revert_failed)

    return NotificationCompat.Builder(""",
    """    return NotificationCompat.Builder(""",
)

edit(
    VM,
    "the notifier injection",
    """    private val settingsWorkTracker: SettingsWorkTracker,
    @param:ApplicationScope private val appScope: CoroutineScope,
) : ViewModel() {""",
    """    private val settingsWorkTracker: SettingsWorkTracker,
    // r4n: the forty-second Shevery timeout raises the author's alerting notification, and
    // the notification wrapper does not reach this module. Depends on no runner, so no cycle.
    private val sheveryStartFailureNotification: SheveryStartFailureNotification,
    @param:ApplicationScope private val appScope: CoroutineScope,
) : ViewModel() {""",
)

edit(
    VM,
    "the timeout branch",
    """                if (came && sheveryStartTracker.wirelessWanted) {
                    withContext(NonCancellable) {
                        raiseWirelessAfterSheveryStart()
                    }
                }""",
    """                if (came && sheveryStartTracker.wirelessWanted) {
                    withContext(NonCancellable) {
                        raiseWirelessAfterSheveryStart()
                    }
                }

                // ⚠ **The forty seconds ran out, and the author asked to be told out of band.**
                // The inline row failure in the dialog is not enough on its own: a Shevery
                // start is long enough that the manager is very often closed by the time it
                // gives up, and the one thing that fixes it - opening Shevery and starting the
                // service by hand - is what the notification's tap does.
                //
                // NonCancellable for the same reason as the wireless settle above: closing the
                // row cancels this job, and the news is about what already happened.
                if (!came && isActive) {
                    withContext(NonCancellable) {
                        sheveryStartFailureNotification.warnStartFailed()
                    }
                }""",
)


def main() -> int:
    staged: dict[Path, str] = {}

    for rel, name, old, new in EDITS:
        path = ROOT / rel

        if not path.is_file():
            print(f"REFUSED: missing {rel}")
            return 1

        text = staged.get(path, path.read_text(encoding="utf-8"))

        found = text.count(old)

        if found != 1:
            print(f"REFUSED: {rel}\n  {name} matched {found} time(s), expected exactly 1")
            return 1

        staged[path] = text.replace(old, new, 1)

    notifier_path = ROOT / NOTIFIER

    if notifier_path.exists():
        print(f"REFUSED: {NOTIFIER} already exists")
        return 1

    staged[notifier_path] = NEW_NOTIFIER

    notification = staged[ROOT / NOTIFICATION]

    # ⚠ **Both builders must go through the shared one**, or the tap behaviour can drift
    # between them. Spelled as the call each makes, never as a bare name — the new KDoc talks
    # about both of them in prose.
    for caller in (
        "fun buildSheveryStartFailedNotification(",
        "fun buildShizukuRevertFailedNotification(",
    ):
        if caller not in notification:
            print(f"REFUSED: {NOTIFICATION} lost {caller!r}")
            return 1

    if notification.count("): Notification = buildForkStartFailedNotification(") != 2:
        print(f"REFUSED: {NOTIFICATION} does not route both builders through the shared one")
        return 1

    # ⚠ **The DOOA notification's id must be untouched.** The whole point of the author's
    # decision this round is that the Shizuku family does not sweep it.
    if "OVERLAY_RESTORE_NOTIFICATION_ID" in staged[notifier_path]:
        print(f"REFUSED: {NOTIFIER} names the DOOA notification's id")
        return 1

    if "SHIZUKU_FALLBACK_NOTIFICATION_ID" not in staged[notifier_path]:
        print(f"REFUSED: {NOTIFIER} does not post under the shared Shizuku id")
        return 1

    # The ViewModel needs the import; it is in a module it already depends on.
    vm = staged[ROOT / VM]

    needed = "import com.android.geto.broadcastreceiver.SheveryStartFailureNotification"

    if needed not in vm:
        vm = vm.replace(
            "import com.android.geto.broadcastreceiver.OverlayRestoreRunner",
            f"import com.android.geto.broadcastreceiver.OverlayRestoreRunner\n{needed}",
            1,
        )

    if vm.count(needed) != 1:
        print(f"REFUSED: {VM} carries the import {vm.count(needed)} time(s)")
        return 1

    staged[ROOT / VM] = vm

    # ⚠ **Position, not presence.** The failure branch has to come after the wait loop's
    # `came` is decided and after `starting.join()`, or it would fire while the start is still
    # in flight.
    join = vm.index("starting.join()")
    failure = vm.index("sheveryStartFailureNotification.warnStartFailed()")

    if not join < failure:
        print("REFUSED: the failure notification is raised before the start has finished")
        return 1

    # And the string must be the author's sentence, character for character.
    strings = staged[ROOT / STRINGS]

    value = strings.split('<string name="shevery_start_failed">', 1)[1].split("</string>", 1)[0]

    verbatim = "Failed to start Shevery, please click here to start it manually."

    if value != verbatim:
        print(f"REFUSED: the string reads {value!r}, not {verbatim!r}")
        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")

    print(f"  ok        {STRINGS}  :: shevery_start_failed")
    print(f"  ok        {CHECK}  :: key deferred")
    print(f"  ok        {NOTIFICATION}  :: one builder, two sentences")
    print(f"  ok        {NOTIFIER}  :: new")
    print(f"  ok        {VM}  :: raised on the forty-second timeout")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s) + 1 new file")

    return 0


if __name__ == "__main__":
    sys.exit(main())
