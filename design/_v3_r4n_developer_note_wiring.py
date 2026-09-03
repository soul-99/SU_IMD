#!/usr/bin/env python3
"""v3-r4n, corrective — the developer note's three injections, and its repost done properly.

`_v3_r4n_developer_note.py` wrote the call sites and left the wiring behind them missing. Four
things, each of which is a compile error Android Studio would report and the sandbox's domain-only
build cannot:

1. **`MainActivityViewModel` calls `developerNoteNotification.clear()` and never injects it.**
2. **`GetoApplication` calls `developerNoteNotification.postIfUnread(...)` and never injects it**,
   nor imports `SETTINGS_NOTICE_REVISION`, which lives in `activity.main`.
3. **The repost branch was written in the wrong shape.** It called a `notificationManager` that
   does not exist in that receiver and returned early, skipping the permission check every other
   branch goes through. `NotificationRepostBroadcastReceiver` builds a notification in an
   `if / else if` chain and posts once at the bottom, behind
   `NotificationManagerCompat.areNotificationsEnabled()` — the note joins the chain instead.
4. **`buildDeveloperNoteNotification` was file-private** and is called from another file in the
   same module, so it becomes `internal`.

⚠ **This is the fourth defect class in handover_6's table — "the two checkers do not ask every
question".** Nothing in the audit suite would have caught any of these: the identifiers are all
real names in scope somewhere, and the files are in `app/` and `broadcast-receiver/`, which the
sandbox never compiles. Caught by reading the tree back after the script wrote it, which is the
only tool there is for this.

Asserts every anchor matches exactly once, that the early-return shape is gone, and that both
callers now inject what they call. Writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REPOST = "broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/NotificationRepostBroadcastReceiver.kt"
BUILDER = "broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/DeveloperNoteNotification.kt"
VM = "app/src/main/kotlin/com/android/geto/activity/main/MainActivityViewModel.kt"
APP = "app/src/main/kotlin/com/android/geto/GetoApplication.kt"

EDITS: list[tuple[str, str, str, str]] = []


def edit(rel: str, name: str, old: str, new: str) -> None:
    EDITS.append((rel, name, old, new))


edit(
    REPOST,
    "the wrongly shaped early return",
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
        }
""",
    """        if (notificationId == -1) return
""",
)

edit(
    REPOST,
    "the note's branch in the chain",
    """        val notification = if (notificationId == REVERT_TO_DEFAULT_NOTIFICATION_ID) {
            buildRevertToDefaultNotification(context = context)
        } else if (notificationId == AUTO_UNHIDE_NOTIFICATION_ID) {""",
    """        val notification = if (notificationId == DEVELOPER_NOTE_NOTIFICATION_ID) {
            // r4n: the developer's note. Ongoing holds it up to Android 13, and from 14 a
            // swipe is allowed - the author's "reappear on dismiss until user clicks on it".
            // Acknowledging the dialog cancels it, and a cancel never reaches this receiver.
            //
            // ⚠ In the chain rather than returned early, so it goes through the permission
            // check at the bottom like every other repost.
            buildDeveloperNoteNotification(context = context)
        } else if (notificationId == REVERT_TO_DEFAULT_NOTIFICATION_ID) {
            buildRevertToDefaultNotification(context = context)
        } else if (notificationId == AUTO_UNHIDE_NOTIFICATION_ID) {""",
)

edit(
    REPOST,
    "the id import",
    """import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.AUTO_UNHIDE_NOTIFICATION_ID""",
    """import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.AUTO_UNHIDE_NOTIFICATION_ID
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.DEVELOPER_NOTE_NOTIFICATION_ID""",
)

edit(
    BUILDER,
    "the builder's visibility",
    """private fun buildDeveloperNoteNotification(context: Context): Notification {""",
    """/**
 * ⚠ **`internal`, not private: [NotificationRepostBroadcastReceiver] rebuilds it after a swipe**,
 * and that lives in another file of this module. Private compiled here and would have failed in
 * the author's build.
 */
internal fun buildDeveloperNoteNotification(context: Context): Notification {""",
)

