#!/usr/bin/env python3
"""r4b — Shevery becomes operable, in the settings manager and nowhere else.

The author's instruction, and the two red points he added to the Shevery pop-up in the same
message are the scope of it:

    "Managing Shevery service & Display over other apps is only allowed in IMD settings
     manager."
    "Hiding-unhiding for app launches is not supported for both settings mentioned above."

So the hide and revert paths are untouched — `withoutShizukuWhenNoIntents` and
`overlayManageable` go on dropping both targets there, and the two configuration dialogs get no
Shevery rows. What changes is the manager:

* **The Shizuku row is called `Shevery service`** when Shevery is the selected fork.
* **It is operable**, where it used to be greyed with an explainer saying that fork has no
  intents. Turning it on writes the debugging transport, which is the only lever Shevery has.
* **Display over other apps is allowed once the Shevery service is seen running** — and locked
  to whatever the user left it at while the service is off, with
  `'Please turn on Shevery service first.'` on a press.
* **USB debugging is blocked for the 40 s wait**, with a theme-coloured countdown, while the
  Shevery row itself stays operable — the author was explicit about that asymmetry.
* **Turning Shevery off before the countdown ends puts USB debugging back where it was.**

⚠ **`SHEVERY_WAIT_SECONDS` is derived from `ShizukuForkMode.Other.serviceWaitMillis`**, not
typed again. Forty is the author's number in two places now — the wait and this countdown — and
a countdown that could disagree with the wait it is counting would be worse than no countdown.

⚠ **The countdown ends early when the service is seen**, because the poll behind
`_targetStates` is what actually knows. The clock is the deadline, not the answer.

⚠ **`usbBeforeSheveryStart` is read before the job is cancelled.** Cancellation runs the job's
`finally`, which clears it — so the off branch captures the value first and cancels second. The
other order loses the thing the restore needs.

⚠ **`overlayManaged` in `ManualTargetStates` becomes the *manager's* rule**, which is where its
only readers are. It is deliberately not `overlayManageable`: that property is the **hiding**
question and is Thedjchi-only by the author's *"we are ditching shevery support from DOOA
completely"*, which is about launches. In the manager, with the service already up, the AppOp
can be written.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import re
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
SHEVERY_DIALOG = ("feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/"
                  "SheveryNoticeDialog.kt")
TESTS = "tools/host-tests/DomainLogicTests.kt"
TRANSLATIONS = "tools/check_translations.py"

DEFERRED_KEYS = ["revert_shevery", "shevery_service_first", "shevery_wait_countdown"]

APPS_NEW_STRINGS = """
    <!-- ======================= r4b: Shevery, in the manager only ======================= -->
    <string name="revert_shevery">Shevery service</string>
    <string name="shevery_service_first">Please turn on Shevery service first.</string>
    <string name="shevery_wait_countdown">Waiting for Shevery service to run...(%1$d)</string>
