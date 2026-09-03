#!/usr/bin/env python3
"""r3 — the 'Manage Shizuku' preference, its migration, and the new 40 s Shevery wait.

The author's spec item 9: *"Add a new toggle in Shizuku configuration at top above everything
including description named 'Manage Shizuku' which is toggled off by default for new installs
and toggled on for anyone updating from lower versions. It can only be toggled on if all the
fields below are filled and gets automatically toggled off if any field below is blank(but
remembers the previous state in case a filed below is emptied and filled again)."*

This script is the storage half only — the field, the plumbing, the migration, the effective
test and the wait times. The section UI, the cascade and the dialogs are separate scripts.

### Two fields, and why the second one is needed

  66  manageShizuku            the user's stored answer
  67  manageShizukuMigratedV3  the one-shot marker

⚠ **"Remembers the previous state" is the *stored* field, and the switch shows the
*effective* one.** `manageShizukuEffective` is `manageShizuku && isShizukuConfigured`, so
emptying a field below drops the switch without touching the answer, and filling it again
puts the switch back exactly where the user left it. Storing the forced-off value instead
would be the app forgetting on the user's behalf.

⚠ **The migration reads `isShizukuConfigured`, not a new-install marker.** There is no
"is this an upgrade" bit in the store, and the two known ways to fake one are worse than the
question actually being asked: an install that already has a fork, a package name, a start
action and (for Thedjchi) an auth key is one that has been using Shizuku, which is precisely
who the author wants switched on. A fresh install has none of them and stays off. An upgrader
who never configured Shizuku also stays off — and would have been forced off anyway by the
rule above, so the two answers agree.

⚠ **The marker is written whether or not anything changed**, exactly as
`MigrateFrameworksUseCase` does: somebody who migrates and then deliberately switches it off
must not have that undone by the next launch.

### The wait times

Spec: *"Set new global wait times for Shevery to start to 40s and for shizuku(thedjchi) to
8s."* Thedjchi is already 8 s. Shevery was 13 s and becomes 40 s. `pollsFor` divides by the
500 ms poll, so 40 s is 80 polls with a resend every 4th — unchanged in shape.

Two doc comments in `StartShizukuUseCase` still said "ten seconds" from before the per-fork
budgets existed. Corrected here rather than left to mislead the next reader.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PROTO = ("data/datastore-proto/src/main/proto/com/android/geto/data/datastore/proto/"
         "user_preferences.proto")
USER_DATA = "domain/model/src/main/kotlin/com/android/geto/domain/model/UserData.kt"
FORK_MODE = "domain/model/src/main/kotlin/com/android/geto/domain/model/ShizukuForkMode.kt"
DATA_SOURCE = "data/datastore/src/main/kotlin/com/android/geto/data/datastore/UserPreferencesDataSource.kt"
REPO_IMPL = "data/repository/src/main/kotlin/com/android/geto/data/repository/DefaultUserDataRepository.kt"
REPO_IFACE = "domain/repository/src/main/kotlin/com/android/geto/domain/repository/UserDataRepository.kt"
APPLICATION = "app/src/main/kotlin/com/android/geto/GetoApplication.kt"
START = "domain/use-case/src/main/kotlin/com/android/geto/domain/usecase/StartShizukuUseCase.kt"
TRACKER = "domain/use-case/src/main/kotlin/com/android/geto/domain/usecase/ShizukuStartTracker.kt"
HOST_TESTS = "tools/host-tests/DomainLogicTests.kt"

MIGRATION = "domain/use-case/src/main/kotlin/com/android/geto/domain/usecase/MigrateManageShizukuUseCase.kt"

MIGRATION_SOURCE = '''/*
 *
 *   Copyright 2023 Einstein Blanco
 *   Modifications Copyright 2026 soul_99 (suIMD)
 *
 *   Licensed under the GNU General Public License v3.0 (the "License");
 *   you may not use this file except in compliance with the License.
 *   You may obtain a copy of the License at
 *
 *       https://www.gnu.org/licenses/gpl-3.0
 *
 *   Unless required by applicable law or agreed to in writing, software
 *   distributed under the License is distributed on an "AS IS" BASIS,
 *   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *   See the License for the specific language governing permissions and
 *   limitations under the License.
 *
 */
package com.android.geto.domain.usecase

import com.android.geto.domain.common.dispatcher.Dispatcher
import com.android.geto.domain.common.dispatcher.GetoDispatchers
import com.android.geto.domain.model.isShizukuConfigured
import com.android.geto.domain.repository.UserDataRepository
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withContext
import javax.inject.Inject

/**
 * Switches 'Manage Shizuku' on for an install that was already using Shizuku, once.
 *
 * The author's rule: off for new installs, on for anyone updating from a lower version. There
 * is no "is this an upgrade" bit in the store to read, so the question actually asked is
 * whether Shizuku is **configured** — a fork, a package name, a start action, and an auth key
 * where the fork needs one.
 *
 * ⚠ **That is not a workaround, it is the same question.** An install carrying a complete
 * Shizuku configuration is one that has been using Shizuku, which is exactly who the author
 * wants switched on. A fresh install has none of it. And an upgrader who never configured
 * Shizuku would have been forced off anyway by the rule that the switch cannot stand on with a
 * blank field below it, so both readings give the same answer for them.
 *
 * ⚠ **The marker is written whether or not anything changed**, like [MigrateFrameworksUseCase]
 * — somebody who migrates on and then deliberately switches it off must not have that undone
 * by the next launch. Once per install, not once per version.
 */
class MigrateManageShizukuUseCase @Inject constructor(
    private val userDataRepository: UserDataRepository,
    @param:Dispatcher(GetoDispatchers.Default) private val defaultDispatcher: CoroutineDispatcher,
) {
    suspend operator fun invoke() = withContext(defaultDispatcher) {
        val userData = userDataRepository.userData.first()

        if (userData.manageShizukuMigratedV3) return@withContext

        userDataRepository.updateManageShizukuMigratedV3(done = true)

        // Only ever switched on here. An install with nothing configured is left at the
        // proto3 default, which is the off this migration exists to leave alone.
        if (userData.isShizukuConfigured) {
            userDataRepository.updateManageShizuku(enabled = true)
        }
    }
}
'''

EDITS: list[tuple[str, list[tuple[str, str, int]]]] = [
    (PROTO, [
        (
            """  bool restoreWirelessDebugging = 65;
