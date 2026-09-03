#!/usr/bin/env python3
"""v3-r4n — the note from the developer, and the notification for the routes with no window.

The author, in full:

    "for anyone who updates t v3 from below show a dialog on first imd app launch or first
     hide(IMD shortcut/IMD+), opening settings manager, using any toggle or intent, dialog title
     'Note from developer 🧑‍🔬' description 'IMD have undergone a major update and I have matched
     your previous settings to your corresponding current ones. But, still:' 1. it is
     recommended to clear IMD app data, or 2. At least check all the settings of IMD once before
     using the app. ... 'New functions in the app to try:' 1. Auto unhide settings(RECOMMENDED)
     2. Auto hide settings (needs background service)."

and, on the two routes that have no window to put a dialog in:

    "yes show notification with body 'IMD: Important note from developer 🧑‍🔬' and make it
     alerting popup non dismissible/ reappear on dismiss until user clicks on it. Notification
     channel 'IMD app update notice', make sure it does not appear again if user have read the
     corresponding dialog."

Every word of both is his. The first two points are bullets, not numbers, at his correction.

---

## It replaces the notice v3 already shows

*"ingonre my previous dialog"* — `SettingsTabNoticeDialog` and its MainActivity branch come out.
Two "your settings changed" dialogs to the same person on the same first launch was the reason
for asking.

⚠ **Its two strings stay declared**, unused, because translations are frozen and deleting an
English string whose eleven locale copies remain is how `check_translations` starts reporting
orphans nobody is allowed to fix.

## No new stored field

`settingsNoticeRevision` is exactly the marker this needs, and it already exists with the rule
attached: shown only when `setupNoticeVersion != 0` — an install that has been through setup,
which is the app's only record that it existed before today — and only while the stored revision
is behind the current one. **Bumped 1 → 2.** Anyone who saw the Settings-tab notice sees this one
too, which is right: it is a different message.

## Why the notification is posted from `GetoApplication` and not from five places

The author listed five triggers. Four of them — the app, a shortcut, IMD+, the settings manager —
open an activity, and `MainActivity` is where the dialog lives. The Hide settings tile and the
Tasker intents have no window at all.

Rather than a call at each of five sites, the notification is posted once from `onCreate`, which
**every** one of those routes goes through: they all start this process. So the rule is simply
"unread, and this install existed before v3" — and the moment an activity does appear, the
dialog is shown and acknowledging it cancels the notification.

⚠ **Ongoing plus a delete intent**, the pattern the auto-unhide notification already uses:
`setOngoing` holds it up to Android 13, and from 14 a swipe is allowed, so the delete intent
puts it back. `NotificationRepostBroadcastReceiver` learns one more id — and its own KDoc is
already explicit that a swipe is the only thing that reaches it, so the app's own cancel on
acknowledgement is final.

Asserts every anchor matches exactly once, that the old dialog is gone but its strings are not,
that the revision moved, and that the notification is cancelled where the revision is written.
Writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DIALOG = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/DeveloperNoteDialog.kt"
OLD_DIALOG = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/SettingsTabNoticeDialog.kt"
STRINGS = "feature/settings/src/main/res/values/strings.xml"
NOTIFICATION_STRINGS = "framework/notification-manager/src/main/res/values/strings.xml"
WRAPPER = "framework/notification-manager/src/main/kotlin/com/android/geto/framework/notificationmanager/AndroidNotificationManagerWrapper.kt"
BUILDER = "broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/DeveloperNoteNotification.kt"
REPOST = "broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/NotificationRepostBroadcastReceiver.kt"
ACTIVITY = "app/src/main/kotlin/com/android/geto/activity/main/MainActivity.kt"
ACTIVITY_VM = "app/src/main/kotlin/com/android/geto/activity/main/MainActivityViewModel.kt"
APP = "app/src/main/kotlin/com/android/geto/GetoApplication.kt"
CHECK = "tools/check_translations.py"

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

NEW_DIALOG = LICENCE + '''package com.android.geto.feature.settings.dialog

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.feature.settings.R

/**
 * Shown once to an install that existed before v3, in the author's own words.
 *
 * ⚠ **Replaces `SettingsTabNoticeDialog`**, which said a smaller version of the same thing to
 * the same person on the same first launch — *"ingonre my previous dialog"*. That one's strings
 * are left declared and unused because their eleven translations are frozen.
 *
 * Never to a fresh install: somebody seeing the app for the first time has no previous settings
 * to have had matched, and telling them their configuration was carried over would be describing
 * a history they were not part of. `settingsNoticeRevision` and `setupNoticeVersion` together
 * decide that — see `MainActivity`.
 *
 * ⚠ **Public, unlike most of its neighbours in this folder, and it has to be.** It is shown from
 * `MainActivity` in the `app` module, and `internal` is module-scoped — the same reason
 * `AutoHideNothingToHideDialog` and `RevertDefaultsNoticeDialog` are public. Marking it internal
 * compiles here and fails in the author's build.
 */
@Composable
fun DeveloperNoteDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = stringResource(R.string.developer_note_title),
                style = MaterialTheme.typography.titleMedium,
            )

            Spacer(modifier = Modifier.height(12.dp))

            Text(
                text = stringResource(R.string.developer_note_body),
                style = MaterialTheme.typography.bodyMedium,
            )

            Spacer(modifier = Modifier.height(8.dp))

            NotePoint(text = stringResource(R.string.developer_note_point_1))

            NotePoint(text = stringResource(R.string.developer_note_point_2))

            Spacer(modifier = Modifier.height(12.dp))

            // Bold, and in the scheme's primary — the green the section headings already take,
            // so "new" reads as an invitation rather than as another caveat.
            Text(
                text = stringResource(R.string.developer_note_new),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.primary,
                fontWeight = FontWeight.Bold,
            )

            Spacer(modifier = Modifier.height(6.dp))

            NotePoint(text = stringResource(R.string.developer_note_new_1))

            NotePoint(text = stringResource(R.string.developer_note_new_2))

            Spacer(modifier = Modifier.height(14.dp))

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
 * One nested bullet.
 *
 * ⚠ **A drawn dot rather than a numbered label**, at the author's correction — *"the first two
 * are nested bullets not numbered"*, and then *"yes use bullets please"* for the second pair.
 * The glyph is a Row of its own so a wrapped second line lines up under the first word rather
 * than under the dot.
 */
@Composable
private fun NotePoint(text: String, modifier: Modifier = Modifier) {
    Row(modifier = modifier.padding(start = 8.dp, top = 4.dp)) {
        Text(text = BULLET, style = MaterialTheme.typography.bodyMedium)

        Spacer(modifier = Modifier.width(8.dp))

        Text(text = text, style = MaterialTheme.typography.bodyMedium)
    }
}

private const val BULLET = "\\u2022"
'''

NEW_BUILDER = LICENCE + '''package com.android.geto.broadcastreceiver

import android.app.Notification
import android.app.PendingIntent
import android.app.PendingIntent.FLAG_IMMUTABLE
import android.app.PendingIntent.FLAG_UPDATE_CURRENT
import android.content.Context
import android.content.Intent
import androidx.core.app.NotificationCompat
import com.android.geto.domain.repository.UserDataRepository
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.ACTION_REPOST_REVERT_NOTIFICATION
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.DEVELOPER_NOTE_NOTIFICATION_ID
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.NOTIFICATION_EXTRA_NOTIFICATION_ID
import com.android.geto.framework.notificationmanager.R
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.first
import javax.inject.Inject
import javax.inject.Singleton

/**
 * The developer's note, for the routes that have no window to put a dialog in.
 *
 * The author listed five triggers: the app, a hide from a shortcut or IMD+, the settings
 * manager, a toggle, and an intent. Four of those open an activity and get the dialog itself.
 * The **Hide settings tile** and the **Tasker intents** do not, and a background route cannot
 * raise a dialog at all.
 *
 * ⚠ **Posted from `GetoApplication.onCreate` rather than from each of those sites.** Every one
 * of them starts this process, so one call covers all of them and cannot fall out of step with a
 * sixth route added later. The moment an activity does appear, `MainActivity` shows the dialog
 * and acknowledging it calls [clear].
 *
 * ⚠ **Ongoing with a delete intent** — the author's *"non dismissible/ reappear on dismiss until
 * user clicks on it"*. `setOngoing` holds it up to Android 13; from 14 a swipe is allowed, and
 * [NotificationRepostBroadcastReceiver] puts it back. That receiver's own KDoc records why this
 * cannot fight the app: a delete intent fires only for a person's swipe, never for
 * `cancel`, so acknowledgement is final.
 */
@Singleton
class DeveloperNoteNotification @Inject constructor(
    @param:ApplicationContext private val context: Context,
    private val userDataRepository: UserDataRepository,
    private val notificationManagerWrapper: AndroidNotificationManagerWrapper,
) {
    /**
     * Posts the note if this install existed before v3 and has not read the dialog.
     *
     * @param currentRevision the revision `MainActivity` writes when the dialog is
     *        acknowledged. Passed in rather than read here, so the one place that decides what
     *        "read" means stays the one place.
     */
    suspend fun postIfUnread(currentRevision: Int) {
        val userData = userDataRepository.userData.first()

        // A fresh install has no previous settings to have had matched, so there is nothing to
        // tell it. Same guard the dialog itself uses.
        if (userData.setupNoticeVersion == 0) return

        if (userData.settingsNoticeRevision >= currentRevision) return

        notificationManagerWrapper.notify(
            id = DEVELOPER_NOTE_NOTIFICATION_ID,
            notification = buildDeveloperNoteNotification(context = context),
        )
    }

    /** Takes it down once the dialog behind it has been read. */
    fun clear() {
        notificationManagerWrapper.cancel(id = DEVELOPER_NOTE_NOTIFICATION_ID)
    }
}

private fun buildDeveloperNoteNotification(context: Context): Notification {
    // Opens IMD, which is where the dialog is. NEW_TASK because the shade is not an activity
    // context; CLEAR_TOP so an IMD already open is reused rather than stacked behind itself.
    val launchIntent = context.packageManager
        .getLaunchIntentForPackage(context.packageName)
        ?.apply {
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)
        }

    val launchPendingIntent = PendingIntent.getActivity(
        context,
        DEVELOPER_NOTE_NOTIFICATION_ID,
        launchIntent,
        FLAG_UPDATE_CURRENT or FLAG_IMMUTABLE,
    )

    val repostIntent = Intent(context, NotificationRepostBroadcastReceiver::class.java).apply {
        action = ACTION_REPOST_REVERT_NOTIFICATION

        putExtra(NOTIFICATION_EXTRA_NOTIFICATION_ID, DEVELOPER_NOTE_NOTIFICATION_ID)
    }

    val repostPendingIntent = PendingIntent.getBroadcast(
        context,
        DEVELOPER_NOTE_NOTIFICATION_ID,
        repostIntent,
        FLAG_UPDATE_CURRENT or FLAG_IMMUTABLE,
    )

    val text = context.getString(R.string.developer_note_notification)

    return NotificationCompat.Builder(
        context,
        AndroidNotificationManagerWrapper.DEVELOPER_NOTE_CHANNEL_ID,
    ).apply {
        setSmallIcon(R.drawable.ic_failure_notification_small)
        setContentTitle(text)
        setStyle(NotificationCompat.BigTextStyle().bigText(text))
        setContentIntent(launchPendingIntent)
        setDeleteIntent(repostPendingIntent)

        // Stays until the dialog behind it has been read, and comes back from a swipe.
        setAutoCancel(false)
        setOngoing(true)

        setPriority(NotificationCompat.PRIORITY_HIGH)
        setCategory(NotificationCompat.CATEGORY_STATUS)
        setDefaults(NotificationCompat.DEFAULT_ALL)
    }.build()
}
'''

EDITS: list[tuple[str, str, str, str]] = []


def edit(rel: str, name: str, old: str, new: str) -> None:
    EDITS.append((rel, name, old, new))


# ---------------------------------------------------------------------------------------
# 1 — the author's words
# ---------------------------------------------------------------------------------------
edit(
    STRINGS,
    "the note's strings",
    """    <string name="settings_tab_notice">App settings updated, please checkout the new Settings tab</string>""",
    """    <!-- ⚠ Unused since r4n, when DeveloperNoteDialog replaced this notice. Left declared
      because eleven locale copies exist and translations are frozen for the project; deleting
      the English half is what turns them into orphans nobody is allowed to fix. -->
    <string name="settings_tab_notice">App settings updated, please checkout the new Settings tab</string>""",
)

edit(
    STRINGS,
    "the developer note",
    """    <string name="settings_tab_notice_name">new Settings tab</string>""",
    """    <string name="settings_tab_notice_name">new Settings tab</string>

    <!-- The developer's note, shown once to an install that existed before v3. Every line is
      the author's own; the two pairs below it are bullets rather than numbers at his
      correction. -->
    <string name="developer_note_title">Note from developer \\U0001F9D1\\u200D\\U0001F52C</string>
    <string name="developer_note_body">IMD have undergone a major update and I have matched your previous settings to your corresponding current ones. But, still:</string>
    <string name="developer_note_point_1">it is recommended to clear IMD app data, or</string>
    <string name="developer_note_point_2">At least check all the settings of IMD once before using the app.</string>
    <string name="developer_note_new">New functions in the app to try:</string>
    <string name="developer_note_new_1">Auto unhide settings(RECOMMENDED)</string>
    <string name="developer_note_new_2">Auto hide settings (needs background service).</string>""",
)

edit(
    NOTIFICATION_STRINGS,
    "the notification's words",
    """    <string name="auto_hide_channel">Auto-hide settings (IMD+)</string>""",
    """    <string name="auto_hide_channel">Auto-hide settings (IMD+)</string>
    <!-- The channel name the author chose, and the one-line body of the note itself. -->
    <string name="developer_note_channel">IMD app update notice</string>
    <string name="developer_note_notification">IMD: Important note from developer \\U0001F9D1\\u200D\\U0001F52C</string>""",
)

edit(
    CHECK,
    "the DEFERRED set",
    """    # r4n: the manager's Shevery start-failure notification.""",
    """    # r4n: the developer's note, its bullets and its notification.
    "developer_note_title",
    "developer_note_body",
    "developer_note_point_1",
    "developer_note_point_2",
    "developer_note_new",
    "developer_note_new_1",
    "developer_note_new_2",
    "developer_note_channel",
    "developer_note_notification",
    # r4n: the manager's Shevery start-failure notification.""",
)

