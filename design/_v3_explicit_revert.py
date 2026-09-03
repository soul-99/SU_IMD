#!/usr/bin/env python3
"""
v3-r2i — an explicit Revert to default now settles everything first, IMD+ arms like everyone
else, and the log says which kind of revert ran.

### 1. The bug the author reported, found in code rather than inferred

`RevertToDefaultRunner` calls `notificationManagerWrapper.cancelAll()` and **never touches
`AutoUnhideWatch` or `AutoRevertPending`**. Only `AutoUnhideWatcher.revertEverything()` clears
those. So an explicit Revert to default put the settings back and left the watch entries
standing: the foreground service kept running, its notification stayed in the shade, and it was
still armed to fire a revert for a device that had already been reverted.

The author's log, 19:34:59:

    revert  device-wide -> RevertToDefaultResult(changed=[UsbDebugging, AccessibilityServices])

and no `svc  auto unhide watcher stopped` after it, where every auto-unhide revert has one.

Its twin, a minute later at 19:36:00: `tile  hide tile hidden=true` — after two full reverts.
That is handover_3 §3 debt item 2, which said clearing the records properly "belongs with r2b".

### 2. The author's rule

> *"revert to default is supposed to clear all pending reverts first including IMD+ (full
> cascade memory), clear autounhide service, and then revert to default"*

So the named function becomes four steps in one place, `SettingsHiddenRunner.revertToDefault`:

1. IMD+'s flag, cleared.
2. Every per-app record, swept.
3. The auto-unhide session and the pending-revert record, cleared.
4. The defaults, driven.

⚠ **Why the flag rather than `autoHideRunner.revert()`.** That call's device-wide branch is
exactly three things: cancel its own notification, clear `autoHideRunning`, and run
`RevertToDefaultRunner`. Step 4 is that third thing, so calling it here would revert twice and
speak twice — two toasts for one press. What is actually needed from IMD+ is the flag, cleared
**before** the revert, for the reason its own comment gives: the revert re-enables the detector
as part of putting the accessibility services back, and a detector coming up while this still
read "running" would find IMD+ disarmed.

⚠ **This cannot live in `RevertToDefaultRunner` itself.** `AutoHideRunner` injects that runner,
so a runner that injected `AutoHideRunner` back would be a Dagger cycle. `SettingsHiddenRunner`
already holds every piece and is injected by nobody in that chain, so it is where the sequence
goes — and putting it there means the three explicit routes each become one call rather than
three copies of a four-step recipe, which is the r1 lesson about eight hide routes applied
again.

**IMD+ is re-armed by the revert itself** — `RevertToDefaultUseCase:361` calls
`restoreAutoHideServiceUseCase()`, and the author's own log shows `imd+service=running` after
every revert. Nothing extra is needed for it.

### 3. IMD+ armed the auto-unhide watch differently from every other route

`revertNamesApp` is `PerApp && Memory`, and the three launch routes pass it through
`AutoUnhideWatch.armIfApplied`. IMD+ did not — it armed with `componentName` whenever the
*hiding* framework was Per app, so under **Per app + Revert to default** the launch routes armed
device-wide (auto unhide waits for every app) while IMD+ armed per-app (auto unhide reverted it
alone, from a record, under a framework that says drive the defaults). Now it asks the same
question as everyone else.

### 4. The log now names the kind of revert

Every revert that drives the defaults logged the same result line whether it was the named
function or a framework-following unhide. The fact existed — r2e put `explicit` on the runner —
it was simply never written down. It could only be *inferred*, from an explicit press having no
`revert  unhide memory=… fallback=…` line before it.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BR = "broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver"

HIDDEN_RUNNER = f"{BR}/SettingsHiddenRunner.kt"

AUTO_HIDE_RUNNER = f"{BR}/AutoHideRunner.kt"

REVERT_RUNNER = f"{BR}/RevertToDefaultRunner.kt"

TASKER = f"{BR}/TaskerIntegrationBroadcastReceiver.kt"

MANAGER_VM = (
    "feature/apps/src/main/kotlin/com/android/geto/feature/apps/manager/"
    "SettingsManagerViewModel.kt"
)

REVERT_ACTIVITY = "app/src/main/kotlin/com/android/geto/activity/revert/RevertActivity.kt"

HIDDEN_RUNNER_EDITS: list[tuple[str, str]] = [
    (
        """import com.android.geto.common.showHiddenToast
""",
        """import com.android.geto.common.AutoRevertPending
