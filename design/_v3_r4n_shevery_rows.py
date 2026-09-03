#!/usr/bin/env python3
"""v3-r4n item 6 — the Shizuku service row greys on Shevery instead of leaving the screen.

The author:

    "Greyed, unchecked (memory-preserving) Shizuku service checkboxes on Shevery in Settings to
     hide, Revert to default configuration, settings templates and per-app config — just like
     for DOOA."

⚠ **This reverses a decision he made earlier in the same session** — *"keep them hidden until
Shevery's engine lands"*, which is what `appSettingHidden` implements. The reversal was named and
confirmed before any of this was written. `appSettingHidden` and its host assertions come out.

---

## What was removing the rows

* both configuration dialogs wrapped the row in `if (shizukuForkMode.supportsIntents)`;
* `AppSettingsViewModel` filtered both the added rows and the template list through
  `appSettingHidden`;
* `SettingsScreen` ran the revert dialog's own state through `withoutShizukuWhenNoIntents`, which
  did more than shorten a count: the dialog saves its draft, so **a Save on Shevery dropped the
  user's stored Shizuku answer altogether.** That is the opposite of "memory-preserving", and it
  goes with the rest.

⚠ **`effectiveRevertDefaults` keeps `withoutShizukuWhenNoIntents`.** The engine is not changed by
any of this: a revert on Shevery still never broadcasts a start it has no intent for. Only the
drawing and the stored answer change.

## The "x of y" line

Now that the row is drawn on Shevery it is counted, which is the author's answer when asked:
the number under the row matches the rows on screen, the same rule the hide dialog follows.
That falls out of dropping `withoutShizukuWhenNoIntents` from `revertStates` — no separate edit.

## Why a new type

`blockedPaths: List<String>?` carried two questions in one value: which paths to show, and —
by being empty — which of two sentences to use. A second empty-path case arrives here (the
Shizuku row on Shevery, which needs its own sentence, not the DOOA one), so the convention stops
working. `BlockedExplanation` says both things out loud. The `paths.isEmpty()` trick is deleted
from both dialogs rather than extended.

## The string

`shizuku_thedjchi_only` — *"managing the Shizuku service is only supported for Thedjchi fork of
Shizuku"*, the author's chosen wording, a parallel of his `dooa_thedjchi_only`. English only;
deferred like the rest.

Asserts every anchor matches exactly once, that no `supportsIntents` wrapper survives in either
dialog, that the engine's gate is untouched, and that `appSettingHidden` is gone from every file
that named it. Writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HIDE = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/SettingsToHideDialog.kt"
REVERT = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/RevertDefaultsDialog.kt"
BLOCKED = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/BlockedExplanation.kt"
SCREEN = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"
MODEL = "domain/model/src/main/kotlin/com/android/geto/domain/model/OverlayManagement.kt"
VM = "feature/app-settings/src/main/kotlin/com/android/geto/feature/appsettings/AppSettingsViewModel.kt"
STRINGS = "feature/settings/src/main/res/values/strings.xml"
CHECK = "tools/check_translations.py"
TESTS = "tools/host-tests/DomainLogicTests.kt"

LICENCE = """/*
 *
 *   Copyright 2026 soul_99 (suIMD)
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
"""

NEW_FILE = LICENCE + '''package com.android.geto.feature.settings.dialog

/**
 * Why a greyed control in one of the two configuration dialogs refuses, in the words the
 * pop-up should say.
 *
 * ⚠ **Replaces `List<String>?`, which carried two questions in one value.** Both dialogs used
 * to keep a nullable list of location trees and pick the sentence from whether it was empty:
 * empty meant "Shevery, and the thing is unsupported rather than unconfigured". That worked
 * while exactly one row had nothing to point at. r4n gives the Shizuku row the same shape on
 * the same fork and a *different* sentence — managing the service, not Display over other
 * apps — so the trick stops being able to tell them apart.
 *
 * [paths] empty is now only what it looks like: nothing to point at. Which sentence to use is
 * [message], said out loud by whoever raised it.
 */