"""

DOMAIN_HELPER = '''
/**
 * Whether the **settings manager** may operate Display over other apps right now.
 *
 * ⚠ **Deliberately not [overlayManageable], and the difference is the whole of the author's
 * Shevery rule.** That property answers the *hiding* question and is Thedjchi-only, because a
 * launch has to be able to bring the shell up on demand and Shevery cannot be asked for
 * anything. This one answers the manager's question, where the user has just turned the service
 * on themselves and it is running — so the AppOp can be written after all.
 *
 * His two new points in the Shevery pop-up are this function in words: *"Managing Shevery
 * service & Display over other apps is only allowed in IMD settings manager"* and
 * *"Hiding-unhiding for app launches is not supported for both settings mentioned above"*.
 *
 * [shizukuRunning] is the live reading, not the configuration — on Shevery the row is locked to
 * whatever the user left it at until the service is actually seen.
 */
fun overlayManageableInManager(userData: UserData, shizukuRunning: Boolean): Boolean =
    userData.manageShizukuEffective &&
        userData.managedOverlayPackages.isNotEmpty() &&
        when (userData.shizukuForkMode) {
            ShizukuForkMode.Thedjchi -> true

            ShizukuForkMode.Other -> shizukuRunning

            ShizukuForkMode.Unset -> false
        }
'''

VM_ADDITIONS = '''
    /**
     * Whether Shevery is the selected fork, which changes what three rows of this dialog do.
     *
     * Read here rather than asked per press: the label, the usability of two rows and the whole
     * countdown below all turn on it, and a press that read it separately could disagree with
     * the row it was pressed on.
     */
    val isShevery = userDataRepository.userData
        .map { it.shizukuForkMode.isShevery && it.manageShizukuEffective }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = false,
        )

    /**
     * Seconds left of the Shevery wait, or null when nothing is waiting.
     *
     * ⚠ **The clock is the deadline, not the answer.** What actually knows whether Shevery came
     * up is the poll behind [targetStates]; this counts down beside it so the user has
     * something to read, and stops the moment the service is seen.
     */
    private val _sheveryWait = MutableStateFlow<Int?>(null)
    val sheveryWait = _sheveryWait.asStateFlow()

    private var sheveryWaitJob: Job? = null

    /** Where USB debugging was before a Shevery start moved it, so an early off can put it back. */
    private var usbBeforeSheveryStart: Boolean? = null

    /**
     * The Shevery half of [setTargetEnabled], which is a different operation from the Thedjchi
     * one despite wearing the same switch.
     *
     * Thedjchi is asked, by broadcast, and answers in about eight seconds. Shevery is not asked
     * at all: the debugging transport goes up, and Shevery's own ErrorProtect watchdog notices
     * and starts the server on its own cycle — which is why the wait is forty seconds and why
     * the row that must not be touched meanwhile is **USB debugging**, not this one.
     *
     * ⚠ **The author's asymmetry, and it is deliberate**: *"blocks USB debugging toggle for 40s
     * ... in this period keep shevery service toggle unblocked for user even during the wait"*.
     * Somebody who changes their mind has to be able to say so, and saying so is what puts USB
     * debugging back.
     */
    private fun setSheveryService(enabled: Boolean) {
        if (!enabled) {
            // ⚠ Read before the cancel. Cancelling runs the job's `finally`, which clears this.
            val before = usbBeforeSheveryStart

            usbBeforeSheveryStart = null

            sheveryWaitJob?.cancel()
            sheveryWaitJob = null

            _sheveryWait.value = null

            viewModelScope.launch {
                setManualTargetUseCase(
                    target = ManualRevertTarget.Shizuku,
                    enabled = false,
                    manual = true,
                )

                // Only what this start moved, and only back to where it was. A user who had USB
                // debugging on before pressing Shevery keeps it on.
                if (before != null) {
                    setManualTargetUseCase(
                        target = ManualRevertTarget.UsbDebugging,
                        enabled = before,
                        manual = true,
                    )
                }

                _targetStates.value = getManualTargetStatesUseCase()
            }

            return
        }

        usbBeforeSheveryStart = _targetStates.value.isEnabled(ManualRevertTarget.UsbDebugging)

        sheveryWaitJob = viewModelScope.launch {
            try {
                var left = SHEVERY_WAIT_SECONDS

                _sheveryWait.value = left

                // The start writes the transport and then polls for the same forty seconds
                // inside StartShizukuUseCase. Launched rather than awaited so the countdown
                // below runs beside it rather than after it.
                val starting = launch {
                    setManualTargetUseCase(
                        target = ManualRevertTarget.Shizuku,
                        enabled = true,
                        manual = true,
                    )
                }

                while (left > 0 && isActive) {
                    delay(1_000)

                    _targetStates.value = getManualTargetStatesUseCase()

                    if (_targetStates.value.isEnabled(ManualRevertTarget.Shizuku)) break

                    left -= 1

                    _sheveryWait.value = left
                }

                starting.join()
            } finally {
                _sheveryWait.value = null

                sheveryWaitJob = null

                usbBeforeSheveryStart = null
            }
        }
    }
'''

HOST_BLOCK = """    // 2d. The manager's own Display over other apps rule, which is not the hiding one.
    check(
        "thedjchi may manage overlay without the service running",
        overlayManageableInManager(userData = dooaReady, shizukuRunning = false),
    )

    val sheveryReady = dooaReady.copy(shizukuForkMode = ShizukuForkMode.Other)

    check(
        "shevery may not manage overlay with the service down",
        !overlayManageableInManager(userData = sheveryReady, shizukuRunning = false),
    )

    check(
        "shevery may manage overlay once the service is up",
        overlayManageableInManager(userData = sheveryReady, shizukuRunning = true),
    )

    check(
        "a running service does not excuse an empty picker",
        !overlayManageableInManager(
            userData = sheveryReady.copy(managedOverlayPackages = emptyList()),
            shizukuRunning = true,
        ),
    )

    check(
        "a running service does not excuse manage shizuku being off",
        !overlayManageableInManager(
            userData = sheveryReady.copy(manageShizuku = false),
            shizukuRunning = true,
        ),
    )

