#!/usr/bin/env python3
"""r3 — the Shizuku configuration section: the master switch, the rewritten red lines, the two
setup pop-ups, and the fork links pointing at the repos.

Everything the author asked for in the section itself. The storage half is
`_v3_manage_shizuku_field.py`; the cascade this switch drives is a later script.

### What goes in

* **`'Manage Shizuku'`** at the very top, above the descriptions, with the bold
  `'RECOMMENDED ON if you use Shizuku'` under it. Drawn from `manageShizukuEffective`, so a
  blank field below drops it without touching the stored answer, and a tap while it cannot be
  switched on explains rather than doing nothing.
* **The section renamed** to `'Shizuku (Thedjchi) configuration in IMD'`.
* **The two red descriptions rewritten**, with the author's bolding.
* **The Thedjchi pop-up** and an ⓘ beside `'Thedjchi'` that is always visible and opens it.
* **The Shevery pop-up replaced** with the author's new contents, ending in a `How this works`
  section whose second point is the flow chart he approved as shape B.
* **Both fork names link to the repo page, not the releases page** — his instruction while this
  was being built.

⚠ **The wrapped-Switch pattern, from `TargetRow`.** A disabled `Switch` swallows the tap, so a
master switch that cannot be turned on yet would read as broken. The row is wrapped in a `Box`
that catches the press and explains instead.

⚠ **`manage_shizuku_blocked` is Claude's sentence, not the author's** — every other string in
this script is his, verbatim, including his numbering and the `'atleast'` spelling. He has been
told and may overwrite it.

⚠ **The Thedjchi pop-up does not gate the choice; the Shevery one still does.** Shevery holds
the fork in `pendingFork` until `Understood`, because what Shevery costs is the reason that
option carries a warning at all. Thedjchi is the recommended fork and its pop-up is a setup
checklist rather than a warning, so it commits and then explains — which is also what lets the
ⓘ open it at any time without changing anything.

⚠ **Numbering lives inside the four step strings** because that is how the author wrote them,
the same decision r2b3d took for the wireless notices. The `How this works` numbers are drawn
instead, because that list is assembled from an existing translated string.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCREEN = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"
VIEW_MODEL = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsViewModel.kt"
STRINGS = "feature/settings/src/main/res/values/strings.xml"
SHEVERY = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/SheveryNoticeDialog.kt"
TRANSLATIONS = "tools/check_translations.py"

SETUP_DIALOGS = ("feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/"
                 "ShizukuSetupDialogs.kt")

LICENCE = '''/*
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
'''

SETUP_DIALOGS_SOURCE = LICENCE + '''package com.android.geto.feature.settings.dialog

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.designsystem.component.emphasised
import com.android.geto.designsystem.icon.GetoIcons
import com.android.geto.feature.settings.R

/**
 * The four setup steps a fork needs before IMD can drive it, with the two paragraphs that
 * follow them.
 *
 * Shared by [ThedjchiSetupDialog] and `SheveryNoticeDialog`, which say the same four things
 * about different apps. The numbering is inside each string because that is how the author
 * wrote them; the ON / OFF word in each is bolded by name rather than by position, so a step
 * that never carries one simply passes null.
 *
 * The first paragraph is in the error colour and the second is bold, both on the author's
 * instruction — one is a security note and the other is the thing people forget after a
 * reboot.
 */
@Composable
internal fun ShizukuSetupBody(
    modifier: Modifier = Modifier,
    steps: List<Pair<Int, Int?>>,
    rebootId: Int,
) {
    Column(modifier = modifier) {
        Text(
            text = stringResource(R.string.shizuku_setup_lead),
            style = MaterialTheme.typography.titleMedium,
        )

        Spacer(modifier = Modifier.height(10.dp))

        // Read by property rather than destructured: `(a, b) ->` on a Pair inside a lambda is
        // the component1()/component2() ambiguity this project has hit four times.
        for (step in steps) {
            val boldId = step.second

            Text(
                modifier = Modifier.padding(start = 12.dp, bottom = 4.dp),
                text = if (boldId == null) {
                    emphasised(text = stringResource(step.first), names = emptyList())
                } else {
                    emphasised(
                        text = stringResource(step.first),
                        names = listOf(stringResource(boldId)),
                    )
                },
                style = MaterialTheme.typography.bodyMedium,
            )
        }

        Spacer(modifier = Modifier.height(10.dp))

        Text(
            text = stringResource(R.string.shizuku_setup_tcp_port),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.error,
        )

        Spacer(modifier = Modifier.height(8.dp))

        Text(
            text = stringResource(rebootId),
            style = MaterialTheme.typography.bodyMedium,
            fontWeight = FontWeight.Bold,
        )
    }
}

/**
 * What to set in the Shizuku app before IMD can drive the Thedjchi fork.
 *
 * Raised when the Thedjchi option is picked, and from the ⓘ beside its name at any time.
 *
 * ⚠ **It does not gate the choice, unlike the Shevery one.** Thedjchi is the recommended fork
 * and this is a setup checklist rather than a warning, so the option commits and then explains
 * — which is also what lets the ⓘ open it without changing anything.
 */
@Composable
fun ThedjchiSetupDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(
            modifier = Modifier
                .verticalScroll(rememberScrollState())
                .padding(20.dp),
        ) {
            ShizukuSetupBody(
                steps = listOf(
                    R.string.thedjchi_setup_1 to R.string.shizuku_setup_off,
                    R.string.thedjchi_setup_2 to R.string.shizuku_setup_on,
                    R.string.thedjchi_setup_3 to R.string.shizuku_setup_off,
                    R.string.thedjchi_setup_4 to null,
                ),
                rebootId = R.string.thedjchi_setup_reboot,
            )

            Spacer(modifier = Modifier.height(12.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(R.string.understood))
                }
            }
        }
    }
}

/**
 * Why 'Manage Shizuku' will not switch on yet.
 *
 * The switch cannot stand on with a blank field below it, and a disabled Switch swallows the
 * tap — so the press lands here instead of doing nothing at all.
 */
@Composable
internal fun ManageShizukuBlockedDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = stringResource(R.string.manage_shizuku),
                style = MaterialTheme.typography.titleLarge,
            )

            Spacer(modifier = Modifier.height(12.dp))

            Text(
                text = stringResource(R.string.manage_shizuku_blocked),
                style = MaterialTheme.typography.bodyMedium,
            )

            Spacer(modifier = Modifier.height(12.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(R.string.understood))
                }
            }
        }
    }
}

/**
 * Points 2 and 3 of the old Shevery notice, summarised as a vertical flow chart.
 *
 * Shape B of the three the author was shown: two labelled halves of two nodes each, rather
 * than one four-node chain, because the two halves answer different questions and a reader
 * arrives wanting one of them.
 *
 * ⚠ **Drawn rather than described.** The whole point of it is that Shevery is not asked to
 * stop or start: the debugging transport goes, the service follows, and the watchdog brings it
 * back. Four boxes and two arrows say that in less space than the two sentences did.
 */
@Composable
internal fun SheveryFlowChart(modifier: Modifier = Modifier) {
    Column(modifier = modifier) {
        FlowHalf(
            title = stringResource(R.string.shevery_flow_stop),
            first = stringResource(R.string.shevery_flow_hide),
            second = stringResource(R.string.shevery_flow_stopped),
        )

        Spacer(modifier = Modifier.height(12.dp))

        FlowHalf(
            title = stringResource(R.string.shevery_flow_restart),
            first = stringResource(R.string.shevery_flow_unhide),
            second = stringResource(R.string.shevery_flow_started),
        )
    }
}

/** One labelled half: a heading, a node, the arrow, and the node it leads to. */
@Composable
private fun FlowHalf(
    modifier: Modifier = Modifier,
    title: String,
    first: String,
    second: String,
) {
    Column(modifier = modifier) {
        Text(
            text = title,
            style = MaterialTheme.typography.labelLarge,
            color = MaterialTheme.colorScheme.primary,
        )

        Spacer(modifier = Modifier.height(6.dp))

        FlowNode(text = first)

        FlowArrow()

        FlowNode(text = second)
    }
}

/** One step of the chart. A filled surface rather than an outline, so the arrows read as the
 *  only lines in the picture. */
@Composable
private fun FlowNode(
    modifier: Modifier = Modifier,
    text: String,
) {
    Surface(
        modifier = modifier.fillMaxWidth(),
        color = MaterialTheme.colorScheme.surfaceVariant,
        shape = RoundedCornerShape(8.dp),
    ) {
        Text(
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 8.dp),
            text = text,
            style = MaterialTheme.typography.bodySmall,
        )
    }
}

/** The join between two nodes. Centred, because a chart whose arrows hug one edge reads as a
 *  list with decoration. */
@Composable
private fun FlowArrow(modifier: Modifier = Modifier) {
    Row(
        modifier = modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.Center,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Icon(
            modifier = Modifier
                .padding(vertical = 2.dp)
                .size(18.dp),
            imageVector = GetoIcons.ArrowDownward,
            contentDescription = null,
            tint = MaterialTheme.colorScheme.outline,
        )
    }
}

/** One numbered point of `How this works`. The number is drawn rather than baked into the
 *  string, because this list is assembled from strings that already existed. */
@Composable
internal fun HowThisWorksPoint(
    modifier: Modifier = Modifier,
    number: Int,
    text: String,
    color: Color = Color.Unspecified,
    content: (@Composable () -> Unit)? = null,
) {
    Row(modifier = modifier.padding(bottom = 8.dp)) {
        Text(
            text = "$number.",
            style = MaterialTheme.typography.bodyMedium,
            color = color,
        )

        Spacer(modifier = Modifier.width(8.dp))

        if (content == null) {
            Text(
                text = text,
                style = MaterialTheme.typography.bodyMedium,
                color = color,
            )
        } else {
            content()
        }
    }
}

/** The rule above `How this works`, so the checklist above it reads as finished. */
@Composable
internal fun SetupDivider(modifier: Modifier = Modifier) {
    HorizontalDivider(modifier = modifier.padding(vertical = 14.dp))
}
'''

SHEVERY_SOURCE = LICENCE + '''package com.android.geto.feature.settings.dialog

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.feature.settings.R

/**
 * What choosing Shevery actually means, shown from the caution beside the option and again
 * every time the option is switched on.
 *
 * ⚠ **Rewritten in v3.** It used to be six bullet points about how Shevery behaves. The author
 * replaced them with a setup checklist — the same four steps the Thedjchi pop-up carries, for
 * a different app — followed by a `How this works` section that keeps only the part of the old
 * dialog that explained the mechanism.
 *
 * Shevery is supported, but not driven. It has no start or stop intent, so IMD cannot ask it
 * for anything: the service goes down when the debugging transport does, and comes back when
 * Shevery's own ErrorProtect watchdog notices the transport again. The flow chart is that
 * sentence as a picture, and it is why the wait for Shevery is forty seconds where Thedjchi's
 * is eight.
 *
 * The last point is in the error colour because it is the one that is a risk rather than an
 * inconvenience.
 *
 * ⚠ **Two of the old points are gone rather than moved.** "Shizuku service toggles will become
 * hidden under hide and unhide settings" stopped being true in this same round — v3 brings
 * those toggles back for Shevery — and the "slight delay" point is now carried by the DOOA
 * picker's own first line, in red, where the delay actually applies.
 */
@Composable
fun SheveryNoticeDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
    onUnderstood: () -> Unit = onDismissRequest,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(
            modifier = Modifier
                .verticalScroll(rememberScrollState())
                .padding(20.dp),
        ) {
            ShizukuSetupBody(
                steps = listOf(
                    R.string.shevery_setup_1 to R.string.shizuku_setup_on,
                    R.string.shevery_setup_2 to R.string.shizuku_setup_on,
                    R.string.shevery_setup_3 to R.string.shizuku_setup_off,
                    R.string.shevery_setup_4 to null,
                ),
                rebootId = R.string.shevery_setup_reboot,
            )

            SetupDivider()

            Text(
                text = stringResource(R.string.shevery_how_title),
                style = MaterialTheme.typography.titleMedium,
            )

            Spacer(modifier = Modifier.height(10.dp))

            HowThisWorksPoint(
                number = 1,
                text = stringResource(R.string.shevery_notice_point_errorprotect),
            )

            HowThisWorksPoint(number = 2, text = "") {
                SheveryFlowChart()
            }

            HowThisWorksPoint(number = 3, text = stringResource(R.string.shevery_how_delay))

            HowThisWorksPoint(
                number = 4,
                text = stringResource(R.string.shevery_how_warning),
                color = MaterialTheme.colorScheme.error,
            )

            Spacer(modifier = Modifier.height(12.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                // The only route that accepts the choice. Dismissing any other way - the
                // scrim, the back gesture - leaves the picker where it was, because this
                // dialog is the explanation the choice is conditional on.
                TextButton(onClick = onUnderstood) {
                    Text(text = stringResource(R.string.understood))
                }
            }
        }
    }
}
'''

NEW_STRINGS = """    <!-- ============================ r3: the Shizuku section ============================ -->

    <!-- The master switch above everything in the Shizuku section. RECOMMENDED... is drawn
      entirely bold, which is how the author wrote it. manage_shizuku_blocked is Claude's
      sentence, not the author's - he has been told. -->
    <string name="manage_shizuku">Manage Shizuku</string>
    <string name="manage_shizuku_recommended">RECOMMENDED ON if you use Shizuku</string>
    <string name="manage_shizuku_blocked">Please fill in all the fields below first.</string>

    <!-- The phrases the two red descriptions bold. Held apart rather than positioned, so a
      translation can move them and still be found. shizuku_fork_shevery carries the third. -->
    <string name="shizuku_rikka_name_rikka">RikkaApps version of Shizuku</string>
    <string name="shizuku_rikka_name_unsupported">not supported</string>
    <string name="shizuku_rikka_name_outdated">outdated</string>

    <!-- The two fork setup pop-ups. The author numbered the steps himself, so the numbers are
      inside the strings; the ON / OFF word in each is bolded by name. -->
    <string name="shizuku_setup_lead">Please open your Shizuku app &gt; Settings and do the following:</string>
    <string name="shizuku_setup_on">ON</string>
    <string name="shizuku_setup_off">OFF</string>
    <string name="shizuku_setup_tcp_port">you should change your TCP port to something random other than 5555 for security</string>
    <string name="thedjchi_setup_1">1. Watchdog OFF</string>
    <string name="thedjchi_setup_2">2. TCP mode ON</string>
    <string name="thedjchi_setup_3">3. Auto disable USB debugging OFF</string>
    <string name="thedjchi_setup_4">4. Stop and restart Shizuku service</string>
    <string name="thedjchi_setup_reboot">You will need to start Shizuku manually atleast once after every device reboot.</string>
    <string name="shevery_setup_1">1. ErrorProtect ON</string>
    <string name="shevery_setup_2">2. TCP mode ON</string>
    <string name="shevery_setup_3">3. Auto-disable USB debugging OFF</string>
    <string name="shevery_setup_4">4. Stop and restart Shevery service</string>
    <string name="shevery_setup_reboot">You will need to start Shevery manually atleast once after every device reboot.</string>

    <!-- The How this works section of the Shevery pop-up. Its numbers are drawn rather than
      baked in, because point 1 reuses a string that already existed. -->
    <string name="shevery_how_title">How this works</string>
    <string name="shevery_flow_stop">To stop</string>
    <string name="shevery_flow_restart">To restart</string>
    <string name="shevery_flow_hide">IMD hides USB debugging settings</string>
    <string name="shevery_flow_stopped">Shevery service stops</string>
    <string name="shevery_flow_unhide">IMD unhides USB debugging settings</string>
    <string name="shevery_flow_started">ErrorProtect starts it again (scans every 10s)</string>
    <string name="shevery_how_delay">Shevery takes upto 40s to restart after revert.</string>
    <string name="shevery_how_warning">Shevery framework might be prone to failures</string>
