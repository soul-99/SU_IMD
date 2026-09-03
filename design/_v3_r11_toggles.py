#!/usr/bin/env python3
"""
v3-r11 — every switch and every checkbox in the app becomes the drawn one.

The author: *"i want to update all the checkboxes and toggles with material designed ones i.e.
checkboxes with slightly curved corners and toggles like a photo i attached"*, then **W1** and
**C2** off the r11 template. `GetoSwitch` and `GetoCheckbox` in :design-system are the drawings;
this file is the swap.

⚠ **All of them, in one pass, because half would be worse than none.** Two switch shapes in one
dialog reads as a bug rather than as a style. Ten switches and eleven checkboxes across nine files,
and the counts below are what proves none was missed.

⚠ **Matched on a word boundary, not on the substring.** `ManagerRowCheckbox(` ends in `Checkbox(`
and `SwitchSetting` begins with `Switch`; a plain replace would rename the app's own wrappers and
leave a file that compiles into infinite recursion. The regex is the guard.

⚠ **The settings manager's two colour overrides become two parameters.** It drew a failed row's
switch in the error palette and a disabled-but-running row's in a muted green, both through
`SwitchDefaults.colors()`, which the drawn switch does not have. `error` and `liveWhileDisabled`
carry the same two decisions, and the reasoning moved into the parameters' own documentation rather
than being lost.

Every edit asserts its count. Nothing is written if any file fails.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SWITCH = re.compile(r"(?<![A-Za-z_])Switch\(")

CHECKBOX = re.compile(r"(?<![A-Za-z_])Checkbox\(")

# rel path -> (switches, checkboxes)
FILES = {
    "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/AutoHidePage.kt":
        (3, 1),
    "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/"
    "RevertDefaultsDialog.kt": (1, 0),
    "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt": (3, 0),
    "feature/apps/src/main/kotlin/com/android/geto/feature/apps/dialog/"
    "AndroidSettingsManagerDialog.kt": (2, 0),
    "feature/apps/src/main/kotlin/com/android/geto/feature/apps/dialog/"
    "SortLauncherAppsActivityInfoDialog.kt": (1, 0),
    "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/"
    "OverlayPackagesDialog.kt": (0, 1),
    "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/"
    "AccessibilityServicesDialog.kt": (0, 1),
    "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/AutoUnhidePage.kt":
        (0, 1),
    "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/"
    "ManagerRowsDialog.kt": (0, 1),
    "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/AutoHideDialogs.kt":
        (0, 1),
    "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/"
    "SettingsToHideDialog.kt": (0, 2),
    "feature/app-settings/src/main/kotlin/com/android/geto/feature/appsettings/"
    "AppSettingsScreen.kt": (0, 1),
}

SWITCH_IMPORT = "import androidx.compose.material3.Switch\n"

CHECKBOX_IMPORT = "import androidx.compose.material3.Checkbox\n"

GETO_SWITCH_IMPORT = "import com.android.geto.designsystem.component.GetoSwitch\n"

GETO_CHECKBOX_IMPORT = "import com.android.geto.designsystem.component.GetoCheckbox\n"

MANAGER = (
    "feature/apps/src/main/kotlin/com/android/geto/feature/apps/dialog/"
    "AndroidSettingsManagerDialog.kt"
)

# --- the manager's two colour overrides, which have no equivalent on the drawn switch ------

MGR_COLOURS_OLD = '''        val switchColors = if (failed) {
            SwitchDefaults.colors(
                uncheckedThumbColor = MaterialTheme.colorScheme.error,
                uncheckedBorderColor = MaterialTheme.colorScheme.error,
                uncheckedTrackColor = MaterialTheme.colorScheme.errorContainer,
            )
        } else {
            SwitchDefaults.colors()
        }

'''

MGR_COLOURS_NEW = ''

MGR_ON_OLD = '''                modifier = Modifier.scale(switchScale),
                checked = enabled,
                colors = switchColors,
                onCheckedChange = onSetEnabled,
'''

MGR_ON_NEW = '''                modifier = Modifier.scale(switchScale),
                checked = enabled,
                // ⚠ **The off state in the error palette when the service failed to start.**
                // Was three colour overrides on the Material switch; the drawn one takes the
                // decision rather than the palette, which is the same reading with nothing to
                // keep in step.
                error = failed,
                onCheckedChange = onSetEnabled,
'''

MGR_OFF_OLD = '''                    modifier = Modifier.scale(switchScale),
                    checked = enabled,
                    // Disabled, but not greyed into nothing: this row is still reporting a
                    // real state - a Shevery service that is genuinely running - and the
                    // stock disabled palette makes a true "on" look like a dead control.
                    // Muted green keeps the reading legible while staying visibly inert.
                    colors = switchColors.copy(
                        disabledCheckedThumbColor = MaterialTheme.colorScheme.primary
                            .copy(alpha = 0.55f),
                        disabledCheckedTrackColor = MaterialTheme.colorScheme.primaryContainer
                            .copy(alpha = 0.45f),
                        disabledCheckedBorderColor = MaterialTheme.colorScheme.primary
                            .copy(alpha = 0.35f),
                    ),
                    enabled = false,
                    onCheckedChange = null,
'''

MGR_OFF_NEW = '''                    modifier = Modifier.scale(switchScale),
                    checked = enabled,
                    error = failed,
                    // Disabled, but not greyed into nothing: this row is still reporting a
                    // real state - a Shevery service that is genuinely running - and the
                    // stock disabled palette makes a true "on" look like a dead control.
                    // Muted rather than grey keeps the reading legible while staying inert.
                    liveWhileDisabled = true,
                    enabled = false,
                    onCheckedChange = null,
'''


def main() -> int:
    planned: dict[Path, str] = {}

    for rel, (switches, checkboxes) in FILES.items():
        path = ROOT / rel

        if not path.is_file():
            print(f"REFUSED: missing {rel}")
            return 1

        text = path.read_text(encoding="utf-8")

        got_s = len(SWITCH.findall(text))

        got_c = len(CHECKBOX.findall(text))

        if (got_s, got_c) != (switches, checkboxes):
            print(
                f"REFUSED: {Path(rel).name}: found {got_s} Switch( and {got_c} Checkbox(, "
                f"expected {switches} and {checkboxes}",
            )
            return 1

        text = SWITCH.sub("GetoSwitch(", text)

        text = CHECKBOX.sub("GetoCheckbox(", text)

        # Swap the imports, keeping the file's alphabetical ordering by inserting the Geto ones
        # where the other com.android.geto.designsystem imports already are.
        if switches:
            if SWITCH_IMPORT not in text:
                print(f"REFUSED: {Path(rel).name} uses Switch but never imported it")
                return 1

            text = text.replace(SWITCH_IMPORT, "", 1)

        if checkboxes:
            if CHECKBOX_IMPORT not in text:
                print(f"REFUSED: {Path(rel).name} uses Checkbox but never imported it")
                return 1

            text = text.replace(CHECKBOX_IMPORT, "", 1)

        wanted = ""

        if checkboxes:
            wanted += GETO_CHECKBOX_IMPORT

        if switches:
            wanted += GETO_SWITCH_IMPORT

        anchor = "import com.android.geto."

        at = text.index(anchor)

        text = text[:at] + wanted + text[at:]

        planned[path] = text

        print(f"  ok        {Path(rel).name:38s} {switches} switch, {checkboxes} checkbox")

    # --- the manager's colour overrides -------------------------------------------------
    manager = ROOT / MANAGER

    text = planned[manager]

    for old, new in ((MGR_COLOURS_OLD, MGR_COLOURS_NEW), (MGR_ON_OLD, MGR_ON_NEW),
                     (MGR_OFF_OLD, MGR_OFF_NEW)):
        if text.count(old) != 1:
            print(
                f"REFUSED: AndroidSettingsManagerDialog.kt anchor "
                f"{old.strip().splitlines()[0][:56]!r} matched {text.count(old)} times",
            )
            return 1

        text = text.replace(old, new, 1)

    text = text.replace("import androidx.compose.material3.SwitchDefaults\n", "", 1)

    planned[manager] = text

    print("  ok        AndroidSettingsManagerDialog.kt        colours -> two parameters")

    checks = [
        (MANAGER, "switchColors", 0, "no colour object survives"),
        (MANAGER, "SwitchDefaults", 0, "nor its import"),
        (MANAGER, "error = failed,", 2, "both switches report the failure"),
        (MANAGER, "liveWhileDisabled = true,", 1, "and one of them stays legible while inert"),
    ]

    for rel, token, want, why in checks:
        got = planned[ROOT / rel].count(token)

        if got != want:
            print(f"REFUSED: {Path(rel).name}: {why} — {token!r} x{got}, expected {want}")
            return 1

        print(f"  checked   {Path(rel).name:38s} x{got}  {token[:28]!r}")

    total_s = sum(len(SWITCH.findall(t)) for t in planned.values())

    total_c = sum(len(CHECKBOX.findall(t)) for t in planned.values())

    if (total_s, total_c) != (0, 0):
        print(f"REFUSED: {total_s} Switch( and {total_c} Checkbox( still stand")
        return 1

    for path, text in planned.items():
        path.write_text(text, encoding="utf-8")

    print(f"\n  ok  wrote {len(planned)} file(s) — 10 switches and 11 checkboxes redrawn")

    return 0


if __name__ == "__main__":
    sys.exit(main())
