#!/usr/bin/env python3
"""r3 — DOOA and accessibility become gated on configuration, and two Advanced rows go.

Three of the author's instructions land together because they are the same change seen from
different sides:

  * *"remove the manage DOOAs setting in advanced, we will show DOOA toggles now for every
    one"* — the switch goes, and what used to be its answer becomes a question about whether
    the feature can actually work.
  * *"We will only be able to open 'DOOAs to manage' now if thedjchi fork is selected"* —
    plus the Manage Shizuku switch, plus a configured 'DOOAs to hide'.
  * *"i do not think there is need of restart shizuku service toggle in advanced section now?
    remove it?"* — answered: removed, and its one read site now always restarts.

### The swap, not a rewrite

`manageOverlay` (proto 38) had one writer — the switch — and a dozen readers threaded through
maps, view models and dialogs. Rather than unpick the readers, the **expression they read**
changes: every `userData.manageOverlay` becomes `userData.overlayManageable`, which asks

    manageShizukuEffective && fork is Thedjchi && 'DOOAs to hide' is not empty

so the same call sites keep working and start answering the right question. The parameter is
still called `manageOverlay` where it is passed down, because from a dialog's point of view
that is still exactly what it means.

⚠ **Proto 38 is now written by nobody and read by nobody.** Left declared rather than
reserved, like `autoHideEnabledBeforeHide` (47), and recorded as debt — an install that had it
switched off simply gets DOOA management on the same terms as everybody else, which is the
instruction.

⚠ **The row is no longer hidden — that is the point of the greying that follows.** This script
makes the *data* right and stops hiding the 'DOOAs to hide' picker; the dialogs' greyed
toggles and their location-tree pop-ups are the next script.

⚠ **`@OptIn(FlowPreview::class)` is kept and moved.** It sat above `RestartShizukuSetting`'s
KDoc but belongs to `ShizukuSection`, which is what actually debounces — deleting the row with
its annotation would have taken the opt-in with it and broken a file the sandbox cannot
compile.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

OVERLAY = "domain/model/src/main/kotlin/com/android/geto/domain/model/OverlayManagement.kt"
SCREEN = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"
VIEW_MODEL = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsViewModel.kt"
APP_SETTINGS_VM = ("feature/app-settings/src/main/kotlin/com/android/geto/feature/appsettings/"
                   "AppSettingsViewModel.kt")
MANAGER_VM = ("feature/apps/src/main/kotlin/com/android/geto/feature/apps/manager/"
              "SettingsManagerViewModel.kt")
APPLY_APP = "domain/use-case/src/main/kotlin/com/android/geto/domain/usecase/ApplyAppSettingsUseCase.kt"
REVERT_APP = "domain/use-case/src/main/kotlin/com/android/geto/domain/usecase/RevertAppSettingsUseCase.kt"
REPORTER = ("broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/"
            "DiagnosticStateReporter.kt")

NOTICE_DIALOG = ("feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/"
                 "ManageOverlayNoticeDialog.kt")

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
 * The three are deliberately not collapsed into one boolean anywhere else: the dialogs need to
 * know *which* of them failed in order to point the user at the right place.
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
'''

EDITS: list[tuple[str, list[tuple[str, str, int]]]] = [
    (OVERLAY, [
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
    ]),
    (APPLY_APP, [
        (
            """        val managesOverlay = userData.manageOverlay &&
""",
            """        val managesOverlay = userData.overlayManageable &&
""",
            1,
        ),
    ]),
    (REPORTER, [
        (
            '''                "manage=${yesNo(userData.manageOverlay)}",''',
            '''                "manage=${yesNo(userData.overlayManageable)}",''',
            1,
        ),
    ]),
    (APP_SETTINGS_VM, [
        (
            """            userDataRepository.userData.map { it.manageOverlay }.distinctUntilChanged(),
""",
            """            userDataRepository.userData.map { it.overlayManageable }.distinctUntilChanged(),
""",
            1,
        ),
        (
            """        userDataRepository.userData.map { it.manageOverlay }.distinctUntilChanged(),
""",
            """        userDataRepository.userData.map { it.overlayManageable }.distinctUntilChanged(),
""",
            1,
        ),
    ]),
    (MANAGER_VM, [
        (
            """        .map { it.manageOverlay }
""",
            """        .map { it.overlayManageable }
""",
            1,
        ),
    ]),
    (REVERT_APP, [
        (
            """                if (SettingSnapshot.SHIZUKU_STOPPED_ID in recorded) {
                    restartShizuku(userData = userData)
                } else if (AppSettingKeys.triggersShizukuRestart(enabledAppSettings)) {
                    restartShizukuIfEnabled(userData = userData)
                }