edit(
    VM,
    "the ViewModel's injection",
    """class MainActivityViewModel @Inject constructor(
    private val userDataRepository: UserDataRepository,
    private val settingsHiddenRunner: SettingsHiddenRunner,
    @param:ApplicationScope private val appScope: CoroutineScope,
) : ViewModel() {""",
    """class MainActivityViewModel @Inject constructor(
    private val userDataRepository: UserDataRepository,
    private val settingsHiddenRunner: SettingsHiddenRunner,
    // r4n: acknowledging the developer's note has to take down the notification the background
    // routes raised for the same message. A leaf - it depends on no runner, so no Hilt cycle.
    private val developerNoteNotification: DeveloperNoteNotification,
    @param:ApplicationScope private val appScope: CoroutineScope,
) : ViewModel() {""",
)

edit(
    APP,
    "the application's injection",
    """    lateinit var notificationManagerWrapper: AndroidNotificationManagerWrapper""",
    """    lateinit var notificationManagerWrapper: AndroidNotificationManagerWrapper

    @Inject
    lateinit var developerNoteNotification: DeveloperNoteNotification""",
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

    # The two imports the call sites need, added where they belong rather than by anchor
    # guessing — each is asserted to land exactly once.
    for rel, needed, anchor in (
        (
            VM,
            "import com.android.geto.broadcastreceiver.DeveloperNoteNotification",
            "import com.android.geto.broadcastreceiver.SettingsHiddenRunner",
        ),
        (
            APP,
            "import com.android.geto.broadcastreceiver.DeveloperNoteNotification",
            "import com.android.geto.domain.usecase.MigrateAutoUnhideUseCase",
        ),
        (
            APP,
            "import com.android.geto.activity.main.SETTINGS_NOTICE_REVISION",
            "import com.android.geto.domain.usecase.MigrateAutoUnhideUseCase",
        ),
    ):
        text = staged[ROOT / rel]

        if anchor not in text:
            print(f"REFUSED: {rel} has no import to anchor {needed!r} against")
            return 1

        if needed not in text:
            text = text.replace(anchor, f"{needed}\n{anchor}", 1)

        if text.count(needed) != 1:
            print(f"REFUSED: {rel} carries {needed!r} {text.count(needed)} time(s)")
            return 1

        staged[ROOT / rel] = text

    # ⚠ **The wrong shape must be gone.** Spelled as the statement it was, not as a bare name.
    repost = staged[ROOT / REPOST]

    if "notificationManager.notify(" in repost:
        print(f"REFUSED: {REPOST} still calls a notificationManager it does not have")
        return 1

    # And the note must be part of the chain that ends at the permission check.
    chain = repost.index("val notification = if (")
    guard = repost.index("areNotificationsEnabled()")
    note = repost.index("buildDeveloperNoteNotification(context = context)")

    if not chain < note < guard:
        print("REFUSED: the note is not built inside the chain that ends at the permission check")
        return 1

    # ⚠ **Everything each file calls, it must also inject.** The defect this script exists to
    # fix, asserted so it cannot come back: the call and the constructor parameter, together.
    for rel, call, field in (
        (VM, "developerNoteNotification.clear()", "private val developerNoteNotification:"),
        (
            APP,
            "developerNoteNotification.postIfUnread(",
            "lateinit var developerNoteNotification:",
        ),
    ):
        text = staged[ROOT / rel]

        if call not in text:
            print(f"REFUSED: {rel} no longer calls {call!r}")
            return 1

        if field not in text:
            print(f"REFUSED: {rel} calls {call!r} without injecting it")
            return 1

    # SETTINGS_NOTICE_REVISION is read in GetoApplication and declared in activity.main.
    app = staged[ROOT / APP]

    if "SETTINGS_NOTICE_REVISION" not in app:
        print(f"REFUSED: {APP} does not pass the revision")
        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")

    print(f"  ok        {REPOST}  :: the note joins the chain")
    print(f"  ok        {BUILDER}  :: internal, so the receiver can rebuild it")
    print(f"  ok        {VM}  :: injected")
    print(f"  ok        {APP}  :: injected, revision imported")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
