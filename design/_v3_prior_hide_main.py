#!/usr/bin/env python3
"""
v3-r2b3b part 4 — the force-close popup on opening IMD itself.

**The author's report:** "it did not open when imd was opened after force kill". Nothing was
broken — the surface did not exist. Every one of the five surfaces r2b3 shipped hangs off a
*launch*: `ApplyAppSettingsUseCase` and `ApplySettingsToHideUseCase` are where the gate is asked,
so the Apps tab, Favourites, the per-app settings screen, a generated shortcut and IMD+ all warn,
and opening the app on its own asks nothing. He confirmed the shortcut and IMD+ routes and asked
for this one as well.

**Why it is worth having, and not merely symmetrical.** A force close is exactly the case where a
person opens IMD rather than launching something: their device is locked down, the notification
went with the process, and the app is where they have come looking for the way back. Warning them
at the moment they arrive is the whole point of the mechanism.

**Both answers are the whole action here, not a preamble to a launch.** On the other five
surfaces the popup interrupts something and both answers resume it. There is nothing to resume
here, so:

* `'Restore settings first'` runs [SettingsHiddenRunner.flushPendingReverts] — the same call the
  Favourites tab's Unhide button makes, which settles every debt that exists and touches nothing
  on a device that owes none.
* `'Ignore all previous reverts'` runs [SettingsHiddenRunner.discardPendingReverts], which is
  permanent, exactly as it is everywhere else.

⚠ **On the application scope, not `viewModelScope`.** A restore can spend the whole Shizuku start
budget, and a rotation part-way through it would cancel the writes half-applied. Same reason
`SettingsManagerViewModel` puts its overlay write there.

⚠ **Asked once, behind the setup and language screens.** [PriorHide.suppress] is set the moment
the dialog is raised, matching every other surface: a dialog nobody has answered yet must not
invite another one behind it. The [LaunchedEffect] sits in the branch that draws the nav host, so
a first-run install being walked through permissions is not interrupted by it.

⚠ **First in the notice chain.** The four notices below it are advice about the app; this one is a
report that the device is still locked down. It also cannot stack with them — the chain is an
`if/else if` for precisely the reason the comment there gives.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

VIEW_MODEL = "app/src/main/kotlin/com/android/geto/activity/main/MainActivityViewModel.kt"

ACTIVITY = "app/src/main/kotlin/com/android/geto/activity/main/MainActivity.kt"

VIEW_MODEL_EDITS: list[tuple[str, str]] = [
    (
        """import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.android.geto.domain.repository.UserDataRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject
""",
        """import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.android.geto.broadcastreceiver.SettingsHiddenRunner