""",
            """                if (
                    SettingSnapshot.SHIZUKU_STOPPED_ID in recorded ||
                    AppSettingKeys.triggersShizukuRestart(enabledAppSettings)
                ) {
                    restartShizuku(userData = userData)
                }
""",
            1,
        ),
        (
            """                // when the profile took the service down as a side effect of switching USB
                // debugging back on — the older, transport-driven restart behind the switch.
""",
            """                // when the profile took the service down as a side effect of switching USB
                // debugging back on.
                //
                // ⚠ **The second case is no longer behind a switch.** 'Restart Shizuku
                // service' was the only thing reading it and v3 removed that row from
                // Advanced at the author's own suggestion, so this path now always puts the
                // service back — which is what the switch did when it was on, and what every
                // other Shizuku restart in the app already does unconditionally.
""",
            1,
        ),
        (
            """    /**
     * The transport-driven restart: fired when a profile switched USB debugging back on and
     * took Shizuku down with it. Kept behind the Advanced-settings switch, so a user who does
     * not want an automatic restart is not surprised by one.
     */
    private suspend fun restartShizukuIfEnabled(userData: UserData) {
        if (!userData.restartShizuku) return

        restartShizuku(userData = userData)
    }

""",
            "",
            1,
        ),
        (
            """     * Starts the service again. The deliberate "hide Shizuku service" toggle reaches this
     * directly — a user who asked for the service to be stopped for an app plainly wants it
     * back on that app's revert — while the transport-driven path comes through
     * [restartShizukuIfEnabled], behind the switch.
""",
            """     * Starts the service again. Both routes reach it directly now: a user who asked for
     * the service to be stopped for an app plainly wants it back on that app's revert, and
     * the transport-driven case used to sit behind the 'Restart Shizuku service' switch that
     * v3 removed at the author's own suggestion.
