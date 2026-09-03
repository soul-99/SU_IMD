#!/usr/bin/env python3
"""
v3-r4m — the revert notification comes down after every per-app revert, not just some.

    "i just opened an app via imd, auto unhide service reverted but the revert notification
     did not dismiss automatically please fix this anywhere u find this"

The author's log, last block:

    23:39:47.361  hide app com.miui.calculator -> Success        <- posts the offer
    23:39:51.848  unhide session ended pkg=... reason=Swiped mode=memory
    23:39:51.856  svc auto unhide reverting, notification withdrawn
    23:39:51.913  svc auto unhide watcher stopped                <- the SERVICE dies here
    23:39:53.943  revert app ... -> Success                      <- two seconds later

⚠ **The service is destroyed in the middle of the revert, and only half the tick is protected.**
`revertOneProfile` is `withContext(NonCancellable)` so the writes and the toast survive - but
`AutoUnhideWatch.forget` and `settledIfNothingLeft()`, which is the ONLY thing on the per-app
path that takes the offer notification down, sit *outside* it. `AutoUnhideService.onDestroy`
cancels the scope, and the first suspension point after `revertOneProfile` returns throws.
Device restored, notification still in the shade. The file's own KDoc predicted exactly this
shape and then guarded one statement short of it.

⚠ **And three more paths never took it down at all.** `revertOneProfile` and `AutoRevertRunner`
cancel `componentName.hashCode()`, an id nothing has posted under since r3; the live offer is
`REVERT_TO_DEFAULT_NOTIFICATION_ID`, one fixed id for everybody. So an auto revert on return, a
Tasker memory revert and the per-app Revert button all left it standing.

The fix is one place rather than five: `SettingsHiddenRunner.clearRevertOfferIfSettled()`, which
asks the same question `settledIfNothingLeft` already asked and is called from every per-app
revert. ⚠ **It stays conditional.** One notification now serves every hide, so cancelling it
while another app is still hidden would take away that app's way back - which is why the
existing per-app path guarded it and why this one does too.

Every edit asserts its anchor matches exactly once. Nothing is written if any file fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BR = "broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver"
VM = (
    "feature/app-settings/src/main/kotlin/com/android/geto/feature/appsettings/"
    "AppSettingsViewModel.kt"
)

RUNNER = f"{BR}/SettingsHiddenRunner.kt"
WATCHER = f"{BR}/AutoUnhideWatcher.kt"
AUTO_REVERT = f"{BR}/AutoRevertRunner.kt"
TASKER = f"{BR}/TaskerIntegrationBroadcastReceiver.kt"

# --- 1. the one place that answers the question ----------------------------------------

RUNNER_OLD = """    suspend fun discardPendingReverts() {"""

RUNNER_NEW = '''    /**
     * Takes the offer to undo a hide out of the shade, once there is no hide left to undo.
     *
     * ⚠ **One notification serves every hide now**, under
     * [AndroidNotificationManagerWrapper.REVERT_TO_DEFAULT_NOTIFICATION_ID] - r3 replaced the
     * per-app notifications with a single fixed id. The per-app revert paths were still
     * cancelling `componentName.hashCode()`, which nothing has posted under since, so they
     * restored the device and left the offer standing. This is what they call instead.
     *
     * ⚠ **Conditional, and it has to stay that way.** One shared notification means cancelling
     * it while a second app is still hidden would take away that app's only way back from the
     * shade. Asked of the records rather than of what this particular revert did, because a
     * memory sweep and a single profile revert both end here and only the records know whether
     * anything is left.
     *
     * `cancelAll` rather than the one id: an install upgrading from before r3 can still have
     * per-app notifications keyed on hashes this cannot compute, and they describe a device
     * that no longer exists either. A foreground service's own notification survives it.
     *
     * Returns whether it cleared, so a caller that also wants to stop can use the same answer.
     */
    suspend fun clearRevertOfferIfSettled(): Boolean {
        val hidden = getSettingsHiddenUseCase()

        if (hidden.deviceWide || hidden.memory) return false

        notificationManagerWrapper.cancelAll()

        return true
    }

    suspend fun discardPendingReverts() {'''

# --- 2. the watcher: the cancellation gap the author's log shows ------------------------

WATCHER_OLD_LOOP = """        for (watchedEntry in ended.keys) {
            val componentName = watchedEntry.componentName ?: continue

            if (ended[watchedEntry] == null) continue

            Diagnostics.log(
                tag = "unhide",
                message = "session ended pkg=${watchedEntry.packageName} " +
                    "reason=${ended[watchedEntry]} mode=memory",
            )

            revertOneProfile(componentName = componentName)

            AutoUnhideWatch.forget(watchedEntry.packageName)
        }"""

WATCHER_NEW_LOOP = """        // ⚠ **The whole loop is NonCancellable, not only the revert inside it.** This is the
        // author's report: `AutoUnhideService` drops out of the foreground the moment
        // `reverting` is set and can be destroyed within milliseconds, which cancels this
        // scope - and `revertAppSettingsUseCase` waits on adbd for over a second before it
        // returns. `revertOneProfile` guarded its own writes and toast; everything after it
        // was left outside, so the forget below and the settle at the end of this function
        // were skipped on every revert that outlived the service. His log:
        //
        //     23:39:51.913  svc auto unhide watcher stopped
        //     23:39:53.943  revert app ... -> Success
        //
        // Device restored two seconds after the scope died, with the offer still in the shade.
        withContext(NonCancellable) {
            for (watchedEntry in ended.keys) {
                val componentName = watchedEntry.componentName ?: continue

                if (ended[watchedEntry] == null) continue

                Diagnostics.log(
                    tag = "unhide",
                    message = "session ended pkg=${watchedEntry.packageName} " +
                        "reason=${ended[watchedEntry]} mode=memory",
                )

                revertOneProfile(componentName = componentName)

                AutoUnhideWatch.forget(watchedEntry.packageName)
            }
        }"""

WATCHER_OLD_TAIL = """        settledIfNothingLeft()
    }"""

WATCHER_NEW_TAIL = """        // ⚠ **NonCancellable for the reason above.** This is the only thing on the per-app
        // path that takes the offer notification down, and it is the statement the author's
        // report landed on.
        withContext(NonCancellable) { settledIfNothingLeft() }
    }"""

WATCHER_OLD_SETTLED = """        val hidden = getSettingsHiddenUseCase()

        if (hidden.deviceWide || hidden.memory) return false

        // Nothing is hidden any more, so nothing in the shade can still be offering to undo
        // it. Only here, and never while a debt remains: a per-app Revert for an app that is
        // still hidden has to stay exactly where it is.
        clearRevertNotifications()"""

WATCHER_NEW_SETTLED = """        // ⚠ **The same question, asked in one place.** Four revert paths needed this answer
        // and each had its own version or none - see SettingsHiddenRunner for why the offer
        // can only be cleared when nothing is left hidden.
        if (!settingsHiddenRunner.clearRevertOfferIfSettled()) return false"""

# --- 3. auto revert on return, memory branch -------------------------------------------

AUTO_REVERT_OLD = """                // ⚠ **For a notification left standing by a build before r3.** Nothing
                // posts under a component name's hash code any more, but an upgrading
                // install can still have one in its shade, offering to undo a device that
                // has just been put back. Cancelling an id nothing holds costs nothing.
                notificationManagerWrapper.cancel(componentName.hashCode())"""

AUTO_REVERT_NEW = """                // ⚠ **For a notification left standing by a build before r3.** Nothing
                // posts under a component name's hash code any more, but an upgrading
                // install can still have one in its shade, offering to undo a device that
                // has just been put back. Cancelling an id nothing holds costs nothing.
                notificationManagerWrapper.cancel(componentName.hashCode())

                // ⚠ **And the one that is actually standing.** The line above was the whole
                // of this route's notification handling, and it names an id nothing has
                // posted under since r3 - so the live offer, under the fixed id every hide
                // shares, was left in the shade over a restored device. The RevertToDefault
                // branch never had this gap: RevertToDefaultRunner sweeps for itself.
                settingsHiddenRunner.clearRevertOfferIfSettled()"""

# --- 4. Tasker's memory revert -----------------------------------------------------------

TASKER_OLD = """                    TaskerIntegration.ACTION_REVERT_USING_MEMORY -> {
                        revertAllMemoryUseCase()

                        context?.showRestoredToast(fromMemory = true)
                    }"""

TASKER_NEW = """                    TaskerIntegration.ACTION_REVERT_USING_MEMORY -> {
                        revertAllMemoryUseCase()

                        // The offer to undo a hide that this has just undone. Same gap as
                        // AutoRevertRunner's memory branch: the sweep had no notification
                        // handling of its own, so an automation could restore the device and
                        // leave the notification standing over it.
                        settingsHiddenRunner.clearRevertOfferIfSettled()

                        context?.showRestoredToast(fromMemory = true)
                    }"""

# --- 5. the per-app Revert button --------------------------------------------------------

VM_OLD = """    fun revertAppSettings() {
        viewModelScope.launch {
            _revertAppSettingsResult.update { revertAppSettingsUseCase(componentName = componentName) }
        }
    }"""

VM_NEW = """    fun revertAppSettings() {
        viewModelScope.launch {
            _revertAppSettingsResult.update { revertAppSettingsUseCase(componentName = componentName) }

            // The notification offering to undo this hide is now describing a device that has
            // been put back. Nothing on this route took it down - it is one fixed id shared by
            // every hide since r3, and the per-app ids the revert paths cancelled have not
            // been posted under since. Conditional inside: another app may still be hidden.
            settingsHiddenRunner.clearRevertOfferIfSettled()
        }
    }"""

EDITS = [
    (RUNNER, "clearRevertOfferIfSettled", RUNNER_OLD, RUNNER_NEW),
    (WATCHER, "the per-app loop", WATCHER_OLD_LOOP, WATCHER_NEW_LOOP),
    (WATCHER, "the tick tail", WATCHER_OLD_TAIL, WATCHER_NEW_TAIL),
    (WATCHER, "settledIfNothingLeft", WATCHER_OLD_SETTLED, WATCHER_NEW_SETTLED),
    (AUTO_REVERT, "the memory branch", AUTO_REVERT_OLD, AUTO_REVERT_NEW),
    (TASKER, "ACTION_REVERT_USING_MEMORY", TASKER_OLD, TASKER_NEW),
    (VM, "revertAppSettings", VM_OLD, VM_NEW),
]

# ⚠ **No imports to add.** AutoUnhideWatcher, TaskerIntegrationBroadcastReceiver and
# AppSettingsViewModel all already hold a SettingsHiddenRunner, and AutoRevertRunner is in the
# same package as it — checked before writing, rather than assumed.
IMPORTS: list[tuple[str, str]] = []

# (path, old constructor line, new constructor line)
INJECTIONS = [
    (
        AUTO_REVERT,
        "    private val revertToDefaultRunner: RevertToDefaultRunner,",
        "    private val revertToDefaultRunner: RevertToDefaultRunner,\n"
        "    private val settingsHiddenRunner: SettingsHiddenRunner,",
    ),
]


def insert_import(text: str, statement: str) -> str:
    lines = text.split("\n")
    idx = [i for i, line in enumerate(lines) if line.startswith("import ")]

    if not idx:
        raise AssertionError("no import block")

    if statement in lines:
        return text

    sortable = [
        i for i in idx
        if not lines[i].startswith(("import javax.", "import java."))
        and " as " not in lines[i]
    ]

    at = next((i for i in sortable if lines[i] > statement), sortable[-1] + 1)
    lines.insert(at, statement)

    return "\n".join(lines)


def main() -> int:
    staged: dict[Path, str] = {}
    report: list[str] = []

    def read(rel: str) -> str:
        path = ROOT / rel

        if path not in staged:
            if not path.is_file():
                raise SystemExit(f"REFUSED: missing {rel}")

            staged[path] = path.read_text(encoding="utf-8")

        return staged[path]

    for rel, name, old, new in EDITS:
        text = read(rel)

        found = text.count(old)

        if found != 1:
            print(f"REFUSED: {rel}\n  {name} matched {found} time(s), expected exactly 1")
            return 1

        if new in text:
            print(f"REFUSED: {rel} already carries {name} — has this run before?")
            return 1

        staged[ROOT / rel] = text.replace(old, new, 1)
        report.append(f"  ok        {rel}  :: {name}")

    for rel, old, new in INJECTIONS:
        text = read(rel)

        if text.count(old) != 1:
            print(f"REFUSED: {rel} constructor anchor matched {text.count(old)} time(s)")
            return 1

        staged[ROOT / rel] = text.replace(old, new, 1)
        report.append(f"  + inject  {rel}")

    for rel, statement in IMPORTS:
        staged[ROOT / rel] = insert_import(read(rel), statement)
        report.append(f"  + import  {rel}")

    # --- the checks that would have caught this bug in the first place ------------------
    watcher = staged[ROOT / WATCHER]

    # `clearRevertNotifications` had exactly one caller left after this; the device-wide
    # path still sweeps before its work and must keep doing so.
    if watcher.count("clearRevertNotifications()") != 2:
        print(
            "REFUSED: clearRevertNotifications should have its declaration and the one "
            f"device-wide call left, found {watcher.count('clearRevertNotifications()')}"
        )
        return 1

    # Assert POSITION: both NonCancellable blocks must sit inside tick(), between the
    # session-kind gate above them and the closing of the withLock body.
    at_gate = watcher.index("val allowed = if (watched.isEmpty())")
    at_loop = watcher.index("        withContext(NonCancellable) {\n            for (watchedEntry")
    at_tail = watcher.index("        withContext(NonCancellable) { settledIfNothingLeft() }")
    at_next = watcher.index("    private suspend fun sessionEnded(")

    if not at_gate < at_loop < at_tail < at_next:
        print(
            "REFUSED: the two NonCancellable blocks are not both inside tick() — "
            f"gate@{at_gate} loop@{at_loop} tail@{at_tail} next@{at_next}"
        )
        return 1

    # NonCancellable and withContext are already imported here; assert rather than assume.
    for needed in ("import kotlinx.coroutines.NonCancellable", "import kotlinx.coroutines.withContext"):
        if needed not in watcher:
            print(f"REFUSED: {WATCHER} is missing {needed}")
            return 1

    # The runner must not have gained an unconditional cancel.
    runner = staged[ROOT / RUNNER]

    if "if (hidden.deviceWide || hidden.memory) return false" not in runner:
        print("REFUSED: clearRevertOfferIfSettled lost its guard")
        return 1

    for path, text in staged.items():
        over = [
            (n, len(line))
            for n, line in enumerate(text.split("\n"), 1)
            if len(line) > 120 and not line.lstrip().startswith("import ")
        ]

        original = (path).read_text(encoding="utf-8").split("\n")

        was = {line for line in original if len(line) > 120}

        gained = [(n, ln) for n, ln in over if text.split("\n")[n - 1] not in was]

        if gained:
            print(f"REFUSED: {path.relative_to(ROOT)} would gain lines over 120: {gained}")
            return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")

    print("\n".join(report))
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