"""

DEFERRED_KEYS = [
    "manage_shizuku", "manage_shizuku_recommended", "manage_shizuku_blocked",
    "shizuku_rikka_name_rikka", "shizuku_rikka_name_unsupported", "shizuku_rikka_name_outdated",
    "shizuku_setup_lead", "shizuku_setup_on", "shizuku_setup_off", "shizuku_setup_tcp_port",
    "thedjchi_setup_1", "thedjchi_setup_2", "thedjchi_setup_3", "thedjchi_setup_4",
    "thedjchi_setup_reboot",
    "shevery_setup_1", "shevery_setup_2", "shevery_setup_3", "shevery_setup_4",
    "shevery_setup_reboot",
    "shevery_how_title", "shevery_flow_stop", "shevery_flow_restart", "shevery_flow_hide",
    "shevery_flow_stopped", "shevery_flow_unhide", "shevery_flow_started",
    "shevery_how_delay", "shevery_how_warning",
]

MANAGE_ROW = '''
/**
 * The master switch for the whole Shizuku section.
 *
 * [configured] is `isShizukuConfigured` — every field below filled. The author's rule is that
 * the switch "can only be toggled on if all the fields below are filled and gets automatically
 * toggled off if any field below is blank (but remembers the previous state in case a field
 * below is emptied and filled again)", which is why [checked] is the *effective* value while
 * the stored answer is left exactly where the user put it.
 *
 * ⚠ **The Switch is wrapped rather than merely disabled.** A disabled Switch swallows the
 * press, and a master control that does nothing at all when tapped reads as a broken app —
 * the same argument the settings manager's `TargetRow` makes, and the same shape.
 */
@Composable
private fun ManageShizukuRow(
    modifier: Modifier = Modifier,
    checked: Boolean,
    configured: Boolean,
    onCheckedChange: (Boolean) -> Unit,
    onBlocked: () -> Unit,
) {
    val contentColour = if (configured) {
        MaterialTheme.colorScheme.onSurface
    } else {
        MaterialTheme.colorScheme.onSurface.copy(alpha = 0.38f)
    }

    Row(
        modifier = modifier
            .clickable { if (configured) onCheckedChange(!checked) else onBlocked() }
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = stringResource(R.string.manage_shizuku),
                style = MaterialTheme.typography.bodyLarge,
                color = contentColour,
            )

            Spacer(modifier = Modifier.height(4.dp))

            // Bold in full, which is how the author wrote it.
            Text(
                text = stringResource(R.string.manage_shizuku_recommended),
                style = MaterialTheme.typography.bodySmall,
                fontWeight = FontWeight.Bold,
            )
        }

        Box(modifier = Modifier.clickable(enabled = !configured, onClick = onBlocked)) {
            Switch(
                checked = checked,
                enabled = configured,
                onCheckedChange = if (configured) onCheckedChange else null,
            )
        }
    }
}

/**
 * The ⓘ beside a fork's name, opening that fork's setup pop-up.
 *
 * Always visible, on the author's instruction, and outside the row's `selectable` so that
 * tapping it explains the option rather than choosing it — the same arrangement
 * [SheveryCaution] already has.
 */
@Composable
private fun ForkInfoButton(
    modifier: Modifier = Modifier,
    onClick: () -> Unit,
) {
    Row(
        modifier = modifier
            .padding(start = 6.dp)
            .clickable(onClick = onClick)
            .padding(vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Icon(
            modifier = Modifier.size(15.dp),
            imageVector = GetoIcons.Info,
            contentDescription = null,
            tint = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}
'''

EDITS: list[tuple[str, list[tuple[str, str, int]]]] = [
    (STRINGS, [
        (
            """    <string name="shizuku">Shizuku configuration</string>
