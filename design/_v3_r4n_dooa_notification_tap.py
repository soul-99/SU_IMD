#!/usr/bin/env python3
"""v3-r4n item 9 — the DOOA failure notification's body opens the Shizuku app.

The author, in the v3 spec (item 6) and again in this round's batch:

    "Also for the DOOA revert failure notification on clicking the notification(not the try
     again button) open current shizuku app."

Today the body opens IMD's own services manager (`setContentIntent(managerPendingIntent)`), and
the KDoc says so in as many words. The **Try again** button is untouched — it still retries the
restore, which is the whole reason the tap must not.

The launch intent is exactly the one `buildShizukuRevertFailedNotification` already uses for the
sibling notification, including its fallback: a blank package, or a fork with no launcher entry —
uninstalled since it was configured, or a stealth build with no icon — falls back to the services
manager, which can at least report the state. Written once here rather than shared, because
sharing it would mean a helper in a file one of them does not otherwise touch; the two are
asserted to stay identical instead.

⚠ **`report()` becomes `suspend`.** The package name lives in `UserDataRepository`, and reading
it is a suspend call. Every one of its five call sites is already inside a suspend function —
`retry`, `reportIfFailed`, and `RevertToDefaultRunner`'s overlay branch, which reads the same
repository eleven lines further down — so nothing else has to change. Asserted below rather than
assumed, because a non-suspend caller would be a compile error the sandbox cannot see.

⚠ **No Hilt cycle.** `OverlayRestoreRunner` gains `UserDataRepository`, which is a leaf: it
depends on neither runner. The r4m trap was a helper placed on a class that was already a
dependency of its caller, and this is the opposite direction.

Asserts every anchor matches exactly once, that the manager intent is gone from the body tap,
that the Try again action survives, and that both notifications derive the launch intent the
same way. Writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

NOTIFICATION = "broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/OverlayRestoreNotification.kt"
RUNNER = "broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/OverlayRestoreRunner.kt"
SIBLING = "broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/ShizukuFallbackNotification.kt"

EDITS: list[tuple[str, str, str, str]] = []


def edit(rel: str, name: str, old: str, new: str) -> None:
    EDITS.append((rel, name, old, new))


edit(
    NOTIFICATION,
    "the KDoc's tap sentence",
    """ * Ongoing, so it stays until a restore actually succeeds - the device is still changed until
 * then, and a prompt that disappeared on a tap or a stray swipe would be retiring a problem
 * that has not gone away. Tapping the body opens the services manager instead of dismissing
 * it.""",
    """ * Ongoing, so it stays until a restore actually succeeds - the device is still changed until
 * then, and a prompt that disappeared on a tap or a stray swipe would be retiring a problem
 * that has not gone away. Tapping the body opens the **current Shizuku app** instead of
 * dismissing it - r4n, the author's instruction, and the same thing its sibling
 * [buildShizukuRevertFailedNotification] does: the text has just asked the user to start
 * Shizuku by hand, and the tap should put them where they can.
 *
 * [shizukuPackage] is the fork configured in IMD. If it is blank, or has no launcher entry -
 * uninstalled since it was configured, or a stealth build with no icon - the tap falls back to
 * IMD's own services manager, which can at least report the state and offer to start it.""",
)

edit(
    NOTIFICATION,
    "the signature",
    """fun buildOverlayRestoreFailedNotification(context: Context): Notification {""",
    """fun buildOverlayRestoreFailedNotification(
    context: Context,
    shizukuPackage: String,
): Notification {""",
)

edit(
    NOTIFICATION,
    "the body intent",
    """    // Tapping the body opens the services manager, which is where the cause can be dealt
    // with: Shizuku can be started from its row there, or from that row's arrow out to the
    // Shizuku app. The restore itself is then this notification's Try again button, which is
    // still in the shade because the tap does not clear it - and which is the only way back
    // through the UI when overlay management is switched off, since the overlay row is not
    // drawn at all then. NEW_TASK because the shade is not an activity context, CLEAR_TOP so
    // a manager already open is reused rather than stacked behind itself.
    val managerIntent = Intent()
        .setClassName(context, SettingsObservationGate.SERVICES_ACTIVITY_CLASS_NAME)
        .setFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)

    val managerPendingIntent = PendingIntent.getActivity(
        context,
        OVERLAY_RESTORE_NOTIFICATION_ID,
        managerIntent,
        FLAG_UPDATE_CURRENT or FLAG_IMMUTABLE,
    )""",
    """    // ⚠ **The Shizuku app, not the services manager - r4n.** The text tells the user to
    // start Shizuku by hand and this is where they do it. The restore itself stays on the
    // Try again button, which is still in the shade because the tap does not clear it - and
    // which remains the only way back through the UI when overlay management is switched
    // off, since the overlay row is not drawn at all then.
    //
    // The fallback is the services manager, for a package that is blank or has no launcher
    // entry: uninstalled since it was configured, or a stealth build with no icon. NEW_TASK
    // because the shade is not an activity context, CLEAR_TOP so a manager already open is
    // reused rather than stacked behind itself.
    val launchIntent = shizukuPackage
        .takeIf { it.isNotBlank() }
        ?.let { context.packageManager.getLaunchIntentForPackage(it) }
        ?.apply { addFlags(Intent.FLAG_ACTIVITY_NEW_TASK) }
        ?: Intent()
            .setClassName(context, SettingsObservationGate.SERVICES_ACTIVITY_CLASS_NAME)
            .setFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)

    val launchPendingIntent = PendingIntent.getActivity(
        context,
        OVERLAY_RESTORE_NOTIFICATION_ID,
        launchIntent,
        FLAG_UPDATE_CURRENT or FLAG_IMMUTABLE,
    )""",
)

