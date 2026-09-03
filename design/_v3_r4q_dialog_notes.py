#!/usr/bin/env python3
"""v3-r4q — the author's own wording under the toggles, and nothing else.

    "in rever to def config dialogue, under all 3 toggles remove descriptions and put 'Only apps
     selected in IMD settings' under DOOA and access. serv. toggles"
    "in settings to hide dialog also remove all descriptions below toggles put these: ..."
    "In dooa to manage dialog description lines update first line '1. Might add slight delay in
     hiding-unhiding process'"

Every replacement string below is his, verbatim, between his own quotes.

## ⚠ `shizukuConfigured` leaves both dialogs, because nothing else was using it

Both dialogs took the flag for exactly one thing: choosing between the overlay note and
*"Shizuku must be configured properly in IMD settings before this can be used"*. His new note has
no such branch, so the parameter is dead the moment the branch goes - and a parameter that is
passed, documented and never read is the kind of thing that survives three rounds because nobody
notices. It is removed here, with both call sites.

⚠ **Nothing is lost by dropping the fallback sentence.** The row is still greyed when Shizuku is
not configured and still raises a `BlockedExplanation` naming the path to fix it - that is
`overlayBlockedPaths`, which is a different parameter and is untouched.

## ⚠ The third DOOA line was already exactly what he asked for

    "third line '3. Only enabled ones are shown below'"

`overlay_packages_dialog_description` already reads *"2. Uses Shizuku to turn Display over other
apps on/off.\\n3. Only enabled ones are shown below"*. The third line is his sentence, character
for character, so this script asserts that and changes nothing there rather than rewriting a
string into itself.

## Translations

Every key here already exists and keeps its name, so `check_translations` stays quiet - it checks
presence and format specifiers, not whether a translation still says the same thing. The locales
now hold the old wording and will be caught by the single translation pass, which is the author's
standing rule.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STRINGS = "feature/settings/src/main/res/values/strings.xml"

HIDE = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/SettingsToHideDialog.kt"

REVERT = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/RevertDefaultsDialog.kt"

SCREEN = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"

# His sentences, verbatim.
ONLY_APPS = "Only apps selected in IMD settings"

EDITS: list[tuple[str, str, str]] = [
    # ---------------- the strings ----------------
    (
        STRINGS,
        """    <string name="settings_to_hide_usb_note">stopping USB debugging will also kill Shizuku service(if running), please configure Shizuku settings under IMD app to restart the Shizuku service after Revert</string>""",
        """    <string name="settings_to_hide_usb_note">stopping USB debugging will kill Shizuku service, so it is advised to also tick Shizuku service here if you use it</string>""",
    ),
    (
        STRINGS,
        """    <string name="settings_to_hide_accessibility_note">Only services selected in IMD settings are managed</string>""",
        f"""    <string name="settings_to_hide_accessibility_note">{ONLY_APPS}</string>""",
    ),
    (
        STRINGS,
        """    <string name="settings_to_hide_shizuku_note">ensure Shizuku is properly configured under IMD settings(uses stop intent), helps avoid watchdog error</string>""",
        """    <string name="settings_to_hide_shizuku_note">ensure Shizuku values are properly configured in IMD settings</string>""",
    ),
    (
        STRINGS,
        """    <string name="settings_to_hide_overlay_note">Shizuku must be configured properly in IMD settings\\nOnly apps selected in IMD settings are managed</string>""",
        f"""    <string name="settings_to_hide_overlay_note">{ONLY_APPS}\\nneeds Shizuku service to function</string>""",
    ),
    (
        STRINGS,
        """    <string name="revert_defaults_accessibility_note">Only apps selected in IMD settings are turned on again if turned off by IMD</string>""",
        f"""    <string name="revert_defaults_accessibility_note">{ONLY_APPS}</string>""",
    ),
    (
        STRINGS,
        """    <string name="revert_defaults_overlay_note">Shizuku must be configured properly in IMD settings\\nOnly apps selected in IMD settings are turned on again if turned off by IMD</string>""",
        f"""    <string name="revert_defaults_overlay_note">{ONLY_APPS}</string>""",
    ),
    (
        STRINGS,
        """    <string name="overlay_packages_dialog_delay">1. Will add slight delay to hiding time</string>""",
        """    <string name="overlay_packages_dialog_delay">1. Might add slight delay in hiding-unhiding process</string>""",
    ),
    # ---------------- Settings to hide: the overlay note stops branching ----------------
    (
        HIDE,
        """            note = if (shizukuConfigured) {
                stringResource(R.string.settings_to_hide_overlay_note)
            } else {
                stringResource(R.string.overlay_needs_shizuku_configured)
            },""",
        """            // ⚠ **One note now, not two.** It used to swap for "Shizuku must be
            // configured properly in IMD settings before this can be used" - the author's
            // replacement says what the row is for rather than what is wrong with it, and the
            // row is still greyed with a BlockedExplanation naming the path when Shizuku is
            // not configured, which is where that sentence belonged all along.
            note = stringResource(R.string.settings_to_hide_overlay_note),""",
    ),
    (
        HIDE,
        """    states: Map<ManualRevertTarget, Boolean>,
    shizukuConfigured: Boolean,""",
        """    states: Map<ManualRevertTarget, Boolean>,""",
    ),
    # ---------------- Revert defaults: the same, plus the Shizuku row loses its note ----
    (
        REVERT,
        """            note = if (shizukuConfigured) {
                stringResource(R.string.revert_defaults_overlay_note)
            } else {
                stringResource(R.string.overlay_needs_shizuku_configured)
            },""",
        """            // One note now - see the same row in SettingsToHideDialog.
            note = stringResource(R.string.revert_defaults_overlay_note),""",
    ),
    (
        REVERT,
        """            label = stringResource(R.string.revert_defaults_shizuku),
            note = stringResource(R.string.revert_defaults_shizuku_note),""",
        """            label = stringResource(R.string.revert_defaults_shizuku),
            // ⚠ **No note, at the author's instruction.** "Depending on which method Shizuku
            // uses to keep service alive, it will enable/disable USB or wireless debugging" was
            // the only one of the three he did not replace, so it goes. Its string is kept
            // rather than deleted: removing an English entry that eleven locales still carry is
            // what check_translations reports as eleven invented names.""",
    ),
    (
        REVERT,
        """    states: Map<ManualRevertTarget, Boolean>,
    shizukuConfigured: Boolean,""",
        """    states: Map<ManualRevertTarget, Boolean>,""",
    ),
    # ---------------- and both call sites ----------------
    (
        SCREEN,
        """        RevertDefaultsDialog(
            states = userData.revertDefaults,
            shizukuConfigured = userData.isShizukuConfigured,""",
        """        RevertDefaultsDialog(
            states = userData.revertDefaults,""",
    ),
    (
        SCREEN,
        """        SettingsToHideDialog(
            states = userData.settingsToHide,
            shizukuConfigured = userData.isShizukuConfigured,""",
        """        SettingsToHideDialog(
            states = userData.settingsToHide,""",
    ),
]

