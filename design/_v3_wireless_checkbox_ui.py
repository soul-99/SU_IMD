#!/usr/bin/env python3
"""
v3 — the 'Restore wireless debugging also' checkbox, and the two popups it splits from.

Three files, one behaviour, two different sentences.

**The checkbox** goes under the Wireless debugging row in Settings to hide/unhide, indented
with an elbow drawn back to its parent (the author picked template E). It is drawn **only
under the memory unhiding framework**: under Revert to default the destination for wireless
debugging is that dialog's own switch, and asking the same question in two places is how a
setting ends up with two answers.

⚠ **It is never greyed out, and that is the author's instruction rather than an oversight.**
A nested checkbox normally follows its parent, and this one does not, because it has a second
job that has nothing to do with the parent: the settings manager's `All on` reads it under
*both* frameworks and whether or not Wireless debugging is ticked for hiding. Disabling it
when the parent is unticked would make the manager's button follow a control the user cannot
reach.

⚠ **It is saved with the dialog, not written on the tick.** Everything else in this dialog is
a draft that Save commits, and a checkbox that wrote through immediately would be the one
control here that a Back press could not undo.

**The two popups are different, and the difference is the point.** The checkbox raises the
author's two-point notice. The Revert to default configuration dialog's Wireless debugging
*switch* raises the one-liner instead, because point 1 of the two-point notice — "IMD only
hides wireless debugging and does not restore it on unhiding" — is false in that dialog: that
switch is precisely what restores it. Confirmed with the author before building.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HIDE_DIALOG = ("feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/"
               "SettingsToHideDialog.kt")
REVERT_DIALOG = ("feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/"
                 "RevertDefaultsDialog.kt")
SCREEN = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"
VIEW_MODEL = ("feature/settings/src/main/kotlin/com/android/geto/feature/settings/"
              "SettingsViewModel.kt")

EDITS: list[tuple[str, list[tuple[str, str, int]]]] = [
    (HIDE_DIALOG, [
        # imports for the elbow and the new checkbox row
        (
            """import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
""",
            """import androidx.compose.foundation.Canvas
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
""",
            1,
        ),
        (
            """import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
""",
            """import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
