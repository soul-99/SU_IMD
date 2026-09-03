#!/usr/bin/env python3
"""v3-r4n — the auto-unhide tile condition and screen-lock trigger are coupled, and everything
is unticked once for everyone.

The v3 spec bullet, never built until now:

    "make screen lock trigger is enabled by default(if requirements are fulfilled) and make it
     so that when hide settings quick settings toggle condition is checked screen lock trigger
     is automatically checked(if requirements are unfulfilled display a popup asking for [that
     pending permission] be granted ...) and when screen lock trigger is unchecked it
     automatically unchecks qs toggle checkbox. All this because only screen lock trigger is
     used by that QS condition, ask me if i am wrong anywhere."

He is not wrong: `AutoUnhideWatcher.tick()` reads `settings.onTile` only for a session with no
watched app, and the screen-lock backup is the only trigger that can end one.

## What he changed when asked

* **No permission popup.** *"no extra permission is needed for screen lock so no need for popup"*
  — and the code already agrees: `AutoUnhide.kt` says *"Screen lock needs no permission of any
  kind."* `DUMP` belongs to the swipe trigger and usage access to the idle one.
* **No default-on, and no new "was it configured" field.** Instead: *"do one thing for everyone
  untick all triggers and all conditions"*. Field 55 was `autoUnhideTriggersConfigured` and is
  already **reserved** — it was retired when the triggers started arriving unticked, so bringing
  it back to make one of them arrive ticked would have undone that on purpose.
* **Nothing to auto-disable.** He spotted this and he is right: `autoUnhideSwitchOn` is
  `autoUnhideEnabled && requirements.satisfied`, so with no trigger left the switch reads off by
  itself. There is no stored flag to clear and no third rule.

## The invariant

One rule, stated from both sides, so each is a one-liner that cannot disagree with the other:

    the tile condition requires the screen-lock trigger

Ticking the tile ticks screen lock; unticking screen lock unticks the tile. The other two
directions leave the neighbour alone, which is why this is two functions and not one.

## ⚠ The gap the reset opens, and the term that closes it

`satisfied` required *a trigger* and never *a condition*. That was invisible while both
conditions arrived on — after the reset they arrive off, so ticking screen lock alone would turn
the switch on with no route: the watcher reads the conditions, finds neither allowed, and settles
immediately. Auto unhide would read on and never act, which is the exact state the file already
refuses one line above for triggers. Put to the author, who chose to close it: `anyUsedFor` joins
`anyTrigger`.

## ⚠ Proto field 68

The reset needs a marker or it re-clears the user's choices on every launch. It is the fifth of
a family the codebase already has — `notificationFunctionResetV16`, `revertDefaultsResetV166`,
`settingsToHideDefaultsV21`, `manageShizukuMigratedV3` — and follows their rule exactly: written
first and whether or not anything changed, so a deliberate re-tick afterwards is never undone.

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
MODEL = "domain/model/src/main/kotlin/com/android/geto/domain/model/AutoUnhide.kt"
VM = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsViewModel.kt"
SCREEN = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"
APP = "app/src/main/kotlin/com/android/geto/GetoApplication.kt"
MIGRATION = "domain/use-case/src/main/kotlin/com/android/geto/domain/usecase/MigrateAutoUnhideUseCase.kt"
TESTS = "tools/host-tests/DomainLogicTests.kt"

NEW_MIGRATION = '''/*
 *
 *   Copyright 2026 soul_99 (suIMD)
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
import com.android.geto.domain.repository.UserDataRepository
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withContext
import javax.inject.Inject

/**
 * The one-shot v3 reset of auto unhide: every trigger and both conditions unticked, once.
 *
 * The author's instruction, when asked whether the screen-lock trigger should arrive ticked and
 * what that would cost: *"do one thing for everyone untick all triggers and all conditions"*.
 *
 * v3 couples the tile condition to the screen-lock trigger, and an install arriving from below
 * carries whatever combination it was left on — including the two conditions, which used to
 * arrive **on** by default and are the half most people never opened. Starting everyone from
 * nothing is one state rather than a matrix of inherited ones, and it is what the developer
 * note this version shows asks people to go and look at.
 *
 * ⚠ **Auto unhide switches itself off as a consequence, and nothing here does that.**
 * `autoUnhideSwitchOn` is `autoUnhideEnabled && requirements.satisfied`, and `satisfied` needs
 * a trigger and a condition — so with neither there is nothing to write. The stored answer is
 * left exactly as the user set it, which is what lets ticking one trigger bring the feature
 * back without asking them to find the master switch again.
 *
 * ⚠ **The marker is written first, and whether or not anything changed** — the rule every other
 * one-shot in this app follows. A process that dies part way through must not reset a second
 * time, and somebody who re-ticks a trigger afterwards must not have it undone by the next
 * launch. Once per install, not once per version.
 */
class MigrateAutoUnhideUseCase @Inject constructor(
    private val userDataRepository: UserDataRepository,
    @param:Dispatcher(GetoDispatchers.Default) private val defaultDispatcher: CoroutineDispatcher,
) {
    suspend operator fun invoke() = withContext(defaultDispatcher) {
        val userData = userDataRepository.userData.first()

        if (userData.autoUnhideResetV3) return@withContext

        userDataRepository.updateAutoUnhideResetV3(done = true)

        userDataRepository.updateAutoUnhideTriggers(
            onSwipe = false,
            onScreenLock = false,
            onIdle = false,
        )

        // ⚠ **Written through the repository, not through the ViewModel.** The page refuses to
        // clear the last condition — a rule about what a user may do to a working
        // configuration, which is exactly right there and exactly wrong here.
        userDataRepository.updateAutoUnhideUsedFor(onAppLaunch = false, onTile = false)
    }
}
'''

EDITS: list[tuple[str, str, str, str]] = []


def edit(rel: str, name: str, old: str, new: str) -> None:
    EDITS.append((rel, name, old, new))


# ---------------------------------------------------------------------------------------
# 1 — the stored marker, all the way through
# ---------------------------------------------------------------------------------------
edit(
    PROTO,
    "field 68",
    """  bool manageShizukuMigratedV3 = 67;""",
    """  bool manageShizukuMigratedV3 = 67;

  /*
   * Marker for the one-shot v3 reset of auto unhide's three triggers and two conditions.
   *
   * Written whether or not anything changed, like every other one-shot here, so somebody who
   * re-ticks a trigger afterwards is not reset again by the next launch. Once per install.
   *
   * ⚠ Not a "were these ever configured" flag. 55 was exactly that for the triggers and is
   * reserved below; the triggers arrive unticked and this only says the reset has run.
   */
  bool autoUnhideResetV3 = 68;""",
)

edit(
    SOURCE,
    "the mapping",
    """            manageShizukuMigratedV3 = it.manageShizukuMigratedV3,""",
    """            manageShizukuMigratedV3 = it.manageShizukuMigratedV3,
            autoUnhideResetV3 = it.autoUnhideResetV3,""",
)

edit(
    SOURCE,
    "the writer",
    """    suspend fun updateManageShizukuMigratedV3(done: Boolean) {
        userPreferences.updateData {
            it.copy {
                manageShizukuMigratedV3 = done
            }
        }
    }""",
    """    suspend fun updateManageShizukuMigratedV3(done: Boolean) {
        userPreferences.updateData {
            it.copy {
                manageShizukuMigratedV3 = done
            }
        }
    }

    suspend fun updateAutoUnhideResetV3(done: Boolean) {
        userPreferences.updateData {
            it.copy {
                autoUnhideResetV3 = done
            }
        }
    }""",
)

edit(
    USERDATA,
    "the field",
    """    val manageShizukuMigratedV3: Boolean,""",
    """    val manageShizukuMigratedV3: Boolean,
    /** Whether the one-shot v3 reset of auto unhide's triggers and conditions has run. */
    val autoUnhideResetV3: Boolean,""",
)

edit(
    REPO_API,
    "the repository method",
    """    suspend fun updateManageShizukuMigratedV3(done: Boolean)""",
    """    suspend fun updateManageShizukuMigratedV3(done: Boolean)

    suspend fun updateAutoUnhideResetV3(done: Boolean)""",
)

edit(
    REPO_IMPL,
    "the repository implementation",
    """    override suspend fun updateManageShizukuMigratedV3(done: Boolean) {
        userPreferencesDataSource.updateManageShizukuMigratedV3(done = done)
    }""",
    """    override suspend fun updateManageShizukuMigratedV3(done: Boolean) {
        userPreferencesDataSource.updateManageShizukuMigratedV3(done = done)
    }

    override suspend fun updateAutoUnhideResetV3(done: Boolean) {
        userPreferencesDataSource.updateAutoUnhideResetV3(done = done)
    }""",
)

# ---------------------------------------------------------------------------------------
# 2 — the invariant, and the term the reset makes necessary
# ---------------------------------------------------------------------------------------
edit(
    MODEL,
    "the used-for fields",
    """    /** "Swipe away from recents" — the user's choice, not the system's. */
    val onSwipe: Boolean = false,""",
    """    /**
     * "Hide from IMD, a shortcut or IMD+" — one of the two conditions a session is watched
     * under.
     *
     * Carried here since r4n because [satisfied] has to ask about it. See [anyUsedFor].
     */
    val onAppLaunch: Boolean = false,
    /** "Hide settings quick settings toggle" — the other condition. */
    val onTile: Boolean = false,
    /** "Swipe away from recents" — the user's choice, not the system's. */
    val onSwipe: Boolean = false,""",
)

edit(
    MODEL,
    "anyTrigger and the new anyUsedFor",
    """    val anyTrigger: Boolean get() = swipeChosen || onScreenLock || onIdle""",
    """    val anyTrigger: Boolean get() = swipeChosen || onScreenLock || onIdle

    /**
     * Whether any kind of hide is watched at all.
     *
     * ⚠ **The same rule as [anyTrigger], from the other end, and it had to be written down when
     * the v3 reset unticked both conditions.** While they arrived on this could not be false,
     * so nothing asked. Now it can: a user who ticks a trigger and no condition would have the
     * switch reading on while `AutoUnhideWatcher.tick()` finds neither condition allowed and
     * settles immediately — a feature switched on that can never act, which is what the
     * paragraph on [anyTrigger] refuses.
     */
    val anyUsedFor: Boolean get() = onAppLaunch || onTile""",
)

edit(
    MODEL,
    "satisfied",
    """    /** Whether auto unhide may be switched on right now. */
    val satisfied: Boolean
        get() = anyTrigger &&
            dumpSatisfied &&""",
    """    /** Whether auto unhide may be switched on right now. */
    val satisfied: Boolean
        get() = anyTrigger &&
            anyUsedFor &&
            dumpSatisfied &&""",
)

edit(
    MODEL,
    "the coupling",
    """fun autoUnhideSwitchOn(""",
    """/**
 * The tile condition after the screen-lock trigger has been set to [onScreenLock].
 *
 * ⚠ **One invariant, written from both ends** — see [screenLockAfterTile] for the other. The
 * author's rule: *"only screen lock trigger is used by that QS condition"*. A session started
 * by the Hide settings tile names no app, and `AutoUnhideWatcher.tick()` has nothing to watch
 * leaving the foreground — so the screen-lock backup is the only thing that can ever end one,
 * and a tile condition without it is a promise the watcher cannot keep.
 *
 * Two functions rather than one, because which side gives way depends on which the user just
 * touched: unticking screen lock takes the tile with it, and unticking the tile leaves screen
 * lock alone.
 */
fun tileAfterScreenLock(onTile: Boolean, onScreenLock: Boolean): Boolean = onTile && onScreenLock

/**
 * The screen-lock trigger after the tile condition has been set to [onTile].
 *
 * The same invariant as [tileAfterScreenLock], from the other side: ticking the tile ticks
 * screen lock, and ticking screen lock leaves the tile alone.
 */
fun screenLockAfterTile(onScreenLock: Boolean, onTile: Boolean): Boolean = onScreenLock || onTile

fun autoUnhideSwitchOn(""",
)

edit(
    SCREEN,
    "the requirements construction",
    """        onSwipe = userData.autoUnhideOnSwipe,
        onScreenLock = userData.autoUnhideOnScreenLock,
        onIdle = userData.autoUnhideOnIdle,
    )""",
    """        // r4n: the two conditions are part of the question now - see anyUsedFor.
        onAppLaunch = userData.autoUnhideOnAppLaunch,
        onTile = userData.autoUnhideOnTile,
        onSwipe = userData.autoUnhideOnSwipe,
        onScreenLock = userData.autoUnhideOnScreenLock,
        onIdle = userData.autoUnhideOnIdle,
    )""",
)

# ---------------------------------------------------------------------------------------
# 3 — the two writes that carry the coupling
# ---------------------------------------------------------------------------------------
edit(
    VM,
    "the trigger write",
    """    fun updateAutoUnhideTriggers(onSwipe: Boolean, onScreenLock: Boolean, onIdle: Boolean) {
        viewModelScope.launch {
            userDataRepository.updateAutoUnhideTriggers(
                onSwipe = onSwipe,
                onScreenLock = onScreenLock,
                onIdle = onIdle,
            )
        }
    }""",
    """    /**
     * The three triggers, and the tile condition that depends on one of them.
     *
     * ⚠ **Unticking the screen-lock trigger unticks the Hide settings tile condition with it**
     * — [tileAfterScreenLock], the author's rule. Applied here rather than in the page so it
     * holds however the call arrives, which is the same reasoning
     * [updateAutoUnhideUsedFor] already uses for its own refusal.
     *
     * If that leaves neither condition ticked, nothing else happens and nothing else has to:
     * `autoUnhideSwitchOn` reads `satisfied`, which needs one of each, so the switch goes off
     * on its own and the user's stored answer is left where they put it.
     */
    fun updateAutoUnhideTriggers(onSwipe: Boolean, onScreenLock: Boolean, onIdle: Boolean) {
        viewModelScope.launch {
            val userData = userDataRepository.userData.first()

            userDataRepository.updateAutoUnhideTriggers(
                onSwipe = onSwipe,
                onScreenLock = onScreenLock,
                onIdle = onIdle,
            )

            val onTile = tileAfterScreenLock(
                onTile = userData.autoUnhideOnTile,
                onScreenLock = onScreenLock,
            )

            if (onTile != userData.autoUnhideOnTile) {
                userDataRepository.updateAutoUnhideUsedFor(
                    onAppLaunch = userData.autoUnhideOnAppLaunch,
                    onTile = onTile,
                )
            }
        }
    }""",
)

edit(
    VM,
    "the used-for write",
    """    fun updateAutoUnhideUsedFor(onAppLaunch: Boolean, onTile: Boolean): Boolean {
        if (!onAppLaunch && !onTile) return false

        viewModelScope.launch {
            userDataRepository.updateAutoUnhideUsedFor(
                onAppLaunch = onAppLaunch,
                onTile = onTile,
            )
        }

        return true
    }""",
    """    fun updateAutoUnhideUsedFor(onAppLaunch: Boolean, onTile: Boolean): Boolean {
        if (!onAppLaunch && !onTile) return false

        viewModelScope.launch {
            val userData = userDataRepository.userData.first()

            userDataRepository.updateAutoUnhideUsedFor(
                onAppLaunch = onAppLaunch,
                onTile = onTile,
            )

            // ⚠ **Ticking the tile condition ticks the screen-lock trigger** -
            // [screenLockAfterTile], the other half of the author's rule. Only ever on: he
            // asked for the tile to *check* it, and unticking the tile is not a statement
            // about a trigger the user may want for its own sake.
            val onScreenLock = screenLockAfterTile(
                onScreenLock = userData.autoUnhideOnScreenLock,
                onTile = onTile,
            )

            if (onScreenLock != userData.autoUnhideOnScreenLock) {
                userDataRepository.updateAutoUnhideTriggers(
                    onSwipe = userData.autoUnhideOnSwipe,
                    onScreenLock = onScreenLock,
                    onIdle = userData.autoUnhideOnIdle,
                )
            }
        }

        return true
    }""",
)

# ---------------------------------------------------------------------------------------
# 4 — the migration, wired where the other four are
# ---------------------------------------------------------------------------------------
edit(
    APP,
    "the migration import",
    """import com.android.geto.domain.usecase.MigrateManageShizukuUseCase""",
    """import com.android.geto.domain.usecase.MigrateAutoUnhideUseCase
