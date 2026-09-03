#!/usr/bin/env python3
"""r4f — the Shevery start leaves wireless debugging alone, then turns it back on if it succeeds.

The author:

    "when i turn on shevery toggle do not manage wireless debugging toggle, only after shevery is
     turned detected turned on(shevery toggle on) then put wireless debugging to on if it was on
     when shevery toggle was first tried to be turned on by the user"

Three things change, and each one narrows what r4e did.

### 1. Only on success, not at the end of the wait

r4e settled wireless debugging once the wait was over, whichever way it went. A start that timed
out after forty seconds still wrote that row. Now the write happens **only when the service is
actually detected up** — the same test the countdown breaks on, read once and kept rather than
asked twice.

A start that never came up has moved nothing worth putting back, and writing a setting after a
failure is the app doing something in the name of an outcome that did not happen.

### 2. One direction only

r4e restored in both: it was `enabled = before`, so a device with wireless debugging **off**
before the press had it switched off again afterwards. The author's rule is narrower — *"put
wireless debugging to on if it was on"* — so off-before is now left exactly where the start put
it. `do not manage wireless debugging toggle` is the sentence that governs everything this code
does not do.

### 3. The value is the one from the press, and later presses no longer replace it

    "if it was on when shevery toggle was first tried to be turned on by the user"

⚠ **This reverses r4d's `"Your press wins"`.** `noteWirelessChosen` existed so that a press on
wireless debugging during the wait replaced the remembered value; the author has now named the
moment the value is taken from, and it is the press on *Shevery*, not a later press on wireless.
So the hook comes out along with the tracker field behind it — a value nothing reads is a
promise the next reader has to check.

⚠ **And it leaves one live hole, which is worth stating rather than quietly fixing.** Somebody
who had wireless debugging on, presses Shevery, then deliberately turns wireless off during the
forty seconds, will have it turned back on when the service comes up. That is what the
instruction says and it is not what the person meant. Flagged to the author; a one-line
restoration of `noteWirelessChosen` is the fix if he wants it back.

⚠ **`settleWirelessAfterStart` stays** — the Thedjchi path in `setTargetEnabled` still uses it,
still in both directions, and nothing here is a reason to change a fork the author has not
mentioned.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TRACKER = ("domain/use-case/src/main/kotlin/com/android/geto/domain/usecase/"
           "SheveryStartTracker.kt")
MANAGER_VM = ("feature/apps/src/main/kotlin/com/android/geto/feature/apps/manager/"
              "SettingsManagerViewModel.kt")

VM_EDITS: list[tuple[str, str, int]] = [
    # The loop remembers whether the service actually came up.
    (
        """                while (left > 0 && isActive) {
                    delay(1_000)

                    _targetStates.value = getManualTargetStatesUseCase()

                    if (_targetStates.value.isEnabled(ManualRevertTarget.Shizuku)) break

                    left -= 1

                    sheveryStartTracker.tick(secondsLeft = left)
                }

                starting.join()
""",
        """                // ⚠ **Read once and kept.** The write below happens only on a start that
                // actually came up, and asking the same question a second time afterwards
                // would be asking it of a device the join may have changed underneath.
                var came = false

                while (left > 0 && isActive) {
                    delay(1_000)

                    _targetStates.value = getManualTargetStatesUseCase()

                    if (_targetStates.value.isEnabled(ManualRevertTarget.Shizuku)) {
                        came = true

                        break
                    }

                    left -= 1

                    sheveryStartTracker.tick(secondsLeft = left)
                }

                starting.join()
""",
        1,
    ),
    # The write itself: on success, one direction, from the value taken at the press.
    (
        """                // ⚠ **After the start, not during it.** Shevery's own start writes the
                // transport on the way up, so anything written before it lands is written
                // over. NonCancellable because turning the row off mid-wait cancels this job,
                // and the off branch has its own USB restore to do - leaving wireless
                // debugging where a start put it would be the app changing a setting nobody
                // asked it to.
                //
                // ⚠ **The tracker's value, not the local one.** A press on wireless debugging
                // during the wait replaces it, and that press is what should be put back - the
                // author's `"Your press wins"`. Falls back to the local reading only if the
                // tracker has been cleared underneath, which means a cancel got here first.
                withContext(NonCancellable) {
                    settleWirelessAfterStart(
                        before = sheveryStartTracker.wirelessBefore ?: wirelessBefore,
                    )
                }
""",
        """                // ⚠ **Only on a start that came up, and only in the on direction.** The
                // author's rule, and both halves of it are narrower than r4e's: a start that
                // timed out has moved nothing worth putting back, and a device that had
                // wireless debugging off before the press is left wherever the start put it.
                // `do not manage wireless debugging toggle` governs everything this does not
                // do.
                //
                // ⚠ **After the start, not during it.** Shevery writes the transport on its
                // way up, so anything written before that lands is written over.
                // NonCancellable because turning the row off mid-wait cancels this job, and
                // the value below would otherwise be lost between the check and the write.
                if (came && wirelessBefore) {
                    withContext(NonCancellable) {
                        raiseWirelessAfterSheveryStart()
                    }
                }
