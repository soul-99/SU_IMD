#!/usr/bin/env python3
"""r3 — the two configuration dialogs grey their DOOA and accessibility rows, and say why.

Wires `ConfigureFirstDialog` into `SettingsToHideDialog` and `RevertDefaultsDialog`, which is
the author's spec item 8:

    "For both dialog boxes 'settings to hide/unhide' 'Revert to default dialog box' and 'IMD
     services manager' if no DOOAs and no Accessibility services set to be hidden (do not count
     IMD+ accessibility service) then disable the toggles and make them unclickable ... on
     clicking any of the greyed out toggles or templates display a popup 'Please configure the
     settings first (from next line)[display a location tree to the setting]"

* The **Display over other apps** row is drawn for everyone now, where it appeared only with
  the Manage DOOAs switch on, and is greyed when `overlayManageable` is false.
* The **accessibility services** row is greyed when nothing is selected to hide.
* A press on either lands rather than being swallowed, and raises the author's sentence with
  the location trees under it.

⚠ **One piece of state for both rows, and it carries the paths.** `blockedPaths` is null while
nothing is blocked, a list of paths for something that can be configured, and an **empty** list
for the one case with nothing to point at — Shevery, where Display over other apps is
unsupported rather than unconfigured. The empty list is what selects the author's fork sentence
instead of his configure-first one.

⚠ **`manageOverlay` is gone from both dialogs, replaced by `overlayBlockedPaths`.** A boolean
can say the row is unusable but not which of the three reasons applied, and the three are fixed
in three different places. `overlayBlockedPaths` on the screen decides once and hands the same
answer to both dialogs, so they cannot disagree about why the same row is grey.

⚠ **The `checked && shizukuConfigured` guard goes with it.** The row used to draw itself
unticked whenever Shizuku was unconfigured, which quietly disagreed with the stored map. Greyed
and honest is the shape every other unusable control in the app already uses.

⚠ **The control is wrapped in a `Box`, not merely disabled.** A disabled `Checkbox` or `Switch`
swallows the press inside its own bounds, so the row's own `clickable` never sees it — which is
exactly how somebody decides the app is broken rather than that they have something left to
configure. This is the settings manager's `TargetRow` pattern, brought to these two dialogs.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HIDE = ("feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/"
        "SettingsToHideDialog.kt")
REVERT = ("feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/"
          "RevertDefaultsDialog.kt")
SCREEN = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"

BLOCKED_PARAMS = """    /**
     * Why the Display over other apps row is greyed, or null while it is usable.
     *
     * A list rather than a boolean because that row has three ways to be unusable and each is
     * fixed somewhere different. An **empty** list is the Shevery case: unsupported rather
     * than unconfigured, so there is nothing to point at. See `overlayBlockedPaths` on the
     * settings screen, which is the single place that decides.
     */
    overlayBlockedPaths: List<String>?,
    /** Whether anything at all is selected under 'Accessibility services to hide'. */
    accessibilityManageable: Boolean,
"""

BLOCKED_STATE = """    // Null while nothing is blocked; a list of location trees for something that can be
    // configured; and empty for the one case with nothing to point at - Shevery, where
    // Display over other apps is unsupported rather than unconfigured. The empty list is what
    // picks the author's fork sentence over his configure-first one.
    var blockedPaths by remember { mutableStateOf<List<String>?>(null) }

    val accessibilityPath = stringResource(R.string.help_path_accessibility)

"""

BLOCKED_RENDER = """    blockedPaths?.let { paths ->
        ConfigureFirstDialog(
            message = if (paths.isEmpty()) {
                stringResource(R.string.dooa_thedjchi_only)
            } else {
                stringResource(R.string.configure_first)
            },
            paths = paths,
            dismissLabel = stringResource(R.string.understood),
            onDismissRequest = { blockedPaths = null },
        )
    }

"""

BLOCKED_PARAM_DOC = """    /**
     * What a press on a greyed row does.
     *
     * ⚠ **Without this a disabled control swallows the tap**, inside its own bounds, so the
     * row's own `clickable` never sees it - and a row that does nothing at all is how somebody
     * decides the app is broken rather than that they have something left to configure. The
     * settings manager's `TargetRow` has had this since r2b; the author asked for the same of
     * every greyed toggle in v3.
     */
    onBlockedClick: (() -> Unit)? = null,