# ---------------------------------------------------------------------------------------
# 2 — the channel and the id
# ---------------------------------------------------------------------------------------
edit(
    WRAPPER,
    "the channel id",
    """        const val AUTO_HIDE_CHANNEL_ID = "imd_auto_hide_channel\"""",
    """        const val AUTO_HIDE_CHANNEL_ID = "imd_auto_hide_channel"

        /**
         * The developer's note, on a channel of its own at IMPORTANCE_HIGH.
         *
         * The author asked for an alerting popup, and it is the one notification in the app
         * that is not about the device's state — so sharing a channel with the failures would
         * mean turning those down to silence this, or the reverse.
         */
        const val DEVELOPER_NOTE_CHANNEL_ID = "imd_app_update_notice\"""",
)

edit(
    WRAPPER,
    "the notification id",
    """        const val PERMISSIONS_LOST_NOTIFICATION_ID = 1_000_006""",
    """        const val PERMISSIONS_LOST_NOTIFICATION_ID = 1_000_006

        /** The developer's note. Its own id, so acknowledging the dialog cancels only it. */
        const val DEVELOPER_NOTE_NOTIFICATION_ID = 1_000_007""",
)

# ---------------------------------------------------------------------------------------
# 3 — the dialog replaces the old notice
# ---------------------------------------------------------------------------------------
edit(
    ACTIVITY,
    "the dialog branch",
    """                                        SettingsTabNoticeDialog(
                                            onDismissRequest =
                                                viewModel::acknowledgeSettingsTabNotice,
                                        )""",
    """                                        DeveloperNoteDialog(
                                            onDismissRequest =
                                                viewModel::acknowledgeSettingsTabNotice,
                                        )""",
)

