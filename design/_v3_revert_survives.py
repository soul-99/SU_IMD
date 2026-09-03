#!/usr/bin/env python3
"""
v3-r2f — auto unhide's revert must outlive the service that started it.

### The bug, measured rather than guessed

`AutoUnhideService` owns its own scope and cancels it in `onDestroy`:

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)
    override fun onDestroy() { ...; scope.cancel() }

The tick loop runs on that scope, and both revert paths in `AutoUnhideWatcher` are awaited
inside the tick. `RevertAppSettingsUseCase` writes the settings early and then waits
`SHIZUKU_START_DELAY_MILLIS = 1_500L` — a `delay()`, the most cancellable construct there is —
before its outer `.also` logs the result. So when the service goes away mid-revert the writes
have landed, the records are cleared, and **everything after the use case never runs**: the
per-app notification is never cancelled, the completion toast is never shown, and no result
line is ever logged.

The author's log shows it, twice per occurrence:

    11:11:21.418  unhide  session ended pkg=com.miui.calculator reason=Swiped mode=memory
    11:11:21.422  write   development_settings_enabled = 1 -> ok
    11:11:21.425  write   adb_enabled = 1 -> ok
    11:11:21.446  svc     auto unhide watcher stopped        <- onDestroy, 21ms after the write
                  (no "revert  app ... -> Success", ever)

against the same profile reverted from the tile, which runs on the application scope:

    11:09:27.298  write   development_settings_enabled = 1 -> ok
    11:09:29.323  revert  app com.miui.calculator/... -> Success      <- 2.0s later

⚠ **The discriminator that rules out every other explanation.** At 09:53:19 a per-app revert ran
while a device-wide entry was *still watched*, so nothing stopped the service — and that one
completed, logging its result 518ms later. Every auto unhide revert that is followed by
`watcher stopped` is truncated; the one that is not, is not. The cause is the service's
lifetime, not anything about the revert.

The user-visible symptoms follow exactly: the device looks restored and the debt reads as
settled, but the hide notification is orphaned in the shade — so the Favourites button, which
asks about debts rather than notifications, correctly answers `'IMD: No hidden settings to
restore'` while a notification sits there implying the opposite.

### The fix

`withContext(NonCancellable)` around both revert bodies. The tail then completes whatever
happens to the service, on any device, for any reason.

⚠ **Not `stopSelf`, and not the foreground drop either.** `AutoUnhideService:141` already
guards against `stopSelf` for this exact hazard — "the revert runs on the scope below, so
stopSelf here would cancel the very work this is reacting to" — but the sibling coroutine that
withdraws the notification calls `stopForeground(STOP_FOREGROUND_REMOVE)`, and a service that
is no longer in the foreground can be reclaimed at once. Moving the revert to the application
scope would fix this instance and leave the same hazard for the next one; `NonCancellable` is
the guarantee itself, and it keeps the author's r1 rule that the notification comes down the
moment unhiding starts.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

WATCHER = (
    "broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/"
    "AutoUnhideWatcher.kt"
)

WATCHER_EDITS: list[tuple[str, str]] = [
    # Two imports, in the project's alphabetical block.
    (
        """import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
""",
        """import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext
