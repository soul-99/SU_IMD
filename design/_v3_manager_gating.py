#!/usr/bin/env python3
"""r3 — the settings manager: the Shizuku row disappears, the DOOA row greys, both say why.

The author's instructions, from two places in the spec:

    "Hide/remove the shizuku toggle completely in IMD services manager."

    "For both dialog boxes ... and 'IMD services manager' if no DOOAs and no Accessibility
     services set to be hidden ... display a popup 'Please configure the settings first'
     [display a location tree to the setting]"

### The reason, decided once, in the domain

`overlayBlockedPaths` was written for the settings screen last script; the manager needs the
same answer and lives in a different module, so the **decision** moves to `:domain:model` as
`overlayBlockReasons` and each surface maps the reasons to its own strings.

⚠ **An enum, not a boolean, and not the paths.** Paths are resources and cannot live in the
domain; a boolean cannot say which of the three terms of `overlayManageable` failed, and the
three are fixed in three different places. The enum is the only shape that survives both
constraints — and it is in `:domain:model`, the one module the host runner compiles, so the
ordering and the Shevery short-circuit are guarded by assertions rather than by comment.

⚠ **Shevery short-circuits.** On that fork Display over other apps is unsupported rather than
unconfigured, so the list is exactly `[ForkUnsupported]` and the surfaces show the author's
fork sentence with no path at all. Sending somebody to a picker that can never help is worse
than saying nothing.

### The manager

* `rows()` now hides the **Shizuku** row when 'Manage Shizuku' is off, and always draws the
  **DOOA** row — the reverse of what it did, and both on the author's instruction.
* `GetManualTargetStatesUseCase.overlayManaged` reads `overlayManageable`, so the DOOA row
  greys for all three reasons rather than only for an empty selection.
* `AccessibilityUnmanagedDialog` and `OverlayUnmanagedDialog` are replaced by the same
  `ConfigureFirstDialog` the two configuration dialogs use, so all three surfaces refuse in
  the same words and the same shape.

⚠ **`usableOf` is what the All on / All off pill reads.** Widening `overlayManaged` narrows
what the pill will move — deliberately: a pill that switched DOOA on through a fork that cannot
write the AppOp would be the one press able to get around the gate.

⚠ **Five strings are duplicated into `feature/apps`.** That module cannot see
`feature/settings`' resources, and `check5_dupes` treats identical strings across modules as
intentional — the precedent is `string/understood`, already shared exactly this way.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

OVERLAY = "domain/model/src/main/kotlin/com/android/geto/domain/model/OverlayManagement.kt"
STATES = "domain/use-case/src/main/kotlin/com/android/geto/domain/usecase/GetManualTargetStatesUseCase.kt"
MANAGER = ("feature/apps/src/main/kotlin/com/android/geto/feature/apps/dialog/"
           "AndroidSettingsManagerDialog.kt")
MANAGER_VM = ("feature/apps/src/main/kotlin/com/android/geto/feature/apps/manager/"
              "SettingsManagerViewModel.kt")
MANAGER_ROUTE = ("feature/apps/src/main/kotlin/com/android/geto/feature/apps/manager/"
                 "SettingsManagerRoute.kt")
APPS_STRINGS = "feature/apps/src/main/res/values/strings.xml"
SCREEN = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"
TESTS = "tools/host-tests/DomainLogicTests.kt"
TRANSLATIONS = "tools/check_translations.py"

REASONS = '''
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

SCREEN_HELPER_OLD = '''
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

SCREEN_HELPER_NEW = '''
@Composable
private fun overlayBlockedPaths(userData: UserData): List<String>? {
    val manageShizukuPath = stringResource(R.string.help_path_manage_shizuku)

    val dooaPath = stringResource(R.string.help_path_dooa)

    val reasons = overlayBlockReasons(userData = userData)

    if (reasons.isEmpty()) return null

    return reasons.mapNotNull { reason ->
        when (reason) {
            // Nothing to point at. The empty list this leaves is what tells the dialog to say
            // the fork sentence instead of the configure-first one.
            OverlayBlockReason.ForkUnsupported -> null

            OverlayBlockReason.ManageShizukuOff -> manageShizukuPath

            OverlayBlockReason.NothingSelected -> dooaPath
        }
    }
}
'''

MANAGER_HELPER = '''
/**
 * The same mapping the settings screen makes, against this module's own copy of the strings.
 *
 * ⚠ **The decision is not repeated, only the wording.** `overlayBlockReasons` in
 * `:domain:model` is the single answer to why the row will not move; `feature/apps` cannot see
 * `feature/settings`' resources, so what is duplicated is five strings rather than a rule.
 */
@Composable
private fun overlayBlockedPaths(reasons: List<OverlayBlockReason>): List<String> {
    val manageShizukuPath = stringResource(R.string.help_path_manage_shizuku)

    val dooaPath = stringResource(R.string.help_path_dooa)

    return reasons.mapNotNull { reason ->
        when (reason) {
            OverlayBlockReason.ForkUnsupported -> null

            OverlayBlockReason.ManageShizukuOff -> manageShizukuPath

            OverlayBlockReason.NothingSelected -> dooaPath
        }
    }
}
'''

APPS_NEW_STRINGS = """
    <!-- ===================== r3: greyed toggles, and where to fix them =====================
      ⚠ Copies of the same five strings in :feature:settings. This module cannot see that
      module's resources, and check5_dupes treats identical strings across modules as
      intentional - string/understood is already shared exactly this way. -->
    <string name="configure_first">Please configure the settings first</string>
    <string name="dooa_thedjchi_only">managing Display over other apps is only supported for Thedjchi fork of Shizuku</string>
    <string name="help_path_accessibility">IMD Settings \\u2192 Default IMD settings \\u2192 Accessibility services to hide</string>
    <string name="help_path_dooa">IMD Settings \\u2192 Default IMD settings \\u2192 Display over other apps to hide</string>
    <string name="help_path_manage_shizuku">IMD Settings \\u2192 Shizuku (Thedjchi) configuration in IMD \\u2192 Manage Shizuku</string>
