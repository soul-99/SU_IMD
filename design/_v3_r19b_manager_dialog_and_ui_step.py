#!/usr/bin/env python3
"""
r19b — the manager-toggles dialog becomes a setup step too, and the four UI rows become one
composable that Settings and the new Customise UI page share.

⚠ **The rule the four existing steps follow, kept.** Each setup step *is* the dialog Settings
already shows, drawn flat with `stepTitle` and `onSkip` set — not a page built to look like one. A
row added to any of those dialogs turns up in the flow without anybody remembering to add it twice.
So `ManagerRowsDialog` gains the two parameters the other dialogs have, and the four User interface
rows come **out** of `SettingsScreen`'s column into `UserInterfaceLookRows`, which both the section
and the new page draw. The theme picker moves with them, because a row whose dialog lived somewhere
else would work on one page and do nothing on the other.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ROWS = ROOT / "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/ManagerRowsDialog.kt"

SETTINGS = ROOT / "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"

STEPS = ROOT / "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SetupSteps.kt"

SETUP = ROOT / "app/src/main/kotlin/com/android/geto/onboarding/SetupScreen.kt"

failures: list[str] = []

pending: list[tuple[Path, str]] = []


def check(condition: bool, message: str) -> bool:
    if not condition:
        failures.append(message)

    return condition


def swap(text: str, old: str, new: str, label: str, count: int = 1) -> str:
    found = text.count(old)

    if check(found == count, f"{label}: found {found}x, expected {count}"):
        return text.replace(old, new, count)

    return text


# ------------------------------------------------------------ 1. ManagerRowsDialog

rows = ROWS.read_text(encoding="utf-8")

rows = swap(
    rows,
    """    shizukuForkMode: ShizukuForkMode,
    onDismissRequest: () -> Unit,""",
    """    shizukuForkMode: ShizukuForkMode,
    /** Set by the setup flow, which draws this page flat and offers Skip beside Next. */
    onSkip: (() -> Unit)? = null,
    stepTitle: String? = null,
    onDismissRequest: () -> Unit,""",
    "rows: step parameters",
)

rows = swap(
    rows,
    """    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = stringResource(R.string.manager_rows_title),
                style = MaterialTheme.typography.titleLarge,
            )
""",
    """    DialogContainer(
        modifier = modifier,
        // A setup page reaches its own edges; a dialog over the settings list does not.
        flat = onSkip != null,
        onDismissRequest = onDismissRequest,
    ) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = stepTitle ?: stringResource(R.string.manager_rows_title),
                style = MaterialTheme.typography.titleLarge,
            )
""",
    "rows: flat and title",
)

rows = swap(
    rows,
    """            Text(
                text = stringResource(R.string.manager_rows_description),
                style = MaterialTheme.typography.bodyMedium,
            )

            Spacer(modifier = Modifier.height(8.dp))
""",
    """            // ⚠ **Two sentences, the author's own.** The first says what the list is, the
            // second says what the thing it configures is *for* — which the old one line
            // ("Only selected options are showed in…") never did, and which is the question
            // somebody opening this dialog for the first time actually has.
            Text(
                text = stringResource(R.string.manager_rows_description),
                style = MaterialTheme.typography.bodyMedium,
            )

            Spacer(modifier = Modifier.height(6.dp))

            Text(
                text = stringResource(R.string.manager_rows_description_two),
                style = MaterialTheme.typography.bodyMedium,
            )

            Spacer(modifier = Modifier.height(10.dp))

            // ⚠ **Dimmed, and it is a caption rather than a sentence** — the author's *"show
            // faded 'only selected ones' just like settings manager under Accessb. and dooa"*.
            // Those two rows carry a small dimmed line under their title saying what the list
            // beneath amounts to; this is the same line doing the same job for this list.
            Text(
                text = stringResource(R.string.manager_rows_only_selected),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurface.copy(alpha = MANAGER_ROWS_CAPTION_ALPHA),
            )

            Spacer(modifier = Modifier.height(8.dp))