""",
        1,
    ),
    # The one-directional write, beside the two-directional one the other fork still uses.
    (
        """    private suspend fun settleWirelessAfterStart(before: Boolean) {
""",
        """    /**
     * Put wireless debugging back **on** after a Shevery start that came up.
     *
     * ⚠ **One direction, deliberately, and separate from [settleWirelessAfterStart].** That one
     * drives the row to whatever it was and is what the Thedjchi path still wants; this one only
     * ever switches it on, because the author's rule for Shevery is *"put wireless debugging to
     * on if it was on"* and says nothing about the other case. Two behaviours under one name
     * with a flag would be the version of this that gets misread later.
     *
     * Writes nothing if the start left the row alone, so a device that never lost wireless
     * debugging is not handed a write it did not need.
     */
    private suspend fun raiseWirelessAfterSheveryStart() {
        val now = getManualTargetStatesUseCase()

        if (now.isEnabled(ManualRevertTarget.WirelessDebugging)) return

        setManualTargetUseCase(
            target = ManualRevertTarget.WirelessDebugging,
            enabled = true,
            manual = true,
        )
    }

    private suspend fun settleWirelessAfterStart(before: Boolean) {
""",
        1,
    ),
    # `noteWirelessChosen` goes: the value is the one from the press on Shevery.
    (
        """        // ⚠ **The user outranks the restore.** Wireless debugging stays unlocked through a
        // Shevery wait, and is also put back when that wait ends; without this the restore
        // would undo a deliberate press made thirty seconds earlier. The author's answer to
        // his own race: the press becomes the value to put back.
        if (target == ManualRevertTarget.WirelessDebugging) {
            sheveryStartTracker.noteWirelessChosen(enabled = enabled)
        }

""",
        "",
        1,
    ),
    (
        """        sheveryStartTracker.begin(
            job = job,
            seconds = SHEVERY_WAIT_SECONDS,
            wirelessBefore = wirelessBefore,
        )
""",
        """        sheveryStartTracker.begin(job = job, seconds = SHEVERY_WAIT_SECONDS)
""",
        1,
    ),
]

TRACKER_EDITS: list[tuple[str, str, int]] = [
    (
        """    /**
     * Where wireless debugging was when the start began — or where the user last put it since.
     *
     * ⚠ **A press during the wait replaces this**, which is the author's answer to the race his
     * own instructions open: wireless debugging stays unlocked through the wait *and* is put
     * back after it. Restoring the pre-start value would undo a deliberate press made thirty
     * seconds earlier, so the deliberate press becomes the value to restore.
     */
    var wirelessBefore: Boolean? = null
        private set

""",
        "",
        1,
    ),
    (
        """    fun begin(job: Job, seconds: Int, wirelessBefore: Boolean) {
        this.job = job

        this.wirelessBefore = wirelessBefore

        _secondsLeft.value = seconds
    }
""",
        """    fun begin(job: Job, seconds: Int) {
        this.job = job

        _secondsLeft.value = seconds
    }
""",
        1,
    ),
    (
        """    /** The user moved wireless debugging themselves; that is the value worth putting back. */
    fun noteWirelessChosen(enabled: Boolean) {
        if (waiting) wirelessBefore = enabled
    }

""",
        "",
        1,
    ),
    (
        """    fun clear() {
        job = null

        wirelessBefore = null

        _secondsLeft.value = null
    }
""",
        """    fun clear() {
        job = null

        _secondsLeft.value = null
    }
""",
        1,
    ),
]


def main() -> int:
    staged: dict[Path, str] = {}
    problems: list[str] = []

    for rel, subs in ((MANAGER_VM, VM_EDITS), (TRACKER, TRACKER_EDITS)):
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

    view_model = staged.get(ROOT / MANAGER_VM, "")
    tracker = staged.get(ROOT / TRACKER, "")

    # ⚠ Asserted against code, never the prose around it, and against *position* where a
    # position is what matters — the two traps this project has paid for twice each.
    for rel, text, token, expected in (
        (MANAGER_VM, view_model, "noteWirelessChosen", 0),
        (MANAGER_VM, view_model, "sheveryStartTracker.wirelessBefore", 0),
        (MANAGER_VM, view_model, "raiseWirelessAfterSheveryStart()", 2),
        (MANAGER_VM, view_model, "if (came && wirelessBefore) {", 1),
        (MANAGER_VM, view_model, "came = true", 1),
        # The Thedjchi path keeps the two-directional settle: one definition, one caller.
        (MANAGER_VM, view_model, "settleWirelessAfterStart", 3),
        (TRACKER, tracker, "wirelessBefore", 0),
        (TRACKER, tracker, "noteWirelessChosen", 0),
    ):
        if text.count(token) != expected:
            problems.append(f"{rel}: expected {expected} of {token!r}, found {text.count(token)}")

    # The new write must live inside setSheveryService's job, after the countdown loop that
    # sets `came` — not merely somewhere in the file. r4d's whole failure was presence without
    # position.
    came = view_model.find("                    came = true")
    call = view_model.find("                        raiseWirelessAfterSheveryStart()")
    end = view_model.find("            } finally {\n                sheveryStartTracker.clear()")

    if came < 0 or call < 0 or end < 0:
        problems.append(f"{MANAGER_VM}: cannot locate the loop, the call, or the job's finally")
    elif not came < call < end:
        problems.append(
            f"{MANAGER_VM}: the write is not between the countdown and the job's finally",
        )

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

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")
        print(f"  wrote {path.relative_to(ROOT)}")

    print("ok - wireless left alone through the wait, raised only on a start that came up")

    return 0


if __name__ == "__main__":
    sys.exit(main())
