#!/usr/bin/env python3
"""v3-r4n — the hide map forces the Shizuku entry false on Shevery instead of dropping it.

**Found by an assertion written for item 6, which failed.** The new host check asserted that on
Shevery `effectiveSettingsToHide[Shizuku]` is `false`. It was `null`: the map ends with
`.withoutShizukuWhenNoIntents(mode = shizukuForkMode)`, which removes the entry.

## Why that has to change now

`effectiveSettingsToHide` is what the hide dialog's **"x of y switched on"** line counts, and its
own KDoc already says which shape it means to have:

    False rather than dropped, as the overlay entry always was: the hide loop asks each target
    whether it is wanted and an absent entry already means no, so the explicit false says the
    same thing and keeps the map's shape stable.

The trailing drop contradicts that, and it only ever mattered because the Shizuku row was not
drawn on Shevery — the same reason `withoutOverlayWhenUnmanaged` used to shorten the same line
before r4m. **Item 6 draws that row.** Leave the drop in and the dialog says "3 of 5" under six
rows, which is exactly the defect r4m fixed for Display over other apps and which the author has
just told me to fix on the revert side too: *"count it"*.

## Why it is safe

Every reader of this map asks `== true` or `none { it.value }`, for which an absent entry and an
explicit `false` are the same answer — checked one by one before writing:

* `ApplySettingsToHideUseCase` — `wanted[target] != true`, `wanted[Shizuku] == true`
* `ApplyAppSettingsUseCase` → `AutoHide.kt` — `profileTargets.all { hiddenTargets[it] == true }`
* `AutoHideRunner` — `effectiveSettingsToHide.none { it.value }`, twice
* `DiagnosticStateReporter.targets` — `configuration[it] == true`

⚠ **`effectiveRevertDefaults` keeps its drop, and must.** The revert path asks
`wanted[target]?.let`, for which absent and false are *not* the same: a false entry would enter
the branch and try to unhide a service IMD has no start intent for. That asymmetry is why
`withoutShizukuWhenNoIntents` exists and it is untouched here.

## The assertion this rewrites

`"the hide config drops shizuku on shevery"` was a deliberate statement about the map's shape,
so it is replaced by the statement that is now true rather than deleted — and the neighbouring
`withoutShizukuWhenNoIntents` assertions, which are about the helper itself, stay exactly as
they are.

Asserts every anchor matches exactly once, that the revert map still drops the entry, and that
no reader uses a null-sensitive form. Writes nothing if any assertion fails.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MODEL = "domain/model/src/main/kotlin/com/android/geto/domain/model/OverlayManagement.kt"
TESTS = "tools/host-tests/DomainLogicTests.kt"

# Every file that reads the hide map, and the only forms they are allowed to read it in.
READERS = (
    "domain/use-case/src/main/kotlin/com/android/geto/domain/usecase/ApplySettingsToHideUseCase.kt",
    "domain/use-case/src/main/kotlin/com/android/geto/domain/usecase/ApplyAppSettingsUseCase.kt",
    "broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/AutoHideRunner.kt",
    "broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/DiagnosticStateReporter.kt",
)

EDITS: list[tuple[str, str, str, str]] = []


def edit(rel: str, name: str, old: str, new: str) -> None:
    EDITS.append((rel, name, old, new))


edit(
    MODEL,
    "the hide map's trailing drop",
    """ * False rather than dropped, as the overlay entry always was: the hide loop asks each target
 * whether it is wanted and an absent entry already means no, so the explicit false says the
 * same thing and keeps the map's shape stable.
 *
 * ⚠ **Hiding only.** [effectiveRevertDefaults] is deliberately not gated the same way.
 */
