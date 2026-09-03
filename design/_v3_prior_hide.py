#!/usr/bin/env python3
"""
v3-r2b3 part 1 — the mechanism behind the force-close popup.

### The case

IMD is force-stopped, or the system reclaims it, while settings are still hidden. Force-stopping
an app takes its notifications with it, so the way back is gone and nothing on screen says the
device is still locked down. The next launch through IMD or IMD+ hides straight over the top and
says nothing.

### The trigger, on the author's variant A

**Settings are hidden AND this process never hid them.** A `@Volatile` set by any successful
hide; false while a debt exists means the debt predates this process, which can only mean the
last one died. No proto field, no migration, no background service — the author asked whether it
could be done without one, and this is the answer: it is read at launch time, in the process
that is already running because the user is launching something.

⚠ **Not "the revert notification is gone"**, the sharper variant that was offered. On Android 13+
with the notification permission denied that notification is *never* posted, so the condition
would be permanently true and the popup would fire on every launch — the exact failure the
trigger exists to avoid.

### The two buttons, as the author settled them

**'Ignore all previous reverts'** — discard every outstanding debt and carry on with the hide.
The current state becomes the new baseline. ⚠ **Permanent, and the label says so**: nothing will
put those settings back afterwards except `Revert to default`. The author confirmed this
explicitly rather than by silence.

**'Restore settings first'** — settle everything, and **only if it settles cleanly** carry on
with the hide. If Shizuku or Display over other apps could not be put back, the existing failure
notifications fire from `RevertToDefaultRunner` — unchanged, no second notification — and the
hide is abandoned.

### Success is observed, not plumbed

`flushPendingReverts` now answers whether the device is actually clear afterwards, which is both
the honest question and the one that needs no new return values threaded through
`AutoHideRunner`, `RevertAllMemoryUseCase` and two branches of `unhide`. It combines what the
revert *reported* with what the records *say*, because either alone can lie: a revert can report
success having cleared a debt it never fully wrote, and a debt can clear while Shizuku failed.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PRIOR_HIDE = "domain/common/src/main/kotlin/com/android/geto/domain/common/PriorHide.kt"

DISCARD = (
    "domain/use-case/src/main/kotlin/com/android/geto/domain/usecase/"
    "DiscardPendingRevertsUseCase.kt"
)

RESULT = "domain/model/src/main/kotlin/com/android/geto/domain/model/AppSettingsResult.kt"

APPLY_APP = (
    "domain/use-case/src/main/kotlin/com/android/geto/domain/usecase/ApplyAppSettingsUseCase.kt"
)

APPLY_HIDE = (
    "domain/use-case/src/main/kotlin/com/android/geto/domain/usecase/"
    "ApplySettingsToHideUseCase.kt"
)

HIDDEN_RUNNER = (
    "broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/"
    "SettingsHiddenRunner.kt"
)

STRINGS = "common/src/main/res/values/strings.xml"

PRIOR_HIDE_BODY = '''/*
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
package com.android.geto.domain.common

/**
 * Whether the settings that are down were hidden by a **previous** run of this app.
 *
 * Force-stopping an app takes its notifications with it, so a hide that outlives the process
 * that made it leaves a device locked down with nothing on screen offering the way back. The
 * next launch through IMD used to hide straight over the top and say nothing.
 *
 * ⚠ **One volatile, and no service.** The author asked whether this could be done without a
 * background service. It can, and this is the whole of it: a debt is persisted, [markHidden] is
 * not, so a debt standing with [markHidden] never called in this process means the process that
 * made it is gone. Read at launch time, in the process that is already running because the user
 * has just launched something.
 *
 * ⚠ **Deliberately not "the revert notification is no longer posted"**, which was the sharper
 * variant offered and refused: on Android 13+ with notifications denied that notification is
 * *never* posted, so the condition would be permanently true and the popup would fire on every
 * launch in ordinary use — the exact failure this trigger exists to avoid.
 *
 * **An object rather than an injected singleton**, for the reason [Diagnostics] is one: the
 * askers are spread across `domain`, `broadcast-receiver`, three feature modules and `app`, and
 * two of them are pure Kotlin use cases with no injector in reach.
 */
object PriorHide {

    @Volatile
    private var hidInThisProcess: Boolean = false

    @Volatile
    private var suppressed: Boolean = false

    /**
     * A hide ran here, so anything outstanding from now on is this process's own doing.
     *
     * Clears [suppressed] with it: a real hide supersedes any earlier "do not ask again", and
     * leaving it set would silence the warning after the *next* force close.
     */
    fun markHidden() {
        hidInThisProcess = true

        suppressed = false
    }

    /**
     * Do not ask again until something changes.
     *
     * Two callers, and they want the same thing for different reasons. **The prompt itself**
     * sets it while the dialog is on screen, because IMD+ draws over the app the user just
     * opened and that is itself a window change the detector would see — without this, a dialog
     * nobody has answered yet would put up another one behind it.
     *
     * **A failed restore** sets it too, and that is the author's rule: the notification is on
     * screen, the app stays open, and IMD+ does not run. Without it the gate would still be
     * true, so the next detection would prompt, fail and prompt again.
     *
     * **Headless callers** set it as well: Tasker has no window, and an automation that stopped
     * to ask a question would simply never run. The first-owner rule makes proceeding safe.
     */
    fun suppress() {
        suppressed = true
    }

    /**
     * Everything outstanding has been settled, by whatever route.
     *
     * ⚠ **The one reset, and it covers the case the author described in terms of notifications.**
     * He asked for the IMD+ suppression to lift when the user starts Shizuku by hand and taps
     * *Try again*, or clears the failure notification. Tapping *Try again* restores from the
     * debt, which clears it, which reaches here — so the behaviour he wanted falls out of the
     * condition that actually matters, with no notification-dismissal plumbing to keep in step.
     * Starting Shizuku without retrying leaves the debt standing, and IMD+ staying blocked is
     * then correct rather than a bug.
     */
    fun settled() {
        hidInThisProcess = false

        suppressed = false
    }

    /**
     * Whether a launch should stop and say the settings predate this run of IMD.
     *
     * [settingsHidden] is asked for rather than read, because this object deliberately holds no
     * dependencies — the callers all have `UserData` in hand at the moment they ask.
     */
    fun shouldWarn(settingsHidden: Boolean): Boolean =
        settingsHidden && !hidInThisProcess && !suppressed
}
'''

DISCARD_BODY = '''/*
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

import com.android.geto.domain.common.Diagnostics
import com.android.geto.domain.repository.UserDataRepository
import javax.inject.Inject

/**
 * Forget every outstanding revert, and take the device as it stands now.
 *
 * ⚠ **This writes nothing to the device and undoes nothing.** It is the *record* that is
 * discarded, not the hide: developer options that are off stay off, and afterwards nothing in
 * IMD knows they were ever on. The only way to a known state from here is `Revert to default`.
 *
 * ⚠ **Permanent, on the author's explicit confirmation.** It is what the popup's
 * `'Ignore all previous reverts'` button does, and the label was written to say so — an earlier
 * draft called it just `'Ignore'`, which read as "carry on" rather than "throw the record away".
 * Keeping a shadow copy to undo it later was considered and rejected: nothing in the UI could
 * reach such a copy, so it would be a second record that only ever disagreed with the first.
 *
 * **Five stores, and all five matter.** The per-app records and the device-wide record are the
 * memory function's debt; the accessibility and overlay holds are what IMD is holding down on
 * somebody's behalf; `autoHideRunning` is IMD+'s claim on the device. Leaving any of them would
 * leave `settingsHidden` reading true, which is the flag the popup's own trigger reads — so a
 * partial discard would show the popup again on the very next launch.
 */
class DiscardPendingRevertsUseCase @Inject constructor(
    private val userDataRepository: UserDataRepository,
) {
    suspend operator fun invoke() {
        Diagnostics.log(tag = "revert", message = "discarding every pending revert")

        userDataRepository.updateSettingStateBefore(states = emptyMap())

        userDataRepository.updateHeldAccessibilityServices(held = emptyMap())

        userDataRepository.updateHeldOverlayPackages(held = emptyMap(), identities = emptyMap())

        userDataRepository.updateSettingsHiddenDeviceWide(hidden = false)

        userDataRepository.updateAutoHideRunning(running = false)
    }
}
'''

RESULT_EDITS: list[tuple[str, str]] = [
    (
        """    NoPermission,
    InvalidValues,
    EmptyAppSettings,
    DisabledAppSettings,
}
""",
        """    NoPermission,
    InvalidValues,
    EmptyAppSettings,
    DisabledAppSettings,

    /**
     * Settings are still hidden from a run of IMD that is no longer alive.
     *
     * Nothing was written and nothing was launched: the hide stops before it touches anything,
     * so that the user can choose between putting the old state back and letting go of it. See
     * [com.android.geto.domain.common.PriorHide] for how "no longer alive" is known.
     *
     * ⚠ **Not a failure**, and it must not be treated as one. Every other value in this enum
     * that stops a launch describes something wrong with the configuration or the device; this
     * one describes a device that is working exactly as asked and a user who has not been told.
     */
    HiddenFromPreviousUse,
}
""",
    ),
]

APPLY_APP_EDITS: list[tuple[str, str]] = [
    (
        """import com.android.geto.domain.common.Diagnostics
