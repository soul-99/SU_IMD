#!/usr/bin/env python3
"""
v3-r2b3b part 2 — the settings manager's own switches can put a setting back with no debt to
release.

**The reported bug.** After the force-close popup's Ignore ran by accident, the accessibility
and "Display over other apps" rows in the settings manager sat at off and would not move.
Nothing was broken in the UI: both **on** paths only ever release what IMD is recorded as having
switched off, and the discard had just erased that record.

    setOverlayPermission(enabled = true)   held[DEVICE_WIDE_HOLD] is empty -> `return true`
    setAccessibilityServices(enabled = true)  releaseAll({}) -> enabledAfter == currentlyEnabled

Both report success and write nothing. The row re-reads the device, still finds the services off,
and springs back — "stuck at off, and on turning even on manually they don't respond".

**The fix the author asked for, in his words: "make manager toggles do so only when manually
clicked to turn on again".** So this is a flag, not a change of behaviour for everybody:

* `manual = false` — every hide, revert, IMD+ and Tasker path. Unchanged to the line.
* `manual = true` — the manager's own row switch, and only on the **on** direction. The user is
  not asking to undo a debt, they are asking for their chosen services to be on full stop.

⚠ **The off direction is untouched in both.** Forcing something *off* that IMD never switched off
is how an app takes a device away from its owner, and the rule at the top of
`AccessibilityServicePlan` has said so since v1.

⚠ **Only the selection, never the live list.** `managedAccessibilityServices` and
`managedOverlayPackages` are what the user picked in IMD settings. Anything else on the device is
somebody else's, in this direction as much as the other.

⚠ **Still never over another holder.** A service or package a per-app profile is holding down is
left alone even here — `stillHeld` for overlay, and for accessibility the fact that `releaseAll`
has already cleared every holder before the forced enable runs. Handing one back while that
profile's app is still open is the bug `heldByOthers` exists to prevent.

For accessibility this needs no new arithmetic: `AccessibilityServicePlan.enable` was written for
exactly this — "the user pressing Re-enable is asking for their chosen services to be on full
stop — including ones no hold was ever recorded for, which is exactly the situation that arises
when the record was lost". That comment predates the bug it describes.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

USE_CASE = (
    "domain/use-case/src/main/kotlin/com/android/geto/domain/usecase/SetManualTargetUseCase.kt"
)

RUNNER = (
    "broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/OverlayRestoreRunner.kt"
)

VIEW_MODEL = (
    "feature/apps/src/main/kotlin/com/android/geto/feature/apps/manager/SettingsManagerViewModel.kt"
)

USE_CASE_EDITS: list[tuple[str, str]] = [
    # 1. The parameter, and what it means.
    (
        """    suspend operator fun invoke(
        target: ManualRevertTarget,
        enabled: Boolean,
    ): Boolean = withContext(defaultDispatcher) {""",
        """    suspend operator fun invoke(
        target: ManualRevertTarget,
        enabled: Boolean,
        /**
         * A person pressing this row's switch in the settings manager, as opposed to a hide, a
         * revert, IMD+ or Tasker.
         *
         * ⚠ **Read on the `enabled = true` paths only**, and it is the difference between
         * "release what IMD is holding" and "put my chosen services back on". The second is what
         * the switch has always claimed to do and could not: with no debt recorded — after a
         * discard, or after the user switched something off in the system settings themselves —
         * both branches found nothing to release, reported success, and wrote nothing. The row
         * then re-read the device, found it unchanged, and looked stuck.
         *
         * ⚠ **False everywhere else, and that default is load-bearing.** A revert forcing the
         * selection on would switch on services the user had turned off by hand since the hide,
         * which is not what "put it back the way it was" means.
         */
        manual: Boolean = false,
    ): Boolean = withContext(defaultDispatcher) {""",
    ),
    (
        """            runCatching { set(target = target, enabled = enabled) }.getOrDefault(false)""",
        """            runCatching {
                set(target = target, enabled = enabled, manual = manual)
            }.getOrDefault(false)""",
    ),
    (
        """    private suspend fun set(target: ManualRevertTarget, enabled: Boolean): Boolean {""",
        """    private suspend fun set(
        target: ManualRevertTarget,
        enabled: Boolean,
        manual: Boolean,
    ): Boolean {""",
    ),
    (
        """            ManualRevertTarget.AccessibilityServices -> setAccessibilityServices(enabled = enabled)
            ManualRevertTarget.Shizuku -> setShizuku(running = enabled)
            ManualRevertTarget.DisplayOverOtherApps -> setOverlayPermission(enabled = enabled)""",
        """            ManualRevertTarget.AccessibilityServices -> setAccessibilityServices(
                enabled = enabled,
                manual = manual,
            )

            ManualRevertTarget.Shizuku -> setShizuku(running = enabled)

            ManualRevertTarget.DisplayOverOtherApps -> setOverlayPermission(
                enabled = enabled,
                manual = manual,
            )""",
    ),
    # 2. Overlay: grant the selection as well as releasing the debt.
    (
        """    private suspend fun setOverlayPermission(enabled: Boolean): Boolean {""",
        """    private suspend fun setOverlayPermission(enabled: Boolean, manual: Boolean): Boolean {""",
    ),
    (
        """        if (enabled) {
            val released = held[holdKey].orEmpty()

            if (released.isEmpty()) return true

            val stillHeld = AccessibilityServicePlan.heldByOthers(
                held = held,
                exceptComponentName = holdKey,
            )
""",
        """        if (enabled) {
            val released = held[holdKey].orEmpty()

            // The early return is kept for every automatic caller: with nothing owed there is
            // nothing for a revert to put back, and saying so costs no binder call.
            if (released.isEmpty() && !manual) return true

            val stillHeld = AccessibilityServicePlan.heldByOthers(
                held = held,
                exceptComponentName = holdKey,
            )
""",
    ),
    (
        """            val restored = if (toRestore.isEmpty()) {
                emptySet()
            } else {
                shizukuWrapper.setOverlayPermission(packages = toRestore, allowed = true)
                    ?: emptySet()
            }
""",
        """            // Everything the user selected that is off right now and that nothing else is
            // holding down. Only asked for on the manual path, because it costs a live AppOp
            // read, and only there does the answer change anything.
            //
            // A null answer is Shizuku out of reach, which is not the same as "nothing to do":
            // the debt below is still released on the author's own record, and the forced part
            // is simply skipped rather than guessed at.
            val forced: Set<String> = if (manual) {
                val allowed = runCatching {
                    shizukuWrapper.getAllowedOverlayPackages()
                }.getOrNull()

                if (allowed == null) {
                    emptySet()
                } else {
                    userData.managedOverlayPackages
                        .filterNot { it in stillHeld || it in allowed }
                        .toSet()
                }
            } else {
                emptySet()
            }

            val wanted = toRestore + forced

            val restored = if (wanted.isEmpty()) {
                emptySet()
            } else {
                shizukuWrapper.setOverlayPermission(packages = wanted, allowed = true)
                    ?: emptySet()
            }
""",
    ),
    (
        """            val restoredEverything = outstanding.none { it !in stillHeld }

            if (userData.overlayRestoreFailed == restoredEverything) {
                userDataRepository.updateOverlayRestoreFailed(failed = !restoredEverything)
            }

            return restoredEverything
        }
""",
        """            val restoredEverything = outstanding.none { it !in stillHeld }

            // The flag stays a statement about the **debt** only. A forced grant that Shizuku
            // refused is a switch that did not move, not a revert that failed, and raising the
            // red row and its notification for it would be reporting a debt that never existed.
            if (userData.overlayRestoreFailed == restoredEverything) {
                userDataRepository.updateOverlayRestoreFailed(failed = !restoredEverything)
            }

            // The caller is told about both, because the manager's switch has to spring back
            // if what the user pressed it for did not happen.
            return restoredEverything && forced.all { it in restored }
        }
""",
    ),
    # 3. Accessibility: the same, through the plan function written for it.
    (
        """    private suspend fun setAccessibilityServices(enabled: Boolean): Boolean {""",
        """    private suspend fun setAccessibilityServices(enabled: Boolean, manual: Boolean): Boolean {""",
    ),
    (
        """            val written = runCatching {
                accessibilityServicesWrapper.setEnabledAccessibilityServices(plan.enabledAfter)
            }.getOrDefault(false)
""",
        """            // Releasing the debt, and then — for the manager's own switch only — switching on
            // whatever of the user's selection is *still* off afterwards. See
            // AccessibilityServicePlan.enable, which was written for this case and describes it
            // exactly: "including ones no hold was ever recorded for, which is exactly the
            // situation that arises when the record was lost".
            //
            // After releaseAll rather than instead of it, so the two cannot disagree about the
            // order of the list, and so a service held by a per-app profile is released by the
            // step that knows about holders rather than forced past it by the step that does not.
            val enabledAfter = if (manual) {
                AccessibilityServicePlan.enable(
                    wanted = userData.managedAccessibilityServices,
                    currentlyEnabled = plan.enabledAfter,
                )
            } else {
                plan.enabledAfter
            }

            val written = runCatching {
                accessibilityServicesWrapper.setEnabledAccessibilityServices(enabledAfter)
            }.getOrDefault(false)
""",
    ),
]

RUNNER_EDITS: list[tuple[str, str]] = [
    (
        """    suspend fun retry(): Boolean = settingsWorkTracker.track(kind = SettingsWorkKind.Unhiding) {
        val restored = setManualTargetUseCase(
            target = ManualRevertTarget.DisplayOverOtherApps,
            enabled = true,
        )
""",
        """    suspend fun retry(
        /**
         * Whether this is the settings manager's own switch rather than the notification's
         * *Try again* button.
         *
         * The notification is about a debt, so it stays as it was: nothing owed, nothing to do.
         * The manager's row is about the device, and has to be able to put the user's selection
         * back when no debt is recorded at all — see [SetManualTargetUseCase].
         */
        manual: Boolean = false,
    ): Boolean = settingsWorkTracker.track(kind = SettingsWorkKind.Unhiding) {
        val restored = setManualTargetUseCase(
            target = ManualRevertTarget.DisplayOverOtherApps,
            enabled = true,
            manual = manual,
        )
""",
    ),
]

VIEW_MODEL_EDITS: list[tuple[str, str]] = [
    (
        """            val written = setManualTargetUseCase(target = target, enabled = enabled)
""",
        """            // manual, because this is the one caller that is a person pressing the switch.
            // It changes nothing in the off direction; on, it means the row can put the user's
            // selection back even when IMD holds no debt for it.
            val written = setManualTargetUseCase(
                target = target,
                enabled = enabled,
                manual = true,
            )
""",
    ),
    (
        """                    overlayRestoreRunner.retry()
""",
        """                    overlayRestoreRunner.retry(manual = true)
""",
    ),
]


def apply(path: Path, edits: list[tuple[str, str]], problems: list[str]) -> str | None:
    if not path.exists():
        problems.append(f"{path.name} is missing")

        return None

    text = path.read_text(encoding="utf-8")

    before = set(text.splitlines())

    for old, new in edits:
        found = text.count(old)

        if found != 1:
            head = old.strip().splitlines()[0][:70]

            problems.append(f"{path.name}: {found} of {head!r}")

            continue

        text = text.replace(old, new, 1)

    for line in set(text.splitlines()) - before:
        if len(line) > 120:
            problems.append(f"{path.name}: {len(line)} chars — {line.strip()[:60]}")

    return text


def main() -> int:
    problems: list[str] = []

    targets = [
        (ROOT / USE_CASE, USE_CASE_EDITS),
        (ROOT / RUNNER, RUNNER_EDITS),
        (ROOT / VIEW_MODEL, VIEW_MODEL_EDITS),
    ]

    written: list[tuple[Path, str]] = []

    for path, edits in targets:
        text = apply(path, edits, problems)

        if text is not None:
            written.append((path, text))

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in written:
        path.write_text(text, encoding="utf-8")

    print("ok — the manager's switches can put the user's selection back with no debt recorded")

    return 0


if __name__ == "__main__":
    sys.exit(main())
