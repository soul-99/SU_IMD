#!/usr/bin/env python3
"""
v3-r2a — the author's toast rework: one progress toast, every completion toast, all short.

Three instructions, in his words:

* "for progress i need toasts only when IMD+ starts trying to hide settings" — so
  `IMD+: Hiding settings...` survives and the other four "..." toasts go, strings and all.
* "i need all toasts for when hiding or unhiding gets completed" — and two paths had none.
* "Make all the toasts that IMD sends to short length, i mean all" — including the three
  failures, which were the only LENGTH_LONG ones in the app.

**Why that one progress toast is the one that stays.** It is the only work the user did not
ask for. IMD+ force-stops the app they just tapped, so without a word the app they opened
simply vanishes for a couple of seconds. Everywhere else somebody pressed a tile, a button or a
notification and is already looking at the thing they pressed; a progress toast there only
queues in front of the completion toast, which is the one carrying the answer.

**The two silent completions this fixes.** Both are unhides under the memory function:

* `AutoHideRunner.revert(componentName != null)` — IMD+'s own per-app revert — said
  `IMD+: Unhiding settings...` and then nothing at all. This is the case the author reported:
  "auto unhide does show start toast ... but does not show unhiding completed toast".
* `AutoUnhideWatcher.revertOneProfile` — the swipe/idle trigger's per-app revert — said nothing
  in either direction. Its r12 comment argued there is nobody in front of the screen, which is
  true of the screen-lock trigger but not of these two: a swipe-away and an idle timeout both
  happen with the screen on.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "common/src/main/res"

LOCALES = [
    "values", "values-ar", "values-b+pt+BR", "values-b+zh+Hans", "values-de",
    "values-es", "values-fr", "values-hi", "values-ja", "values-ko", "values-ru",
]

# The four progress toasts the author removed. `toast_auto_hiding` is deliberately not here.
DROP = [
    "toast_hiding",
    "toast_unhiding",
    "toast_auto_unhiding",
    "toast_auto_revert_running",
]

KEEP = "toast_auto_hiding"

TOASTS = "common/src/main/kotlin/com/android/geto/common/RevertToasts.kt"

TOASTS_EDITS: list[tuple[str, str]] = [
    # The failure trio: the app's only long toasts, and the author's "i mean all" is about
    # exactly this kind of exception.
    (
        """ * Fired after the "Revert to default" toast rather than instead of it: the first says what ran,
 * this says what did not land, and losing the first would make a revert that half worked look
 * like a revert that never started.
 */
fun Context.showRevertShizukuFailedToast() =
    showRevertToast(R.string.revert_failed_shizuku_toast, long = true)

fun Context.showRevertOverlayFailedToast() =
    showRevertToast(R.string.revert_failed_overlay_toast, long = true)

fun Context.showRevertShizukuAndOverlayFailedToast() =
    showRevertToast(R.string.revert_failed_shizuku_and_overlay_toast, long = true)
""",
        """ * Fired **instead of** the completion toast rather than after it: a revert that could not put
 * Shizuku back has not finished, and "Settings reverted" followed a second later by a
 * contradiction is two toasts queued behind each other where only the second one matters.
 *
 * ⚠ **Short, like every other toast in the app now.** These three were the last LENGTH_LONG
 * ones and they are a sentence and a half each, which is more than a short toast comfortably
 * holds — but the author's instruction is that every toast IMD sends is short, and none of
 * these is the only place its news appears: each of the three cases also raises a notification,
 * which is the copy the user can read at their own pace and act on.
 */
fun Context.showRevertShizukuFailedToast() =
    showRevertToast(R.string.revert_failed_shizuku_toast)

fun Context.showRevertOverlayFailedToast() =
    showRevertToast(R.string.revert_failed_overlay_toast)

fun Context.showRevertShizukuAndOverlayFailedToast() =
    showRevertToast(R.string.revert_failed_shizuku_and_overlay_toast)