""",
    "rows: description and caption",
)

rows = swap(
    rows,
    """            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(
                    enabled = savable,
                    onClick = {
                        onUpdateManagerRows(draft.toMap())

                        onDismissRequest()
                    },
                ) {
                    Text(text = stringResource(R.string.save))
                }
            }""",
    """            Row(
                modifier = Modifier.fillMaxWidth(),
                // Skip on the left and Next on the right in the flow; Save alone on the right
                // in Settings. The same arrangement the four steps before this one use.
                horizontalArrangement = if (onSkip != null) {
                    Arrangement.SpaceBetween
                } else {
                    Arrangement.End
                },
            ) {
                if (onSkip != null) {
                    TextButton(onClick = onSkip) {
                        Text(text = stringResource(commonR.string.skip))
                    }
                }

                TextButton(
                    enabled = savable,
                    onClick = {
                        onUpdateManagerRows(draft.toMap())

                        onDismissRequest()
                    },
                ) {
                    Text(
                        text = stringResource(
                            if (onSkip != null) commonR.string.next else R.string.save,
                        ),
                    )
                }
            }""",
    "rows: actions",
)

rows = swap(
    rows,
    "import com.android.geto.feature.settings.R\n",
    "import com.android.geto.feature.settings.R\nimport com.android.geto.common.R as commonR\n",
    "rows: commonR import",
)

rows = swap(
    rows,
    "private val MANAGER_ROWS_INDENT",
    "/** The same dimming the Accessibility and Display over other apps rows use for their line. */\n"
    "private const val MANAGER_ROWS_CAPTION_ALPHA = 0.7f\n\n"
    "private val MANAGER_ROWS_INDENT",
    "rows: caption alpha",
)

pending.append((ROWS, rows))

# ------------------------------------------------------------ 2. the four UI rows come out

settings = SETTINGS.read_text(encoding="utf-8")

OLD_ROWS = """            DynamicThemeSetting(
                dynamicTheme = userData.dynamicTheme,
                onUpdateDynamicTheme = onUpdateDynamicTheme,
            )

            SettingsRowDivider()

            SettingsColumn(
                title = stringResource(R.string.theme),
                subtitle = userData.theme.getTitle(),
                onClick = { showThemeDialog = true },
            )

            // ⚠ **Not drawn at all while the app is light**, at the author's instruction. The
            // mode blacks out a dark scheme's page and returns a light one untouched, so the row
            // would be a switch that visibly does nothing - worse than an absent one.
            //
            // Asked by luminance rather than isSystemInDarkTheme(), for the reason the comment
            // above SHELL_PROMPT_LIGHT gives: the app has its own light/dark/follow-system
            // setting, and the system's answer is the wrong one for a light-themed app on a
            // dark-themed phone. It also survives dynamic colour, where there is no scheme of
            // ours to consult, and it stays true once the mode is on - black is darker still.
            if (MaterialTheme.colorScheme.surface.luminance() < DARK_SURFACE_LUMINANCE) {
                SettingsRowDivider()

                SwitchSetting(
                    title = stringResource(R.string.oled_background_mode),
                    subtitle = stringResource(R.string.oled_background_mode_summary),
                    checked = userData.oledBackground,
                    onCheckedChange = onUpdateOledBackground,
                )
            }

            // ⚠ **Not drawn at all on a device that cannot blur — r13.** Below API 31 there is
            // no `RenderEffect.createBlurEffect`, so those devices get the shadow fade whatever
            // this switch says, and a switch that changes nothing is worse than no switch: the
            // author's *"in that case dont give the option in settings also"*. It replaces r10's
            // answer, which was to rename the row "UI fade" there and leave it working; the fade
            // is not optional any more, so there is nothing left for it to turn off.
            //
            // The divider goes inside the test with it, or the section shows two rules with
            // nothing between them.
            if (supportsProgressiveBlur()) {
                SettingsRowDivider()

                SwitchSetting(
                    title = stringResource(R.string.progressive_ui_blur),
                    subtitle = stringResource(R.string.progressive_ui_blur_summary),
                    checked = userData.progressiveBlur,
                    onCheckedChange = onUpdateProgressiveBlur,
                )
            }

            SettingsRowDivider()
