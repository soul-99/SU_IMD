#!/usr/bin/env python3
"""r3 — rebuilds `OverlayManagement.kt` after a script overwrote it.

⚠ **What went wrong, recorded because it is a trap worth never repeating.**
`_v3_manager_gating.py` appended its new enum with

    overlay = staged.get(ROOT / OVERLAY, "")
    staged[ROOT / OVERLAY] = overlay.rstrip("\\n") + "\\n" + REASONS

and `OVERLAY` was **not in that script's `EDITS` list**, so `staged.get` fell through to its
default of `""` and the file was written as the enum alone — 205 lines replaced by 44. Every
assertion in the script passed, because none of them looked at a file the script had not
listed. The audits then caught it a minute later, as they are supposed to, but the lesson is
the script's: **`staged.get(path, "")` is only safe for a path the edit loop has already
read.** For anything else, read the file.

This rebuilds the file from the **r3 pristine** copy and re-applies, in order, exactly what
the two scripts before this one did to it:

  `_v3_gating_helpers.py`  the two `manageOverlay` reads swapped to `overlayManageable`, and
                           the `overlayManageable` / `accessibilityManageable` helpers appended
  `_v3_manager_gating.py`  `OverlayBlockReason` and `overlayBlockReasons` appended

Every fragment below is asserted against the pristine text before anything is written, so a
rebuild that does not reproduce the intended file refuses instead of guessing.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRISTINE = Path("/home/claude/work/r3-pristine")

OVERLAY = "domain/model/src/main/kotlin/com/android/geto/domain/model/OverlayManagement.kt"

SUBSTITUTIONS = [
    (
        """    get() = (
        if (manageOverlay) {
""",
        """    get() = (
        if (overlayManageable) {
""",
        1,
    ),
    (
        """    get() = when {
        manageOverlay -> revertDefaults
""",
        """    get() = when {
        overlayManageable -> revertDefaults
""",
        1,
    ),
]

HELPERS = '''
/**
 * Whether Display over other apps is something IMD can actually manage right now.
 *
 * ⚠ **This replaces the stored `manageOverlay` switch**, which v3 removed from Advanced. The
 * author's instruction was to show the DOOA toggles to everyone and gate them on whether they
 * can work, rather than on a preference the user had to find first. Three things have to be
 * true, and each of them has a different thing wrong with it if it is not:
 *
 * * **'Manage Shizuku' is on and complete** — the AppOps behind overlay access can only be
 *   written through a running Shizuku, so with the master switch off there is nothing to write
 *   them with.
 * * **The fork is Thedjchi** — *"we are ditching shevery support from DOOA completely"*.
 *   Shevery has no start-stop intent, so IMD cannot bring the shell up on demand to write an
 *   AppOp and put it back.
 * * **'DOOAs to hide' is not empty** — with nothing selected the feature has nothing to do,
 *   and a toggle that can only ever be a no-op is worse than a toggle that says why.
 *
 * The three are deliberately not collapsed into one boolean anywhere that has to *explain* the
 * refusal — see [overlayBlockReasons], which is how a greyed row knows where to send somebody.
 */
val UserData.overlayManageable: Boolean
    get() = manageShizukuEffective &&
        shizukuForkMode == ShizukuForkMode.Thedjchi &&
        managedOverlayPackages.isNotEmpty()

/**
 * Whether hiding accessibility services is something IMD can actually do right now.
 *
 * The author's rule: *"if no DOOAs and no Accessibility services set to be hidden (do not
 * count IMD+ accessibility service) then disable the toggles and make them unclickable"*.
 *
 * ⚠ **IMD+'s own detector is not in this list and never was.** It is held under
 * `AccessibilityServicePlan.AUTO_HIDE_HOLD`, not in the user's selection, which is what makes
 * "do not count IMD+" true by construction rather than by a filter that could drift. The
 * author's other rule — that IMD+'s service is hidden and unhidden before a launch whatever
 * this says — is the same fact from the other side.
 */
val UserData.accessibilityManageable: Boolean
    get() = managedAccessibilityServices.isNotEmpty()

/**
 * Which of [overlayManageable]'s three terms is standing in the way, in the order a user
 * should be sent to fix them.
 *
 * Top level rather than nested, for the mundane reason `SettingsWorkKind` and `HideToggle`
 * are: `check16_when` cannot read an indented enum — it needs the closing brace at column 0.
 */
enum class OverlayBlockReason {
    /** Shevery. Not unconfigured but unsupported: there is nothing to go and set. */
    ForkUnsupported,

    /** 'Manage Shizuku' is off, or a field under it is blank. */
    ManageShizukuOff,

    /** Nothing is selected under 'DOOAs to hide'. */
    NothingSelected,
}

/**
 * Why a Display over other apps control will not move, or an empty list while it will.
 *
 * ⚠ **In `:domain:model` and returning reasons rather than sentences**, because two modules
 * ask this question — the settings screen's two configuration dialogs and the settings
 * manager — and neither can see the other's strings. Each maps the reasons to its own copy of
 * the author's wording.
 *
 * ⚠ **Shevery short-circuits to exactly one reason.** On that fork the feature is unsupported,
 * so the surfaces say so and offer no path; going on to report an empty picker as well would
 * be directions to a screen that can never help.
 */
fun overlayBlockReasons(userData: UserData): List<OverlayBlockReason> = when {
    userData.overlayManageable -> emptyList()

    userData.shizukuForkMode != ShizukuForkMode.Thedjchi ->
        listOf(OverlayBlockReason.ForkUnsupported)

    else -> buildList {
        if (!userData.manageShizukuEffective) add(OverlayBlockReason.ManageShizukuOff)

        if (userData.managedOverlayPackages.isEmpty()) add(OverlayBlockReason.NothingSelected)
    }
}
'''


def main() -> int:
    problems: list[str] = []

    source = PRISTINE / OVERLAY
    target = ROOT / OVERLAY

    if not source.exists():
        print(f"REFUSED, nothing written\n  {source}: no pristine copy to rebuild from")

        return 1

    text = source.read_text(encoding="utf-8")

    for old, new, expected in SUBSTITUTIONS:
        found = text.count(old)

        if found != expected:
            problems.append(
                f"{OVERLAY}: expected {expected} of "
                f"{old.strip().splitlines()[0][:58]!r}, found {found}",
            )

            continue

        text = text.replace(old, new, expected)

    text = text.rstrip("\n") + "\n" + HELPERS

    # What the rebuilt file has to contain, in both directions: everything the pristine had,
    # and everything the two scripts added.
    for wanted in (
        "fun Map<ManualRevertTarget, Boolean>.withoutOverlayWhenUnmanaged(",
        "val UserData.effectiveSettingsToHide:",
        "val UserData.effectiveRevertDefaults:",
        "fun Map<ManualRevertTarget, Boolean>.withoutShizukuWhenNoIntents(",
        "fun overlayAlreadyWithdrawn(",
        "fun List<AppSettingTemplate>.templatesForOverlayState(",
        "fun List<AppSetting>.appSettingsForOverlayState(",
        "val UserData.overlayManageable:",
        "val UserData.accessibilityManageable:",
        "enum class OverlayBlockReason {",
        "fun overlayBlockReasons(",
    ):
        if wanted not in text:
            problems.append(f"{OVERLAY}: rebuilt file is missing {wanted!r}")

    if "userData.manageOverlay" in text or "\n        manageOverlay -> " in text:
        problems.append(f"{OVERLAY}: the rebuilt file still reads the removed switch")

    for line in text.splitlines():
        if len(line) > 120:
            problems.append(f"{OVERLAY}: line of {len(line)} chars: {line.strip()[:58]!r}")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    target.write_text(text, encoding="utf-8")
    print(f"  rebuilt {OVERLAY} ({len(text.splitlines())} lines)")
    print("ok - the file is the pristine plus exactly what the two scripts meant to add")

    return 0


if __name__ == "__main__":
    sys.exit(main())