""",
        """import com.android.geto.domain.common.Diagnostics
import com.android.geto.domain.common.PriorHide
""",
    ),
    (
        """            .also { Diagnostics.log(tag = "hide", message = "app $componentName -> $it") }
""",
        """            .also { Diagnostics.log(tag = "hide", message = "app $componentName -> $it") }
            // Only a hide that actually landed marks the process. A refused one leaves the
            // question open, which is right: nothing about the device changed.
            .also { if (it == AppSettingsResult.Success) PriorHide.markHidden() }
""",
    ),
]

APPLY_HIDE_EDITS: list[tuple[str, str]] = [
    (
        """    }.also { Diagnostics.log(tag = "hide", message = "device-wide -> $it") }
""",
        """    }.also { Diagnostics.log(tag = "hide", message = "device-wide -> $it") }
        // See ApplyAppSettingsUseCase: only a hide that landed marks the process.
        .also { if (it == AppSettingsResult.Success) PriorHide.markHidden() }
""",
    ),
    (
        """import com.android.geto.domain.common.Diagnostics
""",
        """import com.android.geto.domain.common.Diagnostics
import com.android.geto.domain.common.PriorHide
""",
    ),
]

HIDDEN_RUNNER_EDITS: list[tuple[str, str]] = [
    (
        """import com.android.geto.domain.usecase.RevertAllMemoryUseCase
