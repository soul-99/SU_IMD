#!/usr/bin/env python3
"""
v3-r2b2 — cascading launches collapse to one shared debt, one notification, one revert.

### What the author asked for

> *"app 1 launched then revert notification displayed with its icon, but app 2 launched without
> app 1 revert, dismiss app 1 notification and show a generic notification with no app name or
> app icon as we would do for imd defaults config under hiding framework, and this notification
> adds all pending reverts for itself, and this keeps going on ... and for autounhide in this
> case should only run when all the apps with outstanding reverts are swiped away not the first
> or last only, all"*

and then: *"let IMD+ then IMD notifications cascade"*.

### The trigger is derived, never stored

The collapse is in force when **a debt was already outstanding at the moment this hide began** —
`autoHideRunning || settingsHidden`, read from persisted state **before** the apply. Read after
it the answer is always yes, which is why the three call sites take it from the `userData` they
already read for the frameworks.

⚠ **Derived rather than stored is what makes it a state and not an event** (r2b §5.4). A third
launch re-derives the same answer, so it collapses too; and a launch after a process death
re-derives it from the records, which outlive the process, so the chain is not broken by IMD
being killed in the middle of it.

### IMD+ needs no code at all, and that is a finding rather than an omission

IMD+ is **always first in the chain**: `autoHideBlockedByHide` is `settingsHidden`, so a second
IMD+ run is refused the moment anything is outstanding, and the launch path has no equivalent
gate — its only one is `autoHideRunning`, false under Per app. So the order is always
**IMD+ → launch → launch**, never IMD+ → IMD+.

Which means IMD+ never *enters* the collapsed branch; it only ever needs to be *dismissed* by
the launch that follows it, and the `cancelAll()` below does exactly that. The author's "IMD+
then IMD" therefore works with no change to `AutoHideRunner` — verified rather than assumed.

### Auto unhide waits for the last app for free

Marking the watch entries device-wide is the same act as collapsing the notification, so
`AutoUnhideWatcher`'s existing rule fires unchanged:

> "A device-wide hide is one shared debt, so it waits for the last of them."

No second waiting rule beside the per-app branch, and the code that does it has been
device-tested since r1. The revert that follows is `flushPendingReverts` → the memory sweep,
whose toast names no app: `IMD: Settings restored from memory`, which is what the author asked
for.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

WATCH = "common/src/main/kotlin/com/android/geto/common/AutoUnhideWatch.kt"

POSTER = (
    "broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/"
    "PostAppliedSettingsNotification.kt"
)

APPS_VM = "feature/apps/src/main/kotlin/com/android/geto/feature/apps/AppsViewModel.kt"

FAV_VM = "feature/apps/src/main/kotlin/com/android/geto/feature/apps/FavouriteAppsViewModel.kt"

SHORTCUT_VM = (
    "app/src/main/kotlin/com/android/geto/activity/shortcut/ShortcutActivityViewModel.kt"
)

# The line every launch site already has, and the one this inserts after.
COLLAPSED_ANCHOR = """            val unhidingFramework = userData.unhidingFramework
"""

COLLAPSED_INSERT = """            val unhidingFramework = userData.unhidingFramework

            // ⚠ **Read before the apply, and that is the whole of it** — afterwards the answer
            // is always yes. True means this launch is arriving into a window something else
            // already hid: another app, a tile press, or IMD+. The debt becomes one shared
            // debt from here, so the per-app notifications are replaced by a single generic
            // one and auto unhide waits for the last of them rather than reverting each app as
            // its own session ends. See AutoUnhideWatch.collapse.
            val collapsed = userData.autoHideRunning || userData.settingsHidden
"""

WATCH_EDITS: list[tuple[str, str]] = [
    (
        """    fun armIfApplied(applied: Boolean, componentName: String, memory: Boolean) {
        if (!applied) return

        arm(
            packageName = componentName.substringBefore('/'),
            componentName = componentName.takeIf { memory },
        )
    }