"""

EDITS: list[tuple[str, list[tuple[str, str, int]]]] = [
    (APPS_STRINGS, [
        ("""</resources>""", APPS_NEW_STRINGS + """</resources>""", 1),
    ]),
    (TRANSLATIONS, [
        (
            """    "help_path_manage_shizuku",
""",
            """    "help_path_manage_shizuku",
"""
            + "".join(f'    "{key}",\n' for key in DEFERRED_KEYS),
            1,
        ),
    ]),
    (SHEVERY_DIALOG, [
        (
            """ * ⚠ **Two of the old points are gone rather than moved.** "Shizuku service toggles will become
 * hidden under hide and unhide settings" stopped being true in this same round — v3 brings
 * those toggles back for Shevery — and the "slight delay" point is now carried by the DOOA
 * picker's own first line, in red, where the delay actually applies.
""",
            """ * ⚠ **Two of the old points are gone rather than moved.** The "slight delay" point is now
 * carried by the DOOA picker's own first line, in red, where the delay actually applies; and
 * "Shizuku service toggles will become hidden under hide and unhide settings" is replaced by
 * points four and five, which say the same thing far more precisely — Shevery's service and
 * Display over other apps are operable in the **settings manager** and nowhere else, and an app
 * launch hides neither.
""",
            1,
        ),
    ]),
    (STATES, [
        (
            """            // ⚠ **All three terms since r3**, not just the picker. The manager's DOOA row
            // has to grey for a Shevery fork and for a 'Manage Shizuku' that is off as well
            // as for an empty selection, and this is the value its `usableOf` reads.
            overlayManaged = userData.overlayManageable,
""",
            """            // ⚠ **The manager's rule, not the hiding one, and this field has no other
            // reader.** `overlayManageable` is Thedjchi-only because a *launch* must be able to
            // bring the shell up on demand; here the user has just started the service by hand,
            // so a running Shevery can write the AppOp after all. See the author's two new
            // points in the Shevery pop-up, which are exactly this distinction.
            overlayManaged = overlayManageableInManager(
                userData = userData,
                shizukuRunning = shizukuRunning,
            ),
""",
            1,
        ),
        (
            """import com.android.geto.domain.model.overlayManageable
""",
            """import com.android.geto.domain.model.overlayManageableInManager
""",
            1,
        ),
    ]),
    (MANAGER_VM, [
        (
            """import com.android.geto.domain.model.manageShizukuEffective
""",
            """import com.android.geto.domain.model.ShizukuForkMode
import com.android.geto.domain.model.manageShizukuEffective
""",
            1,
        ),
        (
            """private const val TARGET_POLL_MILLIS = 500L
""",
            """private const val TARGET_POLL_MILLIS = 500L

/**
 * The Shevery countdown, in seconds.
 *
 * ⚠ **Derived, not typed again.** Forty is the author's number for how long Shevery's watchdog
 * may take, and it already lives on the fork mode as the wait `StartShizukuUseCase` actually
 * spends. A countdown that could disagree with the wait it is counting would be worse than no
 * countdown at all.
 */
