#!/usr/bin/env python3
"""v3-r4s — a long press that finds nothing to look up still opens something.

    "the bug in the all apps tab i still ocassionally suffer from time to time, only every first
     app icon long press create shortcut diaog does not open sometimes"

r4q put a spinner in front of the lookup on the theory that the first press of a session is simply
slow. That was worth doing and is kept, but it was not the whole of it, because the bug survived
it.

## ⚠ The defect, and it is not a timing one

`ShortcutViewModel.start` is two suspending reads inside one `viewModelScope.launch`, and **not one
line of it is guarded**:

    _target.update { null }
    val icon = packageManagerWrapper.getActivityIcon(componentName)   // can throw
    val result = getPinShortcutUseCase(id = componentName)            // can throw
    _target.update { ShortcutTarget(...) }

If either read throws, the coroutine dies at that line and `_target` is left **null forever** -
`start` is called once per component from a `LaunchedEffect`, so nothing ever tries again. The
route's `target?.takeIf { … } ?: return` then draws the spinner and never leaves it. Before r4q
that was a long press that did nothing at all, which is precisely the report.

⚠ **And both reads really can throw.** `getActivityIcon` catches `NameNotFoundException` only -
the drawable-to-bytes conversion under it can raise a `Resources.NotFoundException` or fail on a
zero-sized bitmap - and `getShortcuts()` under the use case throws `IllegalStateException` while
the user is locked, plus whatever an OEM launcher raises. Every one of those is per-app and
occasional, which is why it is *some* apps, *sometimes*, and why pressing a different app works.

## The repair, in two places, because one of them is a guess and the other is not

* **The ViewModel stops losing the target.** Each read is caught on its own. A failed icon read
  gives a null icon, which the dialog already draws. A failed lookup gives `RequestPinShortcut` -
  "offer to create one" is the honest answer to *I could not find out whether one exists*, and it
  is what the launcher will reconcile anyway. `CancellationException` is rethrown: a cancelled
  composition is not a failed read, and swallowing it would leave a dead coroutine reporting
  success.

* **The dialog stops being a dead end.** After eight seconds with nothing, the spinner becomes a
  line saying so with **Retry** beside **Cancel**. This is the part that is a guess: if the real
  cause is something neither of us has thought of, the author gets a button instead of a wedged
  dialog, and Retry re-runs `start` rather than reopening anything.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

VM = "feature/app-settings/src/main/kotlin/com/android/geto/feature/appsettings/shortcut/ShortcutViewModel.kt"

ROUTE = "feature/app-settings/src/main/kotlin/com/android/geto/feature/appsettings/shortcut/ShortcutRoute.kt"

STRINGS = "feature/app-settings/src/main/res/values/strings.xml"

TRANSLATIONS = "tools/check_translations.py"

EDITS: list[tuple[str, str, str]] = [
    # ---------------- 1. The reads cannot kill the coroutine ----------------
    (
        VM,
        """    fun start(componentName: String) {
        viewModelScope.launch {
            _target.update { null }

            val icon = packageManagerWrapper.getActivityIcon(componentName = componentName)

            val result = getPinShortcutUseCase(id = componentName)

            _target.update {
                ShortcutTarget(componentName = componentName, icon = icon, result = result)
            }
        }
    }""",
        """    fun start(componentName: String) {
        viewModelScope.launch {
            _target.update { null }

            // ⚠ **Both reads are guarded, and that is the whole of the intermittent bug.**
            // Unguarded, a throw from either one ends this coroutine at that line and leaves
            // the target null — and since `start` is called once per component, nothing ever
            // tries again. What the user sees is a long press that opens a spinner and never
            // leaves it, or before r4q, a long press that did nothing.
            //
            // Neither throw is exotic. The icon read catches `NameNotFoundException` and
            // nothing else, so the drawable conversion under it can still raise; and the
            // shortcut query throws while the user is locked.
            val icon = try {
                packageManagerWrapper.getActivityIcon(componentName = componentName)
            } catch (cancellation: CancellationException) {
                // ⚠ Rethrown, always. A cancelled composition is not a failed read, and
                // catching it here would leave a dead coroutine reporting success.
                throw cancellation
            } catch (_: Exception) {
                // The dialog draws a null icon already.
                null
            }

            val result = try {
                getPinShortcutUseCase(id = componentName)
            } catch (cancellation: CancellationException) {
                throw cancellation
            } catch (_: Exception) {
                // ⚠ "Offer to create one" is the honest answer to *I could not find out
                // whether one exists*. The launcher reconciles a duplicate id itself, and the
                // alternative — no dialog — is the bug this is fixing.
                GetPinShortcutResult.RequestPinShortcut
            }

            _target.update {
                ShortcutTarget(componentName = componentName, icon = icon, result = result)
            }
        }
    }""",
    ),
    # ---------------- 2. The dialog offers a way out ----------------
    (
        ROUTE,
        """    LaunchedEffect(componentName) {
        viewModel.start(componentName = componentName)
    }""",
        """    // Bumped by Retry, so a second attempt is a fresh read rather than a reopened dialog.
    var attempt by remember { mutableIntStateOf(0) }

    var waited by remember { mutableStateOf(false) }

    LaunchedEffect(componentName, attempt) {
        waited = false

        viewModel.start(componentName = componentName)

        delay(WAIT_MILLIS)

        waited = true
    }""",
    ),
    (
        ROUTE,
        """    val loaded = target?.takeIf { it.componentName == componentName } ?: run {
        ShortcutLoadingDialog(modifier = modifier, onDismissRequest = onDismissRequest)

        return
    }""",
        """    val loaded = target?.takeIf { it.componentName == componentName } ?: run {
        ShortcutLoadingDialog(
            modifier = modifier,
            failed = waited,
            onRetry = { attempt += 1 },
            onDismissRequest = onDismissRequest,
        )

        return
    }""",
    ),
    (
        ROUTE,
        """/**
 * What a long press shows while the icon and the existing-shortcut lookup are still running.
 *
 * ⚠ **A dialog rather than nothing.** The lookup is fast once warm and slow exactly once per
 * session, and drawing nothing for that interval is indistinguishable from the press having been
 * missed - which is what the author reported and what made him press again.
 *
 * Dismissible, so a press that turns out to have been a mistake is not a wait.
 */