"""

REASON_HELPER = '''
/**
 * Why a greyed Display over other apps row will not move, as the paths that put it right.
 *
 * ⚠ **The three terms of [overlayManageable], asked separately.** That property collapses them
 * into one boolean, which is the right answer to "may this run" and the wrong answer to "where
 * do I go" — the fix is somewhere different for each of the three.
 *
 * Null means the row is usable and there is nothing to explain. An **empty** list means
 * Shevery: there Display over other apps is not unconfigured but unsupported, so the caller
 * says so and offers no path rather than sending somebody to a picker that can never help.
 *
 * Decided once here and handed to both dialogs, so the two cannot disagree about why the same
 * row is grey.
 */
@Composable
private fun overlayBlockedPaths(userData: UserData): List<String>? {
    val manageShizukuPath = stringResource(R.string.help_path_manage_shizuku)

    val dooaPath = stringResource(R.string.help_path_dooa)

    if (userData.overlayManageable) return null

    if (userData.shizukuForkMode != ShizukuForkMode.Thedjchi) return emptyList()

    return buildList {
        if (!userData.manageShizukuEffective) add(manageShizukuPath)

        if (userData.managedOverlayPackages.isEmpty()) add(dooaPath)
    }
}
'''


def imports(module_extra: str) -> tuple[str, str, int]:
    return (
        """import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
""",
        """import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
""",
        1,
    )


EDITS: list[tuple[str, list[tuple[str, str, int]]]] = [
    (HIDE, [
        imports(HIDE),
        (
            """import com.android.geto.designsystem.component.DialogContainer
""",
            """import com.android.geto.designsystem.component.ConfigureFirstDialog
import com.android.geto.designsystem.component.DialogContainer
""",
            1,
        ),
        (
            """    shizukuConfigured: Boolean,
    manageOverlay: Boolean,
""",
            """    shizukuConfigured: Boolean,
""" + BLOCKED_PARAMS,
            1,
        ),
        (
            """    var showShizukuServiceNotice by rememberSaveable { mutableStateOf(false) }

""",
            """    var showShizukuServiceNotice by rememberSaveable { mutableStateOf(false) }

""" + BLOCKED_STATE,
            1,
        ),
        (
            """    if (showShizukuServiceNotice) {
""",
            BLOCKED_RENDER + """    if (showShizukuServiceNotice) {
""",
            1,
        ),
        (
            """            label = stringResource(R.string.revert_defaults_accessibility_services),
            note = stringResource(R.string.settings_to_hide_accessibility_note),
            checked = draft[ManualRevertTarget.AccessibilityServices] == true,
            onCheckedChange = { toggle(ManualRevertTarget.AccessibilityServices, it) },
        )
""",
            """            label = stringResource(R.string.revert_defaults_accessibility_services),
            note = stringResource(R.string.settings_to_hide_accessibility_note),
            checked = draft[ManualRevertTarget.AccessibilityServices] == true,
            // ⚠ **Dead with nothing selected**, on the author's instruction. IMD+'s own
            // detector is not in that selection and never was - it is held under
            // AUTO_HIDE_HOLD - which is what makes his "do not count IMD+ accessibility
            // service" true by construction, and why it is still hidden before every launch
            // whatever this row says.
            enabled = accessibilityManageable,
            onBlockedClick = { blockedPaths = listOf(accessibilityPath) },
            onCheckedChange = { toggle(ManualRevertTarget.AccessibilityServices, it) },
        )
""",
            1,
        ),
        (
            """        // Only once overlay management has been switched on in Advanced. Off is the
        // default, and on a device with no working Shizuku it is the only honest state -
        // a row that can only ever fail is worse than no row, and greying it out here
        // would say "configure Shizuku" to someone who has decided not to use the feature
        // at all.
        if (manageOverlay) {
            SettingToHideRow(
                label = stringResource(R.string.revert_defaults_display_over_other_apps),
                note = if (shizukuConfigured) {
                    stringResource(R.string.settings_to_hide_overlay_note)
                } else {
                    stringResource(R.string.overlay_needs_shizuku_configured)
                },
                checked = draft[ManualRevertTarget.DisplayOverOtherApps] == true &&
                    shizukuConfigured,
                // Overlay AppOps can only be written through Shizuku. Letting this be
                // ticked with no Shizuku configured buys the user a launch that fails ten
                // seconds later for a reason the dialog already knew about.
                enabled = shizukuConfigured,
                onCheckedChange = { toggle(ManualRevertTarget.DisplayOverOtherApps, it) },
            )
        }
