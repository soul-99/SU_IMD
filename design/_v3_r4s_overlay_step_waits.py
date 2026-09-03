#!/usr/bin/env python3
"""v3-r4s — the Display over other apps step is shown to everyone, and waits before giving up.

    "the dooa to manage does not load so make the page apper to everyone and if failed to load
     show 8s spinner if still failed show a skip & retry button."

Three changes, and they are one decision.

## ⚠ The pre-check goes, because it was answering the wrong question

`overlayStepApplies` asked *"is Shizuku configured on a fork that can drive overlay access"* and
hid the step when the answer was no. It is now removed rather than loosened: the author has seen
the step vanish on a device where it should have appeared, and any predicate written from stored
values can be wrong the same way again. The list itself is the only thing that knows whether there
is anything to configure, so the step is drawn and the list is asked.

⚠ **`configuring` stays.** "Everyone" here means everyone the configuration steps are shown to at
all - the author's earlier rule, that these pages are for fresh installs and not for updaters, is
a different rule and is untouched.

## ⚠ The auto-skip goes with it, and this is the reversal

r4r's `onUnavailable` was built from *"if IMD fails to get DOOA list to load skip it"* - the step
took itself out of the flow the moment the read came back empty. That is now the opposite of what
is wanted: a read that returns nothing at once is exactly the case the author hit, and a page that
disappears gives him nothing to retry. So the step stays on screen and says what happened.

⚠ **Eight seconds is a floor, not a timeout.** The spinner is shown for the full wait even if the
read fails in fifty milliseconds, because a "could not load" that appears the instant the page
does reads as the page refusing to try. Nothing is cancelled when the wait ends - if the list
arrives at nine seconds it is drawn, and the failure notice it replaces was only ever a notice.

Retry re-runs the read and starts a fresh eight seconds. Skip moves on, writing nothing, exactly
as the step's own Skip does.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STEPS = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SetupSteps.kt"

DIALOG = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/OverlayPackagesDialog.kt"

SCREEN = "app/src/main/kotlin/com/android/geto/onboarding/SetupScreen.kt"

STRINGS = "common/src/main/res/values/strings.xml"

TRANSLATIONS = "tools/check_translations.py"

EDITS: list[tuple[str, str, str]] = [
    # ---------------- 1. The waiting page ----------------
    (
        DIALOG,
        """/** Why the picker would not open: the list can only be read through a running Shizuku. */""",
        """/**
 * The Display over other apps *step* while its list has not arrived — spinner first, then a way
 * out of it.
 *
 * ⚠ **Separate from [OverlayLoadingDialog], which stays exactly as it was.** That one stands in
 * for a picker the user has just asked for from Settings and resolves in a second or two; this one
 * is a page of the setup flow that has to survive the list never arriving at all, which is the
 * case the author hit. Giving the dialog a failure state would have put a Skip button on a dialog
 * that has nothing to skip.
 *
 * [failed] is the eight-second wait having elapsed with no list, not the read having returned an
 * error — see `OverlayStep`, which owns the timing.
 */
