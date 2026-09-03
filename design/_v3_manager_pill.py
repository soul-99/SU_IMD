#!/usr/bin/env python3
"""
v3 — the settings manager's All on / All off pill, the pending-revert line, and the debt rule.

Three things that arrive together because they are all about the same dialog and the same
promise: that what you do here is honest about whether a revert is going to undo it.

## The pill

A master row below the last toggle, above the two filled actions. Shape A in the templates,
in the theme's own neutral shade (`surfaceVariant`), one long pill with a hairline division —
the author's pick.

⚠ **The dialog decides which rows the pill moves, not the ViewModel.** The per-row `usable`
test is hoisted out of the row loop and used for both, so the pill's promise — it moves
exactly the rows you could have moved by hand — cannot drift from what the rows actually do.
Two tests that could disagree would be one too many, which is the reasoning this file already
applies to `ActionButton`'s `dimmed`.

⚠ **The order is not the enum's.** On: developer options, USB debugging, accessibility,
Shizuku, Display over other apps, and **wireless debugging last** — a Shizuku fork brings the
debugging transport up with it when it starts and moves wireless debugging on the way, so
settling it before the start would have the fork override the user's press. Off is the exact
reverse, which puts Display over other apps before Shizuku stops (its AppOps can only be
written while Shizuku is alive) and developer options last.

⚠ **`All on` skips wireless debugging unless `restoreWirelessDebugging` is set**, on the
author's instruction, and it reads that answer under **both** unhiding frameworks. This one
button is otherwise a way to put wireless debugging back without going near the setting that
governs putting wireless debugging back.

## The pending-revert line

The author's sentence, in red with an information glyph, above the toggles, shown while IMD
is holding something it has not reverted.

⚠ **Never drawn at the same time as the busy note**, which lives in the same slot and opens
with the same five words. His rule: the busy note is work happening *now*, this is a hide that
finished with its revert still owing. Suppressed on `busy` rather than on `settingsWork`,
because the rows go dead on `busy` alone and there is a moment where work has started and has
not yet named a direction.

⚠ **A glyph, not a button.** The author asked for "a red i logo not button" — nothing opens.

## The debt rule

*"Moving any toggle adds to the total revert debt only if a pending revert already exists in
the background."* With nothing outstanding a manual toggle owes nothing and no record is kept;
with a revert pending, the value the row had **before** the press is recorded, so the
outstanding revert puts it back — which is what the red line promises.

⚠ **The three keyed rows only.** Accessibility services and Display over other apps already
record a hold on every switch-off, pending revert or not, and that record is not merely a
debt: it is written *before* the shell command for crash safety, and it is what
`heldByOthers` arithmetic reads so two profiles cannot hand back a service the other is still
holding. Suppressing it would trade a rule about reverts for a device that forgets what it
switched off if the process dies. Shizuku has no "before" value at all — off is a stop
broadcast — so it has nothing to record either way. Reported to the author with the build.

⚠ **First-owner, so a repeat press cannot overwrite the original.** `manualChangeRecord` skips
a key already recorded, exactly as `recordDeviceWideValues` does, and for the same reason: the
first reading is the true one and every later one is a value IMD itself wrote.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FRAMEWORKS = "domain/model/src/main/kotlin/com/android/geto/domain/model/Frameworks.kt"
RECORD_USE_CASE = ("domain/use-case/src/main/kotlin/com/android/geto/domain/usecase/"
                   "RecordManualChangeUseCase.kt")
VIEW_MODEL = ("feature/apps/src/main/kotlin/com/android/geto/feature/apps/manager/"
              "SettingsManagerViewModel.kt")
DIALOG = ("feature/apps/src/main/kotlin/com/android/geto/feature/apps/dialog/"
          "AndroidSettingsManagerDialog.kt")
ROUTE = ("feature/apps/src/main/kotlin/com/android/geto/feature/apps/manager/"
         "SettingsManagerRoute.kt")

NEW_FILE = '''/*
 *
 *   Copyright 2023 Einstein Blanco
 *   Modifications Copyright 2026 soul_99 (suIMD)
 *
 *   Licensed under the GNU General Public License v3.0 (the "License");
 *   you may not use this file except in compliance with the License.
 *   You may obtain a copy of the License at
 *
 *       https://www.gnu.org/licenses/gpl-3.0
 *
 *   Unless required by applicable law or agreed to in writing, software
 *   distributed under the License is distributed on an "AS IS" BASIS,
 *   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *   See the License for the specific language governing permissions and
 *   limitations under the License.
 *
 */
package com.android.geto.domain.usecase

import com.android.geto.domain.model.AccessibilityServicePlan
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.manualChangeRecord
import com.android.geto.domain.model.settingsHidden
import com.android.geto.domain.repository.UserDataRepository
import kotlinx.coroutines.flow.first
import javax.inject.Inject

/**
 * Records what a settings manager row was set to, just before a person changes it by hand.
 *
 * The author's rule: *moving any toggle adds to the total revert debt only if a pending
 * revert already exists in the background.* With nothing outstanding, a manual change is the
 * user managing their own device and nothing should undo it later. With a revert pending, the
 * dialog says in red that changes made here will be undone by it — and this is what makes
 * that sentence true rather than merely printed.
 *
 * ⚠ **Called before the write, never after.** The value being recorded is the one the row is
 * about to stop having.
 *
 * ⚠ **The three keyed targets only.** Accessibility services and Display over other apps
 * already record a hold on every switch-off, and that hold is written before the shell
 * command for crash safety as well as being the debt; Shizuku has no stored "before" value at
 * all. [manualChangeRecord] returns null for all three, so this is a no-op for them.
 */
class RecordManualChangeUseCase @Inject constructor(
    private val userDataRepository: UserDataRepository,
) {
    suspend operator fun invoke(target: ManualRevertTarget, currentlyEnabled: Boolean) {
        val userData = userDataRepository.userData.first()

        // The same pair the dialog draws its red line from, and deliberately the same pair:
        // the line promises the revert will undo this, so the test that records it has to be
        // the test that decided to make the promise.
        val revertPending = userData.autoHideRunning || userData.settingsHidden

        val record = manualChangeRecord(
            settingStateBefore = userData.settingStateBefore,
            target = target,
            currentlyEnabled = currentlyEnabled,
            revertPending = revertPending,
        ) ?: return

        userDataRepository.updateSettingStateBefore(
            states = userData.settingStateBefore +
                (AccessibilityServicePlan.DEVICE_WIDE_HOLD to record),
        )
    }
}
'''

FRAMEWORKS_ADDITION = '''
/**
 * The device-wide record a manual settings-manager change should leave behind, or null.
 *
 * Null means "write nothing", and it covers three separate cases that all come to the same
 * thing:
 *
 *  * **No revert is pending.** The author's rule: with nothing outstanding, a person moving a
 *    switch is managing their own device and no later revert should undo it.
 *  * **The target has no keyed setting.** Accessibility services, Shizuku and Display over
 *    other apps are not stored here at all — the first two record holds of their own and the
 *    third has no "before" value, since switching it off is a broadcast.
 *  * **The key is already recorded.** The first-owner rule, in the shape
 *    `recordDeviceWideValues` uses it: the earliest reading is the true one, and every later
 *    one is a value IMD itself wrote.
 *
 * [currentlyEnabled] is the state the row has **now**, before the press lands.
 */
fun manualChangeRecord(
    settingStateBefore: Map<String, Map<String, String?>>,
    target: ManualRevertTarget,
    currentlyEnabled: Boolean,
    revertPending: Boolean,
): Map<String, String?>? {
    if (!revertPending) return null

    val id = deviceWideSnapshotId(target = target) ?: return null

    val existing = settingStateBefore[AccessibilityServicePlan.DEVICE_WIDE_HOLD].orEmpty()

    if (id in existing) return null

    return SettingSnapshot.merge(
        existing = existing,
        measured = mapOf(id to if (currentlyEnabled) "1" else "0"),
    )
}
'''

EDITS: list[tuple[str, list[tuple[str, str, int]]]] = [
    (VIEW_MODEL, [
        (
            """import com.android.geto.domain.usecase.GetManualTargetStatesUseCase
