#!/usr/bin/env python3
"""
r29d — the three `*Handle` bundles stop defeating skipping.

## What they were doing

`AutoHideHandle`, `AutoUnhideHandle` and `DiagnosticsHandle` are plain `internal class`
declarations — no `data`, so no `equals` — and `SettingsRoute` builds all three **inline, in the
argument list of `SettingsScreen`**, on every recomposition:

    autoHide = AutoHideHandle(
        serviceState = autoHideServiceState,
        …
    ),

`SettingsRoute` collects twelve flows, so any one of them emitting recomposes it, and each
recomposition mints three fresh objects. Compose compares parameters with `equals`, which for a
class without one is identity — and the identity is new every time. **Every composable taking a
handle therefore recomposed on every emission of every one of those twelve flows**, including the
eleven that had nothing to do with it. `ON_RESUME` alone re-reads two of them.

## The two halves of the fix

* **`remember` with the values as keys.** This is what actually does the work: the same instance
  comes back until one of the numbers inside it changes, so identity comparison starts telling the
  truth instead of always saying "different".
* **`data class`.** Belt and braces on top — if a handle is ever rebuilt with identical contents
  by some path that bypasses the `remember`, structural equality catches it where identity would
  not.

⚠ **`viewModel` is a key on all three.** The lambdas are `viewModel::` references, and a new view
model — process death, a configuration change that recreates the store — must produce new handles
rather than ones still pointing at the old instance. It is the first key for that reason, not for
tidiness.

⚠ **`DiagnosticsHandle` keys on `settingsUiState`, not on a boolean read out of it.** Its `enabled`
is `(settingsUiState as? Success)?.userData?.diagnosticsEnabled == true` — computing that in the key
list would evaluate it twice and let the two spellings drift. The state object is the honest key.

This is shortlist item 4. On its own it is worth little; behind r29c's change it is what stops the
settings tree recomposing for reasons that have nothing to do with it.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

VIEW_MODEL = ROOT / "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsViewModel.kt"
SCREEN = ROOT / "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"

HANDLES = ("AutoHideHandle", "AutoUnhideHandle", "DiagnosticsHandle")

failures: list[str] = []


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


# ---------------------------------------------------------------- data classes

view_model = VIEW_MODEL.read_text(encoding="utf-8")

for name in HANDLES:
    view_model = replace_once(
        view_model,
        f"internal class {name}(\n",
        f"internal data class {name}(\n",
        f"view model: the {name} declaration",
    )

for name in HANDLES:
    check(
        code(view_model).count(f"internal data class {name}(") == 1,
        f"view model: {name} is not a data class exactly once",
    )

    check(
        f"internal class {name}(" not in code(view_model),
        f"view model: a plain {name} declaration survived",
    )

# ---------------------------------------------------------------- remembered construction

screen = SCREEN.read_text(encoding="utf-8")

screen = replace_once(
    screen,
    "        autoHide = AutoHideHandle(\n",
    "        autoHide = remember(\n"
    "            viewModel,\n"
    "            autoHideServiceState,\n"
    "            autoHideEnabling,\n"
    "            autoHideBlocked,\n"
    "        ) {\n"
    "            AutoHideHandle(\n",
    "screen: the AutoHideHandle construction",
)

screen = replace_once(
    screen,
    "            onRefresh = viewModel::refreshAutoHideServiceState,\n"
    "        ),\n",
    "                onRefresh = viewModel::refreshAutoHideServiceState,\n"
    "            )\n"
    "        },\n",
    "screen: the AutoHideHandle close",
)

screen = replace_once(
    screen,
    "        autoUnhide = AutoUnhideHandle(\n",
    "        autoUnhide = remember(viewModel, autoUnhideChecks) {\n"
    "            AutoUnhideHandle(\n",
    "screen: the AutoUnhideHandle construction",
)

screen = replace_once(
    screen,
    "            onUpdateUsedFor = viewModel::updateAutoUnhideUsedFor,\n"
    "        ),\n",
    "                onUpdateUsedFor = viewModel::updateAutoUnhideUsedFor,\n"
    "            )\n"
    "        },\n",
    "screen: the AutoUnhideHandle close",
)

screen = replace_once(
    screen,
    "        diagnostics = DiagnosticsHandle(\n",
    "        diagnostics = remember(viewModel, settingsUiState, diagnosticLog) {\n"
    "            DiagnosticsHandle(\n",
    "screen: the DiagnosticsHandle construction",
)

screen = replace_once(
    screen,
    "            onExport = viewModel::exportDiagnosticLog,\n"
    "        ),\n",
    "                onExport = viewModel::exportDiagnosticLog,\n"
    "            )\n"
    "        },\n",
    "screen: the DiagnosticsHandle close",
)

# ⚠ The bodies are now one level deeper. Re-indenting them is the rest of the edit, and it has to
# be bounded to each handle rather than done on the file — `viewModel::` appears forty more times
# below, in `SettingsScreen`'s own argument list, at the indent this would otherwise move.
for opener, closer in (
    ("            AutoHideHandle(\n", "                onRefresh = viewModel::refreshAutoHideServiceState,\n"),
    ("            AutoUnhideHandle(\n", "                onUpdateUsedFor = viewModel::updateAutoUnhideUsedFor,\n"),
    ("            DiagnosticsHandle(\n", "                onExport = viewModel::exportDiagnosticLog,\n"),
):
    if not check(screen.count(opener) == 1, f"screen: {opener.strip()} not found once"):
        continue

    start = screen.index(opener) + len(opener)

    if not check(closer in screen[start:], f"screen: no close for {opener.strip()}"):
        continue

    end = screen.index(closer, start)

    inner = screen[start:end]

    # Every line that is not already re-indented by the two replacements above gains four spaces.
    bumped = "\n".join(
        ("    " + line) if line.strip() else line for line in inner.split("\n")
    )

    screen = screen[:start] + bumped + screen[end:]

for name in HANDLES:
    check(
        code(screen).count(f"{name}(") == 1,
        f"screen: {name} is not constructed exactly once",
    )

# ⚠ Counted per opener, not by searching for "remember(viewModel". AutoHideHandle's key list runs
# over four lines, so the receiver and the first key are not adjacent and that search finds two of
# the three — a needle that is true of the file for a reason other than the one being tested.
for opener in (
    "        autoHide = remember(\n",
    "        autoUnhide = remember(viewModel, autoUnhideChecks) {\n",
    "        diagnostics = remember(viewModel, settingsUiState, diagnosticLog) {\n",
):
    check(
        screen.count(opener) == 1,
        f"screen: {opener.strip()} did not land exactly once",
    )

check(
    "= AutoHideHandle(" not in code(screen),
    "screen: an unremembered handle construction survived",
)

# remember was already imported for other uses in this file — asserted, not inserted.
check(
    "import androidx.compose.runtime.remember\n" in screen,
    "screen: remember is not imported",
)

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

VIEW_MODEL.write_text(view_model, encoding="utf-8")

print(f"wrote {VIEW_MODEL.relative_to(ROOT).as_posix()}")

SCREEN.write_text(screen, encoding="utf-8")

print(f"wrote {SCREEN.relative_to(ROOT).as_posix()}")

print("ok")