""",
        """import com.android.geto.domain.common.PriorHide
import com.android.geto.domain.usecase.DiscardPendingRevertsUseCase
import com.android.geto.domain.usecase.RevertAllMemoryUseCase
""",
    ),
    (
        """    private val revertAllMemoryUseCase: RevertAllMemoryUseCase,
""",
        """    private val revertAllMemoryUseCase: RevertAllMemoryUseCase,
    private val discardPendingRevertsUseCase: DiscardPendingRevertsUseCase,
""",
    ),
    (
        """    suspend fun flushPendingReverts() = unhide(fallbackToDefault = false)
""",
        """    suspend fun flushPendingReverts(): Boolean = unhide(fallbackToDefault = false)

    /**
     * Forget every outstanding revert and take the device as it stands.
     *
     * What `'Ignore all previous reverts'` runs. The use case clears the five stored debts; the
     * two in-memory ones are cleared here, because they live in `:common` where a domain use
     * case cannot see them.
     *
     * ⚠ **[PriorHide.settled] last**, after the debt is genuinely gone: it is the flag the
     * popup's trigger reads, and clearing it while a record still stood would leave the next
     * launch warning about a debt this call was supposed to have ended.
     */
    suspend fun discardPendingReverts() {
        discardPendingRevertsUseCase()

        notificationManagerWrapper.cancelAll()

        AutoUnhideWatch.clear()

        AutoRevertPending.clear()

        PriorHide.settled()
    }

    /**
     * Whether nothing at all is outstanding right now.
     *
     * Read after a revert rather than returned by it, and that is the point: `'Restore settings
     * first'` has to know whether to go on and hide, and threading a result back through
     * `AutoHideRunner.revert`, `RevertAllMemoryUseCase` and both branches below would be four
     * new return types for a question the stored records already answer.
     */
    private suspend fun nothingOutstanding(): Boolean {
        val hidden = getSettingsHiddenUseCase()

        return !userDataRepository.userData.first().autoHideRunning &&
            !hidden.memory &&
            !hidden.deviceWide
    }