import com.android.geto.common.AutoUnhideWatch
import com.android.geto.common.showHiddenToast
""",
    ),
    (
        """    private suspend fun unhide(fallbackToDefault: Boolean) {
""",
        """    /**
     * The named `Revert to default`, and everything that has to be settled before it.
     *
     * ⚠ **Four steps, and the first three are the author's bug report.** `RevertToDefaultRunner`
     * cancels every notification and touches neither [AutoUnhideWatch] nor [AutoRevertPending],
     * so an explicit revert used to put the settings back and leave the auto unhide session
     * standing — service running, notification in the shade, still armed to revert a device
     * that had already been reverted — and leave the per-app records behind it, which is why
     * the Hide settings tile still read "hidden" afterwards.
     *
     * The author's rule: *clear all pending reverts first including IMD+, clear the auto unhide
     * service, and then revert to default.*
     *
     * ⚠ **The IMD+ flag rather than [AutoHideRunner.revert].** That call's device-wide branch is
     * three things — cancel its own notification, clear `autoHideRunning`, run
     * [RevertToDefaultRunner] — and the third is step four below. Calling it would revert twice
     * and speak twice, two toasts for one press. Cleared **before** the revert for the reason
     * its own comment gives: the revert re-enables IMD's detector as part of putting the
     * accessibility services back, and a detector coming up while this still read "running"
     * would find IMD+ disarmed.
     *
     * ⚠ **IMD+ is re-armed by the revert itself**, in `RevertToDefaultUseCase` — nothing here
     * has to do it, and doing it here as well would race that.
     *
     * ⚠ **Here rather than in [RevertToDefaultRunner].** `AutoHideRunner` injects that runner,
     * so a runner reaching back for `AutoHideRunner` would be a Dagger cycle. This class already
     * holds every piece, and one method beats the same four-step recipe written into each of
     * the three explicit routes — the r1 lesson about eight hide routes, applied again.
     *
     * Tracked as one piece of work for the whole press, like [toggle]: the four steps claim the
     * tracker separately underneath, and without this the tile would flicker between them.
     */
    suspend fun revertToDefault() = settingsWorkTracker.track(
        kind = SettingsWorkKind.Unhiding,
    ) {
        if (userDataRepository.userData.first().autoHideRunning) {
            Diagnostics.log(tag = "revert", message = "explicit: clearing IMD+ hold")

            userDataRepository.updateAutoHideRunning(running = false)
        }

        // Every per-app record, whatever hid them — a launch, a shortcut or IMD+ under Per app
        // configuration. The defaults go on top afterwards, which is r2's extras-before-defaults
        // ordering: anything a profile hid outside the six revert targets is put back by this,
        // and the six themselves are then driven wherever the configuration says.
        if (getSettingsHiddenUseCase().memory) {
            Diagnostics.log(tag = "revert", message = "explicit: sweeping memory records")

            // Each per-app Revert notification is about to describe a device that no longer
            // exists. The runner below cancels them too, a moment later; this is early enough
            // that none can be tapped in between.
            notificationManagerWrapper.cancelAll()

            revertAllMemoryUseCase()
        }

        // The session is over however it ended. Clearing the watch is what lets the service
        // settle and take its notification with it; clearing the pending record is
        // AutoRevertPending's own case — "the user reverts by hand first ... firing again on
        // return would be a second revert of nothing".
        AutoUnhideWatch.clear()

        AutoRevertPending.clear()

        revertToDefaultRunner(explicit = true)
    }

    private suspend fun unhide(fallbackToDefault: Boolean) {
""",
    ),
]

AUTO_HIDE_RUNNER_EDITS: list[tuple[str, str]] = [
    (
        """import com.android.geto.domain.model.effectiveSettingsToHide
""",
        """import com.android.geto.domain.model.effectiveSettingsToHide
import com.android.geto.domain.model.revertNamesApp
""",
    ),
    (
        """            AutoUnhideWatch.arm(packageName = packageName, componentName = componentName)
""",
        """            // ⚠ **The same question the three launch routes ask**, through
            // `AutoUnhideWatch.armIfApplied`, and IMD+ used to ask a different one: it armed
            // per-app whenever the *hiding* framework was Per app. Under Per app + Revert to
            // default that left the launch routes arming device-wide — auto unhide waiting for
            // every app — while IMD+ armed per-app, so auto unhide reverted its app alone, from
            // a record, under a framework that says drive the defaults. Which app's record a
            // revert needs is the **unhiding** framework's question, and `revertNamesApp` is
            // where it is answered for everyone else.
            AutoUnhideWatch.arm(
                packageName = packageName,
                componentName = componentName.takeIf {
                    revertNamesApp(
                        hidingFramework = userData.hidingFramework,
                        unhidingFramework = userData.unhidingFramework,
                    )
                },
            )
""",
    ),
]

REVERT_RUNNER_EDITS: list[tuple[str, str]] = [
    (
        """import com.android.geto.domain.model.AccessibilityServicePlan
""",
        """import com.android.geto.domain.common.Diagnostics
import com.android.geto.domain.model.AccessibilityServicePlan
""",
    ),
    (
        """        SettingsObservationGate.pause()

        return try {
""",
        """        // Which kind of revert this is, which the log could previously only *infer* — an
        // explicit press has no `unhide memory=... fallback=...` line before it, because it
        // does not come through SettingsHiddenRunner.unhide at all. The distinction has existed
        // since r2e and was simply never written down.
        Diagnostics.log(
            tag = "revert",
            message = "revert to default explicit=$explicit fromMemory=$fromMemory",
        )

        SettingsObservationGate.pause()

        return try {
""",
    ),
]

MANAGER_VM_EDITS: list[tuple[str, str]] = [
    (
        """import com.android.geto.broadcastreceiver.RevertToDefaultRunner
""",
        """""",
    ),
    (
        """    private val revertToDefaultRunner: RevertToDefaultRunner,
""",
        """""",
    ),
    (
        """        // `explicit`: the manager's button is the named function, so its toast says
        // "reverted" rather than "restored". The author's own list.
        appScope.launch { revertToDefaultRunner(explicit = true) }
""",
        """        // Through the hidden runner, which settles every outstanding debt and ends the auto
        // unhide session before driving the defaults. It is the one that passes `explicit`, so
        // the toast still says "reverted" rather than "restored".
        appScope.launch { settingsHiddenRunner.revertToDefault() }
""",
    ),
]

REVERT_ACTIVITY_EDITS: list[tuple[str, str]] = [
    (
        """import com.android.geto.broadcastreceiver.RevertToDefaultRunner
""",
        """import com.android.geto.broadcastreceiver.SettingsHiddenRunner
""",
    ),
    (
        """    lateinit var revertToDefaultRunner: RevertToDefaultRunner
""",
        """    lateinit var settingsHiddenRunner: SettingsHiddenRunner
""",
    ),
    (
        """        appScope.launch { revertToDefaultRunner(explicit = true) }
""",
        """        appScope.launch { settingsHiddenRunner.revertToDefault() }
""",
    ),
]

# No import edit here: this receiver is in the same package as the runner it drops.
TASKER_EDITS: list[tuple[str, str]] = [
    (
        """    @Inject
    lateinit var revertToDefaultRunner: RevertToDefaultRunner

""",
        """""",
    ),
    (
        """                        revertToDefaultRunner(explicit = true)
""",
        """                        settingsHiddenRunner.revertToDefault()
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

    staged: dict[Path, str] = {}

    everything = {
        HIDDEN_RUNNER: HIDDEN_RUNNER_EDITS,
        AUTO_HIDE_RUNNER: AUTO_HIDE_RUNNER_EDITS,
        REVERT_RUNNER: REVERT_RUNNER_EDITS,
        MANAGER_VM: MANAGER_VM_EDITS,
        REVERT_ACTIVITY: REVERT_ACTIVITY_EDITS,
        TASKER: TASKER_EDITS,
    }

    for name, edits in everything.items():
        path = ROOT / name

        before = set(path.read_text(encoding="utf-8").splitlines()) if path.exists() else set()

        text = apply(path=path, edits=edits, problems=problems)

        if text is None:
            continue

        staged[path] = text

        # ⚠ Only lines this edit adds — handover_3 §4.
        for line in set(text.splitlines()) - before:
            if len(line) > 120:
                problems.append(f"{path.name}: {len(line)} chars — {line.strip()[:60]}")

    # `explicit = true` now has exactly one caller, inside the new method, rather than three
    # copies of a four-step recipe.
    explicit = 0

    for kotlin in sorted(ROOT.rglob("*.kt")):
        if "build" in kotlin.relative_to(ROOT).parts:
            continue

        body = staged.get(kotlin) or kotlin.read_text(encoding="utf-8")

        explicit += body.count("explicit = true")

    if explicit != 1:
        problems.append(f"{explicit} call sites pass explicit = true, expected 1")

    # And the three routes that used to do it all reach the new method instead.
    calls = 0

    for kotlin in sorted(ROOT.rglob("*.kt")):
        if "build" in kotlin.relative_to(ROOT).parts:
            continue

        body = staged.get(kotlin) or kotlin.read_text(encoding="utf-8")

        calls += body.count("settingsHiddenRunner.revertToDefault()")

    if calls != 3:
        problems.append(f"{calls} routes call revertToDefault(), expected 3")

    # No file may keep an injection it no longer uses — Kotlin compiles an unused constructor
    # property happily, and the audits do not read constructor parameters.
    for name in (MANAGER_VM, TASKER):
        body = staged.get(ROOT / name, "")

        if "RevertToDefaultRunner" in body:
            problems.append(f"{Path(name).name}: still injects RevertToDefaultRunner")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")

    print("ok — explicit Revert to default settles everything first; IMD+ arms via "
          "revertNamesApp; the log names the revert")

    return 0


if __name__ == "__main__":
    sys.exit(main())
