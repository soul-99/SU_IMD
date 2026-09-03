#!/usr/bin/env python3
"""
v3-r9 — storage for the two new preferences: which manager rows to draw, and the IMD+ migration.

Two fields, and the whole chain each of them needs: proto -> datastore -> UserData -> repository.

## `managerRows` (73)

The author's "Settings manager options": *"Only selected options are showed in the IMD's Settings
manager"*. Stored the way [RevertDefaults] (field 23) stores its own per-target answers, `"<Name>=0"`
/ `"<Name>=1"`, and that encoding is not decoration — the comment on field 23 spells out why a bare
list of names cannot tell **"the user hid this"** from **"never configured"**, and those two have to
behave differently. This preference has the identical problem: unticking every row and never opening
the dialog would otherwise store the same thing.

## `autoHideDetectorManagedV3` (74)

A one-shot migration flag, exactly like `manageShizukuMigratedV3` beside it. IMD+'s own detector is
about to become a real entry in `managedAccessibilityServices` rather than a tick the picker draws
by itself — see `_v3_autohide_detector_selection.py` — and an install that already has IMD+ on has
an empty list and would go on seeing the greyed row until it toggled IMD+ off and on again. The
migration is what reaches those installs; the hook in the view model is what keeps every install
right afterwards.

Every edit asserts its anchor matches exactly once. Nothing is written if any file fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PROTO = (
    "data/datastore-proto/src/main/proto/com/android/geto/data/datastore/proto/"
    "user_preferences.proto"
)

SOURCE = "data/datastore/src/main/kotlin/com/android/geto/data/datastore/UserPreferencesDataSource.kt"

USERDATA = "domain/model/src/main/kotlin/com/android/geto/domain/model/UserData.kt"

REPO = "domain/repository/src/main/kotlin/com/android/geto/domain/repository/UserDataRepository.kt"

REPO_IMPL = "data/repository/src/main/kotlin/com/android/geto/data/repository/DefaultUserDataRepository.kt"

# --- proto ------------------------------------------------------------------------------

PROTO_OLD = '''  IconStyleProto iconStyle = 72;
'''

PROTO_NEW = '''  IconStyleProto iconStyle = 72;

  // Which rows the settings manager draws, one entry per target encoded by ManagerRows as
  // "<Name>=0" or "<Name>=1".
  //
  // A state per target rather than a list of the ones to show, and for the same reason
  // revertDefaults above is: an absent name could not tell "the user hid this row" apart from
  // "not configured yet", and those behave differently - the first is a decision, the second
  // falls back to ManagerRows.Default, which is every row shown.
  repeated string managerRows = 73;

  // Whether the one-time pass that puts IMD+'s own detector into managedAccessibilityServices
  // has run.
  //
  // The detector used to be drawn ticked by the picker itself and stored nowhere, so an install
  // with IMD+ on and nothing else selected had an empty list - which is what greyed the
  // Accessibility row in the settings manager. It is an ordinary selection now; this reaches the
  // installs that were already in that state, and the write beside the IMD+ switch keeps every
  // install right from here on.
  bool autoHideDetectorManagedV3 = 74;
'''

# --- datastore: read ----------------------------------------------------------------------

READ_OLD = '''            revertDefaults = RevertDefaults.decode(it.revertDefaultsList),
'''

READ_NEW = '''            revertDefaults = RevertDefaults.decode(it.revertDefaultsList),
            managerRows = ManagerRows.decode(it.managerRowsList),
            autoHideDetectorManagedV3 = it.autoHideDetectorManagedV3,
'''

# --- datastore: write ---------------------------------------------------------------------

WRITE_OLD = '''    suspend fun updateRevertDefaultsResetV166(done: Boolean) {
'''

WRITE_NEW = '''    suspend fun updateManagerRows(states: Map<ManualRevertTarget, Boolean>) {
        userPreferences.updateData {
            it.copy {
                managerRows.clear()
                managerRows.addAll(ManagerRows.encode(states))
            }
        }
    }

    suspend fun updateAutoHideDetectorManagedV3(done: Boolean) {
        userPreferences.updateData {
            it.copy { this.autoHideDetectorManagedV3 = done }
        }
    }

    suspend fun updateRevertDefaultsResetV166(done: Boolean) {
'''

IMPORT_OLD = "import com.android.geto.domain.model.RevertDefaults\n"

IMPORT_NEW = (
    "import com.android.geto.domain.model.ManagerRows\n"
    "import com.android.geto.domain.model.RevertDefaults\n"
)

# --- UserData -----------------------------------------------------------------------------

UD_OLD = '''    val revertDefaults: Map<ManualRevertTarget, Boolean>,
'''

UD_NEW = '''    val revertDefaults: Map<ManualRevertTarget, Boolean>,
    /**
     * Which rows the settings manager draws, at the author's "Settings manager options".
     *
     * ⚠ **What is *shown*, not what is managed.** A row hidden here is not switched off, not
     * excluded from a hide, and not left out of "Revert to default" - it is simply not drawn.
     * Everything the engine does still follows [ManualRevertTarget.entries].
     *
     * One consequence is worth naming because it is the author's own instruction rather than a
     * side effect: the manager's All off / All on pill takes its list from what the card drew,
     * so a row hidden here stops being touched by the pill as well.
     */
    val managerRows: Map<ManualRevertTarget, Boolean>,
    /** Whether the one-time pass that made IMD+'s detector an ordinary selection has run. */
    val autoHideDetectorManagedV3: Boolean,
'''

# --- repository ---------------------------------------------------------------------------

REPO_OLD = '''    suspend fun updateRevertDefaults(states: Map<ManualRevertTarget, Boolean>)
'''

REPO_NEW = '''    suspend fun updateRevertDefaults(states: Map<ManualRevertTarget, Boolean>)

    /** Which rows the settings manager draws - see `UserData.managerRows`. */
    suspend fun updateManagerRows(states: Map<ManualRevertTarget, Boolean>)

    suspend fun updateAutoHideDetectorManagedV3(done: Boolean)
'''

IMPL_OLD = '''    override suspend fun updateRevertDefaults(states: Map<ManualRevertTarget, Boolean>) {
        userPreferencesDataSource.updateRevertDefaults(states = states)
'''

IMPL_NEW = '''    override suspend fun updateManagerRows(states: Map<ManualRevertTarget, Boolean>) {
        userPreferencesDataSource.updateManagerRows(states = states)
    }

    override suspend fun updateAutoHideDetectorManagedV3(done: Boolean) {
        userPreferencesDataSource.updateAutoHideDetectorManagedV3(done = done)
    }

    override suspend fun updateRevertDefaults(states: Map<ManualRevertTarget, Boolean>) {
        userPreferencesDataSource.updateRevertDefaults(states = states)
'''

EDITS = [
    (PROTO, PROTO_OLD, PROTO_NEW),
    (SOURCE, IMPORT_OLD, IMPORT_NEW),
    (SOURCE, READ_OLD, READ_NEW),
    (SOURCE, WRITE_OLD, WRITE_NEW),
    (USERDATA, UD_OLD, UD_NEW),
    (REPO, REPO_OLD, REPO_NEW),
    (REPO_IMPL, IMPL_OLD, IMPL_NEW),
]

CHECKS = [
    (PROTO, "repeated string managerRows = 73;", 1, "the field is numbered 73"),
    (PROTO, "bool autoHideDetectorManagedV3 = 74;", 1, "and the flag 74"),
    (PROTO, "= 73;", 1, "73 is used once"),
    (PROTO, "= 74;", 1, "and 74 once"),
    (SOURCE, "ManagerRows.decode", 1, "read once"),
    (SOURCE, "ManagerRows.encode", 1, "written once"),
    (USERDATA, "val managerRows:", 1, "UserData carries it"),
    (REPO, "suspend fun updateManagerRows", 1, "the repository declares it"),
    (REPO_IMPL, "override suspend fun updateManagerRows", 1, "and implements it"),
    (REPO_IMPL, "override suspend fun updateAutoHideDetectorManagedV3", 1, "both of them"),
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

        found = text.count(old)

        if found != 1:
            print(
                f"REFUSED: {Path(rel).name}\n  anchor {old.strip()[:66]!r}\n"
                f"  matched {found} time(s), expected exactly 1",
            )
            return 1

        if new in originals[path]:
            print(f"REFUSED: {Path(rel).name} already carries the replacement")
            return 1

        planned[path] = text.replace(old, new, 1)

        print(f"  ok        {Path(rel).name:34s} {old.strip().splitlines()[0][:40]}")

    for rel, token, want, why in CHECKS:
        got = planned[ROOT / rel].count(token)

        if got != want:
            print(f"REFUSED: {Path(rel).name}: {why} — {token!r} x{got}, expected {want}")
            return 1

        print(f"  checked   {Path(rel).name:34s} x{got}  {token[:38]!r}")

    def over(source: str) -> set[str]:
        return {
            line
            for line in source.split("\n")
            if len(line) > 120 and not line.lstrip().startswith("import ")
        }

    for path, text in planned.items():
        if over(text) - over(originals[path]):
            print(f"REFUSED: {path.name} would gain lines over 120 chars")
            return 1

    for path, text in planned.items():
        path.write_text(text, encoding="utf-8")

    print(f"\n  ok  wrote {len(planned)} file(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