""",
    ),
    # The per-app path. The cancel and the toast are the two statements that were being lost.
    (
        """    private suspend fun revertOneProfile(componentName: String) {
        // Before the work, as on the device-wide path. See AutoUnhideWatch.reverting.
        AutoUnhideWatch.reverting = true

        revertAppSettingsUseCase(componentName = componentName)

        notificationManagerWrapper.cancel(componentName.hashCode())
""",
        """    private suspend fun revertOneProfile(componentName: String) = withContext(NonCancellable) {
        // Before the work, as on the device-wide path. See AutoUnhideWatch.reverting.
        AutoUnhideWatch.reverting = true

        revertAppSettingsUseCase(componentName = componentName)

        notificationManagerWrapper.cancel(componentName.hashCode())
""",
    ),
    # The device-wide path. Its notifications are swept before the work, so the loss here is
    # the sweep of the watch itself and the completion toast the revert underneath says.
    (
        """    private suspend fun revertEverything() {
        Diagnostics.log(tag = "revert", message = "auto unhide: flushPendingReverts")
""",
        """    private suspend fun revertEverything() = withContext(NonCancellable) {
        Diagnostics.log(tag = "revert", message = "auto unhide: flushPendingReverts")
""",
    ),
    # Both doc comments gain the reason, so the next round does not quietly undo it.
    (
        """     * on and the user holding the phone. The author's instruction is a completion toast on
     * every hide and every unhide.
     */
""",
        """     * on and the user holding the phone. The author's instruction is a completion toast on
     * every hide and every unhide.
     *
     * ⚠ **`NonCancellable`, and it is the whole point of this function finishing at all.**
     * This runs on `AutoUnhideService`'s own scope, which `onDestroy` cancels; the service
     * drops out of the foreground the moment a revert starts and can be reclaimed within
     * milliseconds of doing so. `RevertAppSettingsUseCase` writes the settings early and then
     * waits 1.5s for adbd before it returns, so a cancellation lands squarely between the
     * writes and the two statements below - leaving a restored device with its notification
     * still in the shade and nothing said about it. Measured on the author's device: every
     * auto unhide revert followed by `watcher stopped` logged no result, and the one that ran
     * while another entry kept the service alive logged its result 518ms later.
     */
""",
    ),
    (
        """     * mean this deciding what the revert below is allowed to say.
     */
""",
        """     * mean this deciding what the revert below is allowed to say.
     *
     * ⚠ **`NonCancellable`, for the reason on [revertOneProfile].** The device-wide path
     * sweeps its notifications before the work rather than after, so what a cancellation costs
     * here is the watch and the pending-revert record never being cleared and the completion
     * toast never being said - a device that is back to normal and still believes it owes.
     */
""",
    ),
]


def apply(path: Path, edits: list[tuple[str, str]], problems: list[str]) -> str | None:
    if not path.exists():
        problems.append(f"{path} is missing")

        return None

    text = path.read_text(encoding="utf-8")

    for old, new in edits:
        found = text.count(old)

        if found != 1:
            head = old.strip().splitlines()[0][:70] if old.strip() else old[:70]

            problems.append(f"{path.name}: {found} of {head!r}")

            continue

        text = text.replace(old, new, 1)

    return text


def main() -> int:
    problems: list[str] = []

    path = ROOT / WATCHER

    before = set(path.read_text(encoding="utf-8").splitlines()) if path.exists() else set()

    text = apply(path=path, edits=WATCHER_EDITS, problems=problems)

    if text is not None:
        # ⚠ Only lines this edit adds. The file already carries pre-existing lines past
        # 120 characters, and a guard that counted those would refuse for something no round
        # wrote. handover_3 §4, second occurrence in r2e.
        for line in set(text.splitlines()) - before:
            if len(line) > 120:
                problems.append(f"{path.name}: {len(line)} chars — {line.strip()[:60]}")

        # Both bodies must actually be wrapped, and nothing else in the file may be.
        wrapped = text.count("= withContext(NonCancellable) {")

        if wrapped != 2:
            problems.append(f"{path.name}: {wrapped} NonCancellable wrappers, expected 2")

        for name in ("revertOneProfile", "revertEverything"):
            if f"private suspend fun {name}(" not in text:
                problems.append(f"{path.name}: lost {name}")

        # The three statements the truncation was eating must still be there, and after the
        # use case rather than before it.
        # Counts enumerated against the pristine r2e tree, never estimated — handover_2 §9.
        # `AutoUnhideWatch.clear()` appears four times (two early settle branches, this path,
        # and the public reset) and `AutoRevertPending.clear()` twice (this path and reset).
        for needle, expected in (
            ("notificationManagerWrapper.cancel(componentName.hashCode())", 1),
            ("AutoUnhideWatch.clear()", 4),
            ("AutoRevertPending.clear()", 2),
        ):
            if text.count(needle) != expected:
                problems.append(
                    f"{path.name}: {text.count(needle)} of {needle}, expected {expected}",
                )

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    path.write_text(text, encoding="utf-8")

    print("ok — both auto unhide revert paths now run NonCancellable")

    return 0


if __name__ == "__main__":
    sys.exit(main())
