#!/usr/bin/env python3
"""
v3-r9 — wire SyncAutoHideDetectorSelectionUseCase to its two callers.

The use case itself carries the reasoning; this only puts it where it has to run.

  * **`GetoApplication`**, once, behind `autoHideDetectorManagedV3` — the one-shot pass that
    reaches installs which already had IMD+ on when the behaviour changed, including the author's
    own, which is where the report came from. Behind a flag rather than run every start because
    the flag is what makes "we have done this once" a fact rather than a guess.
  * **`updateAutoHideEnabledNow`**, on every flip. That function is the single door onto the
    preference — `updateAutoHideEnabled` and the detector-granting path both go through it — so
    hooking it catches both directions without a second place to keep in step.

⚠ **The sync is idempotent**, so the two callers overlapping costs a read and no write.

⚠ **Called after the preference is written, not before.** It reads `autoHideEnabled` to decide what
the selection should be, so running it first would sync to the value being replaced.

Every edit asserts its anchor matches exactly once. Nothing is written if any file fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

APP = "app/src/main/kotlin/com/android/geto/GetoApplication.kt"

VM = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsViewModel.kt"

APP_IMPORT_OLD = "import com.android.geto.domain.usecase.MigrateRevertDefaultsUseCase\n"

APP_IMPORT_NEW = (
    "import com.android.geto.domain.usecase.MigrateRevertDefaultsUseCase\n"
    "import com.android.geto.domain.usecase.SyncAutoHideDetectorSelectionUseCase\n"
)

APP_FIELD_OLD = '''    lateinit var migrateRevertDefaultsUseCase: MigrateRevertDefaultsUseCase
'''

APP_FIELD_NEW = '''    lateinit var migrateRevertDefaultsUseCase: MigrateRevertDefaultsUseCase

    @Inject
    lateinit var syncAutoHideDetectorSelectionUseCase: SyncAutoHideDetectorSelectionUseCase
'''

APP_LAUNCH_OLD = '''        appScope.launch { migrateRevertDefaultsUseCase() }
'''

APP_LAUNCH_NEW = '''        appScope.launch { migrateRevertDefaultsUseCase() }

        // IMD+'s own detector is an ordinary entry in the managed accessibility list since r9,
        // where it used to be a tick the picker drew by itself and stored nowhere. An install
        // that already had IMD+ on has an empty list and no event coming to fix it - that is
        // what left the manager's Accessibility row greyed - so it is brought into line once,
        // here, and kept there by the IMD+ switch afterwards.
        //
        // Behind the flag rather than run every start: the sync is idempotent and would write
        // nothing anyway, but "this has already been done" is worth being a fact rather than a
        // re-derivation, and it matches every other one-shot in this block.
        appScope.launch {
            if (!userDataRepository.userData.first().autoHideDetectorManagedV3) {
                syncAutoHideDetectorSelectionUseCase()

                userDataRepository.updateAutoHideDetectorManagedV3(done = true)
            }
        }
'''

VM_IMPORT_OLD = "import com.android.geto.domain.usecase.RetireAutoHideServiceUseCase\n"

VM_IMPORT_NEW = (
    "import com.android.geto.domain.usecase.RetireAutoHideServiceUseCase\n"
    "import com.android.geto.domain.usecase.SyncAutoHideDetectorSelectionUseCase\n"
)

VM_FIELD_OLD = '''    private val retireAutoHideServiceUseCase: RetireAutoHideServiceUseCase,
'''

VM_FIELD_NEW = '''    private val retireAutoHideServiceUseCase: RetireAutoHideServiceUseCase,
    private val syncAutoHideDetectorSelectionUseCase: SyncAutoHideDetectorSelectionUseCase,
'''

VM_HOOK_OLD = '''    private suspend fun updateAutoHideEnabledNow(enabled: Boolean) {
        userDataRepository.updateAutoHideEnabled(enabled = enabled)
'''

VM_HOOK_NEW = '''    private suspend fun updateAutoHideEnabledNow(enabled: Boolean) {
        userDataRepository.updateAutoHideEnabled(enabled = enabled)

        // ⚠ **After the write, never before — r9.** The sync reads `autoHideEnabled` to decide
        // whether IMD+'s detector belongs in the managed accessibility list, so running it first
        // would sync it to the value being replaced.
        //
        // This is the single door onto that preference - `updateAutoHideEnabled` and the
        // detector-granting path above both come through here - so one call covers both
        // directions. See SyncAutoHideDetectorSelectionUseCase for why the selection has to
        // exist at all: without it the settings manager's Accessibility row greys itself while
        // the picker shows the detector ticked.
        syncAutoHideDetectorSelectionUseCase()
'''

EDITS = [
    (APP, APP_IMPORT_OLD, APP_IMPORT_NEW),
    (APP, APP_FIELD_OLD, APP_FIELD_NEW),
    (APP, APP_LAUNCH_OLD, APP_LAUNCH_NEW),
    (VM, VM_IMPORT_OLD, VM_IMPORT_NEW),
    (VM, VM_FIELD_OLD, VM_FIELD_NEW),
    (VM, VM_HOOK_OLD, VM_HOOK_NEW),
]

CHECKS = [
    (APP, "syncAutoHideDetectorSelectionUseCase()", 1, "run once at start"),
    (APP, "updateAutoHideDetectorManagedV3(done = true)", 1, "and the flag set once"),
    # Lower-case initial: the setter is updateAutoHideDetectorManagedV3 and does not match.
    (APP, "autoHideDetectorManagedV3", 1, "the flag is read once"),
    (VM, "syncAutoHideDetectorSelectionUseCase()", 1, "and once on every IMD+ flip"),
    (VM, "userDataRepository.updateAutoHideEnabled(enabled = enabled)\n\n        // ⚠", 1,
     "the sync sits directly after the write it depends on"),
]


def main() -> int:
    planned: dict[Path, str] = {}

    originals: dict[Path, str] = {}

    for rel, old, new in EDITS:
        path = ROOT / rel

        if not path.is_file():
            print(f"REFUSED: missing {rel}")
            return 1

        originals.setdefault(path, path.read_text(encoding="utf-8"))

        text = planned.get(path, originals[path])

        if text.count(old) != 1:
            print(f"REFUSED: {Path(rel).name} anchor {old.strip()[:60]!r} x{text.count(old)}")
            return 1

        if new in originals[path]:
            print(f"REFUSED: {Path(rel).name} already applied")
            return 1

        planned[path] = text.replace(old, new, 1)

        print(f"  ok        {Path(rel).name:24s} {old.strip().splitlines()[0][:46]}")

    for rel, token, want, why in CHECKS:
        got = planned[ROOT / rel].count(token)

        if got != want:
            print(f"REFUSED: {Path(rel).name}: {why} — x{got}, expected {want}")
            return 1

        print(f"  checked   {Path(rel).name:24s} x{got}  {token[:40]!r}")

    for path, text in planned.items():
        over = lambda s: {ln for ln in s.split("\n")
                          if len(ln) > 120 and not ln.lstrip().startswith("import ")}

        if over(text) - over(originals[path]):
            print(f"REFUSED: {path.name} would gain lines over 120 chars")
            return 1

    for path, text in planned.items():
        path.write_text(text, encoding="utf-8")

    print(f"\n  ok  wrote {len(planned)} file(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