# ⚠ Asserted, not rewritten: his third DOOA line is already exactly this.
ALREADY = (
    STRINGS,
    """3. Only enabled ones are shown below</string>""",
)

AFTER = [
    (HIDE, "shizukuConfigured", 0),
    (REVERT, "shizukuConfigured", 0),
    (HIDE, "overlay_needs_shizuku_configured", 0),
    (REVERT, "overlay_needs_shizuku_configured", 0),
    # Gone from the dialog, kept in the resources - see the comment left in its place. The
    # first draft asserted 1 against the Kotlin file when it meant the string file.
    (REVERT, "revert_defaults_shizuku_note", 0),
    (STRINGS, 'name="revert_defaults_shizuku_note"', 1),
    # ⚠ One each. `shizukuConfigured` is still a parameter of the two Shizuku *section*
    # helpers in SettingsScreen and must not have been caught by this.
    (SCREEN, "shizukuConfigured = userData.isShizukuConfigured,", 0),
    (SCREEN, ONLY_APPS, 0),
    (STRINGS, ONLY_APPS, 4),
]


def main() -> int:
    staged: dict[str, str] = {}

    for relative, old, new in EDITS:
        path = ROOT / relative

        if not path.is_file():
            print(f"REFUSED: missing {relative}")
            return 1

        text = staged.get(relative, path.read_text(encoding="utf-8"))

        found = text.count(old)

        if found != 1:
            head = old.strip().splitlines()[0][:70]

            print(f"REFUSED: {relative}\n  {head!r} matched {found} time(s), expected 1")
            return 1

        staged[relative] = text.replace(old, new, 1)

    relative, sentence = ALREADY

    if staged[relative].count(sentence) != 1:
        print(
            f"REFUSED: {relative}\n  the third DOOA line is not {sentence!r}; the author's "
            f"instruction assumed it already was",
        )
        return 1

    for relative, token, expected in AFTER:
        found = staged[relative].count(token)

        if found != expected:
            print(
                f"REFUSED: {relative}\n  {token!r} occurs {found} time(s) after the edits, "
                f"expected {expected}",
            )
            return 1

    for relative, text in staged.items():
        (ROOT / relative).write_text(text, encoding="utf-8")

    print(f"  ok        {STRINGS}  :: seven strings replaced with the author's own")
    print(f"  ok        {HIDE}  :: four notes, no branch, no shizukuConfigured")
    print(f"  ok        {REVERT}  :: two notes, Shizuku row unlabelled")
    print(f"  ok        {SCREEN}  :: both call sites narrowed")
    print("  ok        the third DOOA line already read as asked; left alone")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