""",
            """        // ⚠ **Drawn for everyone since v3.** It used to appear only with the Manage DOOAs
        // switch on; the author removed that switch and asked for these toggles to be shown
        // to everybody and greyed when they cannot work. A press says which of the three
        // things `overlayManageable` asks about is missing, and where to go and fix it.
        SettingToHideRow(
            label = stringResource(R.string.revert_defaults_display_over_other_apps),
            note = if (shizukuConfigured) {
                stringResource(R.string.settings_to_hide_overlay_note)
            } else {
                stringResource(R.string.overlay_needs_shizuku_configured)
            },
            // The stored answer, not the stored answer masked by whether it can run. The row
            // used to draw itself unticked with Shizuku unconfigured, which disagreed with
            // the map underneath it - greyed and honest is what every other unusable control
            // in the app does.
            checked = draft[ManualRevertTarget.DisplayOverOtherApps] == true,
            enabled = overlayBlockedPaths == null,
            onBlockedClick = { blockedPaths = overlayBlockedPaths.orEmpty() },
            onCheckedChange = { toggle(ManualRevertTarget.DisplayOverOtherApps, it) },
        )
""",
            1,
        ),
        (
            """private fun SettingToHideRow(
    modifier: Modifier = Modifier,
    label: String,
    note: String? = null,
    checked: Boolean,
    enabled: Boolean = true,
    onCheckedChange: (Boolean) -> Unit,
) {
""",
            """private fun SettingToHideRow(
    modifier: Modifier = Modifier,
    label: String,
    note: String? = null,
    checked: Boolean,
    enabled: Boolean = true,
""" + BLOCKED_PARAM_DOC + """    onCheckedChange: (Boolean) -> Unit,
) {
""",
            1,
        ),
        (
            """            .clickable(enabled = enabled) { onCheckedChange(!checked) }
            .padding(horizontal = 10.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = label,
                style = MaterialTheme.typography.bodyLarge,
                color = contentColour,
            )

            if (note != null) {
                Spacer(modifier = Modifier.height(4.dp))

                Text(
                    text = note,
                    style = MaterialTheme.typography.bodySmall,
                    color = contentColour,
                )
            }
        }

        Checkbox(checked = checked, enabled = enabled, onCheckedChange = onCheckedChange)
    }
}
""",
            """            .clickable(enabled = enabled || onBlockedClick != null) {
                if (enabled) onCheckedChange(!checked) else onBlockedClick?.invoke()
            }
            .padding(horizontal = 10.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = label,
                style = MaterialTheme.typography.bodyLarge,
                color = contentColour,
            )

            if (note != null) {
                Spacer(modifier = Modifier.height(4.dp))

                Text(
                    text = note,
                    style = MaterialTheme.typography.bodySmall,
                    color = contentColour,
                )
            }
        }

        // ⚠ **Wrapped, because a disabled Checkbox swallows the press inside its own bounds**
        // and the row's clickable above never sees it. Half a greyed row explaining itself and
        // the other half doing nothing is worse than neither.
        Box(
            modifier = Modifier.clickable(enabled = !enabled && onBlockedClick != null) {
                onBlockedClick?.invoke()
            },
        ) {
            Checkbox(
                checked = checked,
                enabled = enabled,
                onCheckedChange = if (enabled) onCheckedChange else null,
            )
        }
    }
}
""",
            1,
        ),
    ]),
    (REVERT, [
        imports(REVERT),
        (
            """import com.android.geto.designsystem.component.DialogContainer
""",
            """import com.android.geto.designsystem.component.ConfigureFirstDialog
import com.android.geto.designsystem.component.DialogContainer
""",
            1,
        ),
        (
            """    shizukuConfigured: Boolean,
    manageOverlay: Boolean,
""",
            """    shizukuConfigured: Boolean,
""" + BLOCKED_PARAMS,
            1,
        ),
        (
            """    var showWirelessNotice by rememberSaveable { mutableStateOf(false) }