edit(
    ACTIVITY,
    "the dialog import",
    """import com.android.geto.feature.settings.dialog.SettingsTabNoticeDialog""",
    """import com.android.geto.feature.settings.dialog.DeveloperNoteDialog""",
)

edit(
    ACTIVITY_VM,
    "the revision",
    """internal const val SETTINGS_NOTICE_REVISION = 1""",
    """/**
 * Which "what changed" notice the current build has.
 *
 * ⚠ **Bumped 1 → 2 by r4n**, when the developer's note replaced the Settings-tab notice.
 * Anyone who saw revision 1 sees this one too, which is right: it is a different message, and
 * the author wrote it for exactly the people who had already been through an update.
 */
internal const val SETTINGS_NOTICE_REVISION = 2""",
)

edit(
    ACTIVITY_VM,
    "the acknowledgement",
    """            userDataRepository.updateSettingsNoticeRevision(revision = SETTINGS_NOTICE_REVISION)""",
    """            userDataRepository.updateSettingsNoticeRevision(revision = SETTINGS_NOTICE_REVISION)

            // ⚠ **And the notification the background routes raised for the same message.**
            // The dialog and the notification are one piece of news; reading either has to end
            // both, or a user who opened IMD would still be looking at a note they had just
            // dismissed.
            developerNoteNotification.clear()""",
)