""",
            1,
        ),
        # the two new parameters
        (
            """    hidingFramework: HidingFramework,
    unhidingFramework: UnhidingFramework,
    onDismissRequest: () -> Unit,
    onUpdateSettingsToHide: (Map<ManualRevertTarget, Boolean>) -> Unit,
) {""",
            """    hidingFramework: HidingFramework,
    unhidingFramework: UnhidingFramework,
    /**
     * Whether a memory restore may switch wireless debugging back on.
     *
     * Drawn as a nested checkbox under the Wireless debugging row, and only under
     * [UnhidingFramework.Memory] — see the file's own note on why the other framework asks
     * its question somewhere else.
     */
    restoreWirelessDebugging: Boolean,
    onDismissRequest: () -> Unit,
    onUpdateSettingsToHide: (Map<ManualRevertTarget, Boolean>) -> Unit,
    onUpdateRestoreWirelessDebugging: (Boolean) -> Unit,
) {""",
            1,
        ),
        # draft state for the checkbox, beside the map's
        (
            """    // Raised when the Shizuku row is ticked - see the row itself for why the warning cannot
    // wait until the hide fails.
    var showShizukuServiceNotice by rememberSaveable { mutableStateOf(false) }
""",
            """    // Drafted like the map above rather than written on the tick, so Save commits every
    // answer in this dialog and a Back press abandons all of them together.
    var restoreWirelessDraft by remember(restoreWirelessDebugging) {
        mutableStateOf(restoreWirelessDebugging)
    }

    // Raised when the Shizuku row is ticked - see the row itself for why the warning cannot
    // wait until the hide fails.
    var showShizukuServiceNotice by rememberSaveable { mutableStateOf(false) }

    // Raised when the nested restore checkbox is ticked. The author's two points, and not the
    // one-liner the Revert to default dialog uses - see RestoreWirelessNoticeDialog.
    var showRestoreWirelessNotice by rememberSaveable { mutableStateOf(false) }
""",
            1,
        ),
        (
            """    if (showShizukuServiceNotice) {
        ShizukuServiceNoticeDialog(
            onDismissRequest = { showShizukuServiceNotice = false },
        )
    }
""",
            """    if (showShizukuServiceNotice) {
        ShizukuServiceNoticeDialog(
            onDismissRequest = { showShizukuServiceNotice = false },
        )
    }

    if (showRestoreWirelessNotice) {
        RestoreWirelessNoticeDialog(
            onDismissRequest = { showRestoreWirelessNotice = false },
        )
    }
""",
            1,
        ),
        # save both
        (
            """                onClick = {
                    onUpdateSettingsToHide(draft)

                    onDismissRequest()
                },""",
            """                onClick = {
                    onUpdateSettingsToHide(draft)

                    onUpdateRestoreWirelessDebugging(restoreWirelessDraft)

                    onDismissRequest()
                },""",
            1,
        ),
        # the nested row itself
        (
            """        SettingToHideRow(
            label = stringResource(R.string.revert_defaults_wireless_debugging),
            checked = draft[ManualRevertTarget.WirelessDebugging] == true,
            onCheckedChange = { toggle(ManualRevertTarget.WirelessDebugging, it) },
        )
""",
            """        SettingToHideRow(
            label = stringResource(R.string.revert_defaults_wireless_debugging),
            checked = draft[ManualRevertTarget.WirelessDebugging] == true,
            onCheckedChange = { toggle(ManualRevertTarget.WirelessDebugging, it) },
        )

        // Only under the memory function. Under Revert to default the same question is asked
        // by that dialog's own Wireless debugging switch, which is the destination a revert
        // actually drives to there.
        if (unhidingFramework == UnhidingFramework.Memory) {
            NestedRestoreRow(
                label = stringResource(R.string.restore_wireless_also),
                checked = restoreWirelessDraft,
                onCheckedChange = { wanted ->
                    restoreWirelessDraft = wanted

                    // On the way on only. Switching it back off is returning to the safe
                    // default and needs no warning.
                    if (wanted) showRestoreWirelessNotice = true
                },
            )
        }
""",
            1,
        ),
        # the row composable and its dialog, appended beside the file's existing private ones
        (
            """/**
 * A note that is about the list as a whole rather than about one row.
""",
            """/**
 * A checkbox that belongs to the row above it.
 *
 * The elbow is drawn rather than implied by indentation alone, at the author's choice from
 * the two templates. It matters more here than it would in a plain list: this row is the only
 * one in the dialog that is not itself a setting to hide, so an indent on its own would read
 * as a seventh, oddly-placed target.
 *
 * ⚠ **No `enabled` parameter, deliberately.** Every other row in this dialog can grey out;
 * this one never does, even when the Wireless debugging box above it is unticked, because the
 * settings manager's `All on` reads the same stored answer under both frameworks and whatever
 * the parent says. A control that another screen obeys must not be unreachable here.
 */
@Composable
private fun NestedRestoreRow(
    modifier: Modifier = Modifier,
    label: String,
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit,
) {
    val elbow = MaterialTheme.colorScheme.outlineVariant

    Row(
        modifier = modifier
            .fillMaxWidth()
            .clickable { onCheckedChange(!checked) }
            .padding(start = 10.dp, end = 10.dp, top = 2.dp, bottom = 6.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        // Down from the parent row, then across to the label. Drawn from the top of this row
        // rather than from the parent's baseline, because the two are siblings in a Column and
        // neither can reach into the other's bounds.
        Canvas(modifier = Modifier.size(width = 18.dp, height = 40.dp)) {
            val x = 3.dp.toPx()
            val mid = size.height / 2f
            val stroke = 1.5.dp.toPx()

            drawLine(
                color = elbow,
                start = Offset(x = x, y = 0f),
                end = Offset(x = x, y = mid),
                strokeWidth = stroke,
            )

            drawLine(
                color = elbow,
                start = Offset(x = x, y = mid),
                end = Offset(x = size.width, y = mid),
                strokeWidth = stroke,
            )
        }

        Spacer(modifier = Modifier.width(8.dp))

        Text(
            modifier = Modifier.weight(1f),
            text = label,
            style = MaterialTheme.typography.bodyMedium,
        )

        Checkbox(checked = checked, onCheckedChange = onCheckedChange)
    }
}

/**
 * Why restoring wireless debugging is off by default.
 *
 * ⚠ **Two points, and not the sentence the Revert to default dialog shows.** Point 1 here
 * says IMD does not restore wireless debugging on unhiding, which is true of the memory
 * function this checkbox governs and false of the Revert to default configuration, where a
 * switch exists that does exactly that. Two dialogs rather than one shared sentence, on the
 * author's confirmation.
 *
 * The numbers are inside the strings because that is how the author wrote them. Composing
 * them from `shizuku_help_bullet`, as the numbered lists elsewhere in the app do, would mean
 * stripping his numbering to avoid printing it twice.
 */
@Composable
private fun RestoreWirelessNoticeDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = stringResource(R.string.restore_wireless_notice_1),
                style = MaterialTheme.typography.bodyMedium,
            )

            Spacer(modifier = Modifier.height(10.dp))

            Text(
                text = stringResource(R.string.restore_wireless_notice_2),
                style = MaterialTheme.typography.bodyMedium,
            )

            Spacer(modifier = Modifier.height(12.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(R.string.understood))
                }
            }
        }
    }
}

