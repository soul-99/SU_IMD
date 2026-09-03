#!/usr/bin/env python3
"""v3-r4r — the help/readme step becomes the author's closing page.

    "remove the help/readme page after initialisation as its not needed now"
    "in place of it add this page title 'Setup is now almost complete', body (numbered list): ..."

Every word below is his, verbatim, including the nested numbering. Two changes he approved when
asked: a space after the emoji in the signature, and the two **Add toggle** buttons hidden below
Android 13.

## ⚠ The help content itself is not deleted

`SetupHelpContent` still has its other caller - the Help button in Settings - so only the *step*
changes. Removing the composable because one of its two callers stopped using it is how a Help
button ends up empty.

## ⚠ Add toggle is Android 13 and up, and below that the buttons are absent rather than dead

`StatusBarManager.requestAddTileService` arrives in API 33; `minSdk` here is 24. There is no
older API that adds a tile - it is a thing only the user can do, from the quick settings edit
screen - so a button below 33 could never be anything but a lie. The author's answer: hide them.
The lines they sit under stay, so the tile is still described, just not offered.

⚠ **The result callback is required and is deliberately empty.** Every outcome is already visible
to the user: the system shows its own confirmation, and the tile either appears in their quick
settings or does not. A toast repeating that would be the app narrating something the user just
watched.

## ⚠ 'Let's go' is `onContinue`, not a launch

The app is already running - this page is inside it. `onContinue` is what the reminders page's
Finish already calls: it marks the notice seen and drops the user into the app. Starting an
activity here would restart the app to reach the screen behind the page.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SETUP = "app/src/main/kotlin/com/android/geto/onboarding/SetupScreen.kt"

PAGE = "app/src/main/kotlin/com/android/geto/onboarding/SetupCompletePage.kt"

STRINGS = "app/src/main/res/values/strings.xml"

TRANSLATIONS = "tools/check_translations.py"

LICENCE = '''/*
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
'''

PAGE_TEXT = LICENCE + '''package com.android.geto.onboarding

import android.app.StatusBarManager
import android.content.ComponentName
import android.content.Context
import android.graphics.drawable.Icon
import android.os.Build
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.weight
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.android.geto.R
import com.android.geto.activity.hide.HideTileService
import com.android.geto.activity.services.ServicesTileService

/**
 * The last page of setup, replacing the help/readme step.
 *
 * ⚠ **The help content is not gone, only this use of it.** `SetupHelpContent` still backs the
 * Help button in Settings; removing it because one of its two callers stopped using it is how a
 * Help button ends up empty.
 *
 * The list is the author's, nested numbering and all.
 */
@Composable
internal fun SetupCompletePage(
    modifier: Modifier = Modifier,
    onContinue: () -> Unit,
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .windowInsetsPadding(WindowInsets.safeDrawing)
            .padding(horizontal = 24.dp),
    ) {
        Column(
            modifier = Modifier
                .weight(1f)
                .verticalScroll(rememberScrollState()),
        ) {
            Spacer(modifier = Modifier.height(28.dp))

            Text(
                text = stringResource(R.string.setup_done_title),
                style = MaterialTheme.typography.headlineSmall,
                color = MaterialTheme.colorScheme.primary,
            )

            Spacer(modifier = Modifier.height(20.dp))

            Point(text = stringResource(R.string.setup_done_1))

            Point(text = stringResource(R.string.setup_done_2))

            SubPoint(text = stringResource(R.string.setup_done_2_1))

            SubPoint(text = stringResource(R.string.setup_done_2_2))

            SubPoint(text = stringResource(R.string.setup_done_2_3))

            SubNote(text = stringResource(R.string.setup_done_2_3_tip))

            AddTileButton(
                label = stringResource(R.string.hide_tile_label),
                component = { context -> ComponentName(context, HideTileService::class.java) },
                icon = R.drawable.ic_hide_tile,
            )

            Point(text = stringResource(R.string.setup_done_3))

            SubPoint(text = stringResource(R.string.setup_done_3_1))

            SubPoint(text = stringResource(R.string.setup_done_3_2))

            AddTileButton(
                label = stringResource(R.string.services_shortcut_label),
                component = { context -> ComponentName(context, ServicesTileService::class.java) },
                icon = R.drawable.ic_services_tile,
            )

            Point(text = stringResource(R.string.setup_done_4))

            SubPoint(text = stringResource(R.string.setup_done_4_1))

            SubPoint(text = stringResource(R.string.setup_done_4_2))

            SubPoint(text = stringResource(R.string.setup_done_4_3))

            Spacer(modifier = Modifier.height(16.dp))
        }

        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 12.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                text = stringResource(R.string.setup_done_signature),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )

            Button(onClick = onContinue) {
                Text(text = stringResource(R.string.setup_done_go))
            }
        }
    }
}

/** One of the four numbered points. */
@Composable
private fun Point(text: String) {
    Text(
        modifier = Modifier.padding(top = 12.dp),
        text = text,
        style = MaterialTheme.typography.bodyMedium,
    )
}

/** One of a point's own numbered items, indented under it. */
@Composable
private fun SubPoint(text: String) {
    Text(
        modifier = Modifier.padding(start = 20.dp, top = 6.dp),
        text = text,
        style = MaterialTheme.typography.bodyMedium,
    )
}

/** The parenthesised aside under 2.3, quieter than the item it belongs to. */
@Composable
private fun SubNote(text: String) {
    Text(
        modifier = Modifier.padding(start = 20.dp, top = 2.dp),
        text = text,
        style = MaterialTheme.typography.bodySmall,
        color = MaterialTheme.colorScheme.onSurfaceVariant,
    )
}

/**
 * Asks Android to add one of IMD's tiles to the user's quick settings.
 *
 * ⚠ **Android 13 and up, and absent below it rather than dead.** `requestAddTileService` arrives
 * in API 33 and there is no older equivalent - before that, adding a tile is something only the
 * user can do from the quick settings edit screen. A button that could never work is worse than
 * no button, so below 33 nothing is drawn and the line above it still describes the tile.
 *
 * ⚠ **The result callback is empty on purpose.** Every outcome is already in front of the user:
 * the system puts up its own confirmation, and the tile either appears or does not. A toast
 * afterwards would be the app narrating something they just watched.
 */
@Composable
private fun AddTileButton(
    label: String,
    component: (Context) -> ComponentName,
    icon: Int,
) {
    if (Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU) return

    val context = LocalContext.current

    FilledTonalButton(
        modifier = Modifier.padding(start = 20.dp, top = 8.dp),
        onClick = {
            val statusBar = context.getSystemService(StatusBarManager::class.java) ?: return@FilledTonalButton

            statusBar.requestAddTileService(
                component(context),
                label,
                Icon.createWithResource(context, icon),
                {},
                {},
            )
        },
    ) {
        Text(text = stringResource(R.string.setup_done_add_tile))
    }
}
'''

STRINGS_BLOCK = """    <!-- The closing page of setup, the author's own wording. Its nested numbering is
         written into the strings rather than drawn, so a translation can renumber if its
         own conventions differ. -->
    <string name="setup_done_title">Setup is now almost complete</string>
    <string name="setup_done_1">1. Now simply launch your problematic apps by clicking on them in IMD.</string>
    <string name="setup_done_2">2. For quick access:</string>
    <string name="setup_done_2_1">1. Long press app icons to create homescreen shortcuts</string>
    <string name="setup_done_2_2">2. Add apps to favourite tab</string>
    <string name="setup_done_2_3">3. Add Hide settings quick settings toggle</string>
    <string name="setup_done_2_3_tip">(tip: long pressing toggle opens Settings manager)</string>
    <string name="setup_done_3">3. Use IMD\\'s own Settings manager:</string>
    <string name="setup_done_3_1">1. Use Settings manager app icon in your app drawer</string>
    <string name="setup_done_3_2">2. Add Settings manager quick settings toggle</string>
    <string name="setup_done_4">4. The setup is now complete but you are recommended to checkout:</string>
    <string name="setup_done_4_1">1. All other IMD app settings</string>
    <string name="setup_done_4_2">2. IMD+ (auto hide settings on normal app launches, needs background service)</string>
    <string name="setup_done_4_3">3. IMD intents (Tasker integration)</string>
    <string name="setup_done_add_tile">Add toggle</string>
    <string name="setup_done_go">Let\\'s go</string>
    <string name="setup_done_signature" translatable="false">Made with \\uD83D\\uDC9D by soul_99</string>