"""

NEW_ROWS = """            // ⚠ **The four look rows are a composable now — r19b.** The setup flow's Customise
            // UI page draws exactly these, and the way this app builds a setup step is to draw
            // the thing Settings already draws rather than a copy of it. See
            // [UserInterfaceLookRows].
            UserInterfaceLookRows(
                userData = userData,
                onUpdateDynamicTheme = onUpdateDynamicTheme,
                onUpdateTheme = onUpdateTheme,
                onUpdateOledBackground = onUpdateOledBackground,
                onUpdateProgressiveBlur = onUpdateProgressiveBlur,
            )

            SettingsRowDivider()
"""

settings = swap(settings, OLD_ROWS, NEW_ROWS, "settings: extract UI rows")

settings = swap(
    settings,
    """    if (showThemeDialog) {
        ThemeDialog(
            onDismissRequest = { showThemeDialog = false },
            selected = selectedTheme,
            onSelect = { selectedTheme = it },
            onChangeClick = {
                onUpdateTheme(Theme.entries[selectedTheme])

                showThemeDialog = false
            },
        )
    }

""",
    "",
    "settings: theme dialog block",
)

settings += '''
/**
 * The four rows that decide how the app *looks*: Dynamic Theme, Theme, OLED background mode and
 * Progressive UI blur.
 *
 * ⚠ **Lifted out of the User interface section in r19b so the setup flow can draw the same
 * thing.** The author asked for a Customise UI page *"which shows these settings (first 4 ones of
 * user interface section)"*, and every other setup step in this app is the settings composable
 * itself rather than a page that resembles it — which is what keeps a row added later from
 * appearing in one place and not the other.
 *
 * ⚠ **It owns the theme picker.** The dialog used to live at the bottom of `SettingsScreen`, four
 * hundred lines from the row that opens it; a page drawing these rows without it would have had a
 * Theme row that did nothing. State that belongs to a row belongs with it.
 *
 * ⚠ **Two of the four are conditional, and the conditions are not this composable's opinion.**
 * OLED background mode is absent while the app is light — the mode blacks out a dark scheme's page
 * and returns a light one untouched, so the row would be a switch that visibly does nothing — and
 * Progressive UI blur is absent below API 31, where `RenderEffect.createBlurEffect` does not
 * exist and the edges get the shadow fade whatever a switch says.
 */
@Composable
internal fun UserInterfaceLookRows(
    userData: UserData,
    onUpdateDynamicTheme: (Boolean) -> Unit,
    onUpdateTheme: (Theme) -> Unit,
    onUpdateOledBackground: (Boolean) -> Unit,
    onUpdateProgressiveBlur: (Boolean) -> Unit,
) {
    var showThemeDialog by rememberSaveable { mutableStateOf(false) }

    var selectedTheme by rememberSaveable(userData.theme) {
        mutableIntStateOf(userData.theme.ordinal)
    }

    DynamicThemeSetting(
        dynamicTheme = userData.dynamicTheme,
        onUpdateDynamicTheme = onUpdateDynamicTheme,
    )

    SettingsRowDivider()

    SettingsColumn(
        title = stringResource(R.string.theme),
        subtitle = userData.theme.getTitle(),
        onClick = { showThemeDialog = true },
    )

    // Asked by luminance rather than isSystemInDarkTheme(), for the reason the comment above
    // SHELL_PROMPT_LIGHT gives: the app has its own light/dark/follow-system setting, and the
    // system's answer is the wrong one for a light-themed app on a dark-themed phone. It also
    // survives dynamic colour, where there is no scheme of ours to consult, and it stays true
    // once the mode is on - black is darker still.
    if (MaterialTheme.colorScheme.surface.luminance() < DARK_SURFACE_LUMINANCE) {
        SettingsRowDivider()

        SwitchSetting(
            title = stringResource(R.string.oled_background_mode),
            subtitle = stringResource(R.string.oled_background_mode_summary),
            checked = userData.oledBackground,
            onCheckedChange = onUpdateOledBackground,
        )
    }

    // The divider goes inside the test with it, or the section shows two rules with nothing
    // between them.
    if (supportsProgressiveBlur()) {
        SettingsRowDivider()

        SwitchSetting(
            title = stringResource(R.string.progressive_ui_blur),
            subtitle = stringResource(R.string.progressive_ui_blur_summary),
            checked = userData.progressiveBlur,
            onCheckedChange = onUpdateProgressiveBlur,
        )
    }

    if (showThemeDialog) {
        ThemeDialog(
            onDismissRequest = { showThemeDialog = false },
            selected = selectedTheme,
            onSelect = { selectedTheme = it },
            onChangeClick = {
                onUpdateTheme(Theme.entries[selectedTheme])

                showThemeDialog = false
            },
        )
    }
}
'''

pending.append((SETTINGS, settings))

# ------------------------------------------------------------ 3. the two steps

steps = STEPS.read_text(encoding="utf-8")

steps = swap(
    steps,
    "import com.android.geto.feature.settings.dialog.RevertDefaultsDialog\n",
    "import com.android.geto.feature.settings.dialog.ManagerRowsDialog\n"
    "import com.android.geto.feature.settings.dialog.RevertDefaultsDialog\n"
    "import com.android.geto.feature.settings.dialog.SettingsPage\n",
    "steps: dialog imports",
)

steps += '''
/**
 * Which rows the settings manager draws.
 *
 * ⚠ **Placed after [RevertDefaultsStep] and before the reminders, at the author's instruction.**
 * Everything before it decides what the app *does*; this and the page after it decide what the
 * user *sees*, which is the right way round to be asked.
 */
@Composable
fun ManagerRowsStep(
    modifier: Modifier = Modifier,
    stepTitle: String,
    onSkip: () -> Unit,
    onNext: () -> Unit,
    viewModel: SettingsViewModel = hiltViewModel(),
) {
    val uiState by viewModel.settingsUiState.collectAsStateWithLifecycle()

    val userData = (uiState as? SettingsUiState.Success)?.userData ?: return

    ManagerRowsDialog(
        modifier = modifier,
        states = userData.managerRows,
        shizukuForkMode = userData.shizukuForkMode,
        stepTitle = stepTitle,
        onSkip = onSkip,
        onDismissRequest = onNext,
        onUpdateManagerRows = viewModel::updateManagerRows,
    )
}

/**
 * How the app looks: the four rows at the top of the User interface section.
 *
 * ⚠ **The last page before the reminders, and the only optional one that changes nothing about
 * the device.** It is here because the author asked for it here, and the position is right for a
 * second reason: it is the one step whose answers the user can see the effect of immediately,
 * which is a better note to finish the flow on than another list of services.
 *
 * ⚠ **[UserInterfaceLookRows] rather than four rows written out again.** See that composable.
 */
@Composable
fun CustomiseUiStep(
    modifier: Modifier = Modifier,
    stepTitle: String,
    onSkip: () -> Unit,
    onNext: () -> Unit,
    viewModel: SettingsViewModel = hiltViewModel(),
) {
    val uiState by viewModel.settingsUiState.collectAsStateWithLifecycle()

    val userData = (uiState as? SettingsUiState.Success)?.userData ?: return

    SettingsPage(
        modifier = modifier,
        title = stepTitle,
        flat = true,
        onDismissRequest = onNext,
        actions = {
            TextButton(onClick = onSkip) {
                Text(text = stringResource(commonR.string.skip))
            }

            TextButton(onClick = onNext) {
                Text(text = stringResource(commonR.string.next))
            }
        },
    ) {
        // ⚠ **Every row writes as it is touched**, unlike the four steps before this one, which
        // hold a draft until Next. These are preferences with no invalid combination and an
        // instantly visible effect: a theme that only applied after Next would look broken while
        // the user was still on the page.
        UserInterfaceLookRows(
            userData = userData,
            onUpdateDynamicTheme = viewModel::updateDynamicTheme,
            onUpdateTheme = viewModel::updateTheme,
            onUpdateOledBackground = viewModel::updateOledBackground,
            onUpdateProgressiveBlur = viewModel::updateProgressiveBlur,
        )
    }
}
'''

steps = swap(
    steps,
    "import androidx.compose.ui.res.stringResource\n",
    "import androidx.compose.material3.Text\n"
    "import androidx.compose.material3.TextButton\n"
    "import androidx.compose.ui.res.stringResource\n",
    "steps: button imports",
)

if "import com.android.geto.common.R as commonR" not in steps:
    steps = swap(
        steps,
        "import kotlinx.coroutines.delay\n",
        "import kotlinx.coroutines.delay\nimport com.android.geto.common.R as commonR\n",
        "steps: commonR import",
    )

pending.append((STEPS, steps))

# ------------------------------------------------------------ 4. the flow

setup = SETUP.read_text(encoding="utf-8")

setup = swap(
    setup,
    """/**
 * The reminders, which is where `remindersOnly` opens.""",
    """/** Which rows the settings manager draws — r19b. */