""",
    ),
    (
        """    private suspend fun unhide(fallbackToDefault: Boolean) {
""",
        """    /**
     * Returns whether the device is actually clear afterwards.
     *
     * ⚠ **Both signals, because either alone can lie.** A revert can report success having
     * cleared a debt it never fully wrote, and a debt can clear while Shizuku was left down. So
     * the answer is what the revert *reported* **and** what the records *say* — and only the
     * device-wide branch has a report to give, which is why the other two fall back to the
     * records alone.
     */
    private suspend fun unhide(fallbackToDefault: Boolean): Boolean {
""",
    ),
    (
        """            autoHideRunner.revert()

            return
        }
""",
        """            autoHideRunner.revert()

            return nothingOutstanding()
        }
""",
    ),
    (
        """            revertToDefaultRunner(fromMemory = fromMemory)
        }
    }
}
""",
        """            val result = revertToDefaultRunner(fromMemory = fromMemory)

            return !result.overlayRestoreFailed &&
                ManualRevertTarget.Shizuku !in result.failed &&
                nothingOutstanding()
        }

        return nothingOutstanding()
    }
}
""",
    ),
    (
        """import com.android.geto.domain.model.AppSettingsResult
""",
        """import com.android.geto.domain.model.AppSettingsResult
import com.android.geto.domain.model.ManualRevertTarget
""",
    ),
]

STRINGS_EDITS: list[tuple[str, str]] = [
    (
        """    <string name="permissions_lost">Necessary permissions lost, Please open IMD and re-grant the permissions first.</string>
</resources>""",
        """    <string name="permissions_lost">Necessary permissions lost, Please open IMD and re-grant the permissions first.</string>

    <!--
      The force-close popup. English only for now: the author's rule from this round on is that
      translation happens in one pass when everything is built, so these three are listed in
      check_translations.py's DEFERRED set rather than copied into eleven locales twice.

      'Ignore all previous reverts' says what it does on purpose. An earlier draft read just
      'Ignore', which sounds like "carry on" rather than "throw the record away" - and throwing
      it away is permanent.
    -->
    <string name="prior_hide_title">Previously hidden settings detected, restore them first?</string>
    <string name="prior_hide_restore">Restore settings first</string>
    <string name="prior_hide_ignore">Ignore all previous reverts</string>
</resources>""",
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

    staged: dict[Path, str] = {
        ROOT / PRIOR_HIDE: PRIOR_HIDE_BODY,
        ROOT / DISCARD: DISCARD_BODY,
    }

    everything = {
        RESULT: RESULT_EDITS,
        APPLY_APP: APPLY_APP_EDITS,
        APPLY_HIDE: APPLY_HIDE_EDITS,
        HIDDEN_RUNNER: HIDDEN_RUNNER_EDITS,
        STRINGS: STRINGS_EDITS,
    }

    for name, edits in everything.items():
        path = ROOT / name

        before = set(path.read_text(encoding="utf-8").splitlines()) if path.exists() else set()

        text = apply(path=path, edits=edits, problems=problems)

        if text is None:
            continue

        staged[path] = text

        for line in set(text.splitlines()) - before:
            if len(line) > 120 and not line.lstrip().startswith("<string"):
                problems.append(f"{path.name}: {len(line)} chars — {line.strip()[:60]}")

    runner = staged.get(ROOT / HIDDEN_RUNNER, "")

    # The flush has to answer, and both of its informed branches have to.
    if runner.count("return nothingOutstanding()") != 2:
        problems.append(
            f"SettingsHiddenRunner: {runner.count('return nothingOutstanding()')} plain returns"
            " of the record test, expected 2",
        )

    if "ManualRevertTarget.Shizuku !in result.failed" not in runner:
        problems.append("SettingsHiddenRunner: the device-wide branch ignores the report")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")

    print("ok — PriorHide, the discard path, the answering flush and the three strings")

    return 0


if __name__ == "__main__":
    sys.exit(main())
