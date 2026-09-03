#!/usr/bin/env python3
"""
v3-r2b — the first-owner rule: a hide records a "before" only for what it actually changes.

### The bug, traced not theorised (r2b §0 and §5.1)

Per app configuration, two apps into one hidden window:

| step | what happens | what IMD records |
| --- | --- | --- |
| 1 | Calculator launches, profile hides dev + USB, both on | `Calculator: dev=ON, usb=ON` |
| 2 | Gallery launches into that window, profile hides USB + wireless. IMD measures them **now**, and USB is already off | `Gallery: usb=OFF, wifi=ON` |
| 3 | Calculator's revert runs first: dev→ON, **usb→ON** | USB comes back while Gallery is still open — the leak |
| 4 | Gallery's revert runs: **usb→OFF**, records cleared | **USB is stranded off with nothing left that knows better** |

Step 2 is the poison: Gallery recorded the *hidden* value as though it were the real one.

### The rule, as the author settled it

> *"only count turned off values for the first owner"*

which needs no cross-record lookup at all:

> **Record a "before" value only when the setting is not already at the value this hide is
> about to write.**

At step 2 Gallery finds USB already at its hidden value, records nothing for it, and keeps only
`wifi=ON`. Whichever order the reverts then run, Calculator is the only owner of USB and puts it
back.

⚠ **Better than the version proposed first**, which was "is any existing record carrying a value
for this key". That one missed a case this handles for free: if the **user** had USB debugging
off before any of this began, the *first* app to want it hidden also records nothing, so no
revert ever switches it on. IMD only ever puts back what IMD took.

### Both recorders, and they were subtly different already

`ApplyAppSettingsUseCase.recordCurrentValues` measures per-app profiles; `ApplySettingsToHide
UseCase.recordDeviceWideValues` measures the six manual targets for a device-wide hide. Both
already skip a key that is **already recorded** — deliberately, so a repeat launch cannot
overwrite the original reading. Neither skipped a key that is already **at its hidden value**,
which is the different question this answers. A device-wide hide always drives its targets off,
so there the rule reads as "skip a target that is already off".

The predicate itself goes in `:domain:model` — the only module the host runner compiles — so
the cascade can be asserted rather than argued about.

⚠ **Deliberately NOT in this build: the notification collapse (§5).** It touches four screens,
three view models and a UI state, and it is a presentation change; this one changes what *every
hide in the app records*, which earns its own device test. The strand is the corruption; the
collapse only removes the user's choice of revert order.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FRAMEWORKS = "domain/model/src/main/kotlin/com/android/geto/domain/model/Frameworks.kt"

APPLY_APP = (
    "domain/use-case/src/main/kotlin/com/android/geto/domain/usecase/ApplyAppSettingsUseCase.kt"
)

APPLY_HIDE = (
    "domain/use-case/src/main/kotlin/com/android/geto/domain/usecase/"
    "ApplySettingsToHideUseCase.kt"
)

HOST_TESTS = "tools/host-tests/DomainLogicTests.kt"

FRAMEWORKS_EDITS: list[tuple[str, str]] = [
    (
        """/**
 * The device-wide memory record's id for one manual target.
""",
        """/**
 * **The first-owner rule.** Whether this hide is the one that owes putting [key] back.
 *
 * True only when the setting is not already at the value this hide is about to write — which
 * is to say, only when this hide is the one actually changing it.
 *
 * ### Why it exists
 *
 * A per-app record is measured at the moment of that app's hide and stored under that app's
 * component name, so a **second** app launched into an already-hidden window used to measure the
 * *hidden* values and record them as its "before". Reverting the first app then put a setting
 * back while the second was still open, and reverting the second wrote the hidden value over it
 * — leaving it stranded off with no record left that knew better.
 *
 * With this, the first hide to touch a setting is the only one that records it, and it is
 * therefore the only one that puts it back. Later hides that find it already down record
 * nothing for it and take nothing away when they revert.
 *
 * ### It also fixes a case that predates the cascade
 *
 * If the **user** had a setting off before any of this began, the first hide to want it hidden
 * also records nothing — so no revert ever switches it on. IMD only puts back what IMD took,
 * which is the same instinct as `RevertToDefaultUseCase`'s "a null recording is skipped, not
 * written".
 *
 * ⚠ **Not the same question as "is it already recorded".** Both recorders already skip a key
 * they hold a reading for, so that a repeat launch cannot overwrite the original with the value
 * the previous launch wrote. This asks whether the hide changes anything at all.
 *
 * [currentValue] is null when the setting has never been set; that is not equal to any value a
 * hide writes, so it is recorded — and the revert's own rule skips writing a null back.
 */