"""

HOST_BLOCK = """    // 2c. Why a Display over other apps control will not move. Reasons rather than
    //     sentences, because two modules ask and neither can see the other's strings.
    val dooaReady = userData(
        ShizukuForkMode.Thedjchi,
        authKey = "k",
        manageOverlay = true,
        manageShizuku = true,
    )

    check("a ready overlay setup blocks on nothing", overlayBlockReasons(dooaReady).isEmpty())

    checkEquals(
        "shevery is unsupported rather than unconfigured",
        listOf(OverlayBlockReason.ForkUnsupported),
        overlayBlockReasons(dooaReady.copy(shizukuForkMode = ShizukuForkMode.Other)),
    )

    checkEquals(
        "manage shizuku off is its own reason",
        listOf(OverlayBlockReason.ManageShizukuOff),
        overlayBlockReasons(dooaReady.copy(manageShizuku = false)),
    )

    checkEquals(
        "an empty picker is its own reason",
        listOf(OverlayBlockReason.NothingSelected),
        overlayBlockReasons(dooaReady.copy(managedOverlayPackages = emptyList())),
    )

    checkEquals(
        "both can be missing at once, master switch first",
        listOf(OverlayBlockReason.ManageShizukuOff, OverlayBlockReason.NothingSelected),
        overlayBlockReasons(
            dooaReady.copy(manageShizuku = false, managedOverlayPackages = emptyList()),
        ),
    )

    // ⚠ Shevery short-circuits: it does not also report the empty picker behind it.
    checkEquals(
        "shevery reports one reason even with nothing selected",
        listOf(OverlayBlockReason.ForkUnsupported),
        overlayBlockReasons(
            dooaReady.copy(
                shizukuForkMode = ShizukuForkMode.Other,
                managedOverlayPackages = emptyList(),
            ),
        ),
    )

"""

EDITS: list[tuple[str, list[tuple[str, str, int]]]] = [
    (STATES, [
        (
            """            overlayManaged = userData.managedOverlayPackages.isNotEmpty(),
""",
            """            // ⚠ **All three terms since r3**, not just the picker. The manager's DOOA row
            // has to grey for a Shevery fork and for a 'Manage Shizuku' that is off as well
            // as for an empty selection, and this is the value its `usableOf` reads.
            overlayManaged = userData.overlayManageable,
""",
            1,
        ),
    ]),
    (MANAGER_VM, [
        (
            """    val manageOverlay = userDataRepository.userData
        .map { it.overlayManageable }
