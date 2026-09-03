#!/usr/bin/env python3
"""
v3-r2b3a — the popup dialog moves to `design-system`, because `feature/app-settings` can never
see `feature/apps`.

### The build error

    AppSettingsScreen.kt:72:33 Unresolved reference 'apps'
    AppSettingsScreen.kt:353:9 Unresolved reference 'PriorHideDialog'

`PriorHideDialog` was put beside `PermissionsLostDialog` in `feature/apps`, on the reasoning
recorded in r1i: that module is where the shared launch dialogs live and `app` can see it. That
holds for the shortcut and IMD+ — and not for the per-app settings screen, because
**`feature/apps` depends on `feature/app-settings`**, so the dependency can never run the other
way without a cycle.

⚠ **Nothing in the sandbox could have caught this.** `check4_deps` reads module dependency
declarations, not whether a *new* cross-module reference is legal; `check23` covers `internal`
visibility, not module reachability; and `check_new_types` asks whether a name is imported, which
this one was. The missing check is "does this file's module depend on the module it just imported
from", and it is now worth having — noted for the toolkit rather than bolted on mid-fix.

### Where it goes instead

`design-system`, beside `DialogContainer`, which every one of the five callers already uses.

⚠ **The strings stay in `common` and are passed in.** `design-system` does not depend on
`common` and has no `values/` folder at all; giving it one to hold three sentences would put
product copy in the design system and add a module to the translation sweep. Every caller can see
`common` — that is where `permissions_lost` already lives — so each passes the three strings it
already has access to. A design-system component owning no copy is also just the right shape.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DIALOG = "design-system/src/main/kotlin/com/android/geto/designsystem/component/PriorHideDialog.kt"

APPS = "feature/apps/src/main/kotlin/com/android/geto/feature/apps"

EFFECT = f"{APPS}/AppLaunchEffect.kt"
APPS_SCREEN = f"{APPS}/AppsScreen.kt"
FAV_SCREEN = f"{APPS}/FavouriteAppsScreen.kt"

SHORTCUT = "app/src/main/kotlin/com/android/geto/activity/shortcut/ShortcutActivity.kt"
AUTO_ACTIVITY = "app/src/main/kotlin/com/android/geto/activity/autohide/AutoHideActivity.kt"
APP_SETTINGS = (
    "feature/app-settings/src/main/kotlin/com/android/geto/feature/appsettings/"
    "AppSettingsScreen.kt"
)

DIALOG_BODY = '''/*
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
package com.android.geto.designsystem.component

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

/**
 * Settings are still down from a run of IMD that is no longer alive.
 *
 * Two answers, and both of them end in the launch going ahead — which is why neither button
 * dismisses without doing something and there is no third way out.
 *
 * ⚠ **Ignoring is permanent**, and the label the callers pass is written to say so. Afterwards
 * nothing in IMD knows those settings were ever on, and `Revert to default` is the only way back
 * to a known state.
 *
 * ⚠ **Here rather than in `feature/apps`, where the other launch dialogs live.** It was there
 * first, and it did not build: `feature/apps` depends on `feature/app-settings`, so the per-app
 * settings screen — which is one of the five surfaces that has to show this — can never see it.
 * `design-system` is the one module all five already use, for `DialogContainer` immediately
 * below.
 *
 * ⚠ **The sentences are parameters, not resources.** This module does not depend on `:common`,
 * where they live beside `permissions_lost`, and has no `values/` folder at all — giving it one
 * to hold three sentences would put product copy in the design system and add a module to the
 * translation sweep. Every caller can already read them.
 */
@Composable
fun PriorHideDialog(
    title: String,
    restoreLabel: String,
    ignoreLabel: String,
    modifier: Modifier = Modifier,
    onRestore: () -> Unit,
    onIgnore: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onIgnore) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(20.dp),
        ) {
            Text(text = title, style = MaterialTheme.typography.titleMedium)

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onIgnore) {
                    Text(text = ignoreLabel)
                }

                TextButton(onClick = onRestore) {
                    Text(text = restoreLabel)
                }
            }
        }
    }
}
'''

# The composable as part 2 wrote it into feature/apps, removed wholesale.
OLD_DIALOG = '''/**
 * Settings are still down from a run of IMD that is no longer alive.
 *
 * Two answers, and both of them end in the app opening — which is why neither button dismisses
 * without doing something and there is no third way out.
 *
 * ⚠ **`'Ignore all previous reverts'` is permanent**, and the label is written to say so. An
 * earlier draft read just `'Ignore'`, which sounds like "carry on" rather than "throw the record
 * away". Afterwards nothing in IMD knows those settings were ever on, and `Revert to default` is
 * the only way to a known state.
 *
 * Public, like the two dialogs above it, because the pinned shortcut and IMD+ live in the `app`
 * module and have to say exactly the same thing.
 */
@Composable
fun PriorHideDialog(
    modifier: Modifier = Modifier,
    onRestore: () -> Unit,
    onIgnore: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onIgnore) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(20.dp),
        ) {
            Text(
                text = stringResource(commonR.string.prior_hide_title),
                style = MaterialTheme.typography.titleMedium,
            )

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onIgnore) {
                    Text(text = stringResource(commonR.string.prior_hide_ignore))
                }

                TextButton(onClick = onRestore) {
                    Text(text = stringResource(commonR.string.prior_hide_restore))
                }
            }
        }
    }
}

'''

# The three sentences, at every call site. Callers all see :common already.
ARGS = """            title = stringResource(commonR.string.prior_hide_title),
            restoreLabel = stringResource(commonR.string.prior_hide_restore),
            ignoreLabel = stringResource(commonR.string.prior_hide_ignore),