""",
            """    var showWirelessNotice by rememberSaveable { mutableStateOf(false) }

""" + BLOCKED_STATE,
            1,
        ),
        (
            """    if (showWirelessNotice) {
""",
            BLOCKED_RENDER + """    if (showWirelessNotice) {
""",
            1,
        ),
        (
            """        RevertDefaultRow(
            label = stringResource(R.string.revert_defaults_accessibility_services),
            note = stringResource(R.string.revert_defaults_accessibility_note),
            checked = draft[ManualRevertTarget.AccessibilityServices] == true,
            onCheckedChange = { toggle(ManualRevertTarget.AccessibilityServices, it) },
        )
""",
            """        RevertDefaultRow(
            label = stringResource(R.string.revert_defaults_accessibility_services),
            note = stringResource(R.string.revert_defaults_accessibility_note),
            checked = draft[ManualRevertTarget.AccessibilityServices] == true,
            // Dead with nothing selected, exactly as in Settings to hide/unhide - see the
            // matching row there for why IMD+'s own detector is not part of this question.
            enabled = accessibilityManageable,
            onBlockedClick = { blockedPaths = listOf(accessibilityPath) },
            onCheckedChange = { toggle(ManualRevertTarget.AccessibilityServices, it) },
        )
""",
            1,
        ),
        (
            """        // Shown only once overlay management has been switched on in Advanced. Hiding the
        // row does not abandon anything already hidden: a revert still hands overlay access
        // back to apps IMD took it from, whatever this switch says - see
        // UserData.effectiveRevertDefaults.
        if (manageOverlay) {
            RevertDefaultRow(
                label = stringResource(R.string.revert_defaults_display_over_other_apps),
                note = if (shizukuConfigured) {
                    stringResource(R.string.revert_defaults_overlay_note)
                } else {
                    stringResource(R.string.overlay_needs_shizuku_configured)
                },
                checked = draft[ManualRevertTarget.DisplayOverOtherApps] == true &&
                    shizukuConfigured,
                enabled = shizukuConfigured,
                onCheckedChange = { toggle(ManualRevertTarget.DisplayOverOtherApps, it) },
            )
        }
""",
            """        // ⚠ **Drawn for everyone since v3**, and greyed rather than hidden when it cannot
        // work. Greying it does not abandon anything already hidden: a revert still hands
        // overlay access back to apps IMD took it from, whatever this row says - see
        // UserData.effectiveRevertDefaults.
        RevertDefaultRow(
            label = stringResource(R.string.revert_defaults_display_over_other_apps),
            note = if (shizukuConfigured) {
                stringResource(R.string.revert_defaults_overlay_note)
            } else {
                stringResource(R.string.overlay_needs_shizuku_configured)
            },
            checked = draft[ManualRevertTarget.DisplayOverOtherApps] == true,
            enabled = overlayBlockedPaths == null,
            onBlockedClick = { blockedPaths = overlayBlockedPaths.orEmpty() },
            onCheckedChange = { toggle(ManualRevertTarget.DisplayOverOtherApps, it) },
        )
""",
            1,
        ),
        (
            """private fun RevertDefaultRow(
    modifier: Modifier = Modifier,
    label: String,
    note: String? = null,
    checked: Boolean,
    enabled: Boolean = true,
    onCheckedChange: (Boolean) -> Unit,
) {
""",
            """private fun RevertDefaultRow(
    modifier: Modifier = Modifier,
    label: String,
    note: String? = null,
    checked: Boolean,
    enabled: Boolean = true,
""" + BLOCKED_PARAM_DOC + """    onCheckedChange: (Boolean) -> Unit,
) {
""",
            1,
        ),
        (
            """            .clickable(enabled = enabled) { onCheckedChange(!checked) }
            .padding(horizontal = 10.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = label,
                style = MaterialTheme.typography.bodyLarge,
                color = contentColour,
            )

            if (note != null) {
                Spacer(modifier = Modifier.height(4.dp))

                Text(
                    text = note,
                    style = MaterialTheme.typography.bodySmall,
                    color = contentColour,
                )
            }
        }

        Switch(checked = checked, enabled = enabled, onCheckedChange = onCheckedChange)
    }
}
""",
            """            .clickable(enabled = enabled || onBlockedClick != null) {
                if (enabled) onCheckedChange(!checked) else onBlockedClick?.invoke()
            }
            .padding(horizontal = 10.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = label,
                style = MaterialTheme.typography.bodyLarge,
                color = contentColour,
            )

            if (note != null) {
                Spacer(modifier = Modifier.height(4.dp))

                Text(
                    text = note,
                    style = MaterialTheme.typography.bodySmall,
                    color = contentColour,
                )
            }
        }

        // Wrapped for the same reason the checkbox in Settings to hide/unhide is: a disabled
        // Switch swallows the press inside its own bounds.
        Box(
            modifier = Modifier.clickable(enabled = !enabled && onBlockedClick != null) {
                onBlockedClick?.invoke()
            },
        ) {
            Switch(
                checked = checked,
                enabled = enabled,
                onCheckedChange = if (enabled) onCheckedChange else null,
            )
        }
    }
}
""",
            1,
        ),
    ]),
    (SCREEN, [
        (
            """        RevertDefaultsDialog(
            states = userData.revertDefaults,
            shizukuConfigured = userData.isShizukuConfigured,
            manageOverlay = userData.overlayManageable,
""",
            """        RevertDefaultsDialog(
            states = userData.revertDefaults,
            shizukuConfigured = userData.isShizukuConfigured,
            overlayBlockedPaths = overlayBlockedPaths(userData = userData),
            accessibilityManageable = userData.accessibilityManageable,
""",
            1,
        ),
        (
            """        SettingsToHideDialog(
            states = userData.settingsToHide,
            shizukuConfigured = userData.isShizukuConfigured,
            manageOverlay = userData.overlayManageable,
""",
            """        SettingsToHideDialog(
            states = userData.settingsToHide,
            shizukuConfigured = userData.isShizukuConfigured,
            overlayBlockedPaths = overlayBlockedPaths(userData = userData),
            accessibilityManageable = userData.accessibilityManageable,
""",
            1,
        ),
        (
            """import com.android.geto.domain.model.overlayManageable
""",
            """import com.android.geto.domain.model.overlayManageable
""",
            0,
        ),
    ]),
]

SCREEN_IMPORTS = [
    ("import com.android.geto.domain.model.manageShizukuEffective\n",
     "import com.android.geto.domain.model.isShizukuConfigured\n"),
    ("import com.android.geto.domain.model.overlayManageable\n",
     "import com.android.geto.domain.model.isShizukuConfigured\n"),
    ("import com.android.geto.domain.model.accessibilityManageable\n",
     "import com.android.geto.domain.model.isShizukuConfigured\n"),
]


def main() -> int:
    staged: dict[Path, str] = {}
    problems: list[str] = []

    for rel, subs in EDITS:
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

            if expected:
                text = text.replace(old, new, expected)

        staged[path] = text

    # The three domain reads the screen now makes, each imported beside the one it sits with.
    screen = staged.get(ROOT / SCREEN, "")

    for wanted, anchor in SCREEN_IMPORTS:
        if wanted in screen:
            continue

        if screen.count(anchor) != 1:
            problems.append(f"{SCREEN}: no single anchor for {wanted.strip()[:52]!r}")

            continue

        screen = screen.replace(anchor, anchor + wanted, 1)

    # And the chooser itself, at the end of the file beside the other private helpers.
    if "private fun overlayBlockedPaths(" in screen:
        problems.append(f"{SCREEN}: overlayBlockedPaths is already there")
    else:
        screen = screen.rstrip("\n") + "\n" + REASON_HELPER

    staged[ROOT / SCREEN] = screen

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    # Neither dialog may still take the parameter this replaces, and the new one must be read.
    for rel in (HIDE, REVERT):
        text = staged.get(ROOT / rel, "")

        if "manageOverlay" in text:
            problems.append(f"{rel}: still takes manageOverlay")

        if text.count("onBlockedClick = { blockedPaths =") != 2:
            problems.append(f"{rel}: expected two rows to raise the explainer")

        if text.count("ConfigureFirstDialog(") != 1:
            problems.append(f"{rel}: the explainer is not rendered exactly once")

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

    print("ok - both dialogs grey their DOOA and accessibility rows and say why")

    return 0


if __name__ == "__main__":
    sys.exit(main())