""",
            """    /**
     * Whether the Shizuku row is drawn at all.
     *
     * ⚠ **Hidden rather than greyed, on the author's instruction** — *"Hide/remove the shizuku
     * toggle completely in IMD services manager"* when 'Manage Shizuku' is off. Every other
     * unusable row in this dialog greys and explains itself; this one goes, because with the
     * master switch off IMD is not managing that service at all and a greyed row would be
     * offering something the user has said no to.
     */
    val manageShizuku = userDataRepository.userData
        .map { it.manageShizukuEffective }
""",
            1,
        ),
        (
            """    /**
     * Whether a row refused to move because `WRITE_SECURE_SETTINGS` has gone.
""",
            """    /**
     * Why the Display over other apps row will not move, or empty while it will.
     *
     * The domain decides; this only carries the answer. See `overlayBlockReasons`.
     */
    val overlayBlocked = userDataRepository.userData
        .map { overlayBlockReasons(userData = it) }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = emptyList(),
        )

    /**
     * Whether a row refused to move because `WRITE_SECURE_SETTINGS` has gone.
""",
            1,
        ),
        (
            """import com.android.geto.domain.model.ManualRevertTarget
""",
            """import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.overlayBlockReasons
""",
            1,
        ),
    ]),
    (MANAGER_ROUTE, [
        (
            """    val manageOverlay by viewModel.manageOverlay.collectAsStateWithLifecycle()
""",
            """    val manageShizuku by viewModel.manageShizuku.collectAsStateWithLifecycle()

    val overlayBlocked by viewModel.overlayBlocked.collectAsStateWithLifecycle()
""",
            1,
        ),
        (
            """        manageOverlay = manageOverlay,
""",
            """        manageShizuku = manageShizuku,
        overlayBlocked = overlayBlocked,
""",
            1,
        ),
    ]),
    (MANAGER, [
        (
            """private fun rows(manageOverlay: Boolean): List<ManualRevertTarget> =
    if (manageOverlay) {
        ManualRevertTarget.entries
    } else {
        ManualRevertTarget.entries.filter {
            it != ManualRevertTarget.DisplayOverOtherApps
        }
    }
""",
            """private fun rows(manageShizuku: Boolean): List<ManualRevertTarget> =
    if (manageShizuku) {
        ManualRevertTarget.entries
    } else {
        ManualRevertTarget.entries.filter {
            it != ManualRevertTarget.Shizuku
        }
    }
""",
            1,
        ),
        (
            """    manageOverlay: Boolean = true,
""",
            """    manageShizuku: Boolean = true,
    /**
     * Why the Display over other apps row will not move, or empty while it will.
     *
     * Decided by `overlayBlockReasons` in `:domain:model` and collected by the view model, so
     * this dialog and the two configuration dialogs cannot disagree about the same row.
     */
    overlayBlocked: List<OverlayBlockReason> = emptyList(),
""",
            1,
        ),
        (
            """            val drawnRows = rows(manageOverlay = manageOverlay)
""",
            """            val drawnRows = rows(manageShizuku = manageShizuku)
""",
            1,
        ),
        (
            """                        isAccessibility && !states.accessibilityManaged -> {
                            { showAccessibilityUnmanaged = true }
                        }
""",
            """                        isAccessibility && !states.accessibilityManaged -> {
                            { blockedPaths = listOf(accessibilityPath) }
                        }
""",
            1,
        ),
        (
            """                        isOverlay && !states.overlayManaged -> {
                            { showOverlayUnmanaged = true }
                        }
""",
            """                        isOverlay && !states.overlayManaged -> {
                            { blockedPaths = overlayPaths }
                        }
""",
            1,
        ),
        (
            """    if (showAccessibilityUnmanaged) {
        AccessibilityUnmanagedDialog(onDismissRequest = { showAccessibilityUnmanaged = false })
    }
