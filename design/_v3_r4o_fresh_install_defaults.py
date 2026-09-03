#!/usr/bin/env python3
"""v3-r4o — a fresh install stops being migrated, and the developer's note learns what an
upgrade is.

Three of the author's reports are one defect:

    "where did my restore wireless debugging nested checkbox go?? it is not shown after fresh
     install i think because u set revert to def as def unhiding framework"
    "by default i told memory function is selected for new installs, please fix"
    "only show the note from developer to people who upgrade from previous version not fresh
     installs"

**His diagnosis of the first is exactly right**, and the second follows from it.

---

## The defect

The model already says what he wants — `UnhidingFramework.Default = Memory`,
`HidingFramework.Default = ImdDefaults` — and `MigrateFrameworksUseCase`'s own KDoc says so:

    A fresh install is not this use case's business. It has nothing stored to read … A new
    install gets HidingFramework.ImdDefaults with UnhidingFramework.Memory, at the author's
    instruction.

⚠ **The comment states the intent and the code does not implement it.** Nothing stops the
migration running on a fresh install. It reads `notificationFunction`, which for a field nobody
has written decodes to `NotificationFunction.Default` — **RevertToDefault** — and writes the
pair. So a fresh install lands on `UnhidingFramework.RevertToDefault`, overriding the default it
was supposed to keep, and the nested *Restore wireless debugging also* checkbox disappears
because it is drawn only under the memory function.

One guard fixes both reports.

## What tells a fresh install from an upgrade

`setupNoticeVersion == 0`. It is the app's only record that an install existed before today, and
it is what `MigrateRevertDefaultsUseCase` already uses for exactly this question.

⚠ **It is not perfect and the imprecision is inherited, not introduced**: an install that was
never carried through setup reads as fresh. That is the same answer the revert-defaults migration
has always given, and it errs the safe way — an install with nothing configured is treated as
having nothing to carry forward.

## The note's own gate

The developer's note was gated on `setupNoticeVersion != 0`, which means *"has finished setup"* —
so a **fresh** install that completed setup would see it on a later launch, which is precisely
what the author objected to. It now reads a marker written once, at the only moment the app can
still tell the difference: proto field **69**, `upgradedToV3`, set by the migration above.

## ⚠ A separate flaw, found while checking his question about upgrade defaults

`GetoApplication` launched the v1.6 notification-function reset and the frameworks migration as
**two separate `appScope.launch` blocks**, and the second's comment reads *"After the one above,
and that order is the whole of it"*. Two launches do not order anything. It only bites an install
arriving from **below v1.6** — anyone on 2.4 already carries `notificationFunctionResetV16`, so
the reset returns early and the pairing reads their real mechanism — but for a pre-v1.6 install on
the memory function the result depended on which coroutine won. They are now one block, in order,
which is what the comment always claimed.

The pairing itself is untouched and is exactly the author's specification:
revert-to-default → `ImdDefaults` + `RevertToDefault`; memory function → `PerApp` + `Memory`.

⚠ **Re-run protoc after this** or `check11_proto` reads a stale `/tmp/protogen`.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PROTO = "data/datastore-proto/src/main/proto/com/android/geto/data/datastore/proto/user_preferences.proto"
SOURCE = "data/datastore/src/main/kotlin/com/android/geto/data/datastore/UserPreferencesDataSource.kt"
USERDATA = "domain/model/src/main/kotlin/com/android/geto/domain/model/UserData.kt"
REPO_API = "domain/repository/src/main/kotlin/com/android/geto/domain/repository/UserDataRepository.kt"
REPO_IMPL = "data/repository/src/main/kotlin/com/android/geto/data/repository/DefaultUserDataRepository.kt"
MIGRATION = "domain/use-case/src/main/kotlin/com/android/geto/domain/usecase/MigrateFrameworksUseCase.kt"
APP = "app/src/main/kotlin/com/android/geto/GetoApplication.kt"
ACTIVITY = "app/src/main/kotlin/com/android/geto/activity/main/MainActivity.kt"
NOTE = "broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/DeveloperNoteNotification.kt"
TESTS = "tools/host-tests/DomainLogicTests.kt"

EDITS: list[tuple[str, str, str, str]] = []


def edit(rel: str, name: str, old: str, new: str) -> None:
    EDITS.append((rel, name, old, new))


edit(
    PROTO,
    "field 69",
    """  bool autoUnhideResetV3 = 68;""",
    """  bool autoUnhideResetV3 = 68;

  /*
   * Whether this install existed before v3.
   *
   * Written once by MigrateFrameworksUseCase, which is the last moment the app can still tell:
   * it reads setupNoticeVersion, and after setup has been completed once a fresh install and an
   * upgrade look identical.
   *
   * ⚠ Not "has finished setup", which is what the developer's note used to ask. That is true of
   * a fresh install too, one launch later.
   */
  bool upgradedToV3 = 69;""",
)

edit(
    SOURCE,
    "the mapping",
    """            autoUnhideResetV3 = it.autoUnhideResetV3,""",
    """            autoUnhideResetV3 = it.autoUnhideResetV3,
            upgradedToV3 = it.upgradedToV3,""",
)

edit(
    SOURCE,
    "the writer",
    """    suspend fun updateAutoUnhideResetV3(done: Boolean) {
        userPreferences.updateData {
            it.copy {
                autoUnhideResetV3 = done
            }
        }
    }""",
    """    suspend fun updateAutoUnhideResetV3(done: Boolean) {
        userPreferences.updateData {
            it.copy {
                autoUnhideResetV3 = done
            }
        }
    }

    suspend fun updateUpgradedToV3(upgraded: Boolean) {
        userPreferences.updateData {
            it.copy {
                upgradedToV3 = upgraded
            }
        }
    }""",
)

edit(
    USERDATA,
    "the field",
    """    /** Whether the one-shot v3 reset of auto unhide's triggers and conditions has run. */
    val autoUnhideResetV3: Boolean,""",
    """    /** Whether the one-shot v3 reset of auto unhide's triggers and conditions has run. */
    val autoUnhideResetV3: Boolean,
    /**
     * Whether this install existed before v3.
     *
     * ⚠ **Not the same question as [setupNoticeVersion] being non-zero**, which is only "setup
     * has been completed once" — true of a fresh install a launch later. Decided once, by
     * `MigrateFrameworksUseCase`, at the last moment the two can still be told apart.
     */
    val upgradedToV3: Boolean,""",
)

edit(
    REPO_API,
    "the repository method",
    """    suspend fun updateAutoUnhideResetV3(done: Boolean)""",
    """    suspend fun updateAutoUnhideResetV3(done: Boolean)

    suspend fun updateUpgradedToV3(upgraded: Boolean)""",
)

edit(
    REPO_IMPL,
    "the repository implementation",
    """    override suspend fun updateAutoUnhideResetV3(done: Boolean) {
        userPreferencesDataSource.updateAutoUnhideResetV3(done = done)
    }""",
    """    override suspend fun updateAutoUnhideResetV3(done: Boolean) {
        userPreferencesDataSource.updateAutoUnhideResetV3(done = done)
    }

    override suspend fun updateUpgradedToV3(upgraded: Boolean) {
        userPreferencesDataSource.updateUpgradedToV3(upgraded = upgraded)
    }""",
)

edit(
    MIGRATION,
    "the fresh-install guard",
    """        if (userData.frameworksMigratedV3) return@withContext

        userDataRepository.updateFrameworksMigratedV3(done = true)

        // Read once, up front. The two writes below land separately and a reader could
        // otherwise see the old value for one half and the new for the other.
        val stored = userData.notificationFunction""",
    """        if (userData.frameworksMigratedV3) return@withContext

        userDataRepository.updateFrameworksMigratedV3(done = true)

        // ⚠ **The guard the KDoc above always described and the code never had.** Without it
        // this ran on a fresh install too, read a `notificationFunction` nobody had written -
        // which decodes to NotificationFunction.Default, RevertToDefault - and wrote the pair,
        // overriding UnhidingFramework.Default. A new install therefore landed on Revert to
        // default rather than the memory function, and the nested "Restore wireless debugging
        // also" checkbox, drawn only under the memory function, was never shown at all.
        //
        // setupNoticeVersion is the app's only record that an install existed before today, and
        // is what MigrateRevertDefaultsUseCase already asks for the same reason. Its
        // imprecision is inherited rather than introduced: an install never carried through
        // setup reads as fresh, which errs the safe way - nothing configured, nothing to
        // carry forward.
        val upgraded = userData.setupNoticeVersion != 0

        // Recorded because this is the last moment the two can be told apart: once setup has
        // been completed, a fresh install and an upgrade look identical. The developer's note
        // reads it.
        userDataRepository.updateUpgradedToV3(upgraded = upgraded)

        if (!upgraded) return@withContext

        // Read once, up front. The two writes below land separately and a reader could
        // otherwise see the old value for one half and the new for the other.
        val stored = userData.notificationFunction""",
)

edit(
    APP,
    "the migration ordering",
    """        appScope.launch { migrateNotificationFunctionUseCase() }

        // After the one above, and that order is the whole of it: v3 reads whatever the
        // old mechanism finally settled on, so the v1.6 reset has to have run first or an
        // install arriving from below v1.6 would be split on a value about to change.
        appScope.launch { migrateFrameworksUseCase() }""",
    """        // ⚠ **One block, in order, and it used to be two launches.** The comment below has
        // always said the order is the whole of it, and two `appScope.launch` calls do not
        // order anything. It bites only an install arriving from below v1.6 - anyone above it
        // already carries the reset's marker, so it returns early and the pairing reads their
        // real mechanism - but there the result depended on which coroutine won.
        appScope.launch {
            migrateNotificationFunctionUseCase()

            // v3 reads whatever the old mechanism finally settled on, so the v1.6 reset has to
            // have run first or an install arriving from below v1.6 would be split on a value
            // about to change.
            migrateFrameworksUseCase()
        }""",
)

edit(
    ACTIVITY,
    "the note's gate",
    """                                    } else if (uiState.userData.setupNoticeVersion != 0 &&
                                        uiState.userData.settingsNoticeRevision <
                                        SETTINGS_NOTICE_REVISION
                                    ) {""",
    """                                    } else if (uiState.userData.upgradedToV3 &&
                                        uiState.userData.settingsNoticeRevision <
                                        SETTINGS_NOTICE_REVISION
                                    ) {""",
)

edit(
    NOTE,
    "the notification's gate",
    """        // A fresh install has no previous settings to have had matched, so there is nothing to
        // tell it. Same guard the dialog itself uses.
        if (userData.setupNoticeVersion == 0) return""",
    """        // ⚠ **A fresh install has no previous settings to have had matched.** This used to ask
        // `setupNoticeVersion == 0`, which is "setup has never been completed" - true of a
        // fresh install for one launch and false for ever after, so a new user met the note the
        // second time they opened the app. `upgradedToV3` is decided once, by
        // MigrateFrameworksUseCase, while the two can still be told apart.
        if (!userData.upgradedToV3) return""",
)

edit(
    TESTS,
    "the fixture",
    """    autoUnhideResetV3 = true,""",
    """    autoUnhideResetV3 = true,
    // r4o: fixtures are upgrades, so anything gated on "existed before v3" is reachable.
    upgradedToV3 = true,""",
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

    # ⚠ **Field 69 must be free and the reserved list untouched.**
    proto = staged[ROOT / PROTO]

    if proto.count("= 69;") != 1:
        print(f"REFUSED: {PROTO} uses field 69 {proto.count('= 69;')} time(s)")
        return 1

    if "reserved 9, 14, 46, 55;" not in proto:
        print(f"REFUSED: {PROTO} lost its reserved list")
        return 1

    for higher in range(70, 82):
        if f"= {higher};" in proto:
            print(f"REFUSED: {PROTO} already uses field {higher}")
            return 1

    # ⚠ **Position, not presence.** The marker has to be written before the early return, or a
    # fresh install would leave it unwritten and be asked again next launch — and the pairing
    # has to sit after the return, or the guard does nothing.
    migration = staged[ROOT / MIGRATION]

    marker = migration.index("updateUpgradedToV3(upgraded = upgraded)")
    guard = migration.index("if (!upgraded) return@withContext")
    pairing = migration.index("hidingFrameworkFor(notificationFunction = stored)")

    if not marker < guard < pairing:
        print("REFUSED: the marker, the guard and the pairing are out of order")
        return 1

    # And the pairing itself must be untouched — it is the author's specification.
    for kept in (
        "hidingFrameworkFor(notificationFunction = stored)",
        "unhidingFrameworkFor(notificationFunction = stored)",
    ):
        if kept not in migration:
            print(f"REFUSED: {MIGRATION} lost {kept!r}")
            return 1

    # ⚠ **The two migrations must now be in one block.** Spelled as the calls they are, because
    # the replacement comment names both in prose.
    app = staged[ROOT / APP]

    if "appScope.launch { migrateFrameworksUseCase() }" in app:
        print(f"REFUSED: {APP} still launches the frameworks migration on its own")
        return 1

    reset = app.index("migrateNotificationFunctionUseCase()")
    frameworks = app.index("migrateFrameworksUseCase()")

    block_start = app.rindex("appScope.launch {", 0, reset)
    block_end = app.index("}", frameworks)

    if not block_start < reset < frameworks < block_end:
        print("REFUSED: the two migrations are not in one ordered block")
        return 1

    # ⚠ **Neither gate may still ask the old question.** Spelled as the comparisons they were.
    for rel, gone in (
        (ACTIVITY, "userData.setupNoticeVersion != 0 &&"),
        (NOTE, "userData.setupNoticeVersion == 0) return"),
    ):
        if gone in staged[ROOT / rel]:
            print(f"REFUSED: {rel} still gates on setupNoticeVersion")
            return 1

    # `setupNoticeVersion` is still used elsewhere in MainActivity for the setup screen itself,
    # which is a different question and must be left alone.
    if "val setupEverCompleted = uiState.userData.setupNoticeVersion != 0" not in staged[ROOT / ACTIVITY]:
        print(f"REFUSED: {ACTIVITY} lost the setup screen's own use of setupNoticeVersion")
        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")

    print(f"  ok        {PROTO}  :: field 69, upgradedToV3")
    print(f"  ok        {SOURCE} / {USERDATA} / {REPO_API} / {REPO_IMPL}")
    print(f"  ok        {MIGRATION}  :: a fresh install keeps the model defaults")
    print(f"  ok        {APP}  :: the two migrations are ordered")
    print(f"  ok        {ACTIVITY} / {NOTE}  :: the note is for upgrades only")
    print(f"  ok        {TESTS}  :: fixture")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
