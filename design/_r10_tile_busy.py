#!/usr/bin/env python3
"""
The Hide settings tile goes unavailable for *any* hide or revert, not only its own press.

## What was wrong

`HideTileBusy` was claimed in exactly one place — `HideViewModel.toggle()` — so the tile only
read as busy while a tile press was being carried out. Every other way the device gets hidden or
reverted left it looking idle and pressable: IMD+ noticing a watched app, a launch from inside IMD
or from a pinned shortcut, the revert notification, a Tasker intent, the services manager. A press
landing in one of those windows starts a second hide or revert on top of the first.

## Where the signal is raised, and why not at the callers

There are around eighteen call sites that begin a hide or a revert, and only four use cases
underneath all of them. Wrapping callers would be eighteen chances to miss one and no cover at all
for the nineteenth added later; wrapping the use cases means a path cannot start the work without
saying so. So `SettingsWorkTracker` is injected into:

    ApplySettingsToHideUseCase   ApplyAppSettingsUseCase
    RevertToDefaultUseCase       RevertAppSettingsUseCase

`AutoHideRunner.run` and `.revert` are wrapped as well, on top of the use case inside them: an
IMD+ run force-stops the app and can spend the whole Shizuku budget doing it *before* it reaches
the hide, and the author asked for the tile to be unavailable while IMD+ is *starting*. That
overlap is why the tracker counts rather than flags.

`HideViewModel.toggle()` keeps its own claim for the same reason it had one: it reads and decides
before the use case is reached, and the tile must be unavailable from the press, not from the
write.

## The two fat use cases are not re-indented

`ApplyAppSettingsUseCase` and `RevertAppSettingsUseCase` are long bodies full of
`return@withContext`. Wrapping their `withContext` in a `track { }` would have re-indented a few
hundred lines and changed what those labels refer to. Instead `invoke` becomes a thin wrapper over
a private function holding the untouched body — no re-indentation, and the labels still resolve to
the same `withContext`.

## HideTileBusy is deleted

It is replaced entirely; leaving it would be two mechanisms for one idea. **It is the only file
this round removes** — see the summary printed at the end for the delete command.

Asserts every match count and writes nothing on any mismatch.
"""

import os
import sys

ROOT = os.environ.get(
    "GETO_ROOT",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
)

USECASES = "domain/use-case/src/main/kotlin/com/android/geto/domain/usecase"

IMPORT_TRACKER = "import com.android.geto.domain.usecase.SettingsWorkTracker\n"