"""

EDITS: list[tuple[str, str, str]] = [
    (
        STRINGS,
        """    <!-- The four configuration steps' headings, the author's own wording. -->""",
        STRINGS_BLOCK + """    <!-- The four configuration steps' headings, the author's own wording. -->""",
    ),
    (
        SETUP,
        """        Spacer(modifier = Modifier.height(8.dp))

        // The page's whole body lives in feature/settings, because Settings shows the same
        // thing behind a Help button. Two copies of a page that is nothing but navigation
        // paths would be out of step by the next release that moves a menu.
        SetupHelpContent()

        Spacer(modifier = Modifier.height(24.dp))

        Button(
            modifier = Modifier.fillMaxWidth(),
            onClick = onContinue,
        ) {
            Text(text = stringResource(R.string.setup_finish))
        }

        if (onBack != null) {
            Spacer(modifier = Modifier.height(4.dp))

            TextButton(
                modifier = Modifier.fillMaxWidth(),
                onClick = onBack,
            ) {
                Text(text = stringResource(R.string.setup_back))
            }
        }

        Spacer(modifier = Modifier.height(8.dp))
    }
}""",
        """        Spacer(modifier = Modifier.height(8.dp))

        // ⚠ **The help content is gone from here, at the author's instruction** - "remove the
        // help/readme page after initialisation as its not needed now". `SetupHelpContent` is
        // untouched and still backs the Help button in Settings; only this use of it went.
        //
        // What is here instead closes the flow rather than explaining the app: what to do next,
        // and a button into it.
        SetupCompletePage(onContinue = onContinue)

        if (onBack != null) {
            TextButton(
                modifier = Modifier.fillMaxWidth(),
                onClick = onBack,
            ) {
                Text(text = stringResource(R.string.setup_back))
            }
        }
    }
}""",
    ),
    (
        TRANSLATIONS,
        """    # r4r: the four configuration steps' headings.""",
        """    # r4r: the closing page of setup.
    "setup_done_title",
    "setup_done_1",
    "setup_done_2",
    "setup_done_2_1",
    "setup_done_2_2",
    "setup_done_2_3",
    "setup_done_2_3_tip",
    "setup_done_3",
    "setup_done_3_1",
    "setup_done_3_2",
    "setup_done_4",
    "setup_done_4_1",
    "setup_done_4_2",
    "setup_done_4_3",
    "setup_done_add_tile",
    "setup_done_go",
    # r4r: the four configuration steps' headings.""",
    ),
]