""",
        """    fun armIfApplied(
        applied: Boolean,
        componentName: String,
        memory: Boolean,
        collapsed: Boolean = false,
    ) {
        // ⚠ **Before the `applied` guard, not after it, and a standalone probe of this file
        // found the reason.** `leftSettingsHidden` is `Success || AlreadyHidden`, while the
        // notification is posted on `Success || Failure` — so a **failed** hide arriving into a
        // collapsed window posts a notification and, with the collapse behind the guard, would
        // have posted a *per-app* one beside the generic one. The collapse is a property of the
        // window rather than of what this particular hide managed to write.
        if (collapsed) collapse()

        if (!applied) return

        arm(
            packageName = componentName.substringBefore('/'),
            componentName = componentName.takeIf { memory && !collapsed },
        )
    }

    /**
     * Every outstanding session becomes one shared, device-wide debt.
     *
     * **Collapsing the notification and collapsing auto unhide are the same act**, which is why
     * they are one function. Nulling the component names puts every entry into
     * `AutoUnhideWatcher`'s device-wide branch, whose rule already reads: *a device-wide hide is
     * one shared debt, so it waits for the last of them.* That is the author's "auto unhide
     * should only run when all the apps with outstanding reverts are swiped away", in code that
     * has been on devices since r1 — rather than a second waiting rule beside the per-app branch
     * that reverts each app as its own session ends, which is the leak this exists to close.
     *
     * Iterated by key with a copied key list rather than over the map or by destructuring: this
     * is a `ConcurrentHashMap` the watcher reads on its own thread, and `(a, b) ->` on a map
     * entry is the `component1()/component2()` ambiguity that has already cost this project two
     * rounds.
     */
    fun collapse() {
        collapsed = true

        for (packageName in entries.keys.toList()) {
            val entry = entries[packageName] ?: continue

            if (entry.componentName == null) continue

            entries[packageName] = entry.copy(componentName = null)
        }
    }
""",
    ),
    (
        """    /** Nothing is hidden any more, however it came back. */
    fun clear() {
        entries.clear()
    }
""",
        """    /** Nothing is hidden any more, however it came back. */
    fun clear() {
        entries.clear()

        // The chain is over with the debt. Left set, the next first launch would post the
        // generic notification instead of its own, with no cascade behind it to justify one.
        collapsed = false
    }

    /**
     * Whether the outstanding debt has been collapsed into one shared session.
     *
     * Read by `postAppliedSettingsNotification` to decide whether this hide gets its own per-app
     * notification or folds into the single generic one, and set by [collapse] a moment earlier
     * in the same launch — the arm and the notification are two steps of one flow.
     *
     * ⚠ **In memory, and the decision that sets it is not.** The launch sites derive the answer
     * from persisted records *before* they apply anything, so a process death does not break a
     * chain: the next launch reads the records, finds a debt outstanding, and collapses again.
     * This flag only has to survive the few milliseconds between the arm and the post.
     */
    @Volatile
    var collapsed: Boolean = false
""",
    ),
]

POSTER_EDITS: list[tuple[str, str]] = [
    (
        """import com.android.geto.domain.model.UnhidingFramework
""",
        """import com.android.geto.common.AutoUnhideWatch
