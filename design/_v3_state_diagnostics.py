#!/usr/bin/env python3
"""
v3-r2f — wire the IMD state block into the diagnostic log.

The author: *"if diagnostics dont tell settings state of IMD please add that for all settings
and permissions granted"*. They do not — the file records **events** (a write, a hide, a
revert, a tile state change) and never once says what the install was configured to do or what
it was allowed to do. So a revert that restored two settings where three were expected reads as
a bug until you know the third was never in the list.

`DiagnosticStateReporter` (new file, not touched here) gathers it. This script does the
wiring only, and the wiring is **one place**:

### Why `SettingsWorkTracker.inFlight` and not eighteen call sites

The author asked for the state "on every hide and every revert". There are around eighteen
routes that start one and only four use cases underneath them, which is exactly the reasoning
`SettingsWorkTracker`'s own doc gives for being signalled from the use cases rather than the
callers. Its `inFlight` flow is therefore already a complete, unmissable feed of every hide and
every revert in the app — and it is `distinctUntilChanged`, so the nesting the tracker exists to
handle (the tile claims twice, IMD+ claims around the use case's own claim) collapses to one
report rather than three.

That means **no runner, receiver or use case is edited at all**. One collector in
`GetoApplication`, beside the two that are already there.

⚠ **`.drop(1)`.** `inFlight` is derived from a `MutableStateFlow(0)`, so subscribing replays the
current value — a `false` at process start, before anything has happened. Dropping it stops a
"settled" report firing on a device where nothing has settled. Nothing can be in flight before
`Application.onCreate`, so the dropped emission can never be a real one.

### The baseline

The full block goes out when recording is switched on, and only changed lines after that. The
existing `diagnosticsEnabled` collector is the exact moment: it already exists, it already fires
on the transition, and `DefaultDiagnosticLogStore.setEnabled` has by then written
"session recording started" and created the file. Without a baseline a later `work: permissions
writeSecure=no` line would describe a change from a value the reader never saw.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

APPLICATION = "app/src/main/kotlin/com/android/geto/GetoApplication.kt"

REPORTER = (
    "broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/"
    "DiagnosticStateReporter.kt"
)

EDITS: list[tuple[str, str]] = [
    # Imports, in the project's existing alphabetical blocks.
    (
        """import com.android.geto.broadcastreceiver.AutoHideRunner
""",
        """import com.android.geto.broadcastreceiver.AutoHideRunner
import com.android.geto.broadcastreceiver.DiagnosticStateReporter
""",
    ),
    (
        """import com.android.geto.domain.usecase.MigrateRevertDefaultsUseCase
""",
        """import com.android.geto.domain.usecase.MigrateRevertDefaultsUseCase
import com.android.geto.domain.usecase.SettingsWorkTracker
""",
    ),
    (
        """import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.map
""",
        """import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.drop
import kotlinx.coroutines.flow.map
""",
    ),
    # The two injections, beside the log store they work with.
    (
        """    @Inject
    lateinit var diagnosticLogStore: DefaultDiagnosticLogStore
""",
        """    @Inject
    lateinit var diagnosticLogStore: DefaultDiagnosticLogStore

    @Inject
    lateinit var diagnosticStateReporter: DiagnosticStateReporter

    @Inject
    lateinit var settingsWorkTracker: SettingsWorkTracker
""",
    ),
    # The baseline block, plus the feed of every hide and every revert.
    (
        """        appScope.launch {
            userDataRepository.userData
                .map { it.diagnosticsEnabled }
                .distinctUntilChanged()
                .collect { enabled -> Diagnostics.enabled = enabled }
        }