import com.android.geto.domain.usecase.SetManualTargetUseCase
""",
            """import com.android.geto.domain.usecase.GetManualTargetStatesUseCase
import com.android.geto.domain.usecase.RecordManualChangeUseCase
import com.android.geto.domain.usecase.SetManualTargetUseCase
""",
            1,
        ),
        (
            """    private val setManualTargetUseCase: SetManualTargetUseCase,
""",
            """    private val setManualTargetUseCase: SetManualTargetUseCase,
    private val recordManualChangeUseCase: RecordManualChangeUseCase,
""",
            1,
        ),
        (
            """        viewModelScope.launch {
            // manual, because this is the one caller that is a person pressing the switch.""",
            """        viewModelScope.launch {
            // Before the write, and only when a revert is already pending — the author's
            // rule, and what makes the dialog's red line true. See RecordManualChangeUseCase.
            recordManualChangeUseCase(
                target = target,
                currentlyEnabled = _targetStates.value.isEnabled(target),
            )

            // manual, because this is the one caller that is a person pressing the switch.""",
            1,
        ),
        (
            """    fun dismissPermissionsLost() {""",
            """    /**
     * The master pill: every row the dialog says is usable, moved together.
     *
     * ⚠ **The dialog supplies [targets], and that is deliberate.** It is the thing that knows
     * which rows are operable right now — an unconfigured Shizuku, an unmanaged accessibility
     * selection, an overlay write in flight — and the pill's whole promise is that it moves
     * exactly the rows the user could have moved by hand. Recomputing that test here would be
     * a second answer to a question that already has one.
     *
     * ⚠ **Wireless debugging is written last on the way on, and first on the way off.**
     * Starting a Shizuku fork brings the debugging transport up using its own
     * WRITE_SECURE_SETTINGS, so a wireless debugging value settled before that start is one
     * the fork can overrule; settling it afterwards makes the user's press the final word.
     * The rest of the order follows the same dependency: developer options before USB
     * debugging, Shizuku before Display over other apps whose AppOps can only be written
     * while it is alive, and the exact reverse on the way off.
     *
     * ⚠ **`All on` leaves wireless debugging alone unless the user has asked for it back.**
     * `restoreWirelessDebugging` is read under both unhiding frameworks here, on the author's
     * instruction: this is the one press that could otherwise put wireless debugging back
     * without going anywhere near the setting that governs it.
     *
     * On the application scope, like every other write here: this dialog is often shown from
     * a tile or a shortcut, where dismissing it takes the ViewModel with it.
     */
    fun setAllTargets(enabled: Boolean, targets: List<ManualRevertTarget>) {
        if (targets.isEmpty()) return

        appScope.launch {
            val userData = userDataRepository.userData.first()

            val ordered = ALL_TARGETS_ON_ORDER.filter { it in targets }.let {
                if (enabled) it else it.reversed()
            }

            for (target in ordered) {
                if (enabled &&
                    target == ManualRevertTarget.WirelessDebugging &&
                    !userData.restoreWirelessDebugging
                ) {
                    continue
                }

                // Read per target rather than once, because the writes above this one move
                // the device — starting Shizuku most of all — and a stale reading would
                // record a value that was already gone.
                val before = getManualTargetStatesUseCase()

                recordManualChangeUseCase(
                    target = target,
                    currentlyEnabled = before.isEnabled(target),
                )

                if (before.isEnabled(target) == enabled) continue

                setManualTargetUseCase(target = target, enabled = enabled, manual = enabled)
            }

            _targetStates.value = getManualTargetStatesUseCase()
        }
    }

    fun dismissPermissionsLost() {""",
            1,
        ),
        (
            """/**
 * Everything the settings manager needs, independent of where it is being shown from.""",
            """/**
 * The order the master pill switches things **on** in; off is the exact reverse.
 *
 * Not [ManualRevertTarget.entries]. Wireless debugging is last because starting a Shizuku fork
 * moves it, developer options is first because USB debugging depends on it, and Display over
 * other apps follows Shizuku because its AppOps can only be written while Shizuku is running.
 */
private val ALL_TARGETS_ON_ORDER = listOf(
    ManualRevertTarget.DeveloperSettings,
    ManualRevertTarget.UsbDebugging,
    ManualRevertTarget.AccessibilityServices,
    ManualRevertTarget.Shizuku,
    ManualRevertTarget.DisplayOverOtherApps,
    ManualRevertTarget.WirelessDebugging,
)

/**
 * Everything the settings manager needs, independent of where it is being shown from.""",
            1,
        ),
    ]),
    (DIALOG, [
        (
            """import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
""",
            """import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
""",
            1,
        ),
        (
            """    onSetEnabled: (ManualRevertTarget, Boolean) -> Unit,
    onOpen: (ManualRevertTarget) -> Unit,
""",
            """    onSetEnabled: (ManualRevertTarget, Boolean) -> Unit,
    /**
     * The master pill. The list is every row this dialog considers operable right now, so the
     * ViewModel never has to ask that question a second way — see [SettingsManagerViewModel].
     */
    onSetAll: (Boolean, List<ManualRevertTarget>) -> Unit,
    onOpen: (ManualRevertTarget) -> Unit,
""",
            1,
        ),
        # the pending line, above the rows and below the busy note's slot
        (
            """            settingsWork?.let { work ->
                Spacer(modifier = Modifier.height(8.dp))
""",
            """            // ⚠ **Never drawn beside the busy note below**, which sits in this same slot and
            // opens with the same five words. They mean different things — that one is work
            // running now, this one is a hide that finished with its revert still owing — and
            // the author's rule is that this one waits.
            //
            // Suppressed on `busy` rather than on `settingsWork`: the rows go dead on `busy`
            // alone, and there is a moment where work has started and has not yet named a
            // direction, in which neither line has anything honest to say.
            //
            // The glyph is an Icon and not an IconButton, at the author's instruction — "a red
            // i logo not button". Nothing opens.
            if (anythingHidden && !busy) {
                Spacer(modifier = Modifier.height(8.dp))

                Row(modifier = Modifier.fillMaxWidth()) {
                    Icon(
                        modifier = Modifier.size(15.dp),
                        imageVector = GetoIcons.Info,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.error,
                    )

                    Spacer(modifier = Modifier.width(8.dp))

                    Text(
                        text = stringResource(R.string.settings_manager_pending),
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.error,
                    )
                }
            }

            settingsWork?.let { work ->
                Spacer(modifier = Modifier.height(8.dp))
""",
            1,
        ),
        # hoist the usable test and draw the pill
        (
            """            rows(manageOverlay = manageOverlay).forEach { target ->
                val isShizuku = target == ManualRevertTarget.Shizuku

                val isOverlay = target == ManualRevertTarget.DisplayOverOtherApps

                val isAccessibility = target == ManualRevertTarget.AccessibilityServices

                // Starting a Shizuku fork switches the debugging transport on by itself, so
                // while an overlay write is running these rows are about to move without the user
                // touching them. Locked rather than left live, because a press in that window
                // races the write that puts them back.
                val disturbedByOverlayWrite = overlayWriteInFlight &&
                    (isShizuku || target.usesDebuggingTransport)

""",
            """            val drawnRows = rows(manageOverlay = manageOverlay)

            // ⚠ **One test, read twice.** The rows use it to decide whether a switch moves,
            // and the master pill uses it to decide which rows it is allowed to move — which
            // is the whole of the author's rule that the pill "does not touch untogglable
            // toggles". Computing it separately for the pill would be a second answer to a
            // question this dialog has already answered, and the two would eventually differ.
            val usableOf = { target: ManualRevertTarget ->
                val isShizuku = target == ManualRevertTarget.Shizuku

                val isOverlay = target == ManualRevertTarget.DisplayOverOtherApps

                val isAccessibility = target == ManualRevertTarget.AccessibilityServices

                // Starting a Shizuku fork switches the debugging transport on by itself, so
                // while an overlay write is running these rows are about to move without the
                // user touching them. Locked rather than left live, because a press in that
                // window races the write that puts them back.
                val disturbedByOverlayWrite = overlayWriteInFlight &&
                    (isShizuku || target.usesDebuggingTransport)

                !busy && !disturbedByOverlayWrite &&
                    (!isOverlay || !overlayWriteInFlight) &&
                    (
                        !isShizuku ||
                            (
                                states.shizukuAvailable &&
                                    states.shizukuSupportsIntents &&
                                    !shizukuStarting
                                )
                        ) &&
                    (!isAccessibility || states.accessibilityManaged) &&
                    (!isOverlay || states.overlayManaged)
            }

            val usableTargets = drawnRows.filter(usableOf)

            drawnRows.forEach { target ->
                val isShizuku = target == ManualRevertTarget.Shizuku

                val isOverlay = target == ManualRevertTarget.DisplayOverOtherApps

                val isAccessibility = target == ManualRevertTarget.AccessibilityServices

""",
            1,
        ),
        (
            """                    // Shizuku is the only row that can be switched off in the sense of
                    // "there is nothing here to control".
                    // Locked while an attempt is in flight. The switch already reads on and
                    // the outcome is a few seconds away; letting it be pressed again would
                    // queue a second attempt against a service that is still deciding.
                    usable = !busy && !disturbedByOverlayWrite &&
                        (!isOverlay || !overlayWriteInFlight) &&
                        (
                            !isShizuku ||
                                (
                                    states.shizukuAvailable &&
                                        states.shizukuSupportsIntents &&
                                        !shizukuStarting
                                    )
                            ) &&
                        (!isAccessibility || states.accessibilityManaged) &&
                        (!isOverlay || states.overlayManaged),
""",
            """                    // Shizuku is the only row that can be switched off in the sense of
                    // "there is nothing here to control".
                    // Locked while an attempt is in flight. The switch already reads on and
                    // the outcome is a few seconds away; letting it be pressed again would
                    // queue a second attempt against a service that is still deciding.
                    usable = usableOf(target),
""",
            1,
        ),
        (
            """            // A clear gap before the action rows, so they do not sit hard against the last
            // toggle above them.
            Spacer(modifier = Modifier.height(16.dp))
""",
            """            // The master pill, its own row directly below the last toggle. Above the gap
            // rather than below it: it belongs to the switches it operates, and the two
            // filled buttons under the gap are a different kind of thing entirely — those
            // change the device as a whole, this one is six switches pressed at once.
            Spacer(modifier = Modifier.height(10.dp))

            MasterPill(
                enabled = usableTargets.isNotEmpty(),
                onAllOn = { onSetAll(true, usableTargets) },
                onAllOff = { onSetAll(false, usableTargets) },
            )

            // A clear gap before the action rows, so they do not sit hard against the last
            // toggle above them.
            Spacer(modifier = Modifier.height(16.dp))
""",
            1,
        ),
        (
            """/** What a red switch means. One dialog, because both red switches mean "read this line". */""",
            """/**
 * `All on` and `All off`, as one long pill with a division down the middle.
 *
 * Shape and shade are the author's pick from the templates: a single tonal pill in the
 * theme's own neutral shade rather than the action buttons' colour, so the row reads as
 * belonging to the switches above it rather than joining the two filled buttons below.
 *
 * ⚠ **One Surface with two halves, not two buttons side by side.** Two buttons would need a
 * gap between them, and a gap is what makes a pair of controls look like two decisions; the
 * hairline says these are two ends of one.
 *
 * ⚠ **No red state and no failure reporting**, on the author's instruction. Every row this
 * moves reports for itself, and a master control that also went red would be reporting the
 * same failure twice.
 *
 * [enabled] false is the dialog's busy state, or a device where no row can be operated at
 * all. Dimmed and inert, using the same disabled palette [ActionButton] restates — but
 * genuinely inert here, unlike that one, because there is nothing useful to say about a press
 * on a control whose rows are already explaining themselves.
 */
@Composable
private fun MasterPill(
    modifier: Modifier = Modifier,
    enabled: Boolean,
    onAllOn: () -> Unit,
    onAllOff: () -> Unit,
) {
    val container = if (enabled) {
        MaterialTheme.colorScheme.surfaceVariant
    } else {
        MaterialTheme.colorScheme.onSurface.copy(alpha = DIMMED_CONTAINER_ALPHA)
    }

    val content = if (enabled) {
        MaterialTheme.colorScheme.onSurfaceVariant
    } else {
        MaterialTheme.colorScheme.onSurface.copy(alpha = DIMMED_CONTENT_ALPHA)
    }

    Surface(
        modifier = modifier
            .fillMaxWidth()
            .height(PILL_HEIGHT),
        shape = CircleShape,
        color = container,
        contentColor = content,
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            PillHalf(
                modifier = Modifier.weight(1f),
                label = stringResource(R.string.settings_manager_all_on),
                enabled = enabled,
                onClick = onAllOn,
            )

            // Inset top and bottom so it reads as a division rather than as two shapes that
            // happen to touch.
            Box(
                modifier = Modifier
                    .fillMaxHeight()
                    .padding(vertical = PILL_DIVIDER_INSET)
                    .width(PILL_DIVIDER_WIDTH),
            ) {
                Surface(
                    modifier = Modifier.fillMaxHeight().fillMaxWidth(),
                    color = content.copy(alpha = PILL_DIVIDER_ALPHA),
                    content = {},
                )
            }

            PillHalf(
                modifier = Modifier.weight(1f),
                label = stringResource(R.string.settings_manager_all_off),
                enabled = enabled,
                onClick = onAllOff,
            )
        }
    }
}

/** One end of [MasterPill]. Its own clickable, so the halves are two targets in one shape. */
@Composable
private fun PillHalf(
    modifier: Modifier = Modifier,
    label: String,
    enabled: Boolean,
    onClick: () -> Unit,
) {
    Box(
        modifier = modifier
            .fillMaxHeight()
            .clickable(enabled = enabled, onClick = onClick),
        contentAlignment = Alignment.Center,
    ) {
        Text(text = label, style = MaterialTheme.typography.labelLarge)
    }
}

/** What a red switch means. One dialog, because both red switches mean "read this line". */""",
            1,
        ),
        (
            """private const val DIMMED_CONTAINER_ALPHA = 0.12f""",
            """private val PILL_HEIGHT = 40.dp

private val PILL_DIVIDER_WIDTH = 1.dp

private val PILL_DIVIDER_INSET = 7.dp

private const val PILL_DIVIDER_ALPHA = 0.45f

private const val DIMMED_CONTAINER_ALPHA = 0.12f""",
            1,
        ),
    ]),
    (ROUTE, [
        (
            """        onSetEnabled = { target, enabled ->
            viewModel.setTargetEnabled(target, enabled)
        },""",
            """        onSetEnabled = { target, enabled ->
            viewModel.setTargetEnabled(target, enabled)
        },
        // The dialog hands over the rows it considers operable, so the pill moves exactly
        // what the user could have moved by hand and nothing else.
        onSetAll = { enabled, targets ->
            viewModel.setAllTargets(enabled = enabled, targets = targets)
        },""",
            1,
        ),
    ]),
]