AFTER = [
    # Seventeen: title, four points, nine sub-items, the tip, Add toggle, Let's go, signature.
    (STRINGS, "setup_done_", 17),
    (SETUP, "SetupCompletePage(", 1),
    (SETUP, "SetupHelpContent()", 0),
    (TRANSLATIONS, '"setup_done_title"', 1),
]


def main() -> int:
    page = ROOT / PAGE

    if page.exists():
        print(f"REFUSED: {PAGE}\n  already exists; this script creates it")
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

    # The import of SetupHelpContent is now unused; check12_unusedimports would say so.
    staged[SETUP] = staged[SETUP].replace(
        "import com.android.geto.feature.settings.help.SetupHelpContent\n",
        "",
        1,
    )

    # ⚠ Spelled the way only code can spell it. The first draft checked for the bare name and
    # was refused by its own new comment, which explains that the composable is deliberately
    # being kept for its other caller - the comment trap, for the eighth time.
    for token in ("SetupHelpContent()", "import com.android.geto.feature.settings.help."):
        if token in staged[SETUP]:
            print(f"REFUSED: {SETUP}\n  {token!r} survives the removal")
            return 1

    # ⚠ Still used by its other caller, which is the whole reason it was not deleted.
    help_file = ROOT / "feature/settings/src/main/kotlin/com/android/geto/feature/settings/help/SetupHelp.kt"

    if "SetupHelpContent(" not in help_file.read_text(encoding="utf-8"):
        print("REFUSED: SetupHelpContent is no longer declared; the Help button would be empty")
        return 1

    # The two tile services and their icons, named directly by the new page.
    manifest = (ROOT / "app/src/main/AndroidManifest.xml").read_text(encoding="utf-8")

    for name in (
        ".activity.hide.HideTileService",
        ".activity.services.ServicesTileService",
        "@drawable/ic_hide_tile",
        "@drawable/ic_services_tile",
    ):
        if name not in manifest:
            print(f"REFUSED: AndroidManifest.xml\n  {name!r} is absent")
            return 1

    for relative, token, expected in AFTER:
        found = staged[relative].count(token)

        if found != expected:
            print(
                f"REFUSED: {relative}\n  {token!r} occurs {found} time(s) after the edits, "
                f"expected {expected}",
            )
            return 1

    page.write_text(PAGE_TEXT, encoding="utf-8")

    for relative, text in staged.items():
        (ROOT / relative).write_text(text, encoding="utf-8")

    print(f"  ok        {PAGE}  :: new")
    print(f"  ok        {STRINGS}  :: the author's list, verbatim")
    print(f"  ok        {SETUP}  :: the help step is now the closing page")
    print(f"  ok        {TRANSLATIONS}  :: sixteen deferred")
    print(f"\nwrote {len(staged) + 1} file(s), {len(EDITS) + 1} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