@Composable
private fun ShortcutLoadingDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .padding(32.dp),
            contentAlignment = Alignment.Center,
        ) {
            CircularProgressIndicator()
        }
    }
}""",
        """/**
 * What a long press shows while the icon and the existing-shortcut lookup are still running —
 * and what it shows when they never finish.
 *
 * ⚠ **A dialog rather than nothing.** The lookup is fast once warm and slow exactly once per
 * session, and drawing nothing for that interval is indistinguishable from the press having been
 * missed - which is what the author reported and what made him press again.
 *
 * ⚠ **[failed] is a backstop, not the fix.** The fix is in `ShortcutViewModel.start`, which no
 * longer loses its target when a read throws. This is here because if the cause turns out to be
 * something else again, the author gets a button rather than a wedged dialog - and Retry re-runs
 * the read rather than reopening anything.
 *
 * Dismissible throughout, so a press that turns out to have been a mistake is not a wait.
 */
@Composable
private fun ShortcutLoadingDialog(
    modifier: Modifier = Modifier,
    failed: Boolean,
    onRetry: () -> Unit,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        if (!failed) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(32.dp),
                contentAlignment = Alignment.Center,
            ) {
                CircularProgressIndicator()
            }

            return@DialogContainer
        }

        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = stringResource(R.string.shortcut_lookup_failed),
                style = MaterialTheme.typography.bodyMedium,
            )

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(commonR.string.cancel))
                }

                TextButton(onClick = onRetry) {
                    Text(text = stringResource(commonR.string.retry))
                }
            }
        }
    }
}

/**
 * How long the spinner is held before it offers Retry.
 *
 * The same eight seconds the Display over other apps setup step waits, and for the same reason:
 * long enough not to accuse a slow device of failing, short enough that a wedged one does not
 * look like a hung app.
 */