internal data class BlockedExplanation(
    val message: String,
    val paths: List<String> = emptyList(),
)
'''

EDITS: list[tuple[str, str, str, str]] = []


def edit(rel: str, name: str, old: str, new: str) -> None:
    EDITS.append((rel, name, old, new))


# ---------------------------------------------------------------------------------------
# The shared pieces, applied to both dialogs
# ---------------------------------------------------------------------------------------
OLD_STATE = """    // Null while nothing is blocked; a list of location trees for something that can be
    // configured; and empty for the one case with nothing to point at - Shevery, where
    // Display over other apps is unsupported rather than unconfigured. The empty list is what
    // picks the author's fork sentence over his configure-first one.
    var blockedPaths by remember { mutableStateOf<List<String>?>(null) }

    val accessibilityPath = stringResource(R.string.help_path_accessibility)

    val manageShizukuPath = stringResource(R.string.help_path_manage_shizuku)"""

NEW_STATE = """    // Null while nothing is blocked. ⚠ **A BlockedExplanation since r4n, not a list of
    // paths** - the Shizuku row on Shevery has nothing to point at *and* its own sentence, so
    // "empty list means the fork sentence" could no longer tell the two apart.
    var blocked by remember { mutableStateOf<BlockedExplanation?>(null) }

    val accessibilityPath = stringResource(R.string.help_path_accessibility)

    val manageShizukuPath = stringResource(R.string.help_path_manage_shizuku)

    // Hoisted because stringResource cannot be called from inside the row callbacks below.
    val configureFirst = stringResource(R.string.configure_first)

    val dooaThedjchiOnly = stringResource(R.string.dooa_thedjchi_only)

    val shizukuThedjchiOnly = stringResource(R.string.shizuku_thedjchi_only)

    // ⚠ **One expression for the Shizuku row's three states, read by `checked`, by `enabled`
    // and by the press.** `null` is exactly `UserData.canHide(ManualRevertTarget.Shizuku)` -
    // 'Manage Shizuku' on and a fork that answers intents - so the row and the engine cannot
    // disagree. The fork case comes first: on Shevery there is nothing to go and switch on,
    // so sending the reader to Manage Shizuku would be sending them nowhere.
    val shizukuBlocked: BlockedExplanation? = when {
        !shizukuForkMode.supportsIntents -> BlockedExplanation(message = shizukuThedjchiOnly)

        !manageShizukuEffective -> BlockedExplanation(
            message = configureFirst,
            paths = listOf(manageShizukuPath),
        )

        else -> null
    }"""

OLD_RENDER = """    blockedPaths?.let { paths ->
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
    }"""

NEW_RENDER = """    blocked?.let { explanation ->
        ConfigureFirstDialog(
            message = explanation.message,
            paths = explanation.paths,
            dismissLabel = stringResource(R.string.understood),
            onDismissRequest = { blocked = null },
        )
    }"""

OLD_ACCESSIBILITY = """            onBlockedClick = { blockedPaths = listOf(accessibilityPath) },"""

NEW_ACCESSIBILITY = """            onBlockedClick = {
                blocked = BlockedExplanation(
                    message = configureFirst,
                    paths = listOf(accessibilityPath),
                )
            },"""

OLD_OVERLAY_CLICK = """            onBlockedClick = { blockedPaths = overlayBlockedPaths.orEmpty() },"""

NEW_OVERLAY_CLICK = """            onBlockedClick = {
                blocked = BlockedExplanation(
                    // The fork sentence when there is nothing to point at, his configure-first
                    // one otherwise - the same choice the old empty-list convention made, now
                    // written where it is made instead of inferred at the dialog.
                    message = if (overlayBlockedPaths.isNullOrEmpty()) {
                        dooaThedjchiOnly
                    } else {
                        configureFirst
                    },
                    paths = overlayBlockedPaths.orEmpty(),
                )
            },"""

for rel in (HIDE, REVERT):
    edit(rel, "the blocked state", OLD_STATE, NEW_STATE)
    edit(rel, "the blocked dialog", OLD_RENDER, NEW_RENDER)
    edit(rel, "the accessibility row's press", OLD_ACCESSIBILITY, NEW_ACCESSIBILITY)
    edit(rel, "the overlay row's press", OLD_OVERLAY_CLICK, NEW_OVERLAY_CLICK)

# ---------------------------------------------------------------------------------------
# The Shizuku rows themselves
# ---------------------------------------------------------------------------------------
edit(
    HIDE,
    "the hide dialog's Shizuku row",
    """        // Only for a fork this app can actually start and stop. Shevery's service follows the
        // debugging transport instead - the two rows above already decide it - so a row
        // offering to hide it separately would promise something IMD does not do.
        if (shizukuForkMode.supportsIntents) {
            SettingToHideRow(
                label = stringResource(R.string.revert_defaults_shizuku),
                note = stringResource(R.string.settings_to_hide_shizuku_note),
                // ⚠ **Unticked while blocked, and only in the drawing** - the same rule the
                // two rows around it follow. `draft` is untouched, so the stored answer
                // survives 'Manage Shizuku' being switched off and comes back when it is
                // switched on again; a Save taken in this state writes the same draft back.
                checked = manageShizukuEffective &&
                    draft[ManualRevertTarget.Shizuku] == true,
                // ⚠ **Spec item 9, and it was missing.** This row was drawn live with the
                // master switch off, offering to stop a service IMD is not managing - and
                // since r4m the hide would have refused it anyway, so the control was a
                // promise the engine had already broken.
                enabled = manageShizukuEffective,
                onBlockedClick = { blockedPaths = listOf(manageShizukuPath) },
                onCheckedChange = { wanted ->
                    toggle(ManualRevertTarget.Shizuku, wanted)

                    // Only on the way on, and only then. Both forks need something switched
                    // in their own app before IMD can drive their service, and neither says
                    // so anywhere the user would look - the failure is silent and arrives
                    // later, at the moment a hide is supposed to work.
                    if (wanted) showShizukuServiceNotice = true
                },
            )
        }""",
    """        // ⚠ **Drawn on every fork since r4n, greyed where it cannot work.** It used to be
        // wrapped in `if (shizukuForkMode.supportsIntents)`, so on Shevery the row was not
        // there at all - the author reversed that: *"greyed, unchecked (memory-preserving)
        // Shizuku service checkboxes on Shevery ... just like for DOOA"*. Greying does not
        // change the engine: `effectiveSettingsToHide` already folds a refused target to
        // false, and `withoutShizukuWhenNoIntents` still keeps the entry out of a revert.
        SettingToHideRow(
            label = stringResource(R.string.revert_defaults_shizuku),
            note = stringResource(R.string.settings_to_hide_shizuku_note),
            // ⚠ **Unticked while blocked, and only in the drawing** - the same rule the two
            // rows around it follow. `draft` is untouched, so the stored answer survives both
            // 'Manage Shizuku' being switched off and the fork being Shevery, and comes back
            // when either changes; a Save in this state writes the same draft back.
            checked = shizukuBlocked == null &&
                draft[ManualRevertTarget.Shizuku] == true,
            // ⚠ **Spec item 9 plus the fork, in one expression** - see `shizukuBlocked`. This
            // row was once drawn live with the master switch off, offering to stop a service
            // IMD is not managing, which the engine had already refused.
            enabled = shizukuBlocked == null,
            onBlockedClick = { blocked = shizukuBlocked },
            onCheckedChange = { wanted ->
                toggle(ManualRevertTarget.Shizuku, wanted)

                // Only on the way on, and only then. Both forks need something switched
                // in their own app before IMD can drive their service, and neither says
                // so anywhere the user would look - the failure is silent and arrives
                // later, at the moment a hide is supposed to work.
                if (wanted) showShizukuServiceNotice = true
            },
        )""",
)

edit(
    REVERT,
    "the revert dialog's Shizuku row",
    """        // Only for a fork this app can start and stop. Shevery's service comes back when its
        // own ErrorProtect watchdog sees the debugging transport again, so "unhide Shizuku on
        // revert" is decided by the debugging rows above rather than by anything here.
        if (shizukuForkMode.supportsIntents) {
            RevertDefaultRow(
                label = stringResource(R.string.revert_defaults_shizuku),
                note = stringResource(R.string.revert_defaults_shizuku_note),
                // Unticked and greyed with 'Manage Shizuku' off, in the drawing only - spec
                // item 9 names this dialog as well as the hide one.
                checked = manageShizukuEffective &&
                    draft[ManualRevertTarget.Shizuku] == true,
                enabled = manageShizukuEffective,
                onBlockedClick = { blockedPaths = listOf(manageShizukuPath) },
                onCheckedChange = { toggle(ManualRevertTarget.Shizuku, it) },
            )
        }""",
    """        // ⚠ **Drawn on every fork since r4n, greyed where it cannot work** - the author's
        // reversal, and the same treatment the row above it gets. On Shevery the service
        // still comes back only when its own ErrorProtect watchdog sees the debugging
        // transport again, which the debugging rows above decide; the row says so by being
        // greyed rather than by being absent.
        RevertDefaultRow(
            label = stringResource(R.string.revert_defaults_shizuku),
            note = stringResource(R.string.revert_defaults_shizuku_note),
            // Unticked and greyed while blocked, in the drawing only - spec item 9 names this
            // dialog as well as the hide one, and r4n adds the fork to the same expression.
            checked = shizukuBlocked == null &&
                draft[ManualRevertTarget.Shizuku] == true,
            enabled = shizukuBlocked == null,
            onBlockedClick = { blocked = shizukuBlocked },
            onCheckedChange = { toggle(ManualRevertTarget.Shizuku, it) },
        )""",
)

# ---------------------------------------------------------------------------------------
# The revert dialog's state, and therefore its count and what a Save writes
# ---------------------------------------------------------------------------------------
edit(
    SCREEN,
    "the revert states",
    """    val revertStates = userData.revertDefaults
        .withoutShizukuWhenNoIntents(userData.shizukuForkMode)""",
    """    // ⚠ **The stored ticks, whole, since r4n.** This used to drop the Shizuku entry on a
    // fork with no intents, which did two things: it shortened the "x of y" line, and — because
    // this map is the dialog's draft and the draft is what Save writes — **a Save on Shevery
    // deleted the user's stored Shizuku answer.** That is the opposite of the memory-preserving
    // behaviour the author asked for. The row is drawn and greyed on every fork now, so it is
    // counted too: the number under the row matches the rows on screen, which is his answer.
    //
    // The engine is unaffected: `effectiveRevertDefaults` still applies
    // `withoutShizukuWhenNoIntents`, so no revert broadcasts a start it has no intent for.
    val revertStates = userData.revertDefaults""",
)

# ---------------------------------------------------------------------------------------
# appSettingHidden comes out
# ---------------------------------------------------------------------------------------
edit(
    MODEL,
    "appSettingHidden and the orphaned KDoc above it",
    """/**
 * Whether a per-app template or row should leave the screen altogether rather than grey.
 *
 * ⚠ **Exactly one case, and it is the author's own answer** - the Shizuku marker on a fork with
 * no start-stop intent. Everything else that cannot work is drawn and greyed, because greying
 * says *what to go and configure*; here there is nothing to configure. Shevery's service
 * follows the debugging transport rather than anything IMD sends, so the control has no engine
 * behind it until the stop-intent redesign lands, and a greyed row would be explaining a
 * control that does not exist yet.
 *
 * Held apart from [appSettingBlocked] rather than folded into it so that the difference between
 * "cannot work yet" and "will never work on this fork" stays stated.
 */
fun appSettingHidden(userData: UserData, key: String): Boolean =
    key == AppSettingKeys.SHIZUKU_SERVICE && !userData.shizukuForkMode.supportsIntents

fun appSettingBlocked(userData: UserData, key: String): Boolean =""",
    """fun appSettingBlocked(userData: UserData, key: String): Boolean =""",
)

# ⚠ **The imports go with the calls.** `check12_unusedimports` would catch a leftover, but only
# after the author had already tried to build — and `combine` becomes unused here too, because
# both of this file's uses of it existed only to fold userData into a filter.
edit(
    VM,
    "the appSettingHidden import",
    """import com.android.geto.domain.model.appSettingHidden
""",
    "",
)

edit(
    VM,
    "the now-unused combine import",
    """import kotlinx.coroutines.flow.combine
""",
    "",
)

edit(
    TESTS,
    "the appSettingHidden import",
    """import com.android.geto.domain.model.appSettingHidden
""",
    "",
)

edit(
    VM,
    "the added-rows filter",
    """    // ⚠ **Shown and greyed, not removed.** The author's instruction for open item 2. Only
    // [appSettingHidden] takes a row off the screen, and it answers for exactly one case -
    // the Shizuku marker on a fork with no intents, which has no engine behind it yet.
    val appSettingsUiState =
        combine(
            appSettingsRepository.getAppSettingsFlowByComponentName(componentName = componentName),
            userDataRepository.userData,
        ) { appSettings, userData ->
            appSettings.filterNot { appSettingHidden(userData = userData, key = it.key) }
        }.map(AppSettingsUiState::Success).stateIn(""",
    """    // ⚠ **Shown and greyed, not removed — every row, on every fork, since r4n.** There used
    // to be one exception: the Shizuku marker on a fork with no intents left the screen through
    // `appSettingHidden`. The author reversed that — *"greyed, unchecked (memory-preserving)
    // Shizuku service checkboxes on Shevery ... just like for DOOA"* — so nothing is filtered
    // here at all now, and `appSettingBlocked` greys whatever cannot run.
    val appSettingsUiState =
        appSettingsRepository.getAppSettingsFlowByComponentName(componentName = componentName)
            .map(AppSettingsUiState::Success).stateIn(""",
)

edit(
    VM,
    "the templates filter",
    """    // The same rule as the rows above: offered and greyed, so a press can say what to go and
    // configure. Only the no-intents Shizuku marker leaves the list.
    val appSettingTemplates = combine(
        _appSettingTemplates,
        userDataRepository.userData,
    ) { templates, userData ->
        templates.filterNot { appSettingHidden(userData = userData, key = it.key) }
    }.onStart {
        getAppSettingTemplates()
    }.stateIn(""",
    """    // The same rule as the rows above: offered and greyed, so a press can say what to go and
    // configure. Nothing leaves the list any more — r4n took the one exception out.
    val appSettingTemplates = _appSettingTemplates.onStart {
        getAppSettingTemplates()
    }.stateIn(""",
)

# ---------------------------------------------------------------------------------------
# The string
# ---------------------------------------------------------------------------------------
edit(
    STRINGS,
    "the fork sentence",
    """    <string name="dooa_thedjchi_only">managing Display over other apps is only supported for Thedjchi fork of Shizuku</string>""",
    """    <string name="dooa_thedjchi_only">managing Display over other apps is only supported for Thedjchi fork of Shizuku</string>
    <string name="shizuku_thedjchi_only">managing the Shizuku service is only supported for Thedjchi fork of Shizuku</string>""",
)

edit(
    CHECK,
    "the DEFERRED set",
    """    # r4n: the IMD+ requirement row's Shevery suffix.""",
    """    # r4n: the Shizuku row's fork sentence, beside dooa_thedjchi_only.
    "shizuku_thedjchi_only",
    # r4n: the IMD+ requirement row's Shevery suffix.""",
)

# ---------------------------------------------------------------------------------------
# The host assertions
# ---------------------------------------------------------------------------------------
edit(
    TESTS,
    "the appSettingHidden assertions",
    """    // 7. ⚠ **Hidden is not the same as blocked, and it is one key on one fork.** Everything
    //    else that cannot work is drawn and greyed; only the Shizuku marker on a fork with no
    //    intents leaves the screen, because there the control has no engine behind it yet.
    check(
        "shevery hides the shizuku marker",
        appSettingHidden(userData = shevery, key = AppSettingKeys.SHIZUKU_SERVICE),
    )
    check(
        "and hides nothing else",
        !appSettingHidden(userData = shevery, key = AppSettingKeys.SYSTEM_ALERT_WINDOW) &&
            !appSettingHidden(userData = shevery, key = AppSettingKeys.ACCESSIBILITY_ENABLED) &&
            !appSettingHidden(userData = shevery, key = "screen_brightness"),
    )
    check(
        "thedjchi hides nothing at all, with the master switch either way",
        !appSettingHidden(userData = thedjchi, key = AppSettingKeys.SHIZUKU_SERVICE) &&
            !appSettingHidden(
                userData = thedjchi.copy(manageShizuku = false),
                key = AppSettingKeys.SHIZUKU_SERVICE,
            ),
    )

    // ⚠ **The pairing, and it is the assertion worth having.** A row hidden but not blocked
    // would leave the screen while the hide went on acting on it - the exact defect the two
    // filters r4m removed used to carry.
    for (fork in listOf(shevery, thedjchi, thedjchi.copy(manageShizuku = false))) {
        for (key in listOf(
            AppSettingKeys.SYSTEM_ALERT_WINDOW,
            AppSettingKeys.SHIZUKU_SERVICE,
            AppSettingKeys.ACCESSIBILITY_ENABLED,
            "screen_brightness",
        )) {
            if (appSettingHidden(userData = fork, key = key)) {
                check(
                    "anything hidden is also blocked: $key",
                    appSettingBlocked(userData = fork, key = key),
                )
            }
        }
    }
}""",
    """    // 7. ⚠ **Nothing leaves the screen any more — r4n.** `appSettingHidden` is gone, and with
    //    it the one exception to "grey, don't remove": the Shizuku marker on a fork with no
    //    intents. The author reversed his earlier *"keep them hidden until Shevery's engine
    //    lands"*. What replaces those assertions is the rule the removal has to satisfy —
    //    **every gated key is blocked on every fork that cannot run it**, so a row that is
    //    drawn is either live or greyed, and never drawn-and-acted-on.
    for (fork in listOf(shevery, thedjchi.copy(manageShizuku = false))) {
        for (key in listOf(AppSettingKeys.SYSTEM_ALERT_WINDOW, AppSettingKeys.SHIZUKU_SERVICE)) {
            check(
                "a marker that cannot run is blocked, not removed: $key",
                appSettingBlocked(userData = fork, key = key),
            )
        }
    }

    // And the engine's own gate is the same expression, which is what stops a greyed row and
    // a running hide drifting apart.
    check(
        "the hide map refuses exactly what the screen greys",
        shevery.effectiveSettingsToHide[ManualRevertTarget.Shizuku] == false &&
            shevery.effectiveSettingsToHide[ManualRevertTarget.DisplayOverOtherApps] == false,
    )
}""",
)


def main() -> int:
    staged: dict[Path, str] = {}

    for rel, name, old, new in EDITS:
        path = ROOT / rel

        if not path.is_file():
            print(f"REFUSED: missing {rel}")
            return 1

        text = staged.get(path, path.read_text(encoding="utf-8"))

        found = text.count(old)

        if found != 1:
            print(f"REFUSED: {rel}\n  {name} matched {found} time(s), expected exactly 1")
            return 1

        staged[path] = text.replace(old, new, 1)

    # The new file.
    blocked_path = ROOT / BLOCKED

    if blocked_path.exists():
        print(f"REFUSED: {BLOCKED} already exists")
        return 1

    staged[blocked_path] = NEW_FILE

    # ⚠ **No `supportsIntents` wrapper may survive in either dialog.** Spelled as the statement
    # it can only be, because both replacement comments name the property in prose.
    for rel in (HIDE, REVERT):
        if "if (shizukuForkMode.supportsIntents) {" in staged[ROOT / rel]:
            print(f"REFUSED: {rel} still wraps a row in the fork check")
            return 1

        # And the old state name must be gone, or one call site was missed.
        if "blockedPaths" in staged[ROOT / rel].replace("overlayBlockedPaths", ""):
            print(f"REFUSED: {rel} still carries the old blockedPaths state")
            return 1

    # ⚠ **The engine's gate must be untouched.** This whole item is a drawing change; a build
    # that also dropped `withoutShizukuWhenNoIntents` from `effectiveRevertDefaults` would start
    # broadcasting starts on a fork with no intent for them.
    model = staged[ROOT / MODEL]

    if ".withoutShizukuWhenNoIntents(mode = shizukuForkMode)" not in model:
        print("REFUSED: effectiveRevertDefaults no longer drops Shizuku on a no-intents fork")
        return 1

    # `appSettingHidden` must be gone everywhere. Spelled with its call and import forms, never
    # as a bare word — the replacement comments above name it.
    for rel in (MODEL, VM, TESTS):
        text = staged[ROOT / rel]

        for spelling in ("appSettingHidden(", "import com.android.geto.domain.model.appSettingHidden"):
            if spelling in text:
                print(f"REFUSED: {rel} still carries {spelling!r}")
                return 1

    # ⚠ **`appSettingBlocked` inherits the KDoc that was orphaned above the removed function.**
    # Asserted, because the whole point of the removal is that one question is left, and a
    # question with no documentation is how the next round re-adds the other one.
    marker = "Whether a per-app template or row names something IMD cannot act on right now."

    doc = model.index(marker)
    fn = model.index("fun appSettingBlocked(")

    if not doc < fn:
        print("REFUSED: appSettingBlocked's KDoc no longer sits above it")
        return 1

    if "*/" not in model[doc:fn] or model[doc:fn].count("/**") != 0:
        print("REFUSED: a second KDoc block still sits between the doc and the function")
        return 1

    # The VM must have dropped its now-unused imports rather than leaving them to check12.
    vm = staged[ROOT / VM]

    for gone in ("combine(\n            appSettingsRepository", "combine(\n        _appSettingTemplates"):
        if gone in vm:
            print(f"REFUSED: {VM} still combines where it no longer needs to")
            return 1

    # And the dialogs must actually read the new sentence.
    if "R.string.shizuku_thedjchi_only" not in staged[ROOT / HIDE]:
        print(f"REFUSED: {HIDE} does not read the new fork sentence")
        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")

    print(f"  ok        {BLOCKED}  :: new")
    print(f"  ok        {HIDE}  :: row drawn on every fork")
    print(f"  ok        {REVERT}  :: row drawn on every fork")
    print(f"  ok        {SCREEN}  :: revert draft keeps the Shizuku entry")
    print(f"  ok        {MODEL}  :: appSettingHidden removed")
    print(f"  ok        {VM}  :: both filters removed")
    print(f"  ok        {STRINGS}  :: shizuku_thedjchi_only")
    print(f"  ok        {CHECK}  :: key deferred")
    print(f"  ok        {TESTS}  :: hidden assertions replaced by the blocked rule")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s) + 1 new file")

    return 0


if __name__ == "__main__":
    sys.exit(main())