@Composable
internal fun OverlayStepWaiting(
    modifier: Modifier = Modifier,
    stepTitle: String,
    failed: Boolean,
    onSkip: () -> Unit,
    onRetry: () -> Unit,
) {
    SettingsPage(
        modifier = modifier,
        title = stepTitle,
        flat = true,
        // Nothing to dismiss to during setup; the footer is the only way past this page.
        onDismissRequest = onSkip,
        actions = {
            // ⚠ **No buttons at all while the spinner is up.** A Skip offered in the first
            // second is an invitation to leave before the page has had a chance to work, and a
            // Retry before the first attempt has finished would start a second one on top of it.
            if (failed) {
                TextButton(onClick = onSkip) {
                    Text(text = stringResource(commonR.string.skip))
                }

                TextButton(onClick = onRetry) {
                    Text(text = stringResource(commonR.string.retry))
                }
            }
        },
    ) {
        if (failed) {
            Text(
                modifier = Modifier.padding(vertical = 12.dp),
                text = stringResource(R.string.overlay_load_failed),
                style = MaterialTheme.typography.bodyMedium,
            )
        } else {
            Row(
                modifier = Modifier.padding(vertical = 24.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                CircularProgressIndicator(modifier = Modifier.size(24.dp))

                Text(
                    modifier = Modifier.padding(start = 16.dp),
                    text = stringResource(R.string.overlay_loading_list),
                    style = MaterialTheme.typography.bodyMedium,
                )
            }
        }
    }
}

/** Why the picker would not open: the list can only be read through a running Shizuku. */""",
    ),
    # ---------------- 2. The step itself ----------------
    (
        STEPS,
        """/**
 * The apps whose Display over other apps IMD is allowed to manage.
 *
 * ⚠ **Skips itself when the device will not answer.** A null list after the read has finished is
 * the unreadable case, and a step that could only show an error is a step nobody should be shown
 * - the author's *"if IMD fails to get DOOA list to load skip it"*.
 */
@Composable
fun OverlayStep(
    modifier: Modifier = Modifier,
    stepTitle: String,
    onSkip: () -> Unit,
    onNext: () -> Unit,
    /** Called instead of drawing anything, when the overlay list cannot be read. */
    onUnavailable: () -> Unit,
    viewModel: SettingsViewModel = hiltViewModel(),
) {
    val uiState by viewModel.settingsUiState.collectAsStateWithLifecycle()

    val packages by viewModel.overlayPackages.collectAsStateWithLifecycle()

    val loading by viewModel.overlayPackagesLoading.collectAsStateWithLifecycle()

    LaunchedEffect(Unit) {
        viewModel.refreshOverlayPackages()
    }

    // ⚠ In an effect rather than in the composition: advancing the flow is a state write, and a
    // state write during composition is a write during layout.
    LaunchedEffect(loading, packages) {
        if (!loading && packages == null) onUnavailable()
    }

    val userData = (uiState as? SettingsUiState.Success)?.userData ?: return

    val list = packages

    if (list == null) {
        // Either still reading, or unreadable - and the effect above has already moved past
        // the second case by the time this draws again.
        OverlayLoadingDialog()

        return
    }
""",
        """/**
 * The apps whose Display over other apps IMD is allowed to manage.
 *
 * ⚠ **Always drawn, and it waits rather than vanishing.** r4r hid this step twice over - behind a
 * pre-check built from stored Shizuku values, and again behind an auto-skip the moment the read
 * came back empty - and the author saw it disappear on a device where it should have appeared.
 * Both are gone. The step is shown, the list is asked for, and if it does not arrive the page
 * says so and offers Retry.
 *
 * ⚠ **[WAIT_MILLIS] is a floor, not a timeout.** The spinner is held for the whole wait even when
 * the read fails immediately, because a failure notice that appears at the same moment the page
 * does reads as the page refusing to try. Nothing is cancelled at the end of it: a list that
 * arrives late is still drawn.
 */
@Composable
fun OverlayStep(
    modifier: Modifier = Modifier,
    stepTitle: String,
    onSkip: () -> Unit,
    onNext: () -> Unit,
    viewModel: SettingsViewModel = hiltViewModel(),
) {
    val uiState by viewModel.settingsUiState.collectAsStateWithLifecycle()

    val packages by viewModel.overlayPackages.collectAsStateWithLifecycle()

    // Bumped by Retry. Keying the effect on it is what gives each attempt its own read and its
    // own eight seconds, without a second flag saying whether one is in flight.
    var attempt by remember { mutableIntStateOf(0) }

    var waited by remember { mutableStateOf(false) }

    LaunchedEffect(attempt) {
        waited = false

        viewModel.refreshOverlayPackages()

        delay(WAIT_MILLIS)

        waited = true
    }

    val userData = (uiState as? SettingsUiState.Success)?.userData ?: return

    val list = packages

    if (list == null) {
        OverlayStepWaiting(
            modifier = modifier,
            stepTitle = stepTitle,
            failed = waited,
            onSkip = onSkip,
            onRetry = { attempt += 1 },
        )

        return
    }
""",
    ),
    # ---------------- 3. The pre-check goes ----------------
    (
        STEPS,
        """
/**
 * Whether the Display over other apps step has anything to configure.
 *
 * ⚠ **Read before the step is reached, not inside it.** The author's rule is that the step only
 * appears for an install where Shizuku is fully set up on a fork that can drive overlay access -
 * *"only show if shizuku thedjchi configured fully before"* - and that is a question about stored
 * values, answerable by the flow without composing anything.
 *
 * The other reason the step can be absent - the device refusing to list its overlay packages -
 * is not knowable until the read has run, and is handled by the step itself.
 */
fun overlayStepApplies(userData: UserData): Boolean =
    userData.isShizukuConfigured &&
        userData.shizukuForkMode.supportsIntents &&
        userData.manageShizukuEffective
""",
        """
/**
 * How long the Display over other apps step holds its spinner before offering a way out.
 *
 * The author's eight seconds. Long enough that a slow but working Shizuku is not accused of
 * failing, short enough that a dead one does not look like a hung app.
 */
private const val WAIT_MILLIS = 8_000L
""",
    ),
    # ---------------- 4. The flow stops pre-checking ----------------
    (
        SCREEN,
        """    // Read once per composition rather than at each hop, so a Shizuku configuration saved on the
    // page before cannot change the flow's shape underneath a press.
    val overlayApplies = overlayStepApplies(userData = userData)

    val advance = { from: Int ->
        page = nextAfter(from = from, configuring = configuring, overlayApplies = overlayApplies)
    }""",
        """    val advance = { from: Int ->
        page = nextAfter(from = from, configuring = configuring)
    }""",
    ),
    (
        SCREEN,
        """private fun nextAfter(from: Int, configuring: Boolean, overlayApplies: Boolean): Int {
    var page = from + 1

    while (page < REMINDERS) {
        val skip = when (page) {
            ACCESSIBILITY, SETTINGS_TO_HIDE, AUTO_UNHIDE -> !configuring

            OVERLAY -> !configuring || !overlayApplies

            // SHIZUKU, and anything added between the two without a rule of its own.
            else -> !configuring
        }

        if (!skip) return page

        page += 1
    }

    return REMINDERS
}""",
        """private fun nextAfter(from: Int, configuring: Boolean): Int {
    var page = from + 1

    while (page < REMINDERS) {
        // ⚠ **Every configuration page now has the same rule**, since r4s took the Display over
        // other apps pre-check out — it hid the step on devices where it should have appeared,
        // and the step now shows itself and asks the list directly. The loop stays because the
        // flow is still five hops and a page-by-page decision at each of them is how one becomes
        // unreachable.
        if (configuring) return page

        page += 1
    }

    return REMINDERS
}""",
    ),
    (
        SCREEN,
        """            onSkip = { advance(OVERLAY) },
            onNext = { advance(OVERLAY) },
            // The device would not list its overlay packages. Nothing to configure, so nothing
            // to show — the author's "if IMD fails to get DOOA list to load skip it".
            onUnavailable = { advance(OVERLAY) },
        )""",
        """            onSkip = { advance(OVERLAY) },
            onNext = { advance(OVERLAY) },
        )""",
    ),
    (
        SCREEN,
        "import com.android.geto.feature.settings.overlayStepApplies\n",
        "",
    ),
    # ---------------- 5. The one new string ----------------
    (
        STRINGS,
        """    <string name="next">Next</string>""",
        """    <string name="next">Next</string>
    <string name="retry">Retry</string>""",
    ),
    (
        TRANSLATIONS,
        """    # r4r: the setup flow's Skip and Next.
    "skip",
    "next",""",
        """    # r4r: the setup flow's Skip and Next.
    "skip",
    "next",
    # r4s: Retry, beside Skip on the Display over other apps step.
    "retry",""",
    ),
]

IMPORTS = [
    (STEPS, "import androidx.compose.runtime.mutableIntStateOf"),
    (STEPS, "import kotlinx.coroutines.delay"),
]

# The step file loses its last use of three names when the pre-check goes.
REMOVE_IMPORTS = [
    (STEPS, "import com.android.geto.domain.model.UserData\n"),
    (STEPS, "import com.android.geto.domain.model.isShizukuConfigured\n"),
    (STEPS, "import com.android.geto.feature.settings.dialog.OverlayLoadingDialog\n"),
]

# ⚠ Nothing is imported into the dialog file: `SettingsPage` is in its own package, and every
# other name the waiting page uses was already imported for the dialogs around it.
ADD_IMPORTS_TAIL = [
    (STEPS, "import com.android.geto.feature.settings.dialog.OverlayStepWaiting"),
]

AFTER = [
    (STEPS, "onUnavailable", 0),
    (STEPS, "overlayStepApplies", 0),
    (STEPS, "OverlayLoadingDialog", 0),
    (STEPS, "OverlayStepWaiting(", 1),
    # ⚠ Spelled the way only a statement can be, so the doc comment naming the constant does not
    # count towards it — the trap that has caught this round more than once.
    (STEPS, "private const val WAIT_MILLIS = 8_000L", 1),
    (STEPS, "delay(WAIT_MILLIS)", 1),
    # ⚠ Counted from the file: `manageShizukuEffective` is also used by SettingsToHideStep, so
    # its import stays. `isShizukuConfigured` and `UserData` were the pre-check's alone.
    # Three, counted from the file: the import, plus the argument name *and* the property it
    # reads on SettingsToHideStep's one line. The pre-check's fourth is what goes.
    (STEPS, "manageShizukuEffective", 3),
    (STEPS, "isShizukuConfigured", 0),
    (STEPS, "UserData", 0),
    (SCREEN, "overlayStepApplies", 0),
    (SCREEN, "onUnavailable", 0),
    (SCREEN, "nextAfter(", 2),
    (SCREEN, "overlayApplies", 0),
    (DIALOG, "OverlayStepWaiting(", 1),
    (DIALOG, "OverlayLoadingDialog(", 1),
    (DIALOG, "commonR.string.retry", 1),
    (STRINGS, 'name="retry"', 1),
    (TRANSLATIONS, '"retry",', 1),
]


def add_import(text: str, statement: str) -> str:
    if statement in text:
        return text

    lines = text.splitlines(keepends=True)

    prefix = "import com.android.geto." if statement.startswith("import com.") else "import "

    indices = [i for i, line in enumerate(lines) if line.startswith(prefix)]

    if not indices:
        raise SystemExit(f"REFUSED: nowhere to put {statement!r}")

    target = next(
        (i for i in indices if lines[i] > statement + "\n" and lines[i].startswith(prefix)),
        indices[-1] + 1,
    )

    lines.insert(target, statement + "\n")

    return "".join(lines)


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

    for relative, statement in REMOVE_IMPORTS:
        if staged[relative].count(statement) != 1:
            print(f"REFUSED: {relative}\n  {statement.strip()!r} is not present exactly once")
            return 1

        staged[relative] = staged[relative].replace(statement, "", 1)

    for relative, statement in IMPORTS + ADD_IMPORTS_TAIL:
        staged[relative] = add_import(staged[relative], statement)

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

    print(f"  ok        {DIALOG}  :: a waiting page with Skip and Retry")
    print(f"  ok        {STEPS}  :: the step is always drawn and waits 8s")
    print(f"  ok        {SCREEN}  :: the pre-check and the auto-skip are gone")
    print(f"  ok        {STRINGS}  :: Retry")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