# ---------------------------------------------------------------------------------------
# 4 — the repost, and the one place that posts it
# ---------------------------------------------------------------------------------------
edit(
    APP,
    "the channel registration",
    """            notificationManagerWrapper.createNotificationChannel(
                channelId = AndroidNotificationManagerWrapper.AUTO_HIDE_CHANNEL_ID,
                name = getString(notificationR.string.auto_hide_channel),
                importance = NotificationManager.IMPORTANCE_DEFAULT,
            )""",
    """            notificationManagerWrapper.createNotificationChannel(
                channelId = AndroidNotificationManagerWrapper.AUTO_HIDE_CHANNEL_ID,
                name = getString(notificationR.string.auto_hide_channel),
                importance = NotificationManager.IMPORTANCE_DEFAULT,
            )

            // The developer's note, at the author's chosen name and alerting, because it is
            // the one notification here that has to be read rather than noticed.
            notificationManagerWrapper.createNotificationChannel(
                channelId = AndroidNotificationManagerWrapper.DEVELOPER_NOTE_CHANNEL_ID,
                name = getString(notificationR.string.developer_note_channel),
                importance = NotificationManager.IMPORTANCE_HIGH,
            )""",
)

edit(
    APP,
    "posting the note",
    """        appScope.launch { migrateAutoUnhideUseCase() }""",
    """        appScope.launch { migrateAutoUnhideUseCase() }

        // ⚠ **One call for all five of the author's triggers.** He asked for the note on first
        // app launch, first hide from a shortcut or IMD+, the settings manager, a toggle and an
        // intent. The first four open an activity and get the dialog; the Hide settings tile
        // and the Tasker intents have no window at all. Every one of them starts *this
        // process*, so posting here covers the two that cannot show a dialog without a call at
        // each site — and the moment an activity appears, MainActivity shows the dialog and
        // acknowledging it takes the notification down.
        appScope.launch {
            developerNoteNotification.postIfUnread(currentRevision = SETTINGS_NOTICE_REVISION)
        }""",
)