# (path, [(old, new, expected count)])
EDITS = [
    # --- the two thin use cases: wrapped in place -----------------------
    (
        "%s/ApplySettingsToHideUseCase.kt" % USECASES,
        [
            (
                "    private val shizukuStartTracker: ShizukuStartTracker,\n",
                "    private val shizukuStartTracker: ShizukuStartTracker,\n"
                "    private val settingsWorkTracker: SettingsWorkTracker,\n",
                1,
            ),
            (
                "    suspend operator fun invoke(): AppSettingsResult = withContext(defaultDispatcher) {\n"
                "        // Half-hidden is the worst outcome available: the app still detects whatever is\n"
                "        // left on and refuses to run, while the user's device has been changed anyway.\n"
                "        // Launching an activity is exactly the sort of thing that tears this scope down.\n"
                "        withContext(NonCancellable) { hide() }\n"
                "    }\n",
                "    // Tracked from the outside in, so the Hide settings tile is unavailable for the whole\n"
                "    // of this and not only for the part that writes - the Shizuku start inside a hide is\n"
                "    // ten seconds during which a second press must not land. See SettingsWorkTracker.\n"
                "    suspend operator fun invoke(): AppSettingsResult = settingsWorkTracker.track {\n"
                "        withContext(defaultDispatcher) {\n"
                "            // Half-hidden is the worst outcome available: the app still detects whatever is\n"
                "            // left on and refuses to run, while the user's device has been changed anyway.\n"
                "            // Launching an activity is exactly the sort of thing that tears this scope down.\n"
                "            withContext(NonCancellable) { hide() }\n"
                "        }\n"
                "    }\n",
                1,
            ),
        ],
    ),
    (
        "%s/RevertToDefaultUseCase.kt" % USECASES,
        [
            (
                "    private val shizukuStartTracker: ShizukuStartTracker,\n",
                "    private val shizukuStartTracker: ShizukuStartTracker,\n"
                "    private val settingsWorkTracker: SettingsWorkTracker,\n",
                1,
            ),
            (
                "    suspend operator fun invoke(): RevertToDefaultResult = withContext(defaultDispatcher) {\n"
                "        // A half-applied revert is worse than none — developer options on with USB debugging\n"
                "        // still off is a state the user did not ask for and cannot see. A tile press whose\n"
                "        // service is torn down mid-run must not be able to leave that behind.\n"
                "        withContext(NonCancellable) { revert() }\n"
                "    }\n",
                "    // Tracked from the outside in, so the Hide settings tile is unavailable for the whole\n"
                "    // of this. A revert is the longest thing this app does; it is also the one a stray tile\n"
                "    // press would most like to interrupt. See SettingsWorkTracker.\n"
                "    suspend operator fun invoke(): RevertToDefaultResult = settingsWorkTracker.track {\n"
                "        withContext(defaultDispatcher) {\n"
                "            // A half-applied revert is worse than none — developer options on with USB\n"
                "            // debugging still off is a state the user did not ask for and cannot see. A tile\n"
                "            // press whose service is torn down mid-run must not be able to leave that behind.\n"
                "            withContext(NonCancellable) { revert() }\n"
                "        }\n"
                "    }\n",
                1,
            ),
        ],
    ),
    # --- the two fat ones: thin invoke over an untouched body -----------
    (
        "%s/ApplyAppSettingsUseCase.kt" % USECASES,
        [
            (
                "    private val shizukuStartTracker: ShizukuStartTracker,\n",
                "    private val shizukuStartTracker: ShizukuStartTracker,\n"
                "    private val settingsWorkTracker: SettingsWorkTracker,\n",
                1,
            ),
            (
                "    suspend operator fun invoke(componentName: String): AppSettingsResult = "
                "withContext(defaultDispatcher) {\n",
                "    // A thin wrapper rather than a track { } around the body below, and deliberately: that\n"
                "    // body is a few hundred lines of return@withContext, which would all have had to be\n"
                "    // re-indented and re-labelled. This way the tile is held unavailable for the whole\n"
                "    // launch and not one line of the logic moves. See SettingsWorkTracker.\n"
                "    suspend operator fun invoke(componentName: String): AppSettingsResult =\n"
                "        settingsWorkTracker.track { applyProfile(componentName = componentName) }\n"
                "\n"
                "    private suspend fun applyProfile(componentName: String): AppSettingsResult =\n"
                "        withContext(defaultDispatcher) {\n",
                1,
            ),
        ],
    ),
    (
        "%s/RevertAppSettingsUseCase.kt" % USECASES,
        [
            (
                "    private val shizukuStartTracker: ShizukuStartTracker,\n",
                "    private val shizukuStartTracker: ShizukuStartTracker,\n"
                "    private val settingsWorkTracker: SettingsWorkTracker,\n",
                1,
            ),
            (
                "    suspend operator fun invoke(componentName: String): AppSettingsResult = "
                "withContext(defaultDispatcher) {\n",
                "    // A thin wrapper rather than a track { } around the body below, for the same reason as\n"
                "    // ApplyAppSettingsUseCase: the body is full of return@withContext and does not move.\n"
                "    suspend operator fun invoke(componentName: String): AppSettingsResult =\n"
                "        settingsWorkTracker.track { revertProfile(componentName = componentName) }\n"
                "\n"
                "    private suspend fun revertProfile(componentName: String): AppSettingsResult =\n"
                "        withContext(defaultDispatcher) {\n",
                1,
            ),
        ],
    ),
    # --- IMD+, which starts before it reaches a use case ----------------
    (
        "broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/AutoHideRunner.kt",
        [
            (
                "    private val shizukuStartTracker: ShizukuStartTracker,\n",
                "    private val shizukuStartTracker: ShizukuStartTracker,\n"
                "    private val settingsWorkTracker: SettingsWorkTracker,\n",
                1,
            ),
            (
                "    suspend fun run(packageName: String): Boolean {\n"
                "        try {\n",
                "    suspend fun run(packageName: String): Boolean {\n"
                "        // Claimed here rather than left to the hide inside, because an IMD+ run starts long\n"
                "        // before it reaches one: the kill can spend the whole Shizuku budget on its own. The\n"
                "        // Hide settings tile is unavailable for all of it. Released in the finally below,\n"
                "        // beside the latch, so no early return or throw can leave it standing.\n"
                "        settingsWorkTracker.begin()\n"
                "\n"
                "        try {\n",
                1,
            ),
            (
                "        } finally {\n"
                "            inFlight.set(false)\n"
                "        }\n"
                "    }\n",
                "        } finally {\n"
                "            inFlight.set(false)\n"
                "\n"
                "            settingsWorkTracker.end()\n"
                "        }\n"
                "    }\n",
                1,
            ),
            (
                "    suspend fun revert() {\n"
                "        // First, so the shade is clear before anything else starts. RevertToDefaultRunner\n"
                "        // clears every notification too, but that is a moment away.\n"
                "        notificationManagerWrapper.cancel(\n"
                "            id = AndroidNotificationManagerWrapper.AUTO_HIDE_NOTIFICATION_ID,\n"
                "        )\n"
                "\n"
                "        context.showAutoHideRevertToast()\n"
                "\n"
                "        // Cleared before the revert rather than after it. The revert re-enables IMD's own\n"
                "        // detector as part of putting the accessibility services back, and a detector that\n"
                "        // came up while this still read \"running\" would find IMD+ disarmed.\n"
                "        userDataRepository.updateAutoHideRunning(running = false)\n"
                "\n"
                "        revertToDefaultRunner()\n"
                "    }\n",
                "    suspend fun revert() = settingsWorkTracker.track {\n"
                "        // First, so the shade is clear before anything else starts. RevertToDefaultRunner\n"
                "        // clears every notification too, but that is a moment away.\n"
                "        notificationManagerWrapper.cancel(\n"
                "            id = AndroidNotificationManagerWrapper.AUTO_HIDE_NOTIFICATION_ID,\n"
                "        )\n"
                "\n"
                "        context.showAutoHideRevertToast()\n"
                "\n"
                "        // Cleared before the revert rather than after it. The revert re-enables IMD's own\n"
                "        // detector as part of putting the accessibility services back, and a detector that\n"
                "        // came up while this still read \"running\" would find IMD+ disarmed.\n"
                "        userDataRepository.updateAutoHideRunning(running = false)\n"
                "\n"
                "        revertToDefaultRunner()\n"
                "    }\n",
                1,
            ),
        ],
    ),
    # --- the tile itself -----------------------------------------------
    (
        "app/src/main/kotlin/com/android/geto/activity/hide/HideTileService.kt",
        [
            ("import com.android.geto.common.HideTileBusy\n", "", 1),
            (
                "    @Inject\n    lateinit var userDataRepository: UserDataRepository\n",
                "    @Inject\n    lateinit var userDataRepository: UserDataRepository\n"
                "\n"
                "    @Inject\n    lateinit var settingsWorkTracker: SettingsWorkTracker\n",
                1,
            ),
            (
                "                HideTileBusy.running,\n",
                "                settingsWorkTracker.inFlight,\n",
                1,
            ),
            (
                "        if (HideTileBusy.running.value) return\n",
                "        if (settingsWorkTracker.inFlightNow) return\n",
                1,
            ),
        ],
    ),
    (
        "app/src/main/kotlin/com/android/geto/activity/hide/HideViewModel.kt",
        [
            ("import com.android.geto.common.HideTileBusy\n", "", 1),
            (
                "    shizukuStartTracker: ShizukuStartTracker,\n",
                "    shizukuStartTracker: ShizukuStartTracker,\n"
                "    private val settingsWorkTracker: SettingsWorkTracker,\n",
                1,
            ),
            (
                "            HideTileBusy.begin()\n",
                "            settingsWorkTracker.begin()\n",
                1,
            ),
            (
                "                HideTileBusy.end()\n",
                "                settingsWorkTracker.end()\n",
                1,
            ),
            (
                "            // feedback for a press whose result arrives seconds later - see HideTileBusy.\n",
                "            // feedback for a press whose result arrives seconds later. Kept even though the\n"
                "            // use cases underneath now claim it too: this covers the reads and the decision\n"
                "            // made before one is reached, so the tile is unavailable from the press rather\n"
                "            // than from the write. Nesting is why the tracker counts. See SettingsWorkTracker.\n",
                1,
            ),
        ],
    ),
]