import com.android.geto.common.ApplicationScope
import com.android.geto.domain.common.PriorHide
import com.android.geto.domain.model.settingsHidden
import com.android.geto.domain.repository.UserDataRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject
""",
    ),
    (
        """class MainActivityViewModel @Inject constructor(
    private val userDataRepository: UserDataRepository,
) : ViewModel() {
""",
        """class MainActivityViewModel @Inject constructor(
    private val userDataRepository: UserDataRepository,
    private val settingsHiddenRunner: SettingsHiddenRunner,
    @param:ApplicationScope private val appScope: CoroutineScope,
) : ViewModel() {
    private val _priorHide = MutableStateFlow(false)

    /**
     * Whether the settings that are down were hidden by a run of IMD that is no longer alive.
     *
     * Raised once per process, by [checkPriorHide] below.
     */
    val priorHide = _priorHide.asStateFlow()

    /**
     * Ask the gate, on arriving at the app proper.
     *
     * ⚠ **[PriorHide.suppress] with it**, as on every other surface: the flag is what stops a
     * second prompt appearing behind a dialog nobody has answered. It is cleared again by
     * [PriorHide.markHidden] on the next real hide, or by [PriorHide.settled] once the debt is
     * genuinely gone — so this is "do not ask twice", not "never ask again".
     */
    fun checkPriorHide() {
        viewModelScope.launch {
            if (PriorHide.shouldWarn(userDataRepository.userData.first().settingsHidden)) {
                PriorHide.suppress()

                _priorHide.update { true }
            }
        }
    }

    /**
     * `'Restore settings first'`, with no launch waiting behind it.
     *
     * [SettingsHiddenRunner.flushPendingReverts] rather than `unhide`: this settles the debts
     * that exist and leaves a device that owes none alone, where `unhide` would fall back to
     * applying the configured defaults. The Favourites tab's Unhide button makes the same call
     * for the same reason.
     */
    fun restorePriorHide() {
        _priorHide.update { false }

        appScope.launch {
            settingsHiddenRunner.flushPendingReverts()
        }
    }

    /** `'Ignore all previous reverts'`, and permanent here exactly as it is everywhere else. */
    fun discardPriorHide() {
        _priorHide.update { false }

        appScope.launch {
            settingsHiddenRunner.discardPendingReverts()
        }
    }
""",
    ),
]

ACTIVITY_EDITS: list[tuple[str, str]] = [
    (
        """import androidx.compose.runtime.CompositionLocalProvider
""",
        """import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.LaunchedEffect
""",
    ),
    (
        """import androidx.compose.runtime.setValue
""",
        """import androidx.compose.runtime.setValue
import androidx.compose.ui.res.stringResource
""",
    ),
    (
        """import com.android.geto.designsystem.component.LocalRevertConfigurationRequest
""",
        """import com.android.geto.designsystem.component.LocalRevertConfigurationRequest
import com.android.geto.designsystem.component.PriorHideDialog
""",
    ),
    (
        """import javax.inject.Inject
""",
        """import javax.inject.Inject
import com.android.geto.common.R as commonR
""",
    ),
    (
        """                                } else {
                                    GetoNavHost(navController = navController)
""",
        """                                } else {
                                    // Asked here rather than at the top of the activity, so a
                                    // first run being walked through permissions is not
                                    // interrupted by a report about a device it has not
                                    // touched yet. Keyed on Unit: once per composition of this
                                    // branch, and the ViewModel's own flag makes it once per
                                    // process.
                                    LaunchedEffect(Unit) {
                                        viewModel.checkPriorHide()
                                    }

                                    GetoNavHost(navController = navController)
""",
    ),
    (
        """                                    if (uiState.userData.setupNoticeVersion != 0 &&
                                        uiState.userData.settingsNoticeRevision <
                                        SETTINGS_NOTICE_REVISION
                                    ) {
""",
        """                                    // Ahead of all four, and not one of them: they are
                                    // advice about the app, this is a report that the device
                                    // is still locked down by a run of IMD that is gone.
                                    if (priorHide) {
                                        PriorHideDialog(
                                            title = stringResource(
                                                commonR.string.prior_hide_title,
                                            ),
                                            restoreLabel = stringResource(
                                                commonR.string.prior_hide_restore,
                                            ),
                                            ignoreLabel = stringResource(
                                                commonR.string.prior_hide_ignore,
                                            ),
                                            onRestore = viewModel::restorePriorHide,
                                            onIgnore = viewModel::discardPriorHide,
                                        )
                                    } else if (uiState.userData.setupNoticeVersion != 0 &&
                                        uiState.userData.settingsNoticeRevision <
                                        SETTINGS_NOTICE_REVISION
                                    ) {
""",
    ),
    (
        """                val mainActivityUiState by viewModel.uiState.collectAsStateWithLifecycle()
""",
        """                val mainActivityUiState by viewModel.uiState.collectAsStateWithLifecycle()

                val priorHide by viewModel.priorHide.collectAsStateWithLifecycle()
""",
    ),
]


def apply(path: Path, edits: list[tuple[str, str]], problems: list[str]) -> str | None:
    if not path.exists():
        problems.append(f"{path.name} is missing")

        return None

    text = path.read_text(encoding="utf-8")

    before = set(text.splitlines())

    for old, new in edits:
        found = text.count(old)

        if found != 1:
            head = old.strip().splitlines()[0][:70]

            problems.append(f"{path.name}: {found} of {head!r}")

            continue

        text = text.replace(old, new, 1)

    for line in set(text.splitlines()) - before:
        if len(line) > 120:
            problems.append(f"{path.name}: {len(line)} chars — {line.strip()[:60]}")

    return text


def main() -> int:
    problems: list[str] = []

    targets = [
        (ROOT / VIEW_MODEL, VIEW_MODEL_EDITS),
        (ROOT / ACTIVITY, ACTIVITY_EDITS),
    ]

    written: list[tuple[Path, str]] = []

    for path, edits in targets:
        text = apply(path, edits, problems)

        if text is not None:
            written.append((path, text))

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in written:
        path.write_text(text, encoding="utf-8")

    print("ok — opening IMD with a debt from a dead process now asks the same question")

    return 0


if __name__ == "__main__":
    sys.exit(main())