fun hideOwnsRevert(currentValue: String?, valueOnLaunch: String): Boolean =
    currentValue != valueOnLaunch

/**
 * The device-wide memory record's id for one manual target.
""",
    ),
]

APPLY_APP_EDITS: list[tuple[str, str]] = [
    (
        """import com.android.geto.domain.model.SettingType
""",
        """import com.android.geto.domain.model.SettingType
import com.android.geto.domain.model.hideOwnsRevert
""",
    ),
    (
        """        val measured = unrecorded.associate { setting ->
            SettingSnapshot.idOf(settingType = setting.settingType, key = setting.key) to
                secureSettingsWrapper.getSecureSettingValue(
                    settingType = setting.settingType,
                    key = setting.key,
                )
        }

        userDataRepository.updateSettingStateBefore(""",
        """        // ⚠ **The first-owner rule.** A setting already at the value this profile is about
        // to write is one somebody else is holding down — another app's launch, a device-wide
        // hide, or the user themselves — so this hide is not the one that owes putting it back
        // and records nothing for it. See [hideOwnsRevert] for what went wrong without it.
        //
        // mapNotNull rather than associate + filter: the read is a binder call each, and there
        // is no reason to make one for a key whose answer cannot be recorded anyway — it is
        // needed to *decide* that, but the pair is dropped in the same pass rather than built
        // and thrown away.
        val measured = unrecorded.mapNotNull { setting ->
            val current = secureSettingsWrapper.getSecureSettingValue(
                settingType = setting.settingType,
                key = setting.key,
            )

            if (!hideOwnsRevert(currentValue = current, valueOnLaunch = setting.valueOnLaunch)) {
                return@mapNotNull null
            }

            SettingSnapshot.idOf(settingType = setting.settingType, key = setting.key) to current
        }.toMap()

        // Everything this profile hides was already down. Nothing is owed, and the write is
        // skipped for the same reason as the one above it: a proto rewrite for no change.
        if (measured.isEmpty()) return

        userDataRepository.updateSettingStateBefore(""",
    ),
]

APPLY_HIDE_EDITS: list[tuple[str, str]] = [
    (
        """            if (id in existing) continue

            measured[id] = if (before.isEnabled(target)) "1" else "0"
""",
        """            if (id in existing) continue

            // ⚠ **The first-owner rule**, in its device-wide shape. A device-wide hide always
            // drives its targets off, so "not already at the value about to be written" reads
            // here as "not already off" — and a target that is already off is one somebody else
            // is holding down, or one the user never had on. Either way this hide does not owe
            // putting it back. See `hideOwnsRevert`.
            if (!before.isEnabled(target)) continue

            measured[id] = "1"
""",
    ),
]

HOST_TEST_EDITS: list[tuple[str, str]] = [
    (
        """import com.android.geto.domain.model.hidingFrameworkFor
""",
        """import com.android.geto.domain.model.hideOwnsRevert
import com.android.geto.domain.model.hidingFrameworkFor
""",
    ),
    (
        """    frameworkSplitTests()

    println("passed: $passed")
""",
        """    frameworkSplitTests()
    firstOwnerTests()

    println("passed: $passed")
""",
    ),
    (
        """private fun frameworkSplitTests() {
""",
        """/**
 * The first-owner rule, and the cascade it exists for.
 *
 * The walk below is r2b §5.1's table, run rather than argued: two apps into one hidden window,
 * both revert orders, and the assertion is that the setting they share ends up **on** either
 * way. Before the rule, one of the two orders stranded it off.
 */