private const val WAIT_MILLIS = 8_000L""",
    ),
    # ---------------- 3. The one new string ----------------
    (
        STRINGS,
        """<resources>""",
        """<resources>
    <string name="shortcut_lookup_failed">Could not read this app\\'s shortcut details.</string>""",
    ),
    (
        TRANSLATIONS,
        """    # r4s: the IMD+ section's own warning, above its first row.
    "imd_plus_experimental",""",
        """    # r4s: the IMD+ section's own warning, above its first row.
    "imd_plus_experimental",
    # r4s: what the create-shortcut dialog says when the lookup never lands.
    "shortcut_lookup_failed",""",
    ),
]

IMPORTS = [
    (VM, "import kotlinx.coroutines.CancellationException"),
    (ROUTE, "import androidx.compose.foundation.layout.Arrangement"),
    (ROUTE, "import androidx.compose.foundation.layout.Column"),
    (ROUTE, "import androidx.compose.foundation.layout.Row"),
    (ROUTE, "import androidx.compose.material3.MaterialTheme"),
    (ROUTE, "import androidx.compose.material3.Text"),
    (ROUTE, "import androidx.compose.material3.TextButton"),
    (ROUTE, "import androidx.compose.runtime.mutableIntStateOf"),
    (ROUTE, "import androidx.compose.runtime.mutableStateOf"),
    (ROUTE, "import androidx.compose.runtime.remember"),
    (ROUTE, "import androidx.compose.runtime.setValue"),
    (ROUTE, "import androidx.compose.ui.res.stringResource"),
    (ROUTE, "import kotlinx.coroutines.delay"),
]

TAIL_IMPORTS = [
    (ROUTE, "import com.android.geto.common.R as commonR"),
]

AFTER = [
    (VM, "throw cancellation", 2),
    (VM, "GetPinShortcutResult.RequestPinShortcut", 1),
    (ROUTE, "failed = waited", 1),
    (ROUTE, "attempt += 1", 1),
    (ROUTE, "delay(WAIT_MILLIS)", 1),
    (ROUTE, "private const val WAIT_MILLIS = 8_000L", 1),
    (ROUTE, "commonR.string.retry", 1),
    (ROUTE, "commonR.string.cancel", 1),
    (ROUTE, "ShortcutLoadingDialog(", 2),
    (STRINGS, 'name="shortcut_lookup_failed"', 1),
    (TRANSLATIONS, '"shortcut_lookup_failed",', 1),
]

# The two names the new dialog reaches for that this round did not add. Asserted rather than
# assumed: a missing `cancel` would be a build error found on the author's machine, not here.
REQUIRED_STRINGS = [
    ("common/src/main/res/values/strings.xml", 'name="cancel"'),
    ("common/src/main/res/values/strings.xml", 'name="retry"'),
]


def add_import(text: str, statement: str, tail: bool = False) -> str:
    if statement in text:
        return text

    lines = text.splitlines(keepends=True)

    indices = [i for i, line in enumerate(lines) if line.startswith("import ")]

    if not indices:
        raise SystemExit(f"REFUSED: nowhere to put {statement!r}")

    if tail:
        lines.insert(indices[-1] + 1, statement + "\n")

        return "".join(lines)

    target = next((i for i in indices if lines[i] > statement + "\n"), indices[-1] + 1)

    lines.insert(target, statement + "\n")

    return "".join(lines)


def main() -> int:
    for relative, token in REQUIRED_STRINGS:
        path = ROOT / relative

        if not path.is_file() or token not in path.read_text(encoding="utf-8"):
            print(f"REFUSED: {relative}\n  {token!r} is absent")
            return 1

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

    for relative, statement in IMPORTS:
        staged[relative] = add_import(staged[relative], statement)

    for relative, statement in TAIL_IMPORTS:
        staged[relative] = add_import(staged[relative], statement, tail=True)

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

    print(f"  ok        {VM}  :: a throwing read no longer loses the target")
    print(f"  ok        {ROUTE}  :: the spinner offers Retry after 8s")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