import com.android.geto.domain.usecase.MigrateManageShizukuUseCase""",
)

edit(
    APP,
    "the migration field",
    """    lateinit var migrateManageShizukuUseCase: MigrateManageShizukuUseCase""",
    """    lateinit var migrateManageShizukuUseCase: MigrateManageShizukuUseCase

    @Inject
    lateinit var migrateAutoUnhideUseCase: MigrateAutoUnhideUseCase""",
)

edit(
    APP,
    "the migration call",
    """        appScope.launch { migrateManageShizukuUseCase() }""",
    """        appScope.launch { migrateManageShizukuUseCase() }

        // Independent of every other migration: it writes only auto unhide's own triggers and
        // conditions, which nothing else touches. Here rather than on the settings screen for
        // the same reason as the rest — the watcher can be started by a tile or a shortcut in
        // a process where no activity ever exists.
        appScope.launch { migrateAutoUnhideUseCase() }""",
)

# ---------------------------------------------------------------------------------------
# 5 — the host assertions
# ---------------------------------------------------------------------------------------
edit(
    TESTS,
    "the userData fixture",
    """    settingsNoticeRevision = 0,
""",
    """    settingsNoticeRevision = 0,
    // r4n: the one-shot auto-unhide reset has already run for every fixture, so the
    // triggers and conditions a test sets are the ones it gets.
    autoUnhideResetV3 = true,
