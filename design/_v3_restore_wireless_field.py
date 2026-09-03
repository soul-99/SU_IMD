#!/usr/bin/env python3
"""
v3 — proto field 65, `restoreWirelessDebugging`, plumbed end to end.

The author's rule: by default IMD hides wireless debugging and never puts it back, because a
device that comes out of a hide with wireless debugging on is a device listening on the local
network. Restoring it is opt-in, and this field is the opt-in.

**Off for everybody, and no migration.** A fresh install and an install arriving from any
earlier version both get false — proto3 decodes an unwritten bool to false, so the absence of
the field *is* the default and nothing has to be written to make it so. The author was asked
directly about the update case and chose the same answer for both: someone whose Revert to
default configuration currently ticks wireless debugging keeps that behaviour on the
Revert-to-default framework, because that path reads the configuration rather than this flag.
Only the **memory** framework's restore is gated here, and that path has never been
configurable before, so nothing that used to happen stops happening.

Two readers, both on the memory path:

  * RevertAppSettingsUseCase   — a per-app profile's restore
  * RevertToDefaultUseCase     — the device-wide memory restore, via `wantedOverride`

and one that is not a restore at all: the settings manager's `All on`, which follows this
field on the author's instruction so that the one button that turns everything on cannot be
the thing that quietly puts wireless debugging back.

Field 65. Highest in use was 64; reserved stays 9, 14, 46, 55.

⚠ `protoc` must be re-run after this or `check11_proto` reads a stale `/tmp/protogen` and
reports the new field as unreferenced. The line is in `toolkit/bootstrap.sh`.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PROTO = ("data/datastore-proto/src/main/proto/com/android/geto/data/datastore/proto/"
         "user_preferences.proto")
USER_DATA = "domain/model/src/main/kotlin/com/android/geto/domain/model/UserData.kt"
DATA_SOURCE = ("data/datastore/src/main/kotlin/com/android/geto/data/datastore/"
               "UserPreferencesDataSource.kt")
REPO_API = ("domain/repository/src/main/kotlin/com/android/geto/domain/repository/"
            "UserDataRepository.kt")
REPO_IMPL = ("data/repository/src/main/kotlin/com/android/geto/data/repository/"
             "DefaultUserDataRepository.kt")
HOST_TESTS = "tools/host-tests/DomainLogicTests.kt"

EDITS: list[tuple[str, list[tuple[str, str, int]]]] = [
    (PROTO, [
        (
            """  bool frameworksMigratedV3 = 64;
""",
            """  bool frameworksMigratedV3 = 64;

  /*
   * Whether a memory restore is allowed to switch wireless debugging back on.
   *
   * False by default and left false for every install, new or upgrading, on the author's
   * instruction: a device that comes back from a hide with wireless debugging on is
   * listening on whatever network it is attached to, and the user cannot see that it is.
   *
   * ⚠ Read only on the **memory** unhiding path. Under Revert to default the destination
   * comes from revertDefaults (16), which has its own wireless debugging row and is
   * unaffected by this - so an install that already restores wireless debugging that way
   * keeps doing it.
   *
   * Also read by the settings manager's All on button, which is not a restore: the one
   * control that switches everything on must not be a way around this.
   */
  bool restoreWirelessDebugging = 65;
""",
            1,
        ),
    ]),
    (USER_DATA, [
        (
            """    val revertDefaults: Map<ManualRevertTarget, Boolean>,
    val settingsToHide: Map<ManualRevertTarget, Boolean>,
""",
            """    val revertDefaults: Map<ManualRevertTarget, Boolean>,
    val settingsToHide: Map<ManualRevertTarget, Boolean>,
    /**
     * Whether a **memory** restore may switch wireless debugging back on.
     *
     * Off for everybody until it is ticked, and the one setting in this app that defaults to
     * doing less than it could: a hide that is undone into wireless debugging being on leaves
     * the device listening on the network with nothing on screen saying so.
     *
     * ⚠ **Not read under [UnhidingFramework.RevertToDefault].** That framework drives
     * [revertDefaults], which carries its own wireless debugging row, and gating it here as
     * well would give one question two answers. The checkbox is drawn only under
     * [UnhidingFramework.Memory] for exactly that reason.
     *
     * ⚠ **Read by the settings manager's `All on` under both frameworks**, on the author's
     * instruction. That button is not a restore — it is a person asking for everything to be
     * switched on — but it is also the one press that could put wireless debugging back
     * without going anywhere near this setting, which is why it asks.
     */
    val restoreWirelessDebugging: Boolean,