""",
            """  bool restoreWirelessDebugging = 65;

  /*
   * Whether IMD manages Shizuku at all — the master switch above everything in the Shizuku
   * configuration section.
   *
   * Off by default, which is what proto3 decodes an unwritten bool to, and therefore what a
   * new install gets. An install that was already using Shizuku is switched on once by
   * MigrateManageShizukuUseCase, guarded by the marker below.
   *
   * ⚠ This is the user's stored answer, not what the switch shows. The switch shows
   * manageShizuku && isShizukuConfigured, so emptying a field below drops it without
   * touching this — and filling the field again puts it back where the user left it. That
   * is the author's "remembers the previous state", and storing the forced-off value here
   * instead would be the app forgetting on their behalf.
   */
  bool manageShizuku = 66;

  /*
   * Marker for the one-shot migration above. Written whether or not anything changed, so a
   * deliberate switch-off afterwards is not undone by the next launch.
   */
  bool manageShizukuMigratedV3 = 67;
""",
            1,
        ),
    ]),
    (USER_DATA, [
        (
            """    val restoreWirelessDebugging: Boolean,
""",
            """    val restoreWirelessDebugging: Boolean,
    /**
     * Whether IMD manages Shizuku at all — the user's stored answer to the master switch.
     *
     * ⚠ **Not what the switch shows.** Read [manageShizukuEffective] for that: it is this
     * `&&` [isShizukuConfigured], so emptying a field in the Shizuku section drops the
     * switch without touching this answer, and filling it again puts the switch back where
     * the user left it. The author's "remembers the previous state", by construction.
     */
    val manageShizuku: Boolean,
    /** Whether the one-shot v3 migration for [manageShizuku] has already run. */
    val manageShizukuMigratedV3: Boolean,
""",
            1,
        ),
    ]),
    (FORK_MODE, [
        (
            """     * the server itself. That poll is on a ten-second cycle, so anything at or under ten
     * seconds can miss a whole revolution; thirteen leaves room for the cycle plus the
     * server's own start-up.
""",
            """     * the server itself. That poll is on a ten-second cycle, so anything at or under ten
     * seconds can miss a whole revolution.
     *
     * ⚠ **Forty seconds for Shevery, the author's number in v3**, up from thirteen. Thirteen
     * left room for one cycle plus the server's own start-up and nothing more, so a watchdog
     * that had just gone round when the transport came back was already outside the window.