edit(
    NOTIFICATION,
    "the setContentIntent call",
    """        setContentIntent(managerPendingIntent)""",
    """        setContentIntent(launchPendingIntent)""",
)

edit(
    RUNNER,
    "the runner's constructor",
    """    private val settingsWorkTracker: SettingsWorkTracker,
    private val notificationManagerWrapper: AndroidNotificationManagerWrapper,
) {""",
    """    private val settingsWorkTracker: SettingsWorkTracker,
    private val notificationManagerWrapper: AndroidNotificationManagerWrapper,
    // r4n: the notification's body tap opens the configured fork, so this needs its package.
    // A leaf dependency in both directions — no runner is involved, so no Hilt cycle.
    private val userDataRepository: UserDataRepository,
) {""",
)

edit(
    RUNNER,
    "the report function",
    """    /** Raise, or re-raise, the notification. Posting under the same id replaces it. */
    fun report() {
        notificationManagerWrapper.notify(
            id = OVERLAY_RESTORE_NOTIFICATION_ID,
            notification = buildOverlayRestoreFailedNotification(context = context),
        )
    }""",
    """    /**
     * Raise, or re-raise, the notification. Posting under the same id replaces it.
     *
     * ⚠ **Suspend since r4n**, because the body tap now opens the configured Shizuku app and
     * the package name comes from the repository. Every call site was already inside a suspend
     * function, so nothing else moved.
     */
    suspend fun report() {
        notificationManagerWrapper.notify(
            id = OVERLAY_RESTORE_NOTIFICATION_ID,
            notification = buildOverlayRestoreFailedNotification(
                context = context,
                shizukuPackage = userDataRepository.userData.first().shizukuPackageName,
            ),
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

    notification = staged[ROOT / NOTIFICATION]

    # ⚠ **The manager intent must be gone from the body tap and nowhere else.** Spelled as the
    # identifier it can only be as a value, never as a bare word, because both replacement
    # comments above talk about the services manager in prose — the comment trap.
    for spelling in ("managerPendingIntent", "val managerIntent"):
        if spelling in notification:
            print(f"REFUSED: {NOTIFICATION} still carries {spelling!r}")
            return 1

    # The Try again button is the half that must NOT change. Asserted, because the whole
    # instruction is "the body, not the Try again button".
    if notification.count("retryPendingIntent") != 2:
        print(f"REFUSED: {NOTIFICATION} no longer builds and adds the retry action")
        return 1

    if "context.getString(R.string.overlay_restore_retry)" not in notification:
        print(f"REFUSED: {NOTIFICATION} lost the Try again action")
        return 1

    # ⚠ **Both notifications must derive the launch intent identically.** They are written out
    # twice rather than shared; if they ever diverge, one of them opens the wrong thing on a
    # fork with no launcher entry and nothing else in the suite would notice.
    sibling = (ROOT / SIBLING).read_text(encoding="utf-8")

    derivation = """        .takeIf { it.isNotBlank() }
        ?.let { context.packageManager.getLaunchIntentForPackage(it) }
        ?.apply { addFlags(Intent.FLAG_ACTIVITY_NEW_TASK) }"""

    if derivation not in sibling or derivation not in notification:
        print("REFUSED: the two notifications no longer derive the launch intent the same way")
        return 1

    # Imports the runner needs for the new call. `first` may already be there; the repository
    # type is new either way.
    runner = staged[ROOT / RUNNER]

    for needed in (
        "import com.android.geto.domain.repository.UserDataRepository",
        "import kotlinx.coroutines.flow.first",
    ):
        if needed not in runner:
            runner = runner.replace(
                "import javax.inject.Inject",
                f"{needed}\nimport javax.inject.Inject",
                1,
            )

    # And now they must both be there exactly once.
    for needed in (
        "import com.android.geto.domain.repository.UserDataRepository",
        "import kotlinx.coroutines.flow.first",
    ):
        if runner.count(needed) != 1:
            print(f"REFUSED: {RUNNER} carries {needed!r} {runner.count(needed)} time(s)")
            return 1

    staged[ROOT / RUNNER] = runner

    # ⚠ **Every caller of report() must be inside a suspend function**, or this is a compile
    # error Android Studio reports and the sandbox cannot see. Checked by finding each call and
    # walking back to the nearest `fun` declaration above it.
    import re

    for rel in (
        RUNNER,
        "broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/RevertToDefaultRunner.kt",
    ):
        text = staged.get(ROOT / rel) or (ROOT / rel).read_text(encoding="utf-8")

        # ⚠ **Modifiers come in any order and there are more of them than you remember.** The
        # first draft matched `private fun` and `suspend fun` only, and reported "outside any
        # function" for a call inside `suspend operator fun invoke(` — the checker was wrong,
        # not the tree. Any run of modifiers, then `fun`, and `suspend` is looked for among them.
        declaration = re.compile(
            r"^[ \t]*((?:(?:private|internal|public|protected|override|suspend|operator|"
            r"inline|open|final|tailrec|infix|external)[ \t]+)*)fun[ \t]",
            re.M,
        )

        for match in re.finditer(r"(?<![\w.])report\(\)", text):
            before = text[: match.start()]

            funs = list(declaration.finditer(before))

            if not funs:
                print(f"REFUSED: {rel} calls report() outside any function")
                return 1

            if "suspend" not in funs[-1].group(1).split():
                line = before.count("\n") + 1

                print(f"REFUSED: {rel}:{line} calls report() from a non-suspend function")
                return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")

    print(f"  ok        {NOTIFICATION}  :: body tap opens the Shizuku app")
    print(f"  ok        {RUNNER}  :: report() is suspend, reads the package")
    print("  ok        Try again untouched; both notifications derive the intent alike")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