private val SHEVERY_WAIT_SECONDS =
    (ShizukuForkMode.Other.serviceWaitMillis / 1_000L).toInt()
""",
            1,
        ),
        (
            """    fun setTargetEnabled(target: ManualRevertTarget, enabled: Boolean) {
        if (target == ManualRevertTarget.DisplayOverOtherApps) {
""",
            """    fun setTargetEnabled(target: ManualRevertTarget, enabled: Boolean) {
        // Shevery's service is not asked for, it is induced - see setSheveryService.
        if (target == ManualRevertTarget.Shizuku && isShevery.value) {
            setSheveryService(enabled = enabled)

            return
        }

        if (target == ManualRevertTarget.DisplayOverOtherApps) {
""",
            1,
        ),
    ]),
    (MANAGER_ROUTE, [
        (
            """    val overlayBlocked by viewModel.overlayBlocked.collectAsStateWithLifecycle()
""",
            """    val overlayBlocked by viewModel.overlayBlocked.collectAsStateWithLifecycle()

    val isShevery by viewModel.isShevery.collectAsStateWithLifecycle()

    val sheveryWait by viewModel.sheveryWait.collectAsStateWithLifecycle()
""",
            1,
        ),
        (
            """        overlayBlocked = overlayBlocked,
""",
            """        overlayBlocked = overlayBlocked,
        isShevery = isShevery,
        sheveryWait = sheveryWait,
""",
            1,
        ),
    ]),
    (MANAGER, [
        (
            """    overlayBlocked: List<OverlayBlockReason> = emptyList(),
""",
            """    overlayBlocked: List<OverlayBlockReason> = emptyList(),
    /**
     * Whether Shevery is the selected fork, which renames one row and changes what two of them
     * are allowed to do. See `SettingsManagerViewModel.setSheveryService`.
     */
    isShevery: Boolean = false,
    /** Seconds left of the Shevery wait, or null when nothing is waiting. */
    sheveryWait: Int? = null,
""",
            1,
        ),
        (
            """                    text = target.getTitle(),
""",
            """                    text = target.getTitle(isShevery = isShevery),
""",
            1,
        ),
        (
            """                        target.getTitle(),
""",
            """                        target.getTitle(isShevery = isShevery),
""",
            1,
        ),
        (
            """internal fun ManualRevertTarget.getTitle(): String = when (this) {
""",
            """internal fun ManualRevertTarget.getTitle(isShevery: Boolean = false): String = when (this) {
""",
            1,
        ),
        (
            """    ManualRevertTarget.Shizuku -> stringResource(R.string.revert_shizuku)
""",
            """    // The author's rename: with Shevery selected the row is that service, and calling it
    // Shizuku would name an app the user has not chosen.
    ManualRevertTarget.Shizuku -> stringResource(
        if (isShevery) R.string.revert_shevery else R.string.revert_shizuku,
    )
""",
            1,
        ),
        (
            """                !busy && !disturbedByOverlayWrite &&
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
""",
                """                // ⚠ **USB debugging is the row that goes dead during a Shevery wait, and the
                // Shevery row is not.** The author's asymmetry: the transport is what is
                // holding the service up, so touching it mid-wait would undo the very thing
                // being waited for - while somebody who has changed their mind has to be able
                // to say so, and saying so is what puts USB debugging back.
                val heldBySheveryWait = sheveryWait != null &&
                    target == ManualRevertTarget.UsbDebugging

                !busy && !disturbedByOverlayWrite && !heldBySheveryWait &&
                    (!isOverlay || !overlayWriteInFlight) &&
                    (
                        !isShizuku ||
                            (
                                states.shizukuAvailable &&
                                    // Shevery has no intents and does not need any: the row
                                    // writes the debugging transport instead. Nor is it held
                                    // by a start in flight - that start is its own wait.
                                    (isShevery || states.shizukuSupportsIntents) &&
                                    (isShevery || !shizukuStarting)
                                )
                        ) &&
                    (!isAccessibility || states.accessibilityManaged) &&
                    (!isOverlay || states.overlayManaged)
""",
            1,
        ),
        (
            """                        isOverlay && !states.overlayManaged -> {
                            { blockedPaths = overlayPaths }
                        }
""",
            """                        // Shevery first: with the service down this row is not
                        // unconfigured, it is waiting on something the user can do in one
                        // press, and a location tree would send them somewhere else entirely.
                        isOverlay && isShevery &&
                            !states.isEnabled(ManualRevertTarget.Shizuku) -> {
                            { showSheveryServiceFirst = true }
                        }

                        isOverlay && !states.overlayManaged -> {
                            { blockedPaths = overlayPaths }
                        }
""",
            1,
        ),
        (
            """            if (anythingHidden && !busy) {
""",
            """            // The Shevery wait, in the same slot as the notes below it and above them all:
            // it is the most immediate thing on screen while it is counting, and it is the
            // explanation for the one row that has just gone dead.
            if (sheveryWait != null) {
                Spacer(modifier = Modifier.height(8.dp))

                Text(
                    text = stringResource(R.string.shevery_wait_countdown, sheveryWait),
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.primary,
                )
            }

            if (anythingHidden && !busy) {
""",
            1,
        ),
    ]),
    (TESTS, [
        (
            """import com.android.geto.domain.model.overlayBlockReasons
""",
            """import com.android.geto.domain.model.overlayBlockReasons
import com.android.geto.domain.model.overlayManageableInManager
""",
            1,
        ),
        (
            """    // The auth key is only required where the fork reads it, so Shevery stays on without one.
""",
            HOST_BLOCK
            + """    // The auth key is only required where the fork reads it, so Shevery stays on without one.
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

    overlay = ROOT / OVERLAY
    overlay_text = overlay.read_text(encoding="utf-8")

    if "fun overlayManageableInManager(" in overlay_text:
        problems.append(f"{OVERLAY}: the manager rule is already there")
    else:
        staged[overlay] = overlay_text.rstrip("\n") + "\n" + DOMAIN_HELPER

    # The view model's new state and the Shevery branch, appended inside the class.
    view_model = staged.get(ROOT / MANAGER_VM, "")
    anchor = """    /**
     * Whether a row refused to move because `WRITE_SECURE_SETTINGS` has gone.
"""

    if view_model.count(anchor) != 1:
        problems.append(f"{MANAGER_VM}: no single anchor for the new state")
    else:
        staged[ROOT / MANAGER_VM] = view_model.replace(
            anchor, VM_ADDITIONS.lstrip("\n") + "\n" + anchor, 1,
        )

    manager = staged.get(ROOT / MANAGER, "")
    old_state = """    var blockedPaths by remember { mutableStateOf<List<String>?>(null) }
"""

    if manager.count(old_state) != 1:
        problems.append(f"{MANAGER}: no single blockedPaths state to sit beside")
    else:
        manager = manager.replace(
            old_state,
            old_state + """
    // Shevery's service is down and this row needs it up. Its own flag rather than a path,
    // because the fix is one press on the row above rather than a screen to go to.
    var showSheveryServiceFirst by remember { mutableStateOf(false) }
""",
            1,
        )

    render_anchor = """    blockedPaths?.let { paths ->
"""

    if manager.count(render_anchor) != 1:
        problems.append(f"{MANAGER}: no single explainer render site")
    else:
        manager = manager.replace(
            render_anchor,
            """    if (showSheveryServiceFirst) {
        ConfigureFirstDialog(
            message = stringResource(R.string.shevery_service_first),
            dismissLabel = stringResource(R.string.understood),
            onDismissRequest = { showSheveryServiceFirst = false },
        )
    }

""" + render_anchor,
            1,
        )

    staged[ROOT / MANAGER] = manager

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    # The countdown must read the derived constant, never a literal forty.
    if re.search(r"\b40\b", staged.get(ROOT / MANAGER_VM, "")):
        problems.append(f"{MANAGER_VM}: the wait is written as a literal somewhere")

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

    print("ok - Shevery is operable in the manager, with the 40 s countdown and the USB hold")

    return 0


if __name__ == "__main__":
    sys.exit(main())