/**
 * A note that is about the list as a whole rather than about one row.
""",
            1,
        ),
    ]),
    (REVERT_DIALOG, [
        (
            """import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
""",
            """import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
""",
            1,
        ),
        (
            """import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
""",
            """import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
""",
            1,
        ),
        (
            """import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.ShizukuForkMode
import com.android.geto.domain.model.UnhidingFramework
import com.android.geto.feature.settings.R
""",
            """import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.ShizukuForkMode
import com.android.geto.domain.model.UnhidingFramework
import com.android.geto.feature.settings.R
""",
            1,
        ),
        (
            """    // Each row sets only itself. Shizuku used to drag USB debugging with it and vice versa,
    // which meant a tap could silently undo a choice the user had made two rows up.""",
            """    // Raised when the Wireless debugging switch is turned on. The short sentence, not the
    // checkbox's two points - see WirelessPrivateWifiDialog.
    var showWirelessNotice by rememberSaveable { mutableStateOf(false) }

    if (showWirelessNotice) {
        WirelessPrivateWifiDialog(onDismissRequest = { showWirelessNotice = false })
    }

    // Each row sets only itself. Shizuku used to drag USB debugging with it and vice versa,
    // which meant a tap could silently undo a choice the user had made two rows up.""",
            1,
        ),
        (
            """            checked = draft[ManualRevertTarget.WirelessDebugging] == true,
            onCheckedChange = { toggle(ManualRevertTarget.WirelessDebugging, it) },
        )""",
            """            checked = draft[ManualRevertTarget.WirelessDebugging] == true,
            onCheckedChange = { wanted ->
                toggle(ManualRevertTarget.WirelessDebugging, wanted)

                // On the way on only. This switch is the one thing in the app that can leave
                // a device listening on the network after a revert, and it says so once.
                if (wanted) showWirelessNotice = true
            },
        )""",
            1,
        ),
        (
            """/**
 * One target's row.
""",
            """/**
 * What turning the Wireless debugging switch on means for a device on a public network.
 *
 * ⚠ **One sentence, not the two-point notice** the nested checkbox in Settings to hide/unhide
 * raises. That one opens by saying IMD does not restore wireless debugging on unhiding, which
 * is exactly what this switch makes untrue — so the shared half is all this dialog says.
 */
@Composable
private fun WirelessPrivateWifiDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = stringResource(R.string.wireless_private_wifi_notice),
                style = MaterialTheme.typography.bodyLarge,
            )

            Spacer(modifier = Modifier.height(12.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(R.string.understood))
                }
            }
        }
    }
}

/**
 * One target's row.
""",
            1,
        ),
    ]),
    (SCREEN, [
        (
            """        onUpdateSettingsToHide = viewModel::updateSettingsToHide,""",
            """        onUpdateSettingsToHide = viewModel::updateSettingsToHide,
        onUpdateRestoreWirelessDebugging = viewModel::updateRestoreWirelessDebugging,""",
            1,
        ),
        (
            """    onUpdateSettingsToHide: (Map<ManualRevertTarget, Boolean>) -> Unit,""",
            """    onUpdateSettingsToHide: (Map<ManualRevertTarget, Boolean>) -> Unit,
    onUpdateRestoreWirelessDebugging: (Boolean) -> Unit,""",
            2,
        ),
        (
            """                    onUpdateSettingsToHide = onUpdateSettingsToHide,""",
            """                    onUpdateSettingsToHide = onUpdateSettingsToHide,
                    onUpdateRestoreWirelessDebugging = onUpdateRestoreWirelessDebugging,""",
            1,
        ),
        (
            """            unhidingFramework = userData.unhidingFramework,
            onDismissRequest = { showSettingsToHideDialog = false },
            onUpdateSettingsToHide = onUpdateSettingsToHide,
        )""",
            """            unhidingFramework = userData.unhidingFramework,
            restoreWirelessDebugging = userData.restoreWirelessDebugging,
            onDismissRequest = { showSettingsToHideDialog = false },
            onUpdateSettingsToHide = onUpdateSettingsToHide,
            onUpdateRestoreWirelessDebugging = onUpdateRestoreWirelessDebugging,
        )""",
            1,
        ),
    ]),
    (VIEW_MODEL, [
        (
            """    fun updateManageOverlay(enabled: Boolean) {""",
            """    /**
     * Whether a memory restore may switch wireless debugging back on.
     *
     * Written from the Settings to hide/unhide dialog's Save, alongside the map, so both
     * halves of that dialog commit on the same press.
     */
    fun updateRestoreWirelessDebugging(enabled: Boolean) {
        viewModelScope.launch {
            userDataRepository.updateRestoreWirelessDebugging(enabled = enabled)
        }
    }

    fun updateManageOverlay(enabled: Boolean) {""",
            1,
        ),
    ]),
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

            text = text.replace(old, new, expected)

        staged[path] = text

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    # Every capitalised name these edits introduce has to be importable from the file it lands
    # in. This is `check_new_types` in miniature, run here so the script cannot write a file
    # that needs a second pass to compile - the r2b3c lesson, where five imports were missed.
    needed = {
        ROOT / HIDE_DIALOG: ["Canvas", "Offset", "Checkbox", "DialogContainer"],
        ROOT / REVERT_DIALOG: ["Arrangement", "DialogContainer", "rememberSaveable"],
    }

    for path, names in needed.items():
        text = staged[path]
        imports = [line for line in text.splitlines() if line.startswith("import ")]

        for name in names:
            if not any(line.rsplit(".", 1)[-1] == name for line in imports):
                problems.append(f"{path.relative_to(ROOT)}: {name} used without an import")

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

    print("ok — the checkbox, its elbow, and two different popups")

    return 0


if __name__ == "__main__":
    sys.exit(main())
