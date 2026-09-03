#!/usr/bin/env python3
"""v3-r4p — the Shizuku configuration section becomes the thing the setup page draws.

    "also you removed links and i buttons and not recommended from the shizuku initialisation
     page"
    "keep everything from the original config page"
    "show the RECOMMENDED ON... line in the new shizuku page at the top"

## ⚠ r4o's setup page was a re-implementation, not the section

Fifteen things the section has and it did not: the bold names inside the first red line; the
Thedjchi releases **link** on the second; the fork names as links; the ⓘ beside Thedjchi; the
red underlined *supported, but not recommended* with its own ⓘ; the "view intents" hint; the
package field's monospace, its ⟳ re-detect and its filtered app picker; the *No Shizuku app
found* line; hiding the fields until a fork is picked; masking the auth key; hiding the start
action for Shevery and the auth key for a fork that needs none; holding the Shevery choice until
its notice is acknowledged; and filling the package and action in from `ShizukuForkDefaults` when
a fork is picked.

Copying those over would have produced a second copy that drifts the next time either changes -
so the author chose to share one composable, and this is that change.

## What is added, and why it is only two parameters

`ShizukuSection` is already parameterised by callbacks, so a caller that routes them into its own
draft gets a draft editor for free. Two things stood in the way:

1. **The master switch.** The setup page must not draw it - *"no need to show manage shizuku
   toggle in the new shizuku page as button already enabled it"* - but must keep the **RECOMMENDED
   ON if you use Shizuku** line that lives under it. `showManageRow` draws the row, or the line
   alone.

2. ⚠ **The 500 ms commit debounce.** Settings writes each keystroke to the preferences on a
   pause, which is right for a screen that is always live. On a page whose Manage button reads
   the draft, it is a bug with a precedent in this very file: a field typed 300 ms before the tap
   would not have reached the draft, the button would still be grey, and a full form would be met
   with *"Please fill all fields first"* - the same shape as the *"you need to configure Shizuku
   first"* over full fields that `LaunchedEffect(Unit)` above already exists to fix.
   `commitDelay` is `COMMIT_DEBOUNCE` from Settings and `Duration.ZERO` from the setup page.

Neither parameter takes a default. `COMMIT_DEBOUNCE` is a private top-level val and a public
function's default expression is a place it does not belong; and a boolean this consequential is
better read at both call sites than inferred at one.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCREEN = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"

EDITS: list[tuple[str, str]] = [
    # 1. Duration reaches the file for the new parameter.
    (
        """import kotlin.time.Duration.Companion.milliseconds""",
        """import kotlin.time.Duration
import kotlin.time.Duration.Companion.milliseconds""",
    ),
    # 2. The declaration: public, documented, and two parameters wider.
    (
        """@OptIn(FlowPreview::class)
