#!/usr/bin/env python3
"""
v3-r4z — the settings screen forgets which section was open.

Expand a section on the Settings tab, go to another tab, come back: it is collapsed again.
The author's report.

`expanded` was a plain `remember`, and the tab host tears this screen down the moment another
tab is selected. The bar navigates with `saveState`/`restoreState` — see `navigateToSettings`
and its two siblings — which is exactly the arrangement that keeps a *saveable* alive across
that round trip, and is what every `rememberSaveable` dialog flag already on this screen
relies on. So the state moves to `rememberSaveable`.

⚠ It is held as an **ordinal**, not as the enum: a nullable enum is not a saveable type, and
`-1` for "all closed" plus `getOrNull` on the way out means a stale index can only ever come
back as closed rather than as the wrong section.

⚠ The Advanced request has to become an **effect**. r4y read it into the initial value, which
worked only because the initial value was recomputed on every visit; now that it is not, a
request arriving at a screen whose saved state already exists would never be seen. The
high-water mark is what keeps the effect from fighting the accordion — the same mark
HomeScreen already keeps for these same two requests.

Every edit asserts its anchor matches exactly once. Nothing is written if any file fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCREEN = (
    "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"
)

# --- 1. the state itself -------------------------------------------------------------

OLD_STATE = '''    // Plain remember, not rememberSaveable: the sections reset on every visit so the screen
    // always opens the same way rather than in whatever state it was left in last week.
    // Same reasoning as the Shizuku configuration panel.
    //
    // Opens on Default IMD settings rather than on nothing. The two configurations in there
    // are what decides whether launching an app does anything at all, so a screen that
    // opens as five closed headings hides the only part most people ever need. Opening
    // another section closes this one, as before — it is still an accordion.
    // Advanced instead when the app was re-launched to come back here, which is the one
    // thing that asks for a section by name. Read into the initial value rather than pushed
    // in by an effect: this screen is composed fresh after that re-launch, so the request is
    // already in hand, and an effect would fight the accordion the moment anyone opened
    // another section.
    var expanded by remember {
        mutableStateOf<SettingsSection?>(
            if (advancedSettingsRequest > 0) {
                SettingsSection.Advanced
            } else {
                SettingsSection.AppFunctions
            },
        )
    }

    val toggleSection = { section: SettingsSection ->
        expanded = if (expanded == section) null else section
    }
'''

NEW_STATE = '''    // ⚠ **Saveable, not a plain remember — r4z, and this is the author's report.** Expand a
    // section, switch tab, come back: it was collapsed again. The tab host tears this screen
    // down the moment another tab is selected and composes it afresh on the way back, so a
    // plain `remember` cannot survive the trip. The bar navigates with `saveState` and
    // `restoreState` — see `navigateToSettings` and its two siblings — which is what keeps a
    // *saveable* alive across it, and is what every `rememberSaveable` dialog flag above
    // already relies on. A fresh launch still opens the screen the way it always did; only
    // the trip to another tab and back is remembered.
    //
    // ⚠ **An ordinal because a nullable enum is not a saveable type.** [SECTION_NONE] is all
    // closed, and reading it back through `getOrNull` means a stale index can only ever come
    // back as closed rather than as the wrong section.
    //
    // Opens on Default IMD settings rather than on nothing. The two configurations in there
    // are what decides whether launching an app does anything at all, so a screen that
    // opens as five closed headings hides the only part most people ever need. Opening
    // another section closes this one, as before — it is still an accordion.
    var expandedOrdinal by rememberSaveable {
        mutableIntStateOf(SettingsSection.AppFunctions.ordinal)
    }

    val expanded = SettingsSection.entries.getOrNull(expandedOrdinal)

    // Advanced instead when the app was re-launched to come back here, which is the one
    // thing that asks for a section by name.
    //
    // ⚠ **An effect now, and it has to be one.** r4y read the request into the initial value,
    // which worked only because that initial value was recomputed on every single visit. It
    // is not any more — that is the whole point of the change above — so a request arriving
    // at a screen whose saved state already exists would never be seen.
    //
    // The high-water mark is what stops it fighting the accordion, and it is the same mark
    // HomeScreen keeps for these same two requests: this expands Advanced once per re-launch
    // and then leaves the sections to whoever is pressing them.
    var handledAdvancedRequest by rememberSaveable { mutableIntStateOf(0) }

    LaunchedEffect(advancedSettingsRequest) {
        if (advancedSettingsRequest > handledAdvancedRequest) {
            handledAdvancedRequest = advancedSettingsRequest

            expandedOrdinal = SettingsSection.Advanced.ordinal
        }
    }

    val toggleSection = { section: SettingsSection ->
        expandedOrdinal = if (expandedOrdinal == section.ordinal) {
            SECTION_NONE
        } else {
            section.ordinal
        }
    }
'''

# --- 2. the sentinel, beside the enum it stands outside of ---------------------------

OLD_ENUM = '''private enum class SettingsSection {
    Ui,
'''

NEW_ENUM = '''/**
 * The stored value for "no section is open".
 *
 * The open section is saved as an ordinal rather than as the enum — a nullable enum is not a
 * saveable type — so the closed state needs an index no member can have. Any negative number
 * would do; -1 is the one `getOrNull` already answers `null` for.
 */
private const val SECTION_NONE = -1

private enum class SettingsSection {
    Ui,
'''

# (path, old, new)
EDITS = [
    (SCREEN, OLD_STATE, NEW_STATE),
    (SCREEN, OLD_ENUM, NEW_ENUM),
]


def main() -> int:
    planned: dict[Path, str] = {}

    report: list[str] = []

    for rel, old, new in EDITS:
        path = ROOT / rel

        if not path.is_file():
            print(f"REFUSED: missing {rel}")
            return 1

        text = planned.get(path, path.read_text(encoding="utf-8"))

        found = text.count(old)

        if found != 1:
            print(
                f"REFUSED: {rel}\n  anchor {old[:60]!r}\n"
                f"  matched {found} time(s), expected exactly 1",
            )
            return 1

        if new in text:
            print(f"REFUSED: {rel} already carries the replacement — has this run before?")
            return 1

        planned[path] = text.replace(old, new, 1)

        report.append(f"  ok        {rel}  :: {old.strip().splitlines()[0][:52]}")

    # --- post-conditions, computed on the planned text, before anything is written ----
    #
    # ⚠ Spelled the way only the statement meant can be spelled. `expanded ==` would match
    # inside the five section reads that must survive untouched, and `expanded` on its own
    # matches inside `expandedOrdinal`.
    text = planned[ROOT / SCREEN]

    checks = [
        # ⚠ NOT "var expanded by remember {" — the app-picker further down this file has a
        # boolean of that exact spelling and it is none of this script's business.
        ("mutableStateOf<SettingsSection?>(", 0, "the old nullable enum state is gone"),
        ("expanded = if (expanded == section) null else section", 0, "old toggle is gone"),
        ("var expandedOrdinal by rememberSaveable {", 1, "the saveable state is in"),
        ("val expanded = SettingsSection.entries.getOrNull(expandedOrdinal)", 1, "read-back"),
        ("var handledAdvancedRequest by rememberSaveable", 1, "the high-water mark is in"),
        ("private const val SECTION_NONE = -1", 1, "the sentinel is declared"),
        # Declaration, the KDoc reference above it, and the one use in the toggle.
        ("SECTION_NONE", 3, "the sentinel is declared, referenced and used"),
        # The five section reads are what the whole screen hangs on and no edit here goes
        # near them; if one were disturbed a section would silently stop opening.
        ("expanded == SettingsSection.", 5, "all five section reads survive"),
    ]

    for token, want, why in checks:
        got = text.count(token)

        if got != want:
            print(f"REFUSED: {why} — {token!r} appears {got} time(s), expected {want}")
            return 1

        report.append(f"  checked   {token[:56]!r} × {got}")

    # ⚠ **Against what the file already carried, not against zero.** SettingsScreen.kt has one
    # 127-character line of its own (`labelOf`), which is none of this script's doing and none
    # of its business; a flat "no line over 120" guard refuses on it and so can never pass.
    # What is checked is that this script adds no new one.
    for path, planned_text in planned.items():
        def over(text: str) -> set[str]:
            return {
                line
                for line in text.split("\n")
                if len(line) > 120 and not line.lstrip().startswith("import ")
            }

        added = over(planned_text) - over(path.read_text(encoding="utf-8"))

        if added:
            print(
                f"REFUSED: {path.relative_to(ROOT)} would gain lines over 120 chars: "
                f"{sorted(len(line) for line in added)}",
            )
            return 1

    for path, planned_text in planned.items():
        path.write_text(planned_text, encoding="utf-8")

    print("\n".join(report))

    print(f"\nwrote {len(planned)} file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