""",
        """        appScope.launch {
            userDataRepository.userData
                .map { it.diagnosticsEnabled }
                .distinctUntilChanged()
                .collect { enabled ->
                    Diagnostics.enabled = enabled

                    // The baseline every delta below is a difference from. This transition is
                    // the only moment a file has none: the store has just created it and
                    // written "recording started", and without a full block behind them a
                    // later "work: permissions writeSecure=no" would describe a change from a
                    // value the reader never saw.
                    if (enabled) {
                        diagnosticStateReporter.report(
                            reason = "recording started",
                            full = true,
                        )
                    }
                }
        }

        // What IMD was configured to do, and allowed to do, at the start and the end of every
        // hide and every revert — whichever of the eighteen routes began it.
        //
        // ⚠ **The tracker rather than the routes, for the reason the tracker itself gives.**
        // Those eighteen call sites sit on four use cases, and every one of them claims this
        // before it touches anything, so a path cannot start work without appearing here. A
        // reporter wired into the routes would have eighteen chances to miss one and would
        // silently not cover the nineteenth.
        //
        // ⚠ **`distinctUntilChanged` is what makes this one report rather than three.** The
        // claims genuinely nest — the tile takes two, an IMD+ revert takes one around the use
        // case's own — and the flow only speaks when the answer changes.
        //
        // ⚠ **`drop(1)`** discards the replayed `false` a StateFlow hands every new collector,
        // which at this point in `onCreate` is "nothing has ever run" rather than "something
        // just settled". Nothing can be in flight before this line, so it can never drop a
        // real emission.
        //
        // Costs nothing with recording off: the reporter's first act is one volatile read.
        appScope.launch {
            settingsWorkTracker.inFlight
                .drop(1)
                .collect { running ->
                    diagnosticStateReporter.report(
                        reason = if (running) "work" else "settled",
                    )
                }
        }
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

    reporter = ROOT / REPORTER

    if not reporter.exists():
        problems.append(f"{REPORTER} is missing — the reporter itself is not in the tree")
    else:
        body = reporter.read_text(encoding="utf-8")

        # The reporter must stay read-only. It is collected beside a hide that is still in
        # flight, so anything it wrote would change the very run it is describing.
        #
        # ⚠ Named mutators, not a substring sweep. The first version of this guard forbade
        # `"= true"` and refused on `configuration[it] == true` — the handover_3 §4 trap in a
        # new costume: a pattern that also matches the thing it is not about.
        for forbidden in (
            "userDataRepository.update",
            "Diagnostics.enabled =",
            "setEnabledAccessibilityServices(",
            "canWriteSecureSettings(",
            "setManualTarget",
        ):
            if forbidden in body:
                problems.append(f"DiagnosticStateReporter: writes or mutates — {forbidden!r}")

        # And the only thing it may ask the repository for is the read.
        reads = body.count("userDataRepository.")

        if reads != body.count("userDataRepository.userData"):
            problems.append(f"DiagnosticStateReporter: {reads} repository calls, not all reads")

        # Gated, or it does real I/O on every hide with the log switched off.
        if "if (!Diagnostics.enabled) return" not in body:
            problems.append("DiagnosticStateReporter: not gated on Diagnostics.enabled")

    path = ROOT / APPLICATION

    before = set(path.read_text(encoding="utf-8").splitlines()) if path.exists() else set()

    text = apply(path=path, edits=EDITS, problems=problems)

    if text is not None:
        # ⚠ Only lines this edit adds — handover_3 §4, which has cost two rounds.
        for line in set(text.splitlines()) - before:
            if len(line) > 120:
                problems.append(f"{path.name}: {len(line)} chars — {line.strip()[:60]}")

        # Exactly one collector each, and the existing three launches still there.
        for needle, expected in (
            ("diagnosticStateReporter.report(", 2),
            ("settingsWorkTracker.inFlight", 1),
            ("Diagnostics.install(sink = diagnosticLogStore)", 1),
            ("autoHideRunner.arm(scope = appScope)", 1),
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

    print("ok — state block wired to recording start and to every hide and revert")

    return 0


if __name__ == "__main__":
    sys.exit(main())