import com.android.geto.domain.model.UnhidingFramework
""",
    ),
    (
        """    when (unhidingFramework) {
        UnhidingFramework.Memory -> {
""",
        """    // ⚠ **The cascade.** This launch arrived into a window something else had already
    // hidden, so there is now one shared debt and the per-app offers standing in the shade are
    // each an offer to undo one app of it — which is no longer a thing that can be done on its
    // own. `cancelAll` sweeps them, IMD+'s own fixed-id notification included, and the single
    // generic notification below replaces the lot.
    //
    // ⚠ **A state, not an event, and that is `AutoUnhideWatch.collapsed`'s job.** Cancelling
    // once would not hold: each per-app notification is posted under `componentName.hashCode()`,
    // so a third launch would post a fresh one beside the collapsed one. While the collapse is
    // in force no per-app notification is posted at all.
    //
    // The generic notification is the one IMD defaults already uses, and its Revert button
    // already does the right thing — `RevertToDefaultBroadcastReceiver` calls
    // `settingsHiddenRunner.unhide()`, which under the memory function sweeps every record and
    // says the sentence that names no app.
    if (AutoUnhideWatch.collapsed) {
        notificationManager.cancelAll()

        notificationManager.notify(
            id = REVERT_TO_DEFAULT_NOTIFICATION_ID,
            notification = buildRevertToDefaultNotification(context = context),
        )

        return
    }

    when (unhidingFramework) {
        UnhidingFramework.Memory -> {
""",
    ),
]

APPS_VM_EDITS: list[tuple[str, str]] = [
    (
        """import com.android.geto.domain.model.revertNamesApp
""",
        """import com.android.geto.domain.model.revertNamesApp
import com.android.geto.domain.model.settingsHidden
""",
    ),
    (COLLAPSED_ANCHOR, COLLAPSED_INSERT),
    (
        """            AutoUnhideWatch.armIfApplied(
                applied = result.leftSettingsHidden,
                componentName = componentName,
                memory = revertNamesApp(
                    hidingFramework = hidingFramework,
                    unhidingFramework = unhidingFramework,
                ),
            )
""",
        """            AutoUnhideWatch.armIfApplied(
                applied = result.leftSettingsHidden,
                componentName = componentName,
                memory = revertNamesApp(
                    hidingFramework = hidingFramework,
                    unhidingFramework = unhidingFramework,
                ),
                collapsed = collapsed,
            )
""",
    ),
]

FAV_VM_EDITS: list[tuple[str, str]] = [
    (COLLAPSED_ANCHOR, COLLAPSED_INSERT),
    (
        """            AutoUnhideWatch.armIfApplied(
                applied = result.leftSettingsHidden,
                componentName = componentName,
                memory = revertNamesApp(
                    hidingFramework = hidingFramework,
                    unhidingFramework = unhidingFramework,
                ),
            )
""",
        """            AutoUnhideWatch.armIfApplied(
                applied = result.leftSettingsHidden,
                componentName = componentName,
                memory = revertNamesApp(
                    hidingFramework = hidingFramework,
                    unhidingFramework = unhidingFramework,
                ),
                collapsed = collapsed,
            )
""",
    ),
]

SHORTCUT_VM_EDITS: list[tuple[str, str]] = [
    (
        """import com.android.geto.domain.model.revertNamesApp
""",
        """import com.android.geto.domain.model.revertNamesApp
import com.android.geto.domain.model.settingsHidden
""",
    ),
    (COLLAPSED_ANCHOR, COLLAPSED_INSERT),
    (
        """            AutoUnhideWatch.armIfApplied(
                applied = appSettingsResult.leftSettingsHidden,
                componentName = componentName,
                memory = revertNamesApp(
                    hidingFramework = hidingFramework,
                    unhidingFramework = unhidingFramework,
                ),
            )
""",
        """            AutoUnhideWatch.armIfApplied(
                applied = appSettingsResult.leftSettingsHidden,
                componentName = componentName,
                memory = revertNamesApp(
                    hidingFramework = hidingFramework,
                    unhidingFramework = unhidingFramework,
                ),
                collapsed = collapsed,
            )
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
        WATCH: WATCH_EDITS,
        POSTER: POSTER_EDITS,
        APPS_VM: APPS_VM_EDITS,
        FAV_VM: FAV_VM_EDITS,
        SHORTCUT_VM: SHORTCUT_VM_EDITS,
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

    # Every type name these edits introduce must be imported in its own file. Nothing in the
    # audit suite reads a type reference against the import block — the r2h trap.
    needs = {
        APPS_VM: ["com.android.geto.domain.model.settingsHidden"],
        FAV_VM: ["com.android.geto.domain.model.settingsHidden"],
        SHORTCUT_VM: ["com.android.geto.domain.model.settingsHidden"],
        POSTER: ["com.android.geto.common.AutoUnhideWatch"],
    }

    for name, imports in needs.items():
        body = staged.get(ROOT / name, "")

        for wanted in imports:
            if f"import {wanted}\n" not in body:
                problems.append(f"{Path(name).name}: missing import {wanted}")

    # All three launch sites collapse, and none was missed.
    collapsing = 0

    for kotlin in sorted(ROOT.rglob("*.kt")):
        if "build" in kotlin.relative_to(ROOT).parts:
            continue

        body = staged.get(kotlin) or kotlin.read_text(encoding="utf-8")

        collapsing += body.count("collapsed = collapsed")

    if collapsing != 3:
        problems.append(f"{collapsing} launch sites pass collapsed, expected 3")

    # And every armIfApplied call site is one of those three — a fourth added later without
    # the argument would silently opt out of the cascade.
    arms = 0

    for kotlin in sorted(ROOT.rglob("*.kt")):
        if "build" in kotlin.relative_to(ROOT).parts:
            continue

        body = staged.get(kotlin) or kotlin.read_text(encoding="utf-8")

        arms += body.count("AutoUnhideWatch.armIfApplied(")

    if arms != 3:
        problems.append(f"{arms} armIfApplied call sites, expected 3")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")

    print("ok — cascading launches collapse to one debt, one notification, one revert")

    return 0


if __name__ == "__main__":
    sys.exit(main())