""",
            """    <string name="shizuku">Shizuku (Thedjchi) configuration in IMD</string>
""",
            1,
        ),
        (
            """    <string name="shizuku_rikka_warning">The original RikkaApps version of Shizuku (Playstore/ F-droid/ Github) does not support start-stop intents</string>
""",
            """    <string name="shizuku_rikka_warning">The original RikkaApps version of Shizuku &amp; Shevery are not supported as they do not support start-stop intents.</string>
""",
            1,
        ),
        (
            """    <string name="shizuku_choose_app">Choose an installed app</string>
""",
            NEW_STRINGS + """
    <string name="shizuku_choose_app">Choose an installed app</string>
""",
            1,
        ),
    ]),
    (TRANSLATIONS, [
        (
            """    "settings_manager_pending",
}
""",
            """    "settings_manager_pending",
    # r3: the Shizuku section's master switch, the rewritten red lines' bold phrases, and the
    # two fork setup pop-ups with the Shevery flow chart.
"""
            + "".join(f'    "{key}",\n' for key in DEFERRED_KEYS)
            + """}
""",
            1,
        ),
    ]),
    (VIEW_MODEL, [
        (
            """    fun updateManageOverlay(enabled: Boolean) {
""",
            """    fun updateManageShizuku(enabled: Boolean) {
        viewModelScope.launch {
            userDataRepository.updateManageShizuku(enabled = enabled)
        }
    }

    fun updateManageOverlay(enabled: Boolean) {
""",
            1,
        ),
    ]),
    (SCREEN, [
        # The two fork links, at the author's instruction while this was being built.
        (
            '''private const val SHIZUKU_THEDJCHI_URL = "https://github.com/thedjchi/Shizuku/releases"''',
            '''private const val SHIZUKU_THEDJCHI_URL = "https://github.com/thedjchi/Shizuku"''',
            1,
        ),
        (
            '''private const val SHIZUKU_SHEVERY_URL = "https://github.com/HmnDev-Tech/shevery/releases"''',
            '''private const val SHIZUKU_SHEVERY_URL = "https://github.com/HmnDev-Tech/shevery"''',
            1,
        ),
        (
            """import com.android.geto.designsystem.icon.GetoIcons
""",
            """import com.android.geto.designsystem.component.emphasised
import com.android.geto.designsystem.icon.GetoIcons
""",
            1,
        ),
        # The callback, threaded down the same four steps as every other one.
        (
            """        onUpdateManageOverlay = viewModel::updateManageOverlay,
""",
            """        onUpdateManageOverlay = viewModel::updateManageOverlay,
        onUpdateManageShizuku = viewModel::updateManageShizuku,
""",
            1,
        ),
        (
            """    onUpdateManageOverlay: (Boolean) -> Unit,
    onEnsureTaskerAuthKey: () -> Unit,
    onRefreshTaskerAuthKey: () -> Unit,
    onUpdateTaskerIntegrationEnabled: (Boolean) -> Unit,
    onUpdateAutoRevertOnReturn: (Boolean) -> Unit,
""",
            """    onUpdateManageOverlay: (Boolean) -> Unit,
    onUpdateManageShizuku: (Boolean) -> Unit,
    onEnsureTaskerAuthKey: () -> Unit,
    onRefreshTaskerAuthKey: () -> Unit,
    onUpdateTaskerIntegrationEnabled: (Boolean) -> Unit,
    onUpdateAutoRevertOnReturn: (Boolean) -> Unit,
""",
            2,
        ),
        (
            """                    onUpdateManageOverlay = onUpdateManageOverlay,
""",
            """                    onUpdateManageOverlay = onUpdateManageOverlay,
                    onUpdateManageShizuku = onUpdateManageShizuku,
""",
            1,
        ),
        # Into the section itself.
        (
            """            ShizukuSection(
                userData = userData,
                installedApps = installedApps,
                onUpdateShizukuForkMode = onUpdateShizukuForkMode,
""",
            """            ShizukuSection(
                userData = userData,
                installedApps = installedApps,
                onUpdateManageShizuku = onUpdateManageShizuku,
                onUpdateShizukuForkMode = onUpdateShizukuForkMode,
""",
            1,
        ),
        (
            """private fun ShizukuSection(
    modifier: Modifier = Modifier,
    userData: UserData,
    installedApps: List<InstalledAppData>,
    onUpdateShizukuForkMode: (ShizukuForkMode) -> Unit,
""",
            """private fun ShizukuSection(
    modifier: Modifier = Modifier,
    userData: UserData,
    installedApps: List<InstalledAppData>,
    onUpdateManageShizuku: (Boolean) -> Unit,
    onUpdateShizukuForkMode: (ShizukuForkMode) -> Unit,
""",
            1,
        ),
        # The two dialogs this section can now raise, beside the Shevery one it already had.
        (
            """    var showSheveryNotice by rememberSaveable { mutableStateOf(false) }
""",
            """    var showSheveryNotice by rememberSaveable { mutableStateOf(false) }

    // The Thedjchi checklist. Raised by picking that option and by its own ⓘ, and unlike the
    // Shevery one it gates nothing - see ThedjchiSetupDialog.
    var showThedjchiNotice by rememberSaveable { mutableStateOf(false) }

    // Why the master switch will not move yet.
    var showManageBlocked by rememberSaveable { mutableStateOf(false) }
""",
            1,
        ),
        (
            """    if (showSheveryNotice) {
        SheveryNoticeDialog(
""",
            """    if (showThedjchiNotice) {
        ThedjchiSetupDialog(onDismissRequest = { showThedjchiNotice = false })
    }

    if (showManageBlocked) {
        ManageShizukuBlockedDialog(onDismissRequest = { showManageBlocked = false })
    }

    if (showSheveryNotice) {
        SheveryNoticeDialog(
""",
            1,
        ),
        # The row itself, above everything including the descriptions.
        (
            """    Column(modifier = modifier.fillMaxWidth()) {
        // No heading of its own any more: the section is called "Shizuku configuration",
""",
            """    Column(modifier = modifier.fillMaxWidth()) {
        // ⚠ **Above everything, descriptions included** - the author's placement. It is the
        // switch the whole section is a precondition for, so it reads first and the red lines
        // below it explain which forks it can ever be pointed at.
        ManageShizukuRow(
            checked = userData.manageShizukuEffective,
            configured = userData.isShizukuConfigured,
            onCheckedChange = onUpdateManageShizuku,
            onBlocked = { showManageBlocked = true },
        )

        Spacer(modifier = Modifier.height(4.dp))

        // No heading of its own any more: the section is called "Shizuku configuration",
""",
            1,
        ),
        (
            """        WarningLine(
            text = AnnotatedString(stringResource(R.string.shizuku_rikka_warning)),
            showIcon = false,
        )
""",
            """        WarningLine(
            text = emphasised(
                text = stringResource(R.string.shizuku_rikka_warning),
                names = listOf(
                    stringResource(R.string.shizuku_rikka_name_rikka),
                    stringResource(R.string.shizuku_fork_shevery),
                    stringResource(R.string.shizuku_rikka_name_unsupported),
                ),
            ),
            showIcon = false,
        )
""",
            1,
        ),
        # The ⓘ beside Thedjchi, and the pop-up on picking it.
        (
            """        ForkModeRow(
            label = thedjchiForkLabel(),
            selected = selected == ShizukuForkMode.Thedjchi,
            onSelect = { onSelect(ShizukuForkMode.Thedjchi) },
        )
""",
            """        ForkModeRow(
            label = thedjchiForkLabel(),
            selected = selected == ShizukuForkMode.Thedjchi,
            onSelect = { onSelect(ShizukuForkMode.Thedjchi) },
            trailing = { ForkInfoButton(onClick = onShowThedjchiNotice) },
        )
""",
            1,
        ),
        (
            """private fun ForkModeSelector(
    modifier: Modifier = Modifier,
    selected: ShizukuForkMode,
    onSelect: (ShizukuForkMode) -> Unit,
    onShowSheveryNotice: () -> Unit,
) {
""",
            """private fun ForkModeSelector(
    modifier: Modifier = Modifier,
    selected: ShizukuForkMode,
    onSelect: (ShizukuForkMode) -> Unit,
    onShowSheveryNotice: () -> Unit,
    onShowThedjchiNotice: () -> Unit,
) {
""",
            1,
        ),
        (
            """        ForkModeSelector(
            selected = forkMode,
            onShowSheveryNotice = { showSheveryNotice = true },
            onSelect = { mode ->
                if (mode != forkMode) {
                    if (mode.isShevery) {
""",
            """        ForkModeSelector(
            selected = forkMode,
            onShowSheveryNotice = { showSheveryNotice = true },
            onShowThedjchiNotice = { showThedjchiNotice = true },
            onSelect = { mode ->
                if (mode != forkMode) {
                    if (mode.isShevery) {
""",
            1,
        ),
        (
            """                    } else {
                        commitFork(mode)
                    }
                }
            },
        )
""",
            """                    } else {
                        commitFork(mode)

                        // Committed first, then explained. Unlike Shevery's, this pop-up is a
                        // setup checklist rather than the cost of a choice, so it does not
                        // hold the fork hostage - and that is what lets the ⓘ beside the name
                        // open the same dialog at any time without changing anything.
                        showThedjchiNotice = true
                    }
                }
            },
        )
""",
            1,
        ),
    ]),
]


def main() -> int:
    staged: dict[Path, str] = {}
    problems: list[str] = []

    for rel, subs in EDITS:
        path = ROOT / rel

        if not path.exists():
            problems.append(f"{rel}: missing")

            continue

        text = path.read_text(encoding="utf-8")

        for old, new, expected in subs:
            found = text.count(old)

            if found != expected:
                problems.append(
                    f"{rel}: expected {expected} of "
                    f"{old.strip().splitlines()[0][:58]!r}, found {found}",
                )

                continue

            text = text.replace(old, new, expected)

        staged[path] = text

    # The two new composables go at the end of the screen file, beside the section they serve.
    screen = staged.get(ROOT / SCREEN, "")

    if screen.count("private fun ManageShizukuRow(") or screen.count("private fun ForkInfoButton("):
        problems.append(f"{SCREEN}: the composables this adds are already there")
    else:
        staged[ROOT / SCREEN] = screen.rstrip("\n") + "\n" + MANAGE_ROW

    # The import for what the section now raises.
    if screen and "import com.android.geto.feature.settings.dialog.SheveryNoticeDialog" in screen:
        staged[ROOT / SCREEN] = staged[ROOT / SCREEN].replace(
            "import com.android.geto.feature.settings.dialog.SheveryNoticeDialog\n",
            "import com.android.geto.feature.settings.dialog.ManageShizukuBlockedDialog\n"
            "import com.android.geto.feature.settings.dialog.SheveryNoticeDialog\n"
            "import com.android.geto.feature.settings.dialog.ThedjchiSetupDialog\n",
            1,
        )
    else:
        problems.append(f"{SCREEN}: SheveryNoticeDialog is not imported, so the anchor moved")

    if (ROOT / SETUP_DIALOGS).exists():
        problems.append(f"{SETUP_DIALOGS}: already exists")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        before = set(path.read_text(encoding="utf-8").splitlines())

        for line in text.splitlines():
            if line not in before and len(line) > 120 and not path.name.endswith(".xml"):
                problems.append(
                    f"{path.relative_to(ROOT)}: added line of {len(line)} chars: "
                    f"{line.strip()[:58]!r}",
                )

    for name, source in ((SETUP_DIALOGS, SETUP_DIALOGS_SOURCE), (SHEVERY, SHEVERY_SOURCE)):
        for line in source.splitlines():
            if len(line) > 120:
                problems.append(f"{name}: line of {len(line)} chars: {line.strip()[:58]!r}")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")
        print(f"  wrote {path.relative_to(ROOT)}")

    (ROOT / SETUP_DIALOGS).write_text(SETUP_DIALOGS_SOURCE, encoding="utf-8")
    print(f"  created {SETUP_DIALOGS}")

    (ROOT / SHEVERY).write_text(SHEVERY_SOURCE, encoding="utf-8")
    print(f"  rewrote {SHEVERY}")

    print("ok - Manage Shizuku, the rewritten descriptions, both setup pop-ups, repo links")

    return 0


if __name__ == "__main__":
    sys.exit(main())