val UserData.effectiveSettingsToHide: Map<ManualRevertTarget, Boolean>
    get() = ManualRevertTarget.entries
        .fold(settingsToHideOrLegacy) { map, target ->
            if (canHide(target)) map else map + (target to false)
        }
        .withoutShizukuWhenNoIntents(mode = shizukuForkMode)""",
    """ * False rather than dropped, as the overlay entry always was: the hide loop asks each target
 * whether it is wanted and an absent entry already means no, so the explicit false says the
 * same thing and keeps the map's shape stable.
 *
 * ⚠ **And that now holds for every target, including Shizuku on a fork with no intents.** This
 * used to end with [withoutShizukuWhenNoIntents], which dropped that entry and contradicted the
 * paragraph above. It only mattered because the Shizuku row was not drawn on Shevery - r4n
 * draws it, and this map is what the dialog's "x of y switched on" line counts, so a dropped
 * entry would say "of five" under six rows. Exactly the defect [withoutOverlayWhenUnmanaged]
 * used to cause for Display over other apps.
 *
 * Safe because every reader asks `== true` or `none { it.value }`, for which absent and false
 * are the same answer. ⚠ **[effectiveRevertDefaults] keeps its drop and must**: the revert path
 * asks `wanted[target]?.let`, where a false entry *would* enter the branch and try to restart a
 * service IMD has no intent for.
 *
 * ⚠ **Hiding only.** [effectiveRevertDefaults] is deliberately not gated the same way.
 */
val UserData.effectiveSettingsToHide: Map<ManualRevertTarget, Boolean>
    get() = ManualRevertTarget.entries
        .fold(settingsToHideOrLegacy) { map, target ->
            if (canHide(target)) map else map + (target to false)
        }""",
)

edit(
    TESTS,
    "the shape assertion",
    """    check(
        "the hide config drops shizuku on shevery",
        ManualRevertTarget.Shizuku !in
            userData(ShizukuForkMode.Other, hideStates = both).effectiveSettingsToHide,
    )""",
    """    // ⚠ **Forced false, not dropped — r4n changed this deliberately.** The entry has to stay
    // in the map because the hide dialog counts it and now draws its row on every fork; every
    // reader asks `== true`, so false and absent mean the same thing to the engine. The revert
    // map below still drops it, and that asymmetry is the point: its reader is `?.let`.
    checkEquals(
        "the hide config forces shizuku off on shevery, keeping the entry",
        false,
        userData(ShizukuForkMode.Other, hideStates = both)
            .effectiveSettingsToHide[ManualRevertTarget.Shizuku],
    )""",
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

    model = staged[ROOT / MODEL]

    # ⚠ **Exactly one call left, and it must be the revert one.** Spelled as the call it can
    # only be — the new KDoc names the helper twice in prose, which a bare-name check would hit.
    calls = model.count(".withoutShizukuWhenNoIntents(mode = shizukuForkMode)")

    if calls != 1:
        print(f"REFUSED: {MODEL} has {calls} call(s) left, expected exactly 1")
        return 1

    hide = model.index("val UserData.effectiveSettingsToHide")
    revert = model.index("val UserData.effectiveRevertDefaults")
    call = model.index(".withoutShizukuWhenNoIntents(mode = shizukuForkMode)")

    if not hide < revert < call:
        print("REFUSED: the surviving call is not inside effectiveRevertDefaults")
        return 1

    # ⚠ **No reader may be null-sensitive.** A `?.let`, `!in`, `containsKey` or `.getOrElse`
    # over this map would change behaviour rather than only shape, and the sandbox cannot run
    # any of these files.
    for rel in READERS:
        text = (ROOT / rel).read_text(encoding="utf-8")

        for line in text.splitlines():
            if "effectiveSettingsToHide" not in line:
                continue

            if re.search(r"effectiveSettingsToHide\s*(\?\.|\.containsKey|\.getOrElse)", line):
                print(f"REFUSED: {rel} reads the hide map in a null-sensitive form:\n  {line}")
                return 1

            if re.search(r"!in\s+.*effectiveSettingsToHide", line):
                print(f"REFUSED: {rel} tests membership of the hide map:\n  {line}")
                return 1

    # The helper itself, and its own assertions about it, are untouched.
    tests = staged[ROOT / TESTS]

    for kept in (
        '"shevery drops the shizuku entry"',
        '"thedjchi keeps the shizuku entry"',
        '"the revert config drops shizuku on shevery"',
    ):
        if kept not in tests:
            print(f"REFUSED: {TESTS} lost the assertion {kept}")
            return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")

    print(f"  ok        {MODEL}  :: the hide map keeps every entry")
    print(f"  ok        {TESTS}  :: the shape assertion says what is now true")
    print("  ok        every reader asks == true; the revert map still drops")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