""",
            1,
        ),
        (
            """     * [Unset] never waits, because nothing was ever asked.
     */
    val serviceWaitMillis: Long
        get() = when (this) {
            Unset -> 0L
            Thedjchi -> 8_000L
            Other -> 13_000L
        }
""",
            """     * [Unset] never waits, because nothing was ever asked.
     */
    val serviceWaitMillis: Long
        get() = when (this) {
            Unset -> 0L
            Thedjchi -> 8_000L
            Other -> 40_000L
        }
""",
            1,
        ),
    ]),
    (DATA_SOURCE, [
        (
            """            restoreWirelessDebugging = it.restoreWirelessDebugging,
""",
            """            restoreWirelessDebugging = it.restoreWirelessDebugging,
            manageShizuku = it.manageShizuku,
            manageShizukuMigratedV3 = it.manageShizukuMigratedV3,
""",
            1,
        ),
        (
            """    suspend fun updateManageOverlay(enabled: Boolean) {
""",
            """    suspend fun updateManageShizuku(enabled: Boolean) {
        userPreferences.updateData {
            it.copy {
                manageShizuku = enabled
            }
        }
    }

    suspend fun updateManageShizukuMigratedV3(done: Boolean) {
        userPreferences.updateData {
            it.copy {
                manageShizukuMigratedV3 = done
            }
        }
    }

    suspend fun updateManageOverlay(enabled: Boolean) {
""",
            1,
        ),
    ]),
    (REPO_IMPL, [
        (
            """    override suspend fun updateManageOverlay(enabled: Boolean) {
""",
            """    override suspend fun updateManageShizuku(enabled: Boolean) {
        userPreferencesDataSource.updateManageShizuku(enabled = enabled)
    }

    override suspend fun updateManageShizukuMigratedV3(done: Boolean) {
        userPreferencesDataSource.updateManageShizukuMigratedV3(done = done)
    }

    override suspend fun updateManageOverlay(enabled: Boolean) {
""",
            1,
        ),
    ]),
    (REPO_IFACE, [
        (
            """    suspend fun updateManageOverlay(enabled: Boolean)
""",
            """    /**
     * The user's stored answer to 'Manage Shizuku'. See
     * [com.android.geto.domain.model.UserData.manageShizuku] for why this is not what the
     * switch shows.
     */
    suspend fun updateManageShizuku(enabled: Boolean)

    /** Marks the one-shot 'Manage Shizuku' migration done. */
    suspend fun updateManageShizukuMigratedV3(done: Boolean)

    suspend fun updateManageOverlay(enabled: Boolean)
""",
            1,
        ),
    ]),
    (APPLICATION, [
        (
            """import com.android.geto.domain.usecase.MigrateFrameworksUseCase
""",
            """import com.android.geto.domain.usecase.MigrateFrameworksUseCase
import com.android.geto.domain.usecase.MigrateManageShizukuUseCase
""",
            1,
        ),
        (
            """    lateinit var migrateFrameworksUseCase: MigrateFrameworksUseCase
""",
            """    lateinit var migrateFrameworksUseCase: MigrateFrameworksUseCase

    @Inject
    lateinit var migrateManageShizukuUseCase: MigrateManageShizukuUseCase
""",
            1,
        ),
        (
            """        appScope.launch { migrateFrameworksUseCase() }
""",
            """        appScope.launch { migrateFrameworksUseCase() }

        // Independent of the frameworks migration above, so the order between them does not
        // matter: this one reads only the Shizuku configuration fields, which no migration
        // writes.
        appScope.launch { migrateManageShizukuUseCase() }
""",
            1,
        ),
    ]),
    (START, [
        (
            """    /**
     * Sends the start broadcast, then polls for up to ten seconds, resending the broadcast
     * every couple of seconds until Shizuku is running or the ten seconds are up.
     *
     * One send is not always enough: a fork whose app is closed can miss the first broadcast
     * while its process is still starting, and the old single-shot start then waited out the
     * full ten seconds for a service that would have come up on a second nudge. The window is
     * still exactly ten seconds from here - the resends happen inside it, not after it - so a
     * revert that cannot bring Shizuku up still gives up when it always did and raises its
     * notification then.
""",
            """    /**
     * Sends the start broadcast, then polls for the fork's whole budget, resending the
     * broadcast every couple of seconds until Shizuku is running or the budget is spent.
     *
     * ⚠ **The budget is per fork and lives in `ShizukuForkMode.serviceWaitMillis`** — 8 s for
     * Thedjchi, 40 s for Shevery, both the author's numbers in v3. This comment used to say
     * "ten seconds", which is a figure no build has used since the per-fork budgets arrived.
     *
     * One send is not always enough: a fork whose app is closed can miss the first broadcast
     * while its process is still starting, and the old single-shot start then waited out the
     * whole budget for a service that would have come up on a second nudge. The window is
     * unchanged - the resends happen inside it, not after it - so a revert that cannot bring
     * Shizuku up still gives up when it always did and raises its notification then.
""",
            1,
        ),
    ]),
    (TRACKER, [
        (
            """ * [StartShizuku] is the plain case and the one that was missing: a revert that puts the Shizuku
 * service back without touching overlay access spends the same ten seconds, and used to spend
 * them either in silence or - worse - under a spinner naming "Display over other apps", which
 * that revert is not touching at all.
""",
            """ * [StartShizuku] is the plain case and the one that was missing: a revert that puts the Shizuku
 * service back without touching overlay access spends the same wait as any other start, and
 * used to spend it either in silence or - worse - under a spinner naming "Display over other
 * apps", which that revert is not touching at all.
""",
            1,
        ),
    ]),
    (HOST_TESTS, [
        (
            """    restoreWirelessDebugging: Boolean = false,
) = UserData(""",
            """    restoreWirelessDebugging: Boolean = false,
    manageShizuku: Boolean = true,
) = UserData(""",
            1,
        ),
        (
            """    restoreWirelessDebugging = restoreWirelessDebugging,
""",
            """    restoreWirelessDebugging = restoreWirelessDebugging,
    manageShizuku = manageShizuku,
    manageShizukuMigratedV3 = true,
""",
            1,
        ),
    ]),
]

# `manageShizukuEffective` goes beside `isShizukuConfigured`, which asks the other half of the
# same question and is the only thing this reads.
EFFECTIVE = '''
/**
 * Whether IMD is managing Shizuku right now — the master switch as the UI must read it.
 *
 * [UserData.manageShizuku] is the user's stored answer; this is that answer **and** a Shizuku
 * configuration complete enough to act on. The author's rule is that the switch "gets
 * automatically toggled off if any field below is blank, but remembers the previous state in
 * case a field below is emptied and filled again" — which is this expression exactly, with
 * nothing written on the way through.
 *
 * ⚠ **Every gate in the app reads this, never the stored field.** A row that asked
 * [UserData.manageShizuku] alone would offer to drive a Shizuku IMD cannot reach.
 */
val UserData.manageShizukuEffective: Boolean
    get() = manageShizuku && isShizukuConfigured
'''


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

            if expected:
                text = text.replace(old, new, expected)

        staged[path] = text

    # The effective helper, appended to the file that already holds isShizukuConfigured.
    fork = staged.get(ROOT / FORK_MODE, "")

    if fork.count("val UserData.isShizukuConfigured: Boolean") != 1:
        problems.append(f"{FORK_MODE}: isShizukuConfigured is not where this belongs")
    else:
        staged[ROOT / FORK_MODE] = fork.rstrip("\n") + "\n" + EFFECTIVE

    if (ROOT / MIGRATION).exists():
        problems.append(f"{MIGRATION}: already exists")

    # 66 and 67 must be new, and the reserved list must not have grown to meet them.
    proto = staged.get(ROOT / PROTO, "")

    for field in ("= 66;", "= 67;"):
        if proto.count(field) != 1:
            problems.append(f"{PROTO}: expected exactly one {field}")

    if proto.count("reserved 9, 14, 46, 55;") != 1:
        problems.append(f"{PROTO}: the reserved list moved")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        before = set(path.read_text(encoding="utf-8").splitlines())

        for line in text.splitlines():
            if line not in before and len(line) > 120:
                problems.append(
                    f"{path.relative_to(ROOT)}: added line of {len(line)} chars: "
                    f"{line.strip()[:58]!r}",
                )

    for line in MIGRATION_SOURCE.splitlines():
        if len(line) > 120:
            problems.append(f"{MIGRATION}: line of {len(line)} chars")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")
        print(f"  wrote {path.relative_to(ROOT)}")

    (ROOT / MIGRATION).write_text(MIGRATION_SOURCE, encoding="utf-8")
    print(f"  created {MIGRATION}")

    print("ok - manageShizuku (66), its marker (67), the migration, and the 40 s Shevery wait")

    return 0


if __name__ == "__main__":
    sys.exit(main())