private const val MANAGER_ROWS = 6

/** How the app looks — r19b. */
private const val CUSTOMISE_UI = 7

/**
 * The reminders, which is where `remindersOnly` opens.""",
    "setup: new page constants",
)

setup = swap(
    setup,
    " * gap is a number the walk stops on with nothing to draw. It was 6, then 5 when r4t took auto\n"
    " * unhide out, and is 6 again now that r4u has put Revert to default in.\n */\nprivate const val REMINDERS = 6\n",
    " * gap is a number the walk stops on with nothing to draw. It was 6, then 5 when r4t took auto\n"
    " * unhide out, 6 again once r4u put Revert to default in, and 8 since r19b added the two pages\n"
    " * above.\n */\nprivate const val REMINDERS = 8\n",
    "setup: REMINDERS",
)

setup = swap(
    setup,
    """                // No stepTitle: this page's own heading changes with the unhiding framework.
                REVERT_DEFAULTS -> RevertDefaultsStep(
                    modifier = modifier,
                    onSkip = { advance(REVERT_DEFAULTS) },
                    onNext = { advance(REVERT_DEFAULTS) },
                )
""",
    """                // No stepTitle: this page's own heading changes with the unhiding framework.
                REVERT_DEFAULTS -> RevertDefaultsStep(
                    modifier = modifier,
                    onSkip = { advance(REVERT_DEFAULTS) },
                    onNext = { advance(REVERT_DEFAULTS) },
                )

                MANAGER_ROWS -> ManagerRowsStep(
                    modifier = modifier,
                    stepTitle = stringResource(R.string.setup_step_manager_rows),
                    onSkip = { advance(MANAGER_ROWS) },
                    onNext = { advance(MANAGER_ROWS) },
                )

                CUSTOMISE_UI -> CustomiseUiStep(
                    modifier = modifier,
                    stepTitle = stringResource(R.string.setup_step_customise_ui),
                    onSkip = { advance(CUSTOMISE_UI) },
                    onNext = { advance(CUSTOMISE_UI) },
                )
""",
    "setup: new branches",
)

setup = swap(
    setup,
    "import com.android.geto.feature.settings.AccessibilityStep\n",
    "import com.android.geto.feature.settings.AccessibilityStep\n"
    "import com.android.geto.feature.settings.CustomiseUiStep\n"
    "import com.android.geto.feature.settings.ManagerRowsStep\n",
    "setup: step imports",
)

pending.append((SETUP, setup))

# ------------------------------------------------------------ commit

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

for path, text in pending:
    path.write_text(text, encoding="utf-8")

    print(f"wrote {path.relative_to(ROOT).as_posix()}")

print("ok")