@Composable
private fun ShizukuSection(
    modifier: Modifier = Modifier,
    userData: UserData,
    installedApps: List<InstalledAppData>,
    onUpdateManageShizuku: (Boolean) -> Unit,
    onUpdateShizukuForkMode: (ShizukuForkMode) -> Unit,
    onUpdateShizukuAuthKey: (String) -> Unit,
    onUpdateShizukuPackageName: (String) -> Unit,
    onUpdateShizukuStartAction: (String) -> Unit,
    onRefreshInstalledApps: (Boolean) -> Unit,
    installedAppsRevision: Int,
) {""",
        """/**
 * The whole Shizuku configuration, drawn in Settings and again during setup.
 *
 * ⚠ **Public because the setup page draws this one rather than a copy of it.** r4o's page was a
 * re-implementation and lost fifteen things this has - the links, both ⓘ buttons, the *supported,
 * but not recommended* caution, the app picker and its ⟳, the masked auth key, the fields that
 * stay hidden until a fork is picked, and the Shevery choice being held until its notice is
 * acknowledged. The author's *"keep everything from the original config page"* is only true for
 * as long as there is one of it.
 *
 * ⚠ **Nothing here writes anything itself.** Every value leaves through a callback, which is what
 * lets the setup page point them at a draft and leave the install untouched until its Manage
 * button is pressed. [commitDelay] is the one thing that has to differ - see below.
 *
 * @param showManageRow draws the **Manage Shizuku** switch with its recommendation. The setup
 *   page passes `false` and gets the recommendation alone, because its Manage button is what
 *   turns the switch on.
 * @param commitDelay how long the three text fields wait after the last keystroke before
 *   reporting. `COMMIT_DEBOUNCE` in Settings, where each write is a full proto rewrite;
 *   `Duration.ZERO` on the setup page, whose Manage button reads the draft and would otherwise
 *   meet a full form with *"Please fill all fields first"*.
 */
@OptIn(FlowPreview::class)
@Composable
fun ShizukuSection(
    modifier: Modifier = Modifier,
    userData: UserData,
    installedApps: List<InstalledAppData>,
    onUpdateManageShizuku: (Boolean) -> Unit,
    onUpdateShizukuForkMode: (ShizukuForkMode) -> Unit,
    onUpdateShizukuAuthKey: (String) -> Unit,
    onUpdateShizukuPackageName: (String) -> Unit,
    onUpdateShizukuStartAction: (String) -> Unit,
    onRefreshInstalledApps: (Boolean) -> Unit,
    installedAppsRevision: Int,
    showManageRow: Boolean,
    commitDelay: Duration,
) {""",
    ),
    # 3. The header: the switch, or the line that sits under it.
    (
        """        // ⚠ **Above everything, descriptions included** - the author's placement. It is the
        // switch the whole section is a precondition for, so it reads first and the red lines
        // below it explain which forks it can ever be pointed at.
        ManageShizukuRow(
            checked = userData.manageShizukuEffective,
            configured = userData.isShizukuConfigured,
            onCheckedChange = onUpdateManageShizuku,
            onBlocked = { showManageBlocked = true },
        )""",
        """        // ⚠ **Above everything, descriptions included** - the author's placement. It is the
        // switch the whole section is a precondition for, so it reads first and the red lines
        // below it explain which forks it can ever be pointed at.
        if (showManageRow) {
            ManageShizukuRow(
                checked = userData.manageShizukuEffective,
                configured = userData.isShizukuConfigured,
                onCheckedChange = onUpdateManageShizuku,
                onBlocked = { showManageBlocked = true },
            )
        } else {
            // ⚠ **The recommendation without the switch it belongs to** - the author's
            // *"show the RECOMMENDED ON... line in the new shizuku page at the top from the
            // original manage shizuku toggle"*. The same resource and the same full bold, so
            // the two pages cannot end up wording it differently.
            Text(
                modifier = Modifier.padding(horizontal = 16.dp),
                text = stringResource(R.string.manage_shizuku_recommended),
                style = MaterialTheme.typography.bodySmall,
                fontWeight = FontWeight.Bold,
            )
        }""",
    ),
    # 4-6. The three debounces.
    (
        """        snapshotFlow { startAction }.drop(1).debounce(COMMIT_DEBOUNCE)""",
        """        snapshotFlow { startAction }.drop(1).debounce(commitDelay)""",
    ),
    (
        """        snapshotFlow { packageName }.drop(1).debounce(COMMIT_DEBOUNCE)""",
        """        snapshotFlow { packageName }.drop(1).debounce(commitDelay)""",
    ),
    (
        """        snapshotFlow { authKey }.drop(1).debounce(COMMIT_DEBOUNCE)""",
        """        snapshotFlow { authKey }.drop(1).debounce(commitDelay)""",
    ),
    # 7. The Settings call site keeps exactly what it had.
    (
        """            ShizukuSection(
                userData = userData,
                installedApps = installedApps,
                onUpdateManageShizuku = onUpdateManageShizuku,
                onUpdateShizukuForkMode = onUpdateShizukuForkMode,
                onUpdateShizukuAuthKey = onUpdateShizukuAuthKey,
                onUpdateShizukuPackageName = onUpdateShizukuPackageName,
                onUpdateShizukuStartAction = onUpdateShizukuStartAction,
                onRefreshInstalledApps = onRefreshInstalledApps,
                installedAppsRevision = installedAppsRevision,
            )""",
        """            ShizukuSection(
                userData = userData,
                installedApps = installedApps,
                onUpdateManageShizuku = onUpdateManageShizuku,
                onUpdateShizukuForkMode = onUpdateShizukuForkMode,
                onUpdateShizukuAuthKey = onUpdateShizukuAuthKey,
                onUpdateShizukuPackageName = onUpdateShizukuPackageName,
                onUpdateShizukuStartAction = onUpdateShizukuStartAction,
                onRefreshInstalledApps = onRefreshInstalledApps,
                installedAppsRevision = installedAppsRevision,
                showManageRow = true,
                commitDelay = COMMIT_DEBOUNCE,
            )""",
    ),
]

AFTER = [
    # Declaration and one call site.
    ("fun ShizukuSection(", 1),
    ("ShizukuSection(\n                userData = userData,", 1),
    # The constant survives: declared once, named once in the new KDoc, passed once at the
    # Settings call site. The first draft expected two and forgot its own documentation - the
    # comment trap, in the direction where a comment inflates a count rather than deflating it.
    ("COMMIT_DEBOUNCE", 3),
    ("private val COMMIT_DEBOUNCE", 1),
    ("commitDelay = COMMIT_DEBOUNCE,", 1),
    ("debounce(commitDelay)", 3),
    ("debounce(COMMIT_DEBOUNCE)", 0),
    # The switch is still drawn, once, and still the only thing that reads manageShizukuEffective.
    ("ManageShizukuRow(", 2),
    ("R.string.manage_shizuku_recommended", 2),
    ("import kotlin.time.Duration\n", 1),
]

# Nothing else in this file may have become public by accident.
STILL_PRIVATE = [
    "private fun ManageShizukuRow(",
    "private fun ForkModeSelector(",
    "private fun PackageNameField(",
    "private val COMMIT_DEBOUNCE",
]


def main() -> int:
    path = ROOT / SCREEN

    if not path.is_file():
        print(f"REFUSED: missing {SCREEN}")
        return 1

    text = path.read_text(encoding="utf-8")

    for old, new in EDITS:
        found = text.count(old)

        if found != 1:
            head = old.strip().splitlines()[0][:70]

            print(f"REFUSED: {SCREEN}\n  {head!r} matched {found} time(s), expected 1")
            return 1

        text = text.replace(old, new, 1)

    for token, expected in AFTER:
        found = text.count(token)

        if found != expected:
            print(
                f"REFUSED: {SCREEN}\n  {token!r} occurs {found} time(s) after the edits, "
                f"expected {expected}",
            )
            return 1

    for token in STILL_PRIVATE:
        if text.count(token) != 1:
            print(f"REFUSED: {SCREEN}\n  {token!r} is no longer declared exactly once, privately")
            return 1

    path.write_text(text, encoding="utf-8")

    print(f"  ok        {SCREEN}  :: ShizukuSection is public")
    print("  ok        showManageRow draws the switch, or its recommendation alone")
    print("  ok        commitDelay replaces the hard-coded debounce at all three fields")
    print("  ok        the Settings call site passes true and COMMIT_DEBOUNCE")
    print(f"\nwrote 1 file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