def main() -> int:
    staged: dict[Path, str] = {}
    problems: list[str] = []

    frameworks = ROOT / FRAMEWORKS
    record = ROOT / RECORD_USE_CASE

    if not frameworks.exists():
        problems.append(f"{FRAMEWORKS}: missing")
    else:
        text = frameworks.read_text(encoding="utf-8")

        if "fun manualChangeRecord(" in text:
            problems.append(f"{FRAMEWORKS}: manualChangeRecord already present")
        else:
            staged[frameworks] = text.rstrip("\n") + "\n" + FRAMEWORKS_ADDITION

    if record.exists():
        problems.append(f"{RECORD_USE_CASE}: already present")
    else:
        staged[record] = NEW_FILE

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

    # Every capitalised name these edits introduce has to be importable where it lands. The
    # r2b3c lesson: a green audit suite will pass a file that cannot compile.
    needed = {
        ROOT / VIEW_MODEL: ["RecordManualChangeUseCase", "ManualRevertTarget", "first"],
        ROOT / DIALOG: ["CircleShape", "Surface", "Box", "fillMaxHeight", "clickable"],
        # Frameworks.kt is not listed: AccessibilityServicePlan and SettingSnapshot are in
        # its own package, com.android.geto.domain.model, so they need no import at all.
    }

    for path, names in needed.items():
        text = staged[path]
        imports = [line for line in text.splitlines() if line.startswith("import ")]

        for name in names:
            same_package = f"fun {name}(" in text or f"object {name}" in text

            if same_package:
                continue

            if not any(line.rsplit(".", 1)[-1] == name for line in imports):
                problems.append(f"{path.relative_to(ROOT)}: {name} used without an import")

    # The old inline usable expression must be gone, or the hoist left two copies behind.
    dialog = staged[ROOT / DIALOG]

    if dialog.count("usable = usableOf(target)") != 1:
        problems.append(f"{DIALOG}: the row no longer reads the hoisted test")

    # ⚠ Not a count of `states.accessibilityManaged` — that legitimately appears twice, once
    # in the hoisted test and once in the row's own refusal message. What must be gone is the
    # inline expression the hoist replaced.
    if "usable = !busy && !disturbedByOverlayWrite" in dialog:
        problems.append(f"{DIALOG}: the inline usable expression survived the hoist")

    if dialog.count("val usableOf = { target: ManualRevertTarget ->") != 1:
        problems.append(f"{DIALOG}: the hoisted test is not there exactly once")

    for path, text in staged.items():
        if not path.exists():
            before: set[str] = set()
        else:
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

    print("ok — the pill, the pending line, and the debt rule")

    return 0


if __name__ == "__main__":
    sys.exit(main())