""",
            1,
        ),
    ]),
    (DATA_SOURCE, [
        (
            """            settingsToHide = SettingsToHide.decode(it.settingsToHideList),
""",
            """            settingsToHide = SettingsToHide.decode(it.settingsToHideList),
            restoreWirelessDebugging = it.restoreWirelessDebugging,
""",
            1,
        ),
        (
            """    suspend fun updateManageOverlay(enabled: Boolean) {""",
            """    suspend fun updateRestoreWirelessDebugging(enabled: Boolean) {
        userPreferences.updateData {
            it.copy {
                restoreWirelessDebugging = enabled
            }
        }
    }

    suspend fun updateManageOverlay(enabled: Boolean) {""",
            1,
        ),
    ]),
    (REPO_API, [
        (
            """    suspend fun updateManageOverlay(enabled: Boolean)""",
            """    /**
     * Whether a memory restore may switch wireless debugging back on. Off until ticked; see
     * [com.android.geto.domain.model.UserData.restoreWirelessDebugging].
     */
    suspend fun updateRestoreWirelessDebugging(enabled: Boolean)

    suspend fun updateManageOverlay(enabled: Boolean)""",
            1,
        ),
    ]),
    (REPO_IMPL, [
        (
            """    override suspend fun updateManageOverlay(enabled: Boolean) {""",
            """    override suspend fun updateRestoreWirelessDebugging(enabled: Boolean) {
        userPreferencesDataSource.updateRestoreWirelessDebugging(enabled = enabled)
    }

    override suspend fun updateManageOverlay(enabled: Boolean) {""",
            1,
        ),
    ]),
    (HOST_TESTS, [
        (
            """    setupNoticeVersion: Int = 0,
) = UserData(""",
            """    setupNoticeVersion: Int = 0,
    restoreWirelessDebugging: Boolean = false,
) = UserData(""",
            1,
        ),
        (
            """    settingsToHide = hideStates,
""",
            """    settingsToHide = hideStates,
    restoreWirelessDebugging = restoreWirelessDebugging,
""",
            1,
        ),
    ]),
]


def main() -> int:
    staged: dict[Path, str] = {}
    problems: list[str] = []

    for rel, subs in EDITS:
        path = ROOT / rel

        if not path.exists():
            problems.append(f"{rel}: missing")

            continue

        text = path.read_text(encoding="utf-8")

        for old, new, expected in subs:
            found = text.count(old)

            if found != expected:
                problems.append(
                    f"{rel}: expected {expected} of "
                    f"{old.strip().splitlines()[0][:58]!r}, found {found}",
                )

                continue

            text = text.replace(old, new, expected)

        staged[path] = text

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    # 65 must be free and must be the new highest. Read from the staged proto rather than
    # asserted against a remembered number, so a field added by a parallel edit cannot be
    # silently collided with.
    proto = staged[ROOT / PROTO]

    numbers = []

    for line in proto.splitlines():
        stripped = line.strip()

        if stripped.endswith(";") and " = " in stripped and not stripped.startswith("//"):
            tail = stripped.rsplit(" = ", 1)[1].rstrip(";")

            if tail.isdigit():
                numbers.append(int(tail))

    if numbers.count(65) != 1:
        problems.append(f"field 65 appears {numbers.count(65)} times, expected exactly 1")

    if max(numbers) != 65:
        problems.append(f"highest field is {max(numbers)}, expected 65")

    # Every added line under 120 characters, checked against the lines these edits introduce
    # rather than against the files - several of these carry pre-existing long lines.
    for path, text in staged.items():
        before = set(path.read_text(encoding="utf-8").splitlines())

        for line in text.splitlines():
            if line not in before and len(line) > 120:
                problems.append(
                    f"{path.relative_to(ROOT)}: added line of {len(line)} chars: "
                    f"{line.strip()[:58]!r}",
                )

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")
        print(f"  wrote {path.relative_to(ROOT)}")

    print(f"ok — restoreWirelessDebugging is field 65, {len(numbers)} fields in use")
    print("     re-run protoc before trusting check11_proto")

    return 0


if __name__ == "__main__":
    sys.exit(main())