""",
            1,
        ),
    ]),
    (VIEW_MODEL, [
        (
            """    fun updateManageShizuku(enabled: Boolean) {
""",
            """    fun updateManageShizuku(enabled: Boolean) {
""",
            1,
        ),
    ]),
    (SCREEN, [
        (
            """        .withoutOverlayWhenUnmanaged(userData.manageOverlay)
""",
            """        .withoutOverlayWhenUnmanaged(userData.overlayManageable)
""",
            2,
        ),
        (
            """            manageOverlay = userData.manageOverlay,
""",
            """            manageOverlay = userData.overlayManageable,
""",
            2,
        ),
        # The DOOAs-to-hide picker, now shown to everybody.
        (
            """            // Present only once overlay management has been switched on in Advanced, along
            // with the overlay rows inside the two dialogs above. All three are what that
            // switch's notice asks the user to come here and fill in.
            if (userData.manageOverlay) {
                SettingsRowDivider()

                SettingsColumn(
                    title = stringResource(R.string.overlay_packages),
                    subtitle = overlayPackagesSubtitle(
                        overlayPackages = overlayPackages,
                        managed = userData.managedOverlayPackages,
                    ),
                    onClick = {
                        onRefreshOverlayPackages()

                        showOverlayPackagesDialog = true
                    },
                )
            }
""",
            """            // ⚠ **Shown to everybody since v3**, where it used to appear only once overlay
            // management had been switched on in Advanced. That switch is gone: the DOOA
            // toggles are offered to everyone now and gated on whether they can work, and
            // this picker is one of the three things that decides whether they can. Hiding
            // the way to configure something behind a switch that is itself gated on the
            // configuration would be a circle.
            SettingsRowDivider()

            SettingsColumn(
                title = stringResource(R.string.overlay_packages),
                subtitle = overlayPackagesSubtitle(
                    overlayPackages = overlayPackages,
                    managed = userData.managedOverlayPackages,
                ),
                onClick = {
                    onRefreshOverlayPackages()

                    showOverlayPackagesDialog = true
                },
            )
""",
            1,
        ),
        # The Manage DOOAs row and its notice.
        (
            """            SettingsRowDivider()

            // Was first in Advanced, and is now third: it is the one switch here that adds
            // and removes settings elsewhere in this screen - three overlay rows under
            // Default IMD settings appear and disappear with it. Off by default, since
            // overlay access is the only thing IMD touches that cannot be written at all
            // without a working Shizuku service.
            SwitchSetting(
                title = stringResource(R.string.manage_overlay),
                subtitle = stringResource(R.string.manage_overlay_subtitle),
                checked = userData.manageOverlay,
                onCheckedChange = { wanted ->
                    onUpdateManageOverlay(wanted)

                    // After the switch moves rather than instead of it, and on every
                    // switch-on rather than once: there is nothing to agree to here, only
                    // three rows that have just appeared and do nothing until they are
                    // filled in.
                    if (wanted) showManageOverlayNotice = true
                },
            )

""",
            "",
            1,
        ),
        (
            """    var showManageOverlayNotice by rememberSaveable { mutableStateOf(false) }

""",
            "",
            1,
        ),
        (
            """    if (showManageOverlayNotice) {
        ManageOverlayNoticeDialog(
            onDismissRequest = { showManageOverlayNotice = false },
        )
    }

""",
            "",
            1,
        ),
        (
            """import com.android.geto.feature.settings.dialog.ManageOverlayNoticeDialog
""",
            "",
            1,
        ),
        # The Restart Shizuku service row.
        (
            """            SettingsRowDivider()

            RestartShizukuSetting(
                userData = userData,
                onUpdateRestartShizuku = onUpdateRestartShizuku,
            )

""",
            "",
            1,
        ),
        # Both callbacks, off the four-step chain.
        (
            """        onUpdateRestartShizuku = viewModel::updateRestartShizuku,
        onUpdateManageOverlay = viewModel::updateManageOverlay,
""",
            "",
            1,
        ),
        (
            """    onUpdateRestartShizuku: (Boolean) -> Unit,
    onUpdateManageOverlay: (Boolean) -> Unit,
    onUpdateManageShizuku: (Boolean) -> Unit,
""",
            """    onUpdateManageShizuku: (Boolean) -> Unit,
""",
            2,
        ),
        (
            """                    onUpdateRestartShizuku = onUpdateRestartShizuku,
                    onUpdateManageOverlay = onUpdateManageOverlay,
                    onUpdateManageShizuku = onUpdateManageShizuku,
""",
            """                    onUpdateManageShizuku = onUpdateManageShizuku,
""",
            1,
        ),
    ]),
]

# The two view-model setters nothing calls any more.
VM_REMOVALS = [
    """    fun updateRestartShizuku(restartShizuku: Boolean) {
        viewModelScope.launch {
            userDataRepository.updateRestartShizuku(restartShizuku = restartShizuku)
        }
    }

""",
    """    fun updateManageOverlay(enabled: Boolean) {
        viewModelScope.launch {
            userDataRepository.updateManageOverlay(enabled = enabled)
        }
    }

""",
]

RESTART_START = """@OptIn(FlowPreview::class)
/**
 * Whether a revert that puts USB debugging back should also start Shizuku again.
"""

RESTART_END = """@Composable
private fun ShizukuSection(
"""


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

    # The composable itself, sliced out between two anchors rather than by line number - and
    # the @OptIn kept, because it belongs to what follows rather than to what goes.
    screen = staged.get(ROOT / SCREEN, "")
    start, end = screen.find(RESTART_START), screen.find(RESTART_END)

    if start < 0 or end < 0 or end <= start:
        problems.append(f"{SCREEN}: RestartShizukuSetting is not between its two anchors")
    else:
        staged[ROOT / SCREEN] = (
            screen[:start] + "@OptIn(FlowPreview::class)\n" + screen[end:]
        )

    view_model = staged.get(ROOT / VIEW_MODEL, "")

    for removal in VM_REMOVALS:
        if view_model.count(removal) != 1:
            problems.append(
                f"{VIEW_MODEL}: expected one {removal.strip().splitlines()[0][:48]!r}",
            )
        else:
            view_model = view_model.replace(removal, "", 1)

    staged[ROOT / VIEW_MODEL] = view_model

    # The two helpers, appended to the file that already holds every other overlay gate.
    overlay = staged.get(ROOT / OVERLAY, "")

    if "val UserData.overlayManageable" in overlay:
        problems.append(f"{OVERLAY}: the helpers are already there")
    else:
        staged[ROOT / OVERLAY] = overlay.rstrip("\n") + "\n" + HELPERS

    if not (ROOT / NOTICE_DIALOG).exists():
        problems.append(f"{NOTICE_DIALOG}: already gone")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    # Nothing outside the two dead-field declarations may still read the old switch.
    for rel in (SCREEN, APP_SETTINGS_VM, MANAGER_VM, APPLY_APP, REPORTER, OVERLAY):
        text = staged.get(ROOT / rel, "")

        if "userData.manageOverlay" in text or "it.manageOverlay" in text:
            problems.append(f"{rel}: still reads the removed switch")

    for rel in (SCREEN, VIEW_MODEL):
        text = staged.get(ROOT / rel, "")

        for gone in ("RestartShizukuSetting", "onUpdateRestartShizuku", "ManageOverlayNotice"):
            if gone in text:
                problems.append(f"{rel}: still names {gone}")

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

    (ROOT / NOTICE_DIALOG).unlink()
    print(f"  deleted {NOTICE_DIALOG}")

    print("ok - overlayManageable / accessibilityManageable in, two Advanced rows out")

    return 0


if __name__ == "__main__":
    sys.exit(main())
