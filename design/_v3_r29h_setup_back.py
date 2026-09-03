#!/usr/bin/env python3
"""
r29h — the six configuration steps get a Back button, and Next becomes the filled button.

The author: *"in the setup screens after initial shizuku and notification permission screen add a
back button to take back to previous screen"*, then *"put it left of next button, make naxt button
bold with solid background"*.

Built from `design/template_r29_setup_footer.html`, panel 1.

⚠ **Runs after `_v3_r29f_translations.py`, not before it.** The `back` string is inserted beside
`next` in all eleven `common` string files, and until r29f lands there is no `next` in any of the
ten locale ones — `skip`, `next` and `retry` were among the 150 keys this round translated. Run in
the other order this script asserts its way to a stop and writes nothing, which is the ordering
trap of handover §8 in its scheduling form.

## Where Back appears, and where it stops

Pages `ACCESSIBILITY` (2) through `CUSTOMISE_UI` (7). ⚠ **`SHIZUKU` is the floor**, because that is
what *"after initial shizuku and notification permission screen"* asks for: Back from the first
configuration step lands on the Shizuku page, and nothing walks back into `PERMISSIONS`, which is a
gate rather than a step — it cannot be passed until both permissions are in place, so returning to
it could only ever be a dead end.

`previousBefore` is the mirror of `nextAfter` and is written the same way, for the same reason its
comment gives: five hops through optional pages, and a decision written out at each hop is how one
becomes reachable from a single direction.

⚠ **The reminders page is untouched.** `SetupCompletePage` has had its own `onBack` since r4r, and
it already refuses to offer one when `remindersOnly` opened the flow there.

## The layout, and why it is not SpaceBetween

`SettingsPage(flat = true)` and the three hand-rolled footers all arrange **SpaceBetween**, which
is what put Skip at one edge and Next at the other. With *three* buttons SpaceBetween would space
them evenly across the width and Back would float in the middle of nowhere.

So the setup half of every footer is now one composable, `SetupNextButtons`, and it opens with a
`Spacer(Modifier.weight(1f))`. A weighted spacer eats all the free space, which leaves SpaceBetween
with nothing to distribute — so **every existing arrangement expression is left exactly as it is**
and still does the right thing in the Settings case. Skip stays hard left; Back and Next travel
together at the right.

## What the Settings dialogs keep

⚠ **The filled Next is scoped to the setup flow, and that is the author's own scope** — *"in the
setup screens"*. Five of these six dialogs also open from the settings list, where the same footer
says Cancel/Update or Save. Those branches are untouched: still two flat text buttons, still
`Arrangement.End`. Panel 3 of the template is the version that was not chosen.

## Not done, and said rather than left quiet

`OverlayStepWaiting` — the "still reading the overlay list" state of the Overlay step — has Skip and
Retry and no Next, so there is no Next for a Back to sit left of. It resolves itself in seconds or
falls through to the real step. Left alone; raised in the round notes.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

COMMON_DIR = ROOT / "common/src/main/res"
DIALOGS = ROOT / "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog"
STEPS = ROOT / "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SetupSteps.kt"
ACTIONS = ROOT / "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SetupStepActions.kt"
SETUP = ROOT / "app/src/main/kotlin/com/android/geto/onboarding/SetupScreen.kt"

BACK = {
    "": "Back",
    "hi": "वापस",
    "ar": "رجوع",
    "b+pt+BR": "Voltar",
    "b+zh+Hans": "上一步",
    "de": "Zurück",
    "es": "Atrás",
    "fr": "Retour",
    "ja": "戻る",
    "ko": "뒤로",
    "ru": "Назад",
}

failures: list[str] = []
writes: dict[Path, str] = {}


def check(condition: bool, message: str) -> bool:
    if not condition:
        failures.append(message)

    return condition


def replace_once(text: str, old: str, new: str, label: str) -> str:
    found = text.count(old)

    if not check(found == 1, f"{label}: found {found}x, expected 1"):
        return text

    return text.replace(old, new, 1)


def code(text: str) -> str:
    return "\n".join(
        line for line in text.splitlines()
        if not line.strip().startswith(("//", "*", "/*", "/**"))
    )


# ================================================================ the string

for locale, word in BACK.items():
    folder = "values" if not locale else f"values-{locale}"

    path = COMMON_DIR / folder / "strings.xml"

    if not check(path.exists(), f"common/{folder}: strings.xml is missing"):
        continue

    text = path.read_text(encoding="utf-8")

    if not check(
        '<string name="back">' not in text,
        f"common/{folder}: a 'back' string already exists",
    ):
        continue

    anchor = '<string name="next">'

    if not check(text.count(anchor) == 1, f"common/{folder}: no single 'next' to anchor on"):
        continue

    line = [ln for ln in text.splitlines() if anchor in ln][0]

    text = text.replace(line, f'{line}\n    <string name="back">{word}</string>', 1)

    writes[path] = text

check(len(writes) == 11, f"the back string landed in {len(writes)} files, expected 11")

# ================================================================ the shared buttons

check(not ACTIONS.exists(), "SetupStepActions.kt already exists")

writes[ACTIONS] = '''/*
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
package com.android.geto.feature.settings

import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.width
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.android.geto.common.R as commonR

/**
 * The right-hand end of a setup step's footer: Back, then Next.
 *
 * The author, from the flow: *"put it left of next button, make naxt button bold with solid
 * background"*. Next is a filled [Button] rather than a `TextButton`, and its label is bold — six
 * steps of two identical flat words gave no clue which one carries the flow.
 *
 * ⚠ **It opens with a weighted spacer, and that is what makes it drop into six different
 * footers.** Every one of them arranges **SpaceBetween** so that Skip sits at the left edge; with
 * three buttons SpaceBetween would spread all three evenly and leave Back stranded mid-width. A
 * weighted spacer consumes the free space instead, so there is none left to distribute and the
 * arrangement becomes a no-op — which means not one of those six `horizontalArrangement`
 * expressions had to change, and the Settings case they also serve still behaves exactly as it
 * did.
 *
 * ⚠ **Setup only.** Five of these dialogs also open from the settings list, where this footer
 * reads Cancel/Update or Save and stays two flat text buttons. That is the author's own scope —
 * *"in the setup screens"* — and the callers branch on `onSkip != null` to honour it.
 *
 * @param onBack null on the first step that has nothing behind it, which draws Next alone.
 */
@Composable
internal fun RowScope.SetupNextButtons(
    onBack: (() -> Unit)?,
    onNext: () -> Unit,
    enabled: Boolean = true,
) {
    Spacer(modifier = Modifier.weight(1f))

    if (onBack != null) {
        TextButton(onClick = onBack) {
            Text(text = stringResource(commonR.string.back))
        }

        // The two are a pair and read as one control; the gap is what stops the filled button
        // looking like it has swallowed the word beside it.
        Spacer(modifier = Modifier.width(4.dp))
    }

    Button(onClick = onNext, enabled = enabled) {
        Text(
            text = stringResource(commonR.string.next),
            fontWeight = FontWeight.Bold,
        )
    }
}
'''

# ================================================================ the two list dialogs

for name, updater in (
    ("AccessibilityServicesDialog", "onUpdateManagedAccessibilityServices"),
    ("OverlayPackagesDialog", "onUpdateManagedOverlayPackages"),
):
    path = DIALOGS / f"{name}.kt"

    text = path.read_text(encoding="utf-8")

    text = replace_once(
        text,
        "    onSkip: (() -> Unit)? = null,\n",
        "    onSkip: (() -> Unit)? = null,\n"
        "    /** Set by the setup flow on every step that has one behind it. */\n"
        "    onBack: (() -> Unit)? = null,\n",
        f"{name}: the onBack parameter",
    )

    text = replace_once(
        text,
        "                // ⚠ **The same button, renamed.** Next writes the draft this dialog is already\n"
        "                // holding, exactly as Update does, so the two cannot drift into meaning\n"
        "                // different things.\n"
        "                TextButton(\n"
        "                    onClick = {\n"
        f"                        {updater}(selected.toList())\n"
        "\n"
        "                        onDismissRequest()\n"
        "                    },\n"
        "                ) {\n"
        "                    Text(\n"
        "                        text = stringResource(\n"
        "                            if (onSkip != null) commonR.string.next else commonR.string.update,\n"
        "                        ),\n"
        "                    )\n"
        "                }\n",
        "                // ⚠ **The same button, renamed.** Next writes the draft this dialog is already\n"
        "                // holding, exactly as Update does, so the two cannot drift into meaning\n"
        "                // different things — which is why both branches below call the same lambda.\n"
        "                val commit = {\n"
        f"                    {updater}(selected.toList())\n"
        "\n"
        "                    onDismissRequest()\n"
        "                }\n"
        "\n"
        "                if (onSkip != null) {\n"
        "                    SetupNextButtons(onBack = onBack, onNext = commit)\n"
        "                } else {\n"
        "                    TextButton(onClick = commit) {\n"
        "                        Text(text = stringResource(commonR.string.update))\n"
        "                    }\n"
        "                }\n",
        f"{name}: the footer",
    )

    text = replace_once(
        text,
        "import com.android.geto.common.R as commonR\n",
        "import com.android.geto.feature.settings.SetupNextButtons\n"
        "import com.android.geto.common.R as commonR\n",
        f"{name}: the SetupNextButtons import",
    )

    check(
        code(text).count("SetupNextButtons") == 2,
        f"{name}: SetupNextButtons is not imported once and used once",
    )

    writes[path] = text

# ================================================================ the three SettingsPage dialogs

SLOT = (
    ("SettingsToHideDialog", "commonR.string.next else R.string.save", "commit", None),
    ("RevertDefaultsDialog", "commonR.string.next else R.string.save", "commit", None),
)

for name, _, commit, _ in SLOT:
    path = DIALOGS / f"{name}.kt"

    text = path.read_text(encoding="utf-8")

    text = replace_once(
        text,
        "    onSkip: (() -> Unit)? = null,\n",
        "    onSkip: (() -> Unit)? = null,\n"
        "    /** Set by the setup flow on every step that has one behind it. */\n"
        "    onBack: (() -> Unit)? = null,\n",
        f"{name}: the onBack parameter",
    )

    text = replace_once(
        text,
        "            if (onSkip != null) {\n"
        "                TextButton(onClick = onSkip) {\n"
        "                    Text(text = stringResource(commonR.string.skip))\n"
        "                }\n"
        "            }\n"
        "\n"
        "            TextButton(onClick = commit) {\n"
        "                Text(\n"
        "                    text = stringResource(\n"
        "                        if (onSkip != null) commonR.string.next else R.string.save,\n"
        "                    ),\n"
        "                )\n"
        "            }\n",
        "            if (onSkip != null) {\n"
        "                TextButton(onClick = onSkip) {\n"
        "                    Text(text = stringResource(commonR.string.skip))\n"
        "                }\n"
        "\n"
        "                SetupNextButtons(onBack = onBack, onNext = commit)\n"
        "            } else {\n"
        "                TextButton(onClick = commit) {\n"
        "                    Text(text = stringResource(R.string.save))\n"
        "                }\n"
        "            }\n",
        f"{name}: the footer",
    )

    text = replace_once(
        text,
        "import com.android.geto.common.R as commonR\n",
        "import com.android.geto.feature.settings.SetupNextButtons\n"
        "import com.android.geto.common.R as commonR\n",
        f"{name}: the SetupNextButtons import",
    )

    writes[path] = text

# ManagerRowsDialog: same shape, but its commit is inline and its button carries `enabled`.
path = DIALOGS / "ManagerRowsDialog.kt"

manager = path.read_text(encoding="utf-8")

manager = replace_once(
    manager,
    "    onSkip: (() -> Unit)? = null,\n",
    "    onSkip: (() -> Unit)? = null,\n"
    "    /** Set by the setup flow on every step that has one behind it. */\n"
    "    onBack: (() -> Unit)? = null,\n",
    "ManagerRowsDialog: the onBack parameter",
)

manager = replace_once(
    manager,
    "                if (onSkip != null) {\n"
    "                    TextButton(onClick = onSkip) {\n"
    "                        Text(text = stringResource(commonR.string.skip))\n"
    "                    }\n"
    "                }\n"
    "\n"
    "                TextButton(\n"
    "                    enabled = savable,\n"
    "                    onClick = {\n"
    "                        onUpdateManagerRows(draft.toMap())\n"
    "\n"
    "                        onDismissRequest()\n"
    "                    },\n"
    "                ) {\n"
    "                    Text(\n"
    "                        text = stringResource(\n"
    "                            if (onSkip != null) commonR.string.next else R.string.save,\n"
    "                        ),\n"
    "                    )\n"
    "                }\n",
    "                // ⚠ **`savable` gates both branches.** The last tick cannot be taken out, and\n"
    "                // a Next that committed an empty list would be a different rule from the Save\n"
    "                // beside it.\n"
    "                val commit = {\n"
    "                    onUpdateManagerRows(draft.toMap())\n"
    "\n"
    "                    onDismissRequest()\n"
    "                }\n"
    "\n"
    "                if (onSkip != null) {\n"
    "                    TextButton(onClick = onSkip) {\n"
    "                        Text(text = stringResource(commonR.string.skip))\n"
    "                    }\n"
    "\n"
    "                    SetupNextButtons(onBack = onBack, onNext = commit, enabled = savable)\n"
    "                } else {\n"
    "                    TextButton(enabled = savable, onClick = commit) {\n"
    "                        Text(text = stringResource(R.string.save))\n"
    "                    }\n"
    "                }\n",
    "ManagerRowsDialog: the footer",
)

manager = replace_once(
    manager,
    "import com.android.geto.common.R as commonR\n",
    "import com.android.geto.feature.settings.SetupNextButtons\n"
    "import com.android.geto.common.R as commonR\n",
    "ManagerRowsDialog: the SetupNextButtons import",
)

writes[path] = manager

# ================================================================ the steps

steps = STEPS.read_text(encoding="utf-8")

STEP_NAMES = (
    "AccessibilityStep",
    "OverlayStep",
    "SettingsToHideStep",
    "RevertDefaultsStep",
    "ManagerRowsStep",
    "CustomiseUiStep",
)

for step in STEP_NAMES:
    steps = replace_once(
        steps,
        f"fun {step}(\n    modifier: Modifier = Modifier,\n",
        f"fun {step}(\n"
        "    modifier: Modifier = Modifier,\n"
        "    /** Null on a step with nothing behind it; see previousBefore in SetupScreen. */\n"
        "    onBack: (() -> Unit)? = null,\n",
        f"steps: the {step} parameter",
    )

# Each of the five dialog steps hands it straight through, anchored on its own `onSkip = onSkip,`
# inside the dialog call. ⚠ OverlayStep has two — one on OverlayStepWaiting, which has no Next for
# a Back to sit beside — so it is anchored on the dialog's own line instead.
for anchor, label in (
    ("        stepTitle = stepTitle,\n        onSkip = onSkip,\n        onDismissRequest = onNext,\n        onRefresh = viewModel::refreshAccessibilityServices,\n", "AccessibilityStep"),
    ("        stepTitle = stepTitle,\n        onSkip = onSkip,\n        onDismissRequest = onNext,\n        onRefresh = viewModel::refreshOverlayPackages,\n", "OverlayStep"),
    ("        stepTitle = stepTitle,\n        onSkip = onSkip,\n        overlayBlockedPaths = overlayBlockedPaths(userData = userData),\n", "SettingsToHideStep"),
    ("        unhidingFramework = userData.unhidingFramework,\n        onSkip = onSkip,\n        onDismissRequest = onNext,\n        onUpdateRevertDefaults = viewModel::updateRevertDefaults,\n", "RevertDefaultsStep"),
    ("        stepTitle = stepTitle,\n        onSkip = onSkip,\n        onDismissRequest = onNext,\n        onUpdateManagerRows = viewModel::updateManagerRows,\n", "ManagerRowsStep"),
):
    steps = replace_once(
        steps,
        anchor,
        anchor.replace("        onSkip = onSkip,\n", "        onSkip = onSkip,\n        onBack = onBack,\n", 1),
        f"steps: {label} passing onBack through",
    )

# CustomiseUiStep draws its own footer.
steps = replace_once(
    steps,
    "        actions = {\n"
    "            TextButton(onClick = onSkip) {\n"
    "                Text(text = stringResource(commonR.string.skip))\n"
    "            }\n"
    "\n"
    "            TextButton(onClick = onNext) {\n"
    "                Text(text = stringResource(commonR.string.next))\n"
    "            }\n"
    "        },\n",
    "        actions = {\n"
    "            TextButton(onClick = onSkip) {\n"
    "                Text(text = stringResource(commonR.string.skip))\n"
    "            }\n"
    "\n"
    "            SetupNextButtons(onBack = onBack, onNext = onNext)\n"
    "        },\n",
    "steps: the CustomiseUiStep footer",
)

check(
    code(steps).count("onBack = onBack") == 6,
    f"steps: onBack passed on {code(steps).count('onBack = onBack')} steps, expected 6",
)

writes[STEPS] = steps

# ================================================================ SetupScreen

setup = SETUP.read_text(encoding="utf-8")

setup = replace_once(
    setup,
    "    return REMINDERS\n}\n",
    "    return REMINDERS\n"
    "}\n"
    "\n"
    "/**\n"
    " * The page before [from], stepping back over the ones this install has no use for.\n"
    " *\n"
    " * ⚠ **[SHIZUKU] is the floor, not [PERMISSIONS]** — the author asked for Back *\"after initial\n"
    " * shizuku and notification permission screen\"*. Permissions is a gate rather than a step: it\n"
    " * cannot be passed until both are granted, so walking back into it could only ever be a dead\n"
    " * end, and the Shizuku page behind it is the last thing there was a choice to change.\n"
    " *\n"
    " * The mirror of [nextAfter], written the same way for the same reason its comment gives: a\n"
    " * decision written out at each of five hops is how a page becomes reachable from one direction\n"
    " * only.\n"
    " */\n"
    "private fun previousBefore(from: Int, configuring: Boolean): Int {\n"
    "    var page = from - 1\n"
    "\n"
    "    while (page > SHIZUKU) {\n"
    "        if (configuring) return page\n"
    "\n"
    "        page -= 1\n"
    "    }\n"
    "\n"
    "    return SHIZUKU\n"
    "}\n",
    "setup: previousBefore",
)

setup = replace_once(
    setup,
    "    val advance = { from: Int ->\n"
    "        page = nextAfter(from = from, configuring = configuring)\n"
    "    }\n",
    "    val advance = { from: Int ->\n"
    "        page = nextAfter(from = from, configuring = configuring)\n"
    "    }\n"
    "\n"
    "    // ⚠ **Not `page -= 1`.** The pages this walks over are the same optional ones `advance`\n"
    "    // steps across, and the two have to agree or Back lands somewhere Next never visited.\n"
    "    val retreat = { from: Int ->\n"
    "        page = previousBefore(from = from, configuring = configuring)\n"
    "    }\n",
    "setup: the retreat lambda",
)

for constant in (
    "ACCESSIBILITY",
    "OVERLAY",
    "SETTINGS_TO_HIDE",
    "REVERT_DEFAULTS",
    "MANAGER_ROWS",
    "CUSTOMISE_UI",
):
    setup = replace_once(
        setup,
        f"                    onSkip = {{ advance({constant}) }},\n",
        f"                    onBack = {{ retreat({constant}) }},\n"
        f"                    onSkip = {{ advance({constant}) }},\n",
        f"setup: onBack on {constant}",
    )

# ⚠ Six, not seven. The declaration is `val retreat = { from: Int ->` — a lambda, so the name is
# never followed by a bracket there and counting "the declaration and its uses" counts one too many.
check(
    code(setup).count("retreat(") == 6,
    f"setup: retreat called {code(setup).count('retreat(')}x, expected 6 — one per step",
)

check(
    code(setup).count("val retreat = { from: Int ->") == 1,
    "setup: the retreat lambda is not declared exactly once",
)

writes[SETUP] = setup

# ================================================================ write

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

for path, text in writes.items():
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(text, encoding="utf-8")

print(f"wrote {len(writes)} files")

print("ok")