edit(
    REPOST,
    "the new id",
    """        if (notificationId == -1) return""",
    """        if (notificationId == -1) return

        // r4n: the developer's note. Ongoing so it holds up to Android 13, and reposted here
        // from 14 on, where a swipe is allowed — the author's "reappear on dismiss until user
        // clicks on it". Acknowledging the dialog cancels it, and a cancel never reaches here.
        if (notificationId == DEVELOPER_NOTE_NOTIFICATION_ID) {
            notificationManager.notify(
                DEVELOPER_NOTE_NOTIFICATION_ID,
                buildDeveloperNoteNotification(context = context),
            )

            return
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

    for rel, content in ((DIALOG, NEW_DIALOG), (BUILDER, NEW_BUILDER)):
        if (ROOT / rel).exists():
            print(f"REFUSED: {rel} already exists")
            return 1

        staged[ROOT / rel] = content

    old_dialog = ROOT / OLD_DIALOG

    if not old_dialog.is_file():
        print(f"REFUSED: {OLD_DIALOG} is already gone")
        return 1

    # ⚠ **The strings the removed dialog used must survive it.** Translations are frozen.
    strings = staged[ROOT / STRINGS]

    for key in ("settings_tab_notice", "settings_tab_notice_name"):
        if f'<string name="{key}">' not in strings:
            print(f"REFUSED: {key} was deleted; its translations are frozen")
            return 1

    # And every one of the author's sentences must be present, character for character.
    verbatim = {
        "developer_note_body": "IMD have undergone a major update and I have matched your "
        "previous settings to your corresponding current ones. But, still:",
        "developer_note_point_1": "it is recommended to clear IMD app data, or",
        "developer_note_point_2": "At least check all the settings of IMD once before using "
        "the app.",
        "developer_note_new": "New functions in the app to try:",
        "developer_note_new_1": "Auto unhide settings(RECOMMENDED)",
        "developer_note_new_2": "Auto hide settings (needs background service).",
    }

    for key, expected in verbatim.items():
        value = strings.split(f'<string name="{key}">', 1)[1].split("</string>", 1)[0]

        if value != expected:
            print(f"REFUSED: {key} reads\n  {value!r}\nnot\n  {expected!r}")
            return 1

    # ⚠ **The old dialog must be unreferenced before it is deleted.** Spelled as the call and
    # the import it can only be, never as a bare name — the comments above name it in prose.
    for rel, text in list(staged.items()) + [
        (p, p.read_text(encoding="utf-8"))
        for p in ROOT.rglob("*.kt")
        if p not in staged and p != old_dialog
    ]:
        body = text if isinstance(text, str) else text

        for spelling in ("SettingsTabNoticeDialog(", "dialog.SettingsTabNoticeDialog"):
            if spelling in body:
                print(f"REFUSED: {rel} still references {spelling!r}")
                return 1

    # The two new injections.
    vm = staged[ROOT / ACTIVITY_VM]

    if "developerNoteNotification" not in vm:
        print(f"REFUSED: {ACTIVITY_VM} does not name the notification")
        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")

    old_dialog.unlink()

    print(f"  ok        {STRINGS}  :: seven strings, the author's words")
    print(f"  ok        {NOTIFICATION_STRINGS}  :: channel name + body")
    print(f"  ok        {WRAPPER}  :: channel + id")
    print(f"  ok        {DIALOG}  :: new")
    print(f"  ok        {BUILDER}  :: new")
    print(f"  ok        {REPOST}  :: reposts on a swipe")
    print(f"  ok        {ACTIVITY} / {ACTIVITY_VM}  :: revision 1 -> 2")
    print(f"  ok        {APP}  :: channel registered, note posted once")
    print(f"  ok        {OLD_DIALOG}  :: deleted, its strings kept")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s) + 2 new, 1 deleted")

    return 0


if __name__ == "__main__":
    sys.exit(main())