""",
)

edit(
    TESTS,
    "the coupling assertions",
    """private fun taskerIntegrationTests() {""",
    """/**
 * r4n — the auto-unhide coupling, and the term the v3 reset made necessary.
 *
 * The invariant is the author's: the Hide settings tile condition can only be honoured by the
 * screen-lock trigger, because a session the tile starts names no app for the watcher to see
 * leaving the foreground.
 */
private fun autoUnhideCouplingTests() {
    // Ticking the tile ticks screen lock; ticking screen lock says nothing about the tile.
    check("the tile brings the screen lock trigger with it", screenLockAfterTile(
        onScreenLock = false,
        onTile = true,
    ))
    check("and leaves it alone when it is already on", screenLockAfterTile(
        onScreenLock = true,
        onTile = true,
    ))
    check("unticking the tile does not take the trigger with it", screenLockAfterTile(
        onScreenLock = true,
        onTile = false,
    ))
    check("and does not switch it on either", !screenLockAfterTile(
        onScreenLock = false,
        onTile = false,
    ))

    // Unticking screen lock unticks the tile; ticking it says nothing about the tile.
    check("losing the trigger loses the tile", !tileAfterScreenLock(
        onTile = true,
        onScreenLock = false,
    ))
    check("the tile survives a trigger that is still on", tileAfterScreenLock(
        onTile = true,
        onScreenLock = true,
    ))
    check("and a trigger coming on does not tick the tile", !tileAfterScreenLock(
        onTile = false,
        onScreenLock = true,
    ))

    // ⚠ **The pairing, which is the assertion worth having.** Whichever side moved, the state
    // the two functions leave behind must satisfy the invariant: no tile without screen lock.
    for (tile in listOf(false, true)) {
        for (lock in listOf(false, true)) {
            check(
                "after a screen-lock edit the invariant holds: tile=$tile lock=$lock",
                !tileAfterScreenLock(onTile = tile, onScreenLock = lock) || lock,
            )
            check(
                "after a tile edit the invariant holds: tile=$tile lock=$lock",
                !tile || screenLockAfterTile(onScreenLock = lock, onTile = tile),
            )
        }
    }

    // r4n: satisfied needs one of each. The reset unticks both conditions, so this is the
    // difference between the switch reading off and reading on while nothing can act.
    val ready = AutoUnhideRequirements(
        batteryUnrestricted = true,
        notificationsAllowed = true,
        onAppLaunch = true,
        onScreenLock = true,
    )

    check("a trigger and a condition satisfy it", ready.satisfied)
    check("no condition does not", !ready.copy(onAppLaunch = false).satisfied)
    check("no trigger does not either", !ready.copy(onScreenLock = false).satisfied)
    check(
        "the tile alone is a condition too",
        ready.copy(onAppLaunch = false, onTile = true).satisfied,
    )
}

private fun taskerIntegrationTests() {""",
)

edit(
    TESTS,
    "the test runner",
    """    stopActionTests()""",
    """    stopActionTests()
    autoUnhideCouplingTests()""",
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

    migration_path = ROOT / MIGRATION

    if migration_path.exists():
        print(f"REFUSED: {MIGRATION} already exists")
        return 1

    staged[migration_path] = NEW_MIGRATION

    # ⚠ **Field 68 must be free and must not collide with the reserved list.**
    proto = staged[ROOT / PROTO]

    for taken in ("= 68;",):
        if proto.count(taken) != 1:
            print(f"REFUSED: {PROTO} uses {taken} {proto.count(taken)} time(s)")
            return 1

    if "reserved 9, 14, 46, 55;" not in proto:
        print(f"REFUSED: {PROTO} lost its reserved list")
        return 1

    for higher in range(69, 80):
        if f"= {higher};" in proto:
            print(f"REFUSED: {PROTO} already uses field {higher}; 68 is not the highest")
            return 1

    # The tests need the two new functions imported.
    tests = staged[ROOT / TESTS]

    for symbol in ("screenLockAfterTile", "tileAfterScreenLock", "AutoUnhideRequirements"):
        needed = f"import com.android.geto.domain.model.{symbol}"

        if needed not in tests:
            # ⚠ **Anchored on an import this file really has.** The first draft anchored on
            # `autoUnhideSwitchOn`, which DomainLogicTests does not import — it tests the
            # auto-*hide* switch, not this one. `autoHideSwitchOn` is the neighbour that exists.
            tests = tests.replace(
                "import com.android.geto.domain.model.autoHideSwitchOn",
                f"{needed}\nimport com.android.geto.domain.model.autoHideSwitchOn",
                1,
            )

        if tests.count(needed) != 1:
            print(f"REFUSED: {TESTS} imports {symbol} {tests.count(needed)} time(s)")
            return 1

    staged[ROOT / TESTS] = tests

    # The ViewModel needs `first` for the snapshot it now takes.
    vm = staged[ROOT / VM]

    for symbol in (
        "import com.android.geto.domain.model.screenLockAfterTile",
        "import com.android.geto.domain.model.tileAfterScreenLock",
        "import kotlinx.coroutines.flow.first",
    ):
        if symbol not in vm:
            # `first` is already there; only the two model functions are added, and they go
            # beside the other domain.model imports rather than among the coroutines ones.
            anchor = (
                "import kotlinx.coroutines.launch"
                if symbol.startswith("import kotlinx")
                else "import com.android.geto.domain.repository.UserDataRepository"
            )

            vm = vm.replace(anchor, f"{symbol}\n{anchor}", 1)

        if vm.count(symbol) != 1:
            print(f"REFUSED: {VM} carries {symbol!r} {vm.count(symbol)} time(s)")
            return 1

    staged[ROOT / VM] = vm

    # ⚠ **Position, not presence.** The reset must write its marker before it clears anything,
    # or a process that dies between the two resets again on the next launch.
    migration = staged[migration_path]

    marker = migration.index("updateAutoUnhideResetV3(done = true)")
    triggers = migration.index("updateAutoUnhideTriggers(")
    used_for = migration.index("updateAutoUnhideUsedFor(")

    if not marker < triggers < used_for:
        print("REFUSED: the reset clears state before writing its marker")
        return 1

    # And `satisfied` must carry the new term beside the old one, in that order.
    model = staged[ROOT / MODEL]

    block = model[model.index("val satisfied: Boolean") : model.index("val anyTrigger", model.index("val satisfied: Boolean")) if "val anyTrigger" in model[model.index("val satisfied: Boolean"):] else len(model)]

    satisfied_block = model.split("val satisfied: Boolean", 1)[1].split("\n\n", 1)[0]

    if "anyTrigger &&" not in satisfied_block or "anyUsedFor &&" not in satisfied_block:
        print("REFUSED: satisfied does not carry both anyTrigger and anyUsedFor")
        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")

    print(f"  ok        {PROTO}  :: field 68")
    print(f"  ok        {SOURCE}  :: mapping + writer")
    print(f"  ok        {USERDATA} / {REPO_API} / {REPO_IMPL}")
    print(f"  ok        {MODEL}  :: the coupling, anyUsedFor, satisfied")
    print(f"  ok        {VM}  :: both writes carry the invariant")
    print(f"  ok        {MIGRATION}  :: new")
    print(f"  ok        {APP}  :: wired beside the other four")
    print(f"  ok        {TESTS}  :: autoUnhideCouplingTests")
    print("\n⚠ re-run protoc before check11_proto")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s) + 1 new file")

    return 0


if __name__ == "__main__":
    sys.exit(main())