"""

SCREEN_CALL_OLD = """        PriorHideDialog(
            onRestore = {
"""

SCREEN_CALL_NEW = """        PriorHideDialog(
""" + ARGS + """            onRestore = {
"""

EDITS: dict[str, list[tuple[str, str]]] = {
    EFFECT: [(OLD_DIALOG, "")],
    APPS_SCREEN: [
        (
            """import com.android.geto.designsystem.icon.GetoIcons
""",
            """import com.android.geto.designsystem.component.PriorHideDialog
import com.android.geto.designsystem.icon.GetoIcons
""",
        ),
        (
            """import kotlin.time.Duration.Companion.milliseconds
""",
            """import kotlin.time.Duration.Companion.milliseconds
import com.android.geto.common.R as commonR
""",
        ),
        (SCREEN_CALL_OLD, SCREEN_CALL_NEW),
    ],
    FAV_SCREEN: [
        (
            """import com.android.geto.designsystem.icon.GetoIcons
""",
            """import com.android.geto.designsystem.component.PriorHideDialog
import com.android.geto.designsystem.icon.GetoIcons
""",
        ),
        (
            """import com.android.geto.designsystem.R as designR
""",
            """import com.android.geto.common.R as commonR
import com.android.geto.designsystem.R as designR
""",
        ),
        (SCREEN_CALL_OLD, SCREEN_CALL_NEW),
    ],
    SHORTCUT: [
        (
            """import com.android.geto.feature.apps.PriorHideDialog
""",
            """import com.android.geto.designsystem.component.PriorHideDialog
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
            """import javax.inject.Inject
""",
            """import javax.inject.Inject
import com.android.geto.common.R as commonR
""",
        ),
        (
            """                    TerminalScreen.PriorHide -> PriorHideDialog(
                        onRestore = {
""",
            """                    TerminalScreen.PriorHide -> PriorHideDialog(
                        title = stringResource(commonR.string.prior_hide_title),
                        restoreLabel = stringResource(commonR.string.prior_hide_restore),
                        ignoreLabel = stringResource(commonR.string.prior_hide_ignore),
                        onRestore = {
""",
        ),
    ],
    AUTO_ACTIVITY: [
        (
            """import com.android.geto.feature.apps.PriorHideDialog
""",
            """import com.android.geto.designsystem.component.PriorHideDialog
""",
        ),
        (
            """import androidx.lifecycle.compose.collectAsStateWithLifecycle
""",
            """import androidx.compose.ui.res.stringResource
import androidx.lifecycle.compose.collectAsStateWithLifecycle
""",
        ),
        (
            """import dagger.hilt.android.AndroidEntryPoint
""",
            """import dagger.hilt.android.AndroidEntryPoint
import com.android.geto.common.R as commonR
""",
        ),
        (
            """                    PriorHideDialog(
                        onRestore = viewModel::restoreThenRun,
                        onIgnore = viewModel::discardThenRun,
                    )
""",
            """                    PriorHideDialog(
                        title = stringResource(commonR.string.prior_hide_title),
                        restoreLabel = stringResource(commonR.string.prior_hide_restore),
                        ignoreLabel = stringResource(commonR.string.prior_hide_ignore),
                        onRestore = viewModel::restoreThenRun,
                        onIgnore = viewModel::discardThenRun,
                    )
""",
        ),
    ],
    APP_SETTINGS: [
        (
            """import com.android.geto.feature.apps.PriorHideDialog
""",
            """import com.android.geto.designsystem.component.PriorHideDialog
""",
        ),
        (SCREEN_CALL_OLD, SCREEN_CALL_NEW),
    ],
}


def apply(path: Path, edits: list[tuple[str, str]], problems: list[str]) -> str | None:
    if not path.exists():
        problems.append(f"{path} is missing")

        return None

    text = path.read_text(encoding="utf-8")

    for old, new in edits:
        found = text.count(old)

        if found != 1:
            head = old.strip().splitlines()[0][:70] if old.strip() else old[:70]

            problems.append(f"{path.name}: {found} of {head!r}")

            continue

        text = text.replace(old, new, 1)

    return text


def main() -> int:
    problems: list[str] = []

    staged: dict[Path, str] = {ROOT / DIALOG: DIALOG_BODY}

    for name, edits in EDITS.items():
        path = ROOT / name

        before = set(path.read_text(encoding="utf-8").splitlines()) if path.exists() else set()

        text = apply(path=path, edits=edits, problems=problems)

        if text is None:
            continue

        staged[path] = text

        for line in set(text.splitlines()) - before:
            if len(line) > 120:
                problems.append(f"{path.name}: {len(line)} chars — {line.strip()[:60]}")

    # Nothing anywhere may still reach for the dialog in its old home.
    for kotlin in sorted(ROOT.rglob("*.kt")):
        if "build" in kotlin.relative_to(ROOT).parts:
            continue

        body = staged.get(kotlin) or kotlin.read_text(encoding="utf-8")

        if "com.android.geto.feature.apps.PriorHideDialog" in body:
            problems.append(f"{kotlin.relative_to(ROOT)}: still imports the old home")

    # Five call sites, each passing all three sentences.
    calls = sum(
        (staged.get(k) or k.read_text(encoding="utf-8")).count("PriorHideDialog(")
        for k in sorted(ROOT.rglob("*.kt"))
        if "build" not in k.relative_to(ROOT).parts
    )

    # Five uses plus the declaration.
    if calls != 6:
        problems.append(f"{calls} PriorHideDialog( occurrences, expected 6")

    titles = sum(
        (staged.get(k) or k.read_text(encoding="utf-8")).count("commonR.string.prior_hide_title")
        for k in sorted(ROOT.rglob("*.kt"))
        if "build" not in k.relative_to(ROOT).parts
    )

    if titles != 5:
        problems.append(f"{titles} call sites pass the title, expected 5")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")

    print("ok — the dialog lives in design-system; five callers pass their own sentences")

    return 0


if __name__ == "__main__":
    sys.exit(main())