private fun firstOwnerTests() {
    check("a hide that changes a setting owns putting it back", hideOwnsRevert("1", "0"))

    check("a hide that changes nothing owns nothing", !hideOwnsRevert("0", "0"))

    // Never set is not equal to anything a hide writes, so it is recorded. The revert's own
    // rule then declines to write a null back, which is where that case is actually handled.
    check("an unset setting is recorded", hideOwnsRevert(null, "0"))

    // A profile that drives a setting to something other than off is the same question.
    check("a non-zero target still compares by value", hideOwnsRevert("0", "2"))

    check("and owns nothing when it is already there", !hideOwnsRevert("2", "2"))

    // --- the cascade, both orders -------------------------------------------------------
    //
    // Two apps, one shared key. `live` is what the device reads; `records` is what each app
    // owes. A hide writes "0" and records the old value only if it owns the revert.
    val live = mutableMapOf("dev" to "1", "usb" to "1", "wifi" to "1")

    val records = mutableMapOf<String, MutableMap<String, String>>()

    fun hide(app: String, keys: List<String>) {
        val owed = mutableMapOf<String, String>()

        for (key in keys) {
            val current = live.getValue(key)

            if (hideOwnsRevert(currentValue = current, valueOnLaunch = "0")) {
                owed[key] = current
            }

            live[key] = "0"
        }

        records[app] = owed
    }

    fun revert(app: String) {
        val owed = records.remove(app) ?: return

        for (key in owed.keys) {
            live[key] = owed.getValue(key)
        }
    }

    hide(app = "calculator", keys = listOf("dev", "usb"))
    hide(app = "gallery", keys = listOf("usb", "wifi"))

    check(
        "the second app records nothing for a key the first already holds",
        records.getValue("gallery").keys == setOf("wifi"),
    )

    check(
        "and the first app still owns both of its own",
        records.getValue("calculator").keys == setOf("dev", "usb"),
    )

    revert(app = "calculator")
    revert(app = "gallery")

    check(
        "first-then-second leaves the shared setting on",
        live == mapOf("dev" to "1", "usb" to "1", "wifi" to "1"),
    )

    // The other order, from the same start. This is the one that used to strand it.
    live.putAll(mapOf("dev" to "1", "usb" to "1", "wifi" to "1"))

    records.clear()

    hide(app = "calculator", keys = listOf("dev", "usb"))
    hide(app = "gallery", keys = listOf("usb", "wifi"))

    revert(app = "gallery")
    revert(app = "calculator")

    check(
        "second-then-first leaves the shared setting on too",
        live == mapOf("dev" to "1", "usb" to "1", "wifi" to "1"),
    )

    // And the user's own choice is never overridden: a setting they had off before any hide
    // is owned by nobody, so no revert switches it on.
    live.putAll(mapOf("dev" to "1", "usb" to "0", "wifi" to "1"))

    records.clear()

    hide(app = "calculator", keys = listOf("dev", "usb"))

    check(
        "a setting the user had off is owned by nobody",
        records.getValue("calculator").keys == setOf("dev"),
    )

    revert(app = "calculator")

    check(
        "so a revert leaves it off",
        live == mapOf("dev" to "1", "usb" to "0", "wifi" to "1"),
    )
}

private fun frameworkSplitTests() {
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
        FRAMEWORKS: FRAMEWORKS_EDITS,
        APPLY_APP: APPLY_APP_EDITS,
        APPLY_HIDE: APPLY_HIDE_EDITS,
        HOST_TESTS: HOST_TEST_EDITS,
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

    # One declaration, one import per user, one call per recorder, plus the host tests.
    uses = 0

    for kotlin in sorted(ROOT.rglob("*.kt")):
        if "build" in kotlin.relative_to(ROOT).parts:
            continue

        body = staged.get(kotlin) or kotlin.read_text(encoding="utf-8")

        uses += body.count("hideOwnsRevert")

    # 1 declaration + 1 KDoc self-reference in Frameworks, 1 import + 1 call in ApplyApp,
    # 1 comment reference in ApplyHide, 1 import + 9 uses in the host tests.
    if uses < 10:
        problems.append(f"hideOwnsRevert named {uses} times, expected at least 10")

    # Both recorders must have stopped writing an already-hidden reading.
    hide_body = staged.get(ROOT / APPLY_HIDE, "")

    if 'measured[id] = if (before.isEnabled(target)) "1" else "0"' in hide_body:
        problems.append("ApplySettingsToHideUseCase: still records an already-off target")

    app_body = staged.get(ROOT / APPLY_APP, "")

    if "unrecorded.associate {" in app_body:
        problems.append("ApplyAppSettingsUseCase: still records unconditionally")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")

    print("ok — both recorders now obey the first-owner rule, with the cascade asserted")

    return 0


if __name__ == "__main__":
    sys.exit(main())