# Files that need the tracker imported. The use cases are in its own package and do not.
NEEDS_IMPORT = {
    "broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/AutoHideRunner.kt":
        "import com.android.geto.domain.usecase.ShizukuStartTracker\n",
    "app/src/main/kotlin/com/android/geto/activity/hide/HideTileService.kt": None,
    "app/src/main/kotlin/com/android/geto/activity/hide/HideViewModel.kt":
        "import com.android.geto.domain.usecase.ShizukuStartTracker\n",
}

DELETE = "common/src/main/kotlin/com/android/geto/common/HideTileBusy.kt"


def main():
    print("ROOT = %s" % ROOT)

    errors = []
    pending = {}

    for rel, edits in EDITS:
        path = os.path.join(ROOT, rel)

        if not os.path.exists(path):
            errors.append("%s: missing" % rel)

            continue

        text = open(path, encoding="utf-8").read()

        for old, new, expected in edits:
            found = text.count(old)

            if found != expected:
                errors.append(
                    "%s: %r matched %d times, expected %d"
                    % (rel, old.strip().splitlines()[0][:70], found, expected)
                )

                continue

            text = text.replace(old, new, expected)

        pending[path] = text

    if errors:
        print("\nREFUSED, nothing written:\n  " + "\n  ".join(errors))

        return 1

    # --- the import, where the package does not already provide it ------
    for rel, anchor in NEEDS_IMPORT.items():
        path = os.path.join(ROOT, rel)

        text = pending[path]

        if IMPORT_TRACKER in text:
            continue

        if anchor is None:
            # HideTileService imports nothing from this package yet; sit beside the repository
            # import, which is the alphabetical neighbour.
            anchor = "import com.android.geto.domain.repository.UserDataRepository\n"

        if text.count(anchor) != 1:
            errors.append("%s: import anchor %r matched %d times" % (rel, anchor.strip(), text.count(anchor)))

            continue

        # domain.repository sorts before domain.usecase; ShizukuStartTracker before SettingsWork?
        # No - SettingsWorkTracker sorts before ShizukuStartTracker ("Se" < "Sh").
        if "ShizukuStartTracker" in anchor:
            text = text.replace(anchor, IMPORT_TRACKER + anchor, 1)
        else:
            text = text.replace(anchor, anchor + IMPORT_TRACKER, 1)

        pending[path] = text

    if errors:
        print("\nREFUSED, nothing written:\n  " + "\n  ".join(errors))

        return 1

    # --- validation -----------------------------------------------------
    problems = []

    for rel, _ in EDITS:
        text = pending[os.path.join(ROOT, rel)]

        if "HideTileBusy" in text:
            problems.append("%s: still references HideTileBusy" % rel)

        if "SettingsWorkTracker" not in text:
            problems.append("%s: does not mention SettingsWorkTracker" % rel)

        for line in text.splitlines():
            if len(line) > 120:
                problems.append("%s: line over 120 chars: %s" % (rel, line[:60]))

    # Nothing anywhere else in the tree may still reach for the deleted object.
    for dirpath, dirnames, filenames in os.walk(ROOT):
        if "/build" in dirpath or "/.git" in dirpath:
            continue

        for name in filenames:
            if not name.endswith(".kt"):
                continue

            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, ROOT)

            if rel == DELETE:
                continue

            text = pending.get(full) or open(full, encoding="utf-8").read()

            if "HideTileBusy" in text:
                problems.append("%s: references HideTileBusy and was not updated" % rel)

    if not os.path.exists(os.path.join(ROOT, DELETE)):
        problems.append("%s: not there to delete" % DELETE)

    if problems:
        print("\nVALIDATION FAILED, nothing written:\n  " + "\n  ".join(problems))

        return 1

    for path, text in sorted(pending.items()):
        open(path, "w", encoding="utf-8").write(text)

    os.remove(os.path.join(ROOT, DELETE))

    print("\n%d files rewired to SettingsWorkTracker" % len(pending))

    for rel, _ in EDITS:
        print("   %s" % rel)

    print("\ndeleted %s" % DELETE)
    print("\n⚠ THIS ROUND REMOVES A FILE. Extracting the zip over an old tree does not delete it,")
    print("  and a stale copy compiles but is dead. Tell the author to run, in the project root:")
    print("\n  Remove-Item -Force %s\n" % DELETE.replace("/", "\\"))

    return 0


if __name__ == "__main__":
    sys.exit(main())