""",
    ),
    # The v3 set's header, and four helpers deleted.
    (
        """/**
 * The v3 toast set: one pair said as the work starts, five said when it has finished.
 *
 * ⚠ **The completion toasts name the framework that acted, and that is the whole point of
 * them.** After the split "the settings came back" is no longer one sentence: they may have
 * been driven to the configured defaults or restored to what was actually there, for the
 * device or for one app, and a user who cannot tell which cannot tell whether the app did what
 * they asked. The start toasts stay short because they are said over a device that is still
 * changing; the completion ones are long because they are the answer.
 *
 * The IMD+ forms differ only in the prefix, at the author's instruction, so that a toast the
 * user did not ask for is identifiable as IMD+'s at a glance.
 */
fun Context.showHidingToast() = showRevertToast(R.string.toast_hiding)

fun Context.showUnhidingToast() = showRevertToast(R.string.toast_unhiding)

fun Context.showAutoHidingToast() = showRevertToast(R.string.toast_auto_hiding)

fun Context.showAutoUnhidingToast() = showRevertToast(R.string.toast_auto_unhiding)

fun Context.showAutoRevertRunningToast() =
    showRevertToast(R.string.toast_auto_revert_running)
""",
        """/**
 * The v3 toast set: **one** said as the work starts, five said when it has finished.
 *
 * ⚠ **The completion toasts name the framework that acted, and that is the whole point of
 * them.** After the split "the settings came back" is no longer one sentence: they may have
 * been driven to the configured defaults or restored to what was actually there, for the
 * device or for one app, and a user who cannot tell which cannot tell whether the app did what
 * they asked.
 *
 * ⚠ **One progress toast, and it is IMD+'s hide.** The author's rule, and the reason it is
 * this one: it is the only work nobody asked for. IMD+ force-stops the app the user has just
 * tapped, so without a word the app they opened simply vanishes. Every other route was pressed
 * — a tile, a button, a notification — and the user is already looking at the thing they
 * pressed, so a progress toast there says nothing and queues in front of the completion toast,
 * which is the one carrying the answer. Two toasts for one press also read as two things
 * happening.
 *
 * The IMD+ prefix marks a toast the user did not ask for, which is why only the **hide** has
 * one. An unhide is always asked for — a notification button, a tile, a swipe-away the user
 * chose — whichever framework hid the settings, so every unhide speaks as IMD.
 */