""",
            """    blockedPaths?.let { paths ->
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
""",
            1,
        ),
        (
            """    if (showOverlayUnmanaged) {
        OverlayUnmanagedDialog(onDismissRequest = { showOverlayUnmanaged = false })
    }

""",
            "",
            1,
        ),
        (
            """import com.android.geto.designsystem.component.DialogContainer
""",
            """import com.android.geto.designsystem.component.ConfigureFirstDialog
import com.android.geto.designsystem.component.DialogContainer
""",
            1,
        ),
        (
            """import com.android.geto.domain.model.ManualRevertTarget
""",
            """import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.OverlayBlockReason
""",
            1,
        ),
    ]),
    (SCREEN, [
        (SCREEN_HELPER_OLD, SCREEN_HELPER_NEW, 1),
        (
            """import com.android.geto.domain.model.overlayManageable
""",
            """import com.android.geto.domain.model.OverlayBlockReason
import com.android.geto.domain.model.overlayBlockReasons
import com.android.geto.domain.model.overlayManageable
""",
            1,
        ),
    ]),
    (APPS_STRINGS, [
        (
            """</resources>""",
            APPS_NEW_STRINGS + """</resources>""",
            1,
        ),
    ]),
    (TESTS, [
        (
            """import com.android.geto.domain.model.manageShizukuEffective
""",
            """import com.android.geto.domain.model.OverlayBlockReason
import com.android.geto.domain.model.manageShizukuEffective
import com.android.geto.domain.model.overlayBlockReasons
""",
            1,
        ),
        (
            """    // The auth key is only required where the fork reads it, so Shevery stays on without one.
""",
            HOST_BLOCK + """    // The auth key is only required where the fork reads it, so Shevery stays on without one.
""",
            1,
        ),
    ]),
    (TRANSLATIONS, [
        (
            """    "help_path_manage_shizuku",
""",
            """    "help_path_manage_shizuku",
""",
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

    overlay = staged.get(ROOT / OVERLAY, "")

    if "enum class OverlayBlockReason" in overlay:
        problems.append(f"{OVERLAY}: the reasons are already there")
    else:
        staged[ROOT / OVERLAY] = overlay.rstrip("\n") + "\n" + REASONS

    manager = staged.get(ROOT / MANAGER, "")

    # The state the two replaced dialogs used, and the two paths the rows now hand it.
    old_state = """    var showAccessibilityUnmanaged by rememberSaveable { mutableStateOf(false) }
"""

    if manager.count(old_state) != 1:
        problems.append(f"{MANAGER}: no single accessibility-unmanaged state to replace")
    else:
        manager = manager.replace(
            old_state,
            """    // Null while nothing is blocked; the location trees otherwise; and empty for the one
    // case with nothing to point at - Shevery, where Display over other apps is unsupported
    // rather than unconfigured. Same three-way shape as the two configuration dialogs.
    var blockedPaths by remember { mutableStateOf<List<String>?>(null) }

    val accessibilityPath = stringResource(R.string.help_path_accessibility)

    val overlayPaths = overlayBlockedPaths(reasons = overlayBlocked)
""",
            1,
        )

    old_overlay_state = """    var showOverlayUnmanaged by rememberSaveable { mutableStateOf(false) }

"""

    if manager.count(old_overlay_state) != 1:
        problems.append(f"{MANAGER}: no single overlay-unmanaged state to remove")
    else:
        manager = manager.replace(old_overlay_state, "", 1)

    # Both replaced composables, sliced out between the KDoc that opens the first and the one
    # that opens whatever follows the second. Their two strings are left in place on the r2i
    # principle that a removed line is cheaper to restore than to re-translate.
    dead_start = manager.find(
        "/**\n * Why the accessibility row is off and will not move",
    )

    dead_end = manager.find("/**\n * The rows a Shizuku start moves on its own.")

    if dead_start < 0 or dead_end < 0 or dead_end <= dead_start:
        problems.append(f"{MANAGER}: the two replaced dialogs are not between their anchors")
    else:
        manager = manager[:dead_start] + manager[dead_end:]

    manager = manager.rstrip("\n") + "\n" + MANAGER_HELPER

    staged[ROOT / MANAGER] = manager

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for gone in ("AccessibilityUnmanagedDialog", "OverlayUnmanagedDialog", "manageOverlay"):
        if gone in manager:
            problems.append(f"{MANAGER}: still names {gone}")

    for path, text in staged.items():
        before = set(path.read_text(encoding="utf-8").splitlines())

        for line in text.splitlines():
            if line not in before and len(line) > 120 and not path.name.endswith(".xml"):
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

    print("ok - the manager hides Shizuku, greys DOOA for all three reasons, and says why")

    return 0


if __name__ == "__main__":
    sys.exit(main())
