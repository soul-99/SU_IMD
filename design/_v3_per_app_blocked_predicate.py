#!/usr/bin/env python3
"""
v3-r4m — the per-app screen asks `appSettingBlocked` instead of the two filters it lost.

⚠ **This is the ENGINE half of open item 2 only. Nothing is greyed yet.** The rows and
templates the gate refuses are still *removed* from the screen, exactly as before - the visual
change waits on the author's approval of the rendered template, which is his standing rule
("show me a template of anything visual before you build it") and which he has not answered.

What changes is what the screen asks. `templatesForOverlayState` and `appSettingsForOverlayState`
are gone with `_v3_hide_gate.py`; both were built out of two private predicates that disagreed
with the hide itself - they hid the Shizuku marker on a fork with no intents while
`ApplyAppSettingsUseCase` went on stopping the service anyway. `appSettingBlocked` reads
`canHide`, which is what the hide reads, so the screen and the engine now answer together.

Behaviour on the device is therefore **unchanged by this script**, and that is deliberate: it
leaves the tree compiling and the visual decision still open.

⚠ The accessibility flag joins the two markers here, because `canHide` gates it now. A profile
carrying `accessibility_enabled` with nothing in 'Accessibility services to hide' used to write
the raw flag - switching off every service including IMD+'s own detector - and its row now
leaves the screen the way the other two do.

Every edit asserts its anchor matches exactly once. Nothing is written if any file fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

VM = (
    "feature/app-settings/src/main/kotlin/com/android/geto/feature/appsettings/"
    "AppSettingsViewModel.kt"
)

OLD_IMPORTS = """import com.android.geto.domain.model.appSettingsForOverlayState
import com.android.geto.domain.model.templatesForOverlayState
"""

NEW_IMPORT = "import com.android.geto.domain.model.appSettingBlocked"

OLD_ROWS = """    val appSettingsUiState =
        combine(
            appSettingsRepository.getAppSettingsFlowByComponentName(componentName = componentName),
            userDataRepository.userData.map { it.overlayManageable }.distinctUntilChanged(),
            userDataRepository.userData.map { it.shizukuForkMode }.distinctUntilChanged(),
        ) { appSettings, manageOverlay, forkMode ->
            appSettings.appSettingsForOverlayState(
                manageOverlay = manageOverlay,
                shizukuForkMode = forkMode,
            )
        }.map(AppSettingsUiState::Success).stateIn("""

NEW_ROWS = """    val appSettingsUiState =
        combine(
            appSettingsRepository.getAppSettingsFlowByComponentName(componentName = componentName),
            userDataRepository.userData,
        ) { appSettings, userData ->
            // ⚠ **One question, and the hide asks the same one.** This used to be two private
            // predicates in :domain:model that answered for the overlay marker and the Shizuku
            // marker separately - and disagreed with the engine, which went on acting on the
            // Shizuku marker after the screen had hidden it. `appSettingBlocked` reads
            // `canHide`, so a row that leaves the screen is a row the hide will not act on.
            appSettings.filterNot { appSettingBlocked(userData = userData, key = it.key) }
        }.map(AppSettingsUiState::Success).stateIn("""

OLD_TEMPLATES = """    val appSettingTemplates = combine(
        _appSettingTemplates,
        userDataRepository.userData.map { it.overlayManageable }.distinctUntilChanged(),
        userDataRepository.userData.map { it.shizukuForkMode }.distinctUntilChanged(),
    ) { templates, manageOverlay, forkMode ->
        templates.templatesForOverlayState(
            manageOverlay = manageOverlay,
            shizukuForkMode = forkMode,
        )
    }.onStart {"""

NEW_TEMPLATES = """    val appSettingTemplates = combine(
        _appSettingTemplates,
        userDataRepository.userData,
    ) { templates, userData ->
        templates.filterNot { appSettingBlocked(userData = userData, key = it.key) }
    }.onStart {"""

# The two comments above these flows name the filters that no longer exist.
OLD_ROWS_DOC = """    // The stored rows with the overlay marker filtered out while overlay management is off.
    // The filter is on the way to the screen only - the Room rows are untouched, so a DOOA
    // row a user added comes straight back when they switch the feature on again, in this app
    // and every other it was added to. Showing it while off would promise a hide the memory
    // function will not perform, since ApplyAppSettingsUseCase stops acting on the marker then."""

NEW_ROWS_DOC = """    // The stored rows, minus anything IMD cannot act on right now - Display over other apps
    // without a Thedjchi Shizuku to write the AppOp through, the Shizuku service with 'Manage
    // Shizuku' off, the accessibility flag with nothing in the picker.
    //
    // The filter is on the way to the screen only: the Room rows are untouched, so a row comes
    // straight back when the thing it needs is configured again, in this app and every other
    // it was added to.
    //
    // ⚠ **Still removed rather than greyed.** The author asked for these to be shown and
    // greyed with a pop-up; that is the half of open item 2 waiting on his approval of the
    // rendered template. What changed here is only which question decides it."""

OLD_TEMPLATES_DOC = """    // The "Hide Display over other apps" template is dropped from the picker while overlay
    // management is off, for the same reason and by the same marker as the rows above: it
    // cannot be added to do nothing."""

NEW_TEMPLATES_DOC = """    // The same question as the rows above, for the same reason: a template that cannot be
    // added to do anything is worse than a template that is not offered. Greying these is the
    // other half of open item 2."""

# `overlayManageable` was read only by the two filters' arguments, which are gone.
OLD_OVERLAY_IMPORT = "import com.android.geto.domain.model.overlayManageable\n"

EDITS = [
    ("the two removed imports", OLD_IMPORTS, ""),
    ("the overlayManageable import", OLD_OVERLAY_IMPORT, ""),
    ("the rows doc", OLD_ROWS_DOC, NEW_ROWS_DOC),
    ("appSettingsUiState", OLD_ROWS, NEW_ROWS),
    ("the templates doc", OLD_TEMPLATES_DOC, NEW_TEMPLATES_DOC),
    ("appSettingTemplates", OLD_TEMPLATES, NEW_TEMPLATES),
]


def insert_import(text: str, statement: str) -> str:
    lines = text.split("\n")
    idx = [i for i, line in enumerate(lines) if line.startswith("import ")]

    if statement in lines:
        return text

    sortable = [
        i for i in idx
        if not lines[i].startswith(("import javax.", "import java."))
        and " as " not in lines[i]
    ]

    at = next((i for i in sortable if lines[i] > statement), sortable[-1] + 1)
    lines.insert(at, statement)

    return "\n".join(lines)


def main() -> int:
    path = ROOT / VM

    if not path.is_file():
        print(f"REFUSED: missing {VM}")
        return 1

    original = path.read_text(encoding="utf-8")
    text = original

    if "appSettingBlocked" in text:
        print("REFUSED: appSettingBlocked already present — has this run before?")
        return 1

    for name, old, _ in EDITS:
        found = text.count(old)

        if found != 1:
            print(f"REFUSED: {name} matched {found} time(s), expected exactly 1")
            return 1

    for _, old, new in EDITS:
        text = text.replace(old, new, 1)

    text = insert_import(text, NEW_IMPORT)

    # Nothing may still name the two removed functions.
    for gone in ("templatesForOverlayState", "appSettingsForOverlayState", "overlayManageable"):
        if gone in text:
            print(f"REFUSED: {VM} still names {gone}")
            return 1

    # `combine`, `map` and `onStart` are all still used; `distinctUntilChanged` may not be, and
    # an unused import is what check12 exists to catch — so this refuses rather than leaving it.
    for used in ("combine(", ".map(", ".onStart {"):
        if used not in text:
            print(f"REFUSED: {VM} no longer uses {used}, its import would be dead")
            return 1

    if "distinctUntilChanged" not in text.split("import ", 1)[1].split("\n\n", 1)[-1]:
        text = text.replace("import kotlinx.coroutines.flow.distinctUntilChanged\n", "", 1)

        print("  - import  distinctUntilChanged (no longer used)")

    # Assert POSITION: the new predicate is read in both flows, and nowhere else.
    if text.count("appSettingBlocked(userData = userData, key = it.key)") != 2:
        print(
            "REFUSED: appSettingBlocked should be read exactly twice, found "
            f"{text.count('appSettingBlocked(userData = userData, key = it.key)')}"
        )
        return 1

    at_rows = text.index("    val appSettingsUiState =")
    at_templates = text.index("    val appSettingTemplates = combine(")
    first, second = (
        text.index("appSettingBlocked(userData = userData, key = it.key)"),
        text.rindex("appSettingBlocked(userData = userData, key = it.key)"),
    )

    if not at_rows < first < at_templates < second:
        print("REFUSED: the two reads are not one per flow")
        return 1

    was = {line for line in original.split("\n") if len(line) > 120}

    gained = [
        (n, len(line))
        for n, line in enumerate(text.split("\n"), 1)
        if len(line) > 120 and not line.lstrip().startswith("import ") and line not in was
    ]

    if gained:
        print(f"REFUSED: {VM} would gain lines over 120 chars: {gained}")
        return 1

    path.write_text(text, encoding="utf-8")

    print(f"  ok        {VM}")
    print("  ~ both flows ask appSettingBlocked; behaviour unchanged, greying still to come")
    print(f"\nwrote 1 file, {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