fun Context.showAutoHidingToast() = showRevertToast(R.string.toast_auto_hiding)
""",
    ),
    # Every toast short, so the flag has nothing left to select and goes with it.
    (
        """private fun Context.showRevertToast(
    message: Int,
    long: Boolean = false,
    argument: String? = null,
) {
    val application = applicationContext

    // LENGTH_LONG for the failures. They are a sentence and a half naming two things and
    // where to fix them, and the short duration is about two seconds - enough to notice a
    // toast, not enough to read one. Android allows no third option: the duration is a flag,
    // not a number, and anything longer than this needs a dialog or the notification, both of
    // which the failures already have.
    val duration = if (long) Toast.LENGTH_LONG else Toast.LENGTH_SHORT

""",
        """private fun Context.showRevertToast(
    message: Int,
    argument: String? = null,
) {
    val application = applicationContext

""",
    ),
    (
        "        Toast.makeText(application, text, duration).show()",
        "        Toast.makeText(application, text, Toast.LENGTH_SHORT).show()",
    ),
]

RUNNER = "broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/RevertToDefaultRunner.kt"

RUNNER_EDITS: list[tuple[str, str]] = [
    (
        "import com.android.geto.common.SettingsObservationGate\n"
        "import com.android.geto.common.showAutoRevertRunningToast\n"
        "import com.android.geto.common.showRevertOverlayFailedToast\n",
        "import com.android.geto.common.SettingsObservationGate\n"
        "import com.android.geto.common.showRevertOverlayFailedToast\n",
    ),
    (
        "import com.android.geto.common.showRevertedToast\n"
        "import com.android.geto.common.showUnhidingToast\n",
        "import com.android.geto.common.showRevertedToast\n",
    ),
    (
        """    /**
     * [auto] only changes what the toast says. The work is identical, and the six manual
     * entry points and the automatic one must not be able to drift apart in what they do.
     *
     * [fromMemory] is the device-wide **memory** revert: instead of the configured defaults,
""",
        """    /**
     * ⚠ **No progress toast any more, and the `auto` parameter went with it.** It existed only
     * to choose between two "..." toasts, and the author has removed both: the toast for this
     * work is the one at the end, which says which framework actually acted. Nothing else ever
     * branched on it — every one of the seven entry points ran identical work — so there is no
     * behaviour left for it to select.
     *
     * [fromMemory] is the device-wide **memory** revert: instead of the configured defaults,
""",
    ),
    (
        """    suspend operator fun invoke(
        auto: Boolean = false,
        fromMemory: Boolean = false,
    ): RevertToDefaultResult {
        // ⚠ **Two toasts now, not one, and the split is the author's.** This one is said
        // before the work because reverting takes a couple of seconds — longer when Shizuku
        // has to wait for adbd — and silence for that long from a tile press reads as nothing
        // having happened. It says only that something is running; the one at the end says
        // which framework acted, which is the answer and could not honestly be given here.
        if (auto) {
            context.showAutoRevertRunningToast()
        } else {
            context.showUnhidingToast()
        }

        // Every per-app Revert button now describes a device that no longer exists, and
""",
        """    suspend operator fun invoke(fromMemory: Boolean = false): RevertToDefaultResult {
        // Every per-app Revert button now describes a device that no longer exists, and
""",
    ),
]

AUTO_HIDE = "broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/AutoHideRunner.kt"

AUTO_HIDE_EDITS: list[tuple[str, str]] = [
    (
        "import com.android.geto.common.showHiddenToast\n"
        "import com.android.geto.common.showAutoUnhidingToast\n"
        "import com.android.geto.common.showRevertOverlayFailedToast\n",
        "import com.android.geto.common.showHiddenToast\n"
        "import com.android.geto.common.showRevertOverlayFailedToast\n"
        "import com.android.geto.common.showRevertedToast\n",
    ),
    (
        "import com.android.geto.domain.model.HidingFramework\n",
        "import com.android.geto.domain.model.HidingFramework\n"
        "import com.android.geto.domain.model.UnhidingFramework\n",
    ),
    (
        """        context.showAutoUnhidingToast()

        // The memory function's revert: put back exactly what this run hid for this one app,
""",
        """        // The memory function's revert: put back exactly what this run hid for this one app,
""",
    ),
    (
        """            if (overlayRestoreRunner.reportIfFailed()) {
                context.showRevertOverlayFailedToast()
            }

            return@track
        }
""",
        """            if (overlayRestoreRunner.reportIfFailed()) {
                context.showRevertOverlayFailedToast()
            } else {
                // ⚠ **This branch used to say nothing at all, and it is the author's report.**
                // The route announced itself on the way in and then went silent, so an IMD+
                // per-app revert that worked was indistinguishable from one that hung. The
                // start toast is gone and this is what replaces it.
                //
                // It speaks as IMD rather than IMD+: the prefix marks work nobody asked for,
                // and this revert was asked for — the user tapped the notification, pressed
                // the tile or swiped the app away.
                context.showRevertedToast(
                    fromMemory = true,
                    appName = packageManagerWrapper.getActivityLabel(
                        componentName = componentName,
                    ),
                )
            }

            return@track
        }
""",
    ),
    (
        """        userDataRepository.updateAutoHideRunning(running = false)

        revertToDefaultRunner()
""",
        """        userDataRepository.updateAutoHideRunning(running = false)

        // ⚠ **The Unhiding framework decides where a device-wide IMD+ hide comes back to, and
        // this call used to ignore it.** Under UnhidingFramework.Memory the keyed targets go
        // back to what the hide measured; a bare call drives the configured defaults instead,
        // which is precisely the "IMD touching settings the user never had before hiding" the
        // memory function exists to prevent. `SettingsHiddenRunner.unhide` asks this same
        // question for the tile, but every IMD+ hide short-circuits past it to here.
        revertToDefaultRunner(
            fromMemory = userDataRepository.userData.first().unhidingFramework ==
                UnhidingFramework.Memory,
        )
""",
    ),
]

AUTO_REVERT = "broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/AutoRevertRunner.kt"

AUTO_REVERT_EDITS: list[tuple[str, str]] = [
    (
        "            UnhidingFramework.RevertToDefault -> revertToDefaultRunner(auto = true)",
        "            UnhidingFramework.RevertToDefault -> revertToDefaultRunner()",
    ),
]

WATCHER = "broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/AutoUnhideWatcher.kt"

WATCHER_EDITS: list[tuple[str, str]] = [
    (
        """import android.os.SystemClock
import com.android.geto.common.AutoRevertPending
import com.android.geto.common.AutoUnhideWatch
import com.android.geto.domain.common.Diagnostics
import com.android.geto.domain.framework.AppSessionWrapper
""",
        """import android.content.Context
import android.os.SystemClock
import com.android.geto.common.AutoRevertPending
import com.android.geto.common.AutoUnhideWatch
import com.android.geto.common.showRevertOverlayFailedToast
import com.android.geto.common.showRevertedToast
import com.android.geto.domain.common.Diagnostics
import com.android.geto.domain.framework.AppSessionWrapper
import com.android.geto.domain.framework.PackageManagerWrapper
""",
    ),
    (
        """import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper
import kotlinx.coroutines.sync.Mutex
""",
        """import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.sync.Mutex
""",
    ),
    (
        """class AutoUnhideWatcher @Inject constructor(
    private val getAutoUnhideSettingsUseCase: GetAutoUnhideSettingsUseCase,
    private val getSettingsHiddenUseCase: GetSettingsHiddenUseCase,
    private val revertAppSettingsUseCase: RevertAppSettingsUseCase,
    private val settingsHiddenRunner: SettingsHiddenRunner,
    private val settingsWorkTracker: SettingsWorkTracker,
    private val appSessionWrapper: AppSessionWrapper,
    private val notificationManagerWrapper: AndroidNotificationManagerWrapper,
) {
""",
        """class AutoUnhideWatcher @Inject constructor(
    @param:ApplicationContext private val context: Context,
    private val getAutoUnhideSettingsUseCase: GetAutoUnhideSettingsUseCase,
    private val getSettingsHiddenUseCase: GetSettingsHiddenUseCase,
    private val revertAppSettingsUseCase: RevertAppSettingsUseCase,
    private val settingsHiddenRunner: SettingsHiddenRunner,
    private val settingsWorkTracker: SettingsWorkTracker,
    private val appSessionWrapper: AppSessionWrapper,
    private val packageManagerWrapper: PackageManagerWrapper,
    private val overlayRestoreRunner: OverlayRestoreRunner,
    private val notificationManagerWrapper: AndroidNotificationManagerWrapper,
) {
""",
    ),
    (
        """     * The notification is cancelled here rather than left to the revert, for the reason
     * [AutoRevertRunner] cancels it too: it is posted under the component name's hash code and
     * would otherwise sit there offering to undo a device that has already been put back.
     */
    private suspend fun revertOneProfile(componentName: String) {
        // Before the work, as on the device-wide path. See AutoUnhideWatch.reverting.
        AutoUnhideWatch.reverting = true

        revertAppSettingsUseCase(componentName = componentName)

        notificationManagerWrapper.cancel(componentName.hashCode())
    }
""",
        """     * The notification is cancelled here rather than left to the revert, for the reason
     * [AutoRevertRunner] cancels it too: it is posted under the component name's hash code and
     * would otherwise sit there offering to undo a device that has already been put back.
     *
     * ⚠ **It says so now, and r12's reasoning for silence only ever covered one trigger.** That
     * comment argued there is nobody in front of the screen — true of the screen-lock timer,
     * which does not come through here at all: it calls [revertEverything]. The two triggers
     * that do reach this are a swipe-away and an idle timeout, and both happen with the screen
     * on and the user holding the phone. The author's instruction is a completion toast on
     * every hide and every unhide.
     */
    private suspend fun revertOneProfile(componentName: String) {
        // Before the work, as on the device-wide path. See AutoUnhideWatch.reverting.
        AutoUnhideWatch.reverting = true

        revertAppSettingsUseCase(componentName = componentName)

        notificationManagerWrapper.cancel(componentName.hashCode())

        // Same shape as [AutoRevertRunner]'s memory branch, and for the same reason: the
        // overlay step is deliberately allowed to fail without failing the rest of the
        // profile, so its outcome is reported here or nowhere. Saying "reverted from memory"
        // over a device that did not get its overlay access back would be the wrong news.
        // Shizuku is never a target of a per-app revert, so only the one message applies.
        if (overlayRestoreRunner.reportIfFailed()) {
            context.showRevertOverlayFailedToast()
        } else {
            context.showRevertedToast(
                fromMemory = true,
                appName = packageManagerWrapper.getActivityLabel(componentName = componentName),
            )
        }
    }
""",
    ),
    (
        """     * It also routes an IMD+ hide into IMD+'s own revert, which force-stops the watched apps
     * before restoring anything — so that path stays correct without this knowing about it.
     *
     * No toast. Every other automatic revert says something because the user is looking at
     * IMD when it happens; this one fires because they swiped an app away or put the phone
     * down, and there is nobody in front of the screen to read it.
     */
    private suspend fun revertEverything() {
        Diagnostics.log(tag = "revert", message = "auto unhide: flushPendingReverts")

        // Before the work, not after it. See AutoUnhideWatch.reverting.
        AutoUnhideWatch.reverting = true

        settingsHiddenRunner.flushPendingReverts()

        clearRevertNotifications()

""",
        """     * It also routes an IMD+ hide into IMD+'s own revert, which force-stops the watched apps
     * before restoring anything — so that path stays correct without this knowing about it.
     *
     * The toast comes from the revert underneath, which is the only thing that knows which
     * framework acted. On the screen-lock trigger nobody sees it, and that is fine: a toast
     * over a dark screen costs nothing, and inventing a way to suppress it per trigger would
     * mean this deciding what the revert below is allowed to say.
     */
    private suspend fun revertEverything() {
        Diagnostics.log(tag = "revert", message = "auto unhide: flushPendingReverts")

        // Before the work, not after it. See AutoUnhideWatch.reverting.
        AutoUnhideWatch.reverting = true

        // ⚠ **Swept before the revert, not after it, and the order is load-bearing.** This is a
        // cancelAll, and afterwards was late enough to catch the two notifications the revert
        // raises about *itself* — overlay access it could not give back, a Shizuku it could not
        // restart. Both were posted and then wiped a moment later by the same run, leaving a
        // failure the user was never told about. Everything this is here to clear is already
        // standing before the revert begins.
        clearRevertNotifications()

        settingsHiddenRunner.flushPendingReverts()

""",
    ),
    (
        """        // Nothing is hidden any more, so nothing in the shade can still be offering to undo
        // it. Only here, and never while a debt remains: a per-app Revert for an app that is
        // still hidden has to stay exactly where it is.
        clearRevertNotifications()

""",
        """        // Nothing is hidden any more, so nothing in the shade can still be offering to undo
        // it. Only here, and never while a debt remains: a per-app Revert for an app that is
        // still hidden has to stay exactly where it is.
        clearRevertNotifications()

        // The one thing the sweep above must not take with it. [revertOneProfile] runs before
        // this line and can leave overlay access still owed; its report is the only notice the
        // user gets, and cancelAll does not know to spare it. Re-raised rather than reordered
        // because the per-app reverts happen in a loop further up, with no single point before
        // the sweep to put this at. Reads a stored flag, so it is silent unless something
        // really is outstanding.
        overlayRestoreRunner.reportIfFailed()

""",
    ),
]


def strip_key(text: str, key: str, locale: str, problems: list[str]) -> str:
    pattern = re.compile(rf'^    <string name="{key}">.*?</string>\n', re.M | re.S)

    found = pattern.findall(text)

    if len(found) != 1:
        problems.append(f"{locale}: {len(found)} of {key}, expected 1")

        return text

    return pattern.sub("", text, count=1)


def apply(path: Path, edits: list[tuple[str, str]], problems: list[str]) -> str | None:
    if not path.exists():
        problems.append(f"{path} is missing")

        return None

    text = path.read_text(encoding="utf-8")

    for old, new in edits:
        found = text.count(old)

        if found != 1:
            problems.append(f"{path.name}: {found} of {old.strip().splitlines()[0][:70]!r}")

            continue

        text = text.replace(old, new, 1)

    return text


def main() -> int:
    problems: list[str] = []

    staged: dict[Path, str] = {}

    for locale in LOCALES:
        path = RES / locale / "strings.xml"

        if not path.exists():
            problems.append(f"{locale}: no strings.xml")

            continue

        text = path.read_text(encoding="utf-8")

        for key in DROP:
            text = strip_key(text=text, key=key, locale=locale, problems=problems)

        # The one that survives, asserted in every locale rather than assumed.
        if f'<string name="{KEEP}">' not in text:
            problems.append(f"{locale}: {KEEP} is gone and it must not be")

        staged[path] = text

    for path, text in staged.items():
        try:
            ET.fromstring(text)
        except ET.ParseError as error:
            problems.append(f"{path.parent.name}: does not parse — {error}")

    for name, edits in (
        (TOASTS, TOASTS_EDITS),
        (RUNNER, RUNNER_EDITS),
        (AUTO_HIDE, AUTO_HIDE_EDITS),
        (AUTO_REVERT, AUTO_REVERT_EDITS),
        (WATCHER, WATCHER_EDITS),
    ):
        path = ROOT / name

        text = apply(path=path, edits=edits, problems=problems)

        if text is not None:
            staged[path] = text

    # The five `long = true,` arguments inside the two completion helpers, which the block
    # edits above deliberately do not cover — they sit in the middle of code that is otherwise
    # unchanged, and rewriting both functions whole to delete one line each is how a round
    # loses a declaration it did not mean to.
    toasts = ROOT / TOASTS

    if toasts in staged:
        text = staged[toasts]

        lines = re.findall(r"^ +long = true,\n", text, re.M)

        if len(lines) != 5:
            problems.append(f"{TOASTS}: {len(lines)} `long = true,` lines, expected 5")
        else:
            text = re.sub(r"^ +long = true,\n", "", text, flags=re.M)

        if "long" in text.replace("longer", ""):
            problems.append(f"{TOASTS}: the word `long` survives somewhere")

        staged[toasts] = text

    # Nothing anywhere may still call the four that are going.
    gone = [
        "showHidingToast",
        "showUnhidingToast",
        "showAutoUnhidingToast",
        "showAutoRevertRunningToast",
    ]

    for kotlin in sorted(ROOT.rglob("*.kt")):
        if "build" in kotlin.relative_to(ROOT).parts:
            continue

        body = staged.get(kotlin) or kotlin.read_text(encoding="utf-8")

        for name in gone:
            if re.search(rf"\b{name}\b", body):
                problems.append(f"{kotlin.relative_to(ROOT)}: still mentions {name}")

    for kotlin in (ROOT / TOASTS, ROOT / RUNNER, ROOT / AUTO_HIDE, ROOT / WATCHER):
        for line in staged.get(kotlin, "").splitlines():
            if len(line) > 120:
                problems.append(f"{kotlin.name}: {len(line)} chars — {line.strip()[:60]}")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")

    print(f"ok — {len(DROP)} progress toasts dropped from {len(LOCALES)} locales, "
          f"{len(staged) - len(LOCALES)} Kotlin files rewired, every toast now LENGTH_SHORT")

    return 0


if __name__ == "__main__":
    sys.exit(main())
