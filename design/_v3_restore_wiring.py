#!/usr/bin/env python3
"""
v3-r2e — the Kotlin side of restore/reverted, the four removed toasts, and the Favourites button.

Four jobs, all of them consequences of the same set of instructions, and separating them into
four scripts would mean four half-states any one of which does not compile.

### 1. `showRevertedToast` splits in two

The author's exception — restore everywhere "except for when explicitly revert to default is
run from anywhere other than reverts. like IMD services manager/ intent/ revert to default qs
toggle" — is a distinction the old single helper could not draw, because the *named* function
and a framework-following unhide reach the same runner with the same arguments.

* `showRestoredToast(fromMemory, appName)` — the way back from a hide, whatever drove it.
* `showRevertedToDefaultToast()` — the named `Revert to default` function, invoked on purpose.
* `showNothingToRestoreToast()` — the Favourites button with nothing outstanding.

`RevertToDefaultRunner` gains `explicit`, set true at exactly three call sites: the settings
manager's button, `RevertActivity` (the Revert to default tile **and** the launcher shortcut,
which share it) and Tasker's `ACTION_REVERT_TO_DEFAULT`. Everything else is a way back from a
hide and says restored — including `AutoRevertRunner`, which reaches the same runner but is the
automatic unhide rather than a press of the named button.

⚠ `autoHide` leaves `showRevertedToast` with it. The author: **"only hiding ones say IMD+ other
say IMD"** — so the three IMD+ unhide strings are gone and the branch that chose them with them.
`showHiddenToast` keeps its `autoHide`; the hide is the half that still says IMD+.

### 2. The three failure toasts and the Shizuku wait toast go

Checked before removing rather than after: **every case they covered already raises a
notification.** Overlay access fails → `OverlayRestoreRunner.report()`; Shizuku fails →
`buildShizukuRevertFailedNotification`; both fail → the overlay notification, which names
Shizuku as the cause and carries a Try again. So the `if (reportIfFailed()) toast else
completion` shape everywhere becomes `if (!reportIfFailed()) completion` — the report still
happens, it just no longer also speaks.

⚠ **A failed revert now says nothing at all in a toast, and that is deliberate.** Showing the
completion toast instead would have the app claim success over a revert that half worked.

### 3. The Favourites FAB unhides

It ran `Revert to default`. It now runs what the Hide settings tile runs when settings are
hidden — `SettingsHiddenRunner.unhidePending`, which is `flushPendingReverts` plus the author's
"and if no current reverts are pending display toast".

⚠ **`flushPendingReverts`, not `unhide`.** `unhide` is the tile's behaviour and falls back to
the configured defaults when nothing is hidden, because a tile that did nothing reads as broken.
Here the author asked for the opposite: say there is nothing to restore and change no setting.

The icon is unchanged at the author's instruction. The content description is not — it is what
TalkBack reads aloud, and "Revert to default" is no longer what the button does.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BR = "broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver"
APPS = "feature/apps/src/main/kotlin/com/android/geto/feature/apps"

TOASTS = "common/src/main/kotlin/com/android/geto/common/RevertToasts.kt"

TOASTS_EDITS: list[tuple[str, str]] = [
    # The failure trio, and the doc comment that was only about them.
    (
        """/**
 * The three ways a revert can end without having finished.
 *
 * Only Shizuku and overlay access get a message, because they are the only two that depend on
 * something outside this app and so the only two a user cannot simply fix from the services
 * manager. A failed settings write is already visible there as a switch in the wrong position.
 *
 * Fired **instead of** the completion toast rather than after it: a revert that could not put
 * Shizuku back has not finished, and "Settings reverted" followed a second later by a
 * contradiction is two toasts queued behind each other where only the second one matters.
 *
 * ⚠ **Short, like every other toast in the app.** These three were the longest of them and are
 * a sentence and a half each, which is more than a short toast comfortably holds — but the
 * author's instruction is that every toast IMD sends is short, and none of these is the only
 * place its news appears: each of the three cases also raises a notification, which is the copy
 * the user can read at their own pace and act on.
 *
 * There is no LENGTH_LONG anywhere in the app now, here or in the six module-local toasts that
 * call `Toast.makeText` directly. `design/_v3_toast_length.py` asserts it.
 */
fun Context.showRevertShizukuFailedToast() =
    showRevertToast(R.string.revert_failed_shizuku_toast)

fun Context.showRevertOverlayFailedToast() =
    showRevertToast(R.string.revert_failed_overlay_toast)

fun Context.showRevertShizukuAndOverlayFailedToast() =
    showRevertToast(R.string.revert_failed_shizuku_and_overlay_toast)

/**
""",
        """/**
""",
    ),
    (
        """ * The IMD+ prefix marks a toast the user did not ask for, which is why only the **hide** has
 * one. An unhide is always asked for — a notification button, a tile, a swipe-away the user
 * chose — whichever framework hid the settings, so every unhide speaks as IMD.
 */
""",
        """ * ⚠ **Only the hiding ones say IMD+, and that is the author's rule stated outright.** The
 * prefix marks work the user did not ask for, and an unhide is always asked for — a
 * notification button, a tile, a swipe-away, a phone put down — whichever framework hid the
 * settings. Both prefixes respect the Hiding and Unhiding frameworks; the prefix says who
 * started the work, not which framework ran.
 *
 * ⚠ **There are no failure toasts any more.** Every case the old three covered already raises
 * a notification — `OverlayRestoreRunner.report()` for overlay access,
 * `buildShizukuRevertFailedNotification` for Shizuku, and the overlay one names Shizuku as the
 * cause when both fail — so removing them lost no news, only a duplicate of it. A revert that
 * did not finish therefore says **nothing** rather than borrowing the completion toast: the
 * notification is the honest report, and "Settings restored" over a half-done revert is not.
 */
""",
    ),
    # The single revert helper becomes three, one per thing there is to say.
    (
        """/**
 * [appName] is the per-app memory revert's app, and null is not a missing value — it is the
 * device-wide memory record, which names no app because no app owns it. The two sentences
 * differ by a bracket for exactly that reason.
 *
 * ⚠ **[autoHide] is never passed true, and that is a question for the author rather than dead
 * weight to delete.** Every unhide in the app is something the user asked for — a notification
 * button, a tile, a swipe-away — so all of them currently speak as IMD, and the three
 * `toast_auto_done_reverted_*` strings behind this branch are unreachable. They are translated
 * and ready in all eleven locales if he decides an unhide that IMD+ set in motion should carry
 * the IMD+ prefix after all. Deleting the branch would make that a re-translation.
 */
fun Context.showRevertedToast(
    fromMemory: Boolean,
    appName: String? = null,
    autoHide: Boolean = false,
) {
    if (!fromMemory) {
        showRevertToast(
            if (autoHide) {
                R.string.toast_auto_done_reverted_defaults
            } else {
                R.string.toast_done_reverted_defaults
            },
        )

        return
    }

    if (appName == null) {
        showRevertToast(
            if (autoHide) {
                R.string.toast_auto_done_reverted_memory
            } else {
                R.string.toast_done_reverted_memory
            },
        )

        return
    }

    showRevertToast(
        if (autoHide) {
            R.string.toast_auto_done_reverted_memory_for
        } else {
            R.string.toast_done_reverted_memory_for
        },
        argument = appName,
    )
}
""",
        """/**
 * The way back from a hide, whatever set it in motion and whichever framework drove it.
 *
 * [appName] is the per-app memory revert's app, and null is not a missing value — it is the
 * device-wide memory record, which names no app because no app owns it. The two sentences
 * differ by a bracket for exactly that reason.
 *
 * ⚠ **"Restored", not "reverted", and [showRevertedToDefaultToast] is the exception that
 * defines it.** The author's rule: a hide is undone, so the settings are *restored* — even on
 * the `RevertToDefault` unhiding framework, where the destination happens to be the configured
 * list. Only the named `Revert to default` function, run on purpose from somewhere that is not
 * an unhide, still says reverted. Same work underneath; two different things to say about it.
 */
fun Context.showRestoredToast(fromMemory: Boolean, appName: String? = null) {
    if (!fromMemory) {
        showRevertToast(R.string.toast_done_restored_defaults)

        return
    }

    if (appName == null) {
        showRevertToast(R.string.toast_done_restored_memory)

        return
    }

    showRevertToast(R.string.toast_done_restored_memory_for, argument = appName)
}

/**
 * The named `Revert to default` function, invoked on purpose.
 *
 * Three routes reach this and the author named all three: the settings manager's button, the
 * Revert to default Quick Settings tile (and the launcher shortcut, which shares its activity),
 * and Tasker's `ACTION_REVERT_TO_DEFAULT`. What they have in common is that nobody was undoing
 * a hide — they asked for the device to be put into the state they nominated as normal, which
 * is a thing you revert to rather than restore.
 */
fun Context.showRevertedToDefaultToast() = showRevertToast(R.string.toast_done_reverted_defaults)

/**
 * The Favourites button when there is no debt to settle.
 *
 * Only that button says this, and only because it is the one unhide route that refuses to fall
 * back. The Hide settings tile in the same position reverts to default instead, on the grounds
 * that a tile which did nothing reads as broken; this button is pressed from a screen that can
 * answer in words, so it answers.
 */
fun Context.showNothingToRestoreToast() = showRevertToast(R.string.toast_nothing_to_restore)
""",
    ),
]

RUNNER = f"{BR}/RevertToDefaultRunner.kt"

RUNNER_EDITS: list[tuple[str, str]] = [
    (
        """import com.android.geto.common.SettingsObservationGate
import com.android.geto.common.showRevertOverlayFailedToast
import com.android.geto.common.showRevertShizukuAndOverlayFailedToast
import com.android.geto.common.showRevertShizukuFailedToast
import com.android.geto.common.showRevertedToast
""",
        """import com.android.geto.common.SettingsObservationGate
import com.android.geto.common.showRestoredToast
import com.android.geto.common.showRevertedToDefaultToast
""",
    ),
    (
        """     * [fromMemory] is the device-wide **memory** revert: instead of the configured defaults,
     * every keyed target is driven back to what the hide measured. Only the framework-following
     * routes pass it — the notification, the Hide settings QS toggle and the
     * `Unhide settings and services` intent. The explicit `Revert to default` routes never do,
     * on the author's instruction that Revert to default always means the defaults.
     */""",
        """     * [fromMemory] is the device-wide **memory** revert: instead of the configured defaults,
     * every keyed target is driven back to what the hide measured. Only the framework-following
     * routes pass it — the notification, the Hide settings QS toggle and the
     * `Unhide settings and services` intent. The explicit `Revert to default` routes never do,
     * on the author's instruction that Revert to default always means the defaults.
     *
     * [explicit] changes **only what the toast says**, and it is the author's restore/revert
     * exception: the named `Revert to default` function says reverted, every way back from a
     * hide says restored. Three routes set it — the settings manager's button, `RevertActivity`
     * (the tile and the launcher shortcut share it) and Tasker's `ACTION_REVERT_TO_DEFAULT`.
     *
     * ⚠ It is **not** the same question as [fromMemory], and neither implies the other. A
     * framework-following unhide under `UnhidingFramework.RevertToDefault` arrives here with
     * both false and drives the configured defaults — the same work as an explicit revert, but
     * it is undoing a hide, so it says restored.
     */""",
    ),
    (
        """    suspend operator fun invoke(fromMemory: Boolean = false): RevertToDefaultResult {""",
        """    suspend operator fun invoke(
        fromMemory: Boolean = false,
        explicit: Boolean = false,
    ): RevertToDefaultResult {""",
    ),
    (
        """                // Only these two are worth a toast: they are the pair that depends on
                // something outside this app, so a user cannot simply put them right from
                // the services manager the way they can a settings write.
                val shizukuFailed = ManualRevertTarget.Shizuku in result.failed

                when {
                    shizukuFailed && result.overlayRestoreFailed ->
                        context.showRevertShizukuAndOverlayFailedToast()

                    shizukuFailed -> context.showRevertShizukuFailedToast()

                    result.overlayRestoreFailed -> context.showRevertOverlayFailedToast()

                    // Nothing went wrong, so say what happened. Named for the destination
                    // this run actually drove to rather than for the framework stored right
                    // now: a framework changed between the press and this line would
                    // otherwise have the toast describe a revert that did not run.
                    else -> context.showRevertedToast(fromMemory = fromMemory)
                }
""",
        """                val shizukuFailed = ManualRevertTarget.Shizuku in result.failed

                // ⚠ **Only when nothing went wrong, and there is no failure toast to take
                // its place.** The author removed those, and his reasoning holds: both cases
                // raise a notification below or through `report()` above, which is the copy
                // he can act on. What must not happen is the completion toast standing in for
                // them — a revert that could not put Shizuku back has not finished, and
                // "Settings restored" over it would be the app claiming something untrue.
                //
                // Named for the destination this run actually drove to rather than for the
                // framework stored right now: a framework changed between the press and this
                // line would otherwise have the toast describe a revert that did not run.
                if (!shizukuFailed && !result.overlayRestoreFailed) {
                    if (explicit) {
                        context.showRevertedToDefaultToast()
                    } else {
                        context.showRestoredToast(fromMemory = fromMemory)
                    }
                }
""",
    ),
]

HIDDEN_RUNNER = f"{BR}/SettingsHiddenRunner.kt"

HIDDEN_RUNNER_EDITS: list[tuple[str, str]] = [
    (
        """import com.android.geto.common.showHiddenToast
import com.android.geto.common.showRevertedToast
""",
        """import com.android.geto.common.showHiddenToast
import com.android.geto.common.showNothingToRestoreToast
import com.android.geto.common.showRestoredToast
""",
    ),
    (
        "            if (!deviceWide) context.showRevertedToast(fromMemory = true)",
        "            if (!deviceWide) context.showRestoredToast(fromMemory = true)",
    ),
    (
        """    suspend fun flushPendingReverts() = unhide(fallbackToDefault = false)
""",
        """    suspend fun flushPendingReverts() = unhide(fallbackToDefault = false)

    /**
     * The Favourites tab's button: settle whatever is outstanding, or say there is nothing.
     *
     * ⚠ **[flushPendingReverts], not [unhide], and the difference is the author's
     * instruction.** `unhide` is the Hide settings tile's behaviour and falls back to the
     * configured defaults on a device with nothing hidden, because a tile that did nothing
     * reads as broken. This button is pressed from a screen that can answer in words, and the
     * author asked it to answer: `'IMD: No hidden settings to restore'`, and no setting touched.
     *
     * The three questions are asked together because a device can owe on more than one at
     * once — an IMD+ run, a device-wide hide and a pile of per-app records are three separate
     * debts, and having any one of them means there is work to do here.
     */
    suspend fun unhidePending() {
        val running = userDataRepository.userData.first().autoHideRunning

        val hidden = getSettingsHiddenUseCase()

        if (!running && !hidden.memory && !hidden.deviceWide) {
            Diagnostics.log(tag = "revert", message = "favourites: nothing outstanding")

            context.showNothingToRestoreToast()

            return
        }

        flushPendingReverts()
    }
""",
    ),
]

# path -> edits. The straightforward renames and the failure branches that collapse.
SIMPLE: dict[str, list[tuple[str, str]]] = {
    f"{BR}/AutoHideRunner.kt": [
        (
            """import com.android.geto.common.showRevertOverlayFailedToast
import com.android.geto.common.showRevertedToast
""",
            """import com.android.geto.common.showRestoredToast
""",
        ),
        (
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
""",
            """            // ⚠ **This branch used to say nothing at all, and it was the author's report.**
            // The route announced itself on the way in and then went silent, so an IMD+
            // per-app revert that worked was indistinguishable from one that hung. The start
            // toast is gone and this is what replaces it.
            //
            // It speaks as IMD rather than IMD+: the prefix marks work nobody asked for, and
            // this revert was asked for — the user tapped the notification, pressed the tile
            // or swiped the app away.
            //
            // Nothing is said when the report fires. The overlay failure has a notification
            // of its own and the completion sentence would be untrue over it.
            if (!overlayRestoreRunner.reportIfFailed()) {
                context.showRestoredToast(
                    fromMemory = true,
                    appName = packageManagerWrapper.getActivityLabel(
                        componentName = componentName,
                    ),
                )
            }
""",
        ),
    ],
    f"{BR}/AutoRevertRunner.kt": [
        (
            """import com.android.geto.common.showRevertedToast
import com.android.geto.common.showRevertOverlayFailedToast
""",
            """import com.android.geto.common.showRestoredToast
""",
        ),
        (
            """                if (overlayRestoreRunner.reportIfFailed()) {
                    context.showRevertOverlayFailedToast()
                } else {
                    context.showRevertedToast(
                        fromMemory = true,
                        appName = packageManagerWrapper.getActivityLabel(
                            componentName = componentName,
                        ),
                        autoHide = false,
                    )
                }
""",
            """                if (!overlayRestoreRunner.reportIfFailed()) {
                    context.showRestoredToast(
                        fromMemory = true,
                        appName = packageManagerWrapper.getActivityLabel(
                            componentName = componentName,
                        ),
                    )
                }
""",
        ),
    ],
    f"{BR}/AutoUnhideWatcher.kt": [
        (
            """import com.android.geto.common.showRevertOverlayFailedToast
import com.android.geto.common.showRevertedToast
""",
            """import com.android.geto.common.showRestoredToast
""",
        ),
        (
            """        if (overlayRestoreRunner.reportIfFailed()) {
            context.showRevertOverlayFailedToast()
        } else {
            context.showRevertedToast(
                fromMemory = true,
                appName = packageManagerWrapper.getActivityLabel(componentName = componentName),
            )
        }
""",
            """        if (!overlayRestoreRunner.reportIfFailed()) {
            context.showRestoredToast(
                fromMemory = true,
                appName = packageManagerWrapper.getActivityLabel(componentName = componentName),
            )
        }
""",
        ),
    ],
    f"{BR}/RevertSettingsBroadcastReceiver.kt": [
        (
            "import com.android.geto.common.showRevertedToast\n",
            "import com.android.geto.common.showRestoredToast\n",
        ),
        (
            "        context?.showRevertedToast(fromMemory = true)",
            "        context?.showRestoredToast(fromMemory = true)",
        ),
        (
            """                if (overlayRestoreRunner.reportIfFailed()) {
                    context?.showRevertOverlayFailedToast()
                }
""",
            """                overlayRestoreRunner.reportIfFailed()
""",
        ),
        (
            "import com.android.geto.common.showRevertOverlayFailedToast\n",
            "",
        ),
    ],
    f"{BR}/TaskerIntegrationBroadcastReceiver.kt": [
        (
            "import com.android.geto.common.showRevertedToast\n",
            "import com.android.geto.common.showRestoredToast\n",
        ),
        (
            """                    // Runs the same revert the notification button and the tile do; it shows
                    // its own toast, so none is added here.
                    TaskerIntegration.ACTION_REVERT_TO_DEFAULT -> revertToDefaultRunner()
""",
            """                    // Runs the same revert the notification button and the tile do; it shows
                    // its own toast, so none is added here. `explicit` because this **is** the
                    // named function — the author listed the intent among the three routes that
                    // still say "reverted".
                    TaskerIntegration.ACTION_REVERT_TO_DEFAULT ->
                        revertToDefaultRunner(explicit = true)
""",
        ),
        (
            "                        context?.showRevertedToast(fromMemory = true)",
            "                        context?.showRestoredToast(fromMemory = true)",
        ),
    ],
    "feature/app-settings/src/main/kotlin/com/android/geto/feature/appsettings/"
    "AppSettingsScreen.kt": [
        (
            "import com.android.geto.common.showRevertedToast\n",
            "import com.android.geto.common.showRestoredToast\n",
        ),
        (
            """            context.showRevertedToast(
                fromMemory = true,
                appName = appSettingsRouteData.activityLabel,
            )""",
            """            context.showRestoredToast(
                fromMemory = true,
                appName = appSettingsRouteData.activityLabel,
            )""",
        ),
    ],
    "app/src/main/kotlin/com/android/geto/activity/revert/RevertActivity.kt": [
        (
            "        appScope.launch { revertToDefaultRunner() }",
            "        // `explicit`: this activity is the Revert to default tile and the launcher\n"
            "        // shortcut, two of the three routes the author named as still saying\n"
            "        // \"reverted\" rather than \"restored\". Nothing here is undoing a hide.\n"
            "        appScope.launch { revertToDefaultRunner(explicit = true) }",
        ),
    ],
    f"{APPS}/manager/SettingsManagerViewModel.kt": [
        (
            "    fun revertToDefault() {\n"
            "        appScope.launch { revertToDefaultRunner() }\n"
            "    }",
            "    fun revertToDefault() {\n"
            "        // `explicit`: the manager's button is the named function, so its toast says\n"
            "        // \"reverted\" rather than \"restored\". The author's own list.\n"
            "        appScope.launch { revertToDefaultRunner(explicit = true) }\n"
            "    }",
        ),
    ],
    f"{APPS}/manager/SettingsManagerRoute.kt": [
        (
            """            if (target == ManualRevertTarget.Shizuku && enabled) {
                context.showShizukuWaitToast()
            }
""",
            "",
        ),
        (
            """/**
 * Shizuku's own start is not instant on every fork — Shevery in particular takes a few
 * seconds to come up after the broadcast — and the switch flipping back to off in the
 * meantime looks exactly like a failure. Saying so up front is cheaper than making the
 * poll lie about it.
 */
internal fun Context.showShizukuWaitToast() {
    Toast.makeText(this, R.string.settings_manager_shizuku_wait, Toast.LENGTH_SHORT).show()
}
""",
            "",
        ),
    ],
    f"{APPS}/FavouriteAppsViewModel.kt": [
        (
            "import com.android.geto.broadcastreceiver.RevertToDefaultRunner\n",
            "import com.android.geto.broadcastreceiver.SettingsHiddenRunner\n",
        ),
        (
            "    private val revertToDefaultRunner: RevertToDefaultRunner,\n",
            "    private val settingsHiddenRunner: SettingsHiddenRunner,\n",
        ),
        (
            """    /**
     * Puts the device back into the configured default.
     *
     * Launched on the application scope rather than [viewModelScope]: leaving the Favourites
     * tab — which is exactly what someone does after pressing this — would otherwise cancel
     * a revert that takes seconds, and can wait on adbd before it is finished.
     */
    fun revertToDefault() {
        appScope.launch { revertToDefaultRunner() }
    }
""",
            """    /**
     * Unhides whatever is actually outstanding, the way the Hide settings tile does.
     *
     * ⚠ **It was `Revert to default` and the author changed it.** The button sits on the tab
     * whose whole purpose is an app that has just refused to start, so what the user wants from
     * it is the hide undone — not the device driven to a configured state that may have nothing
     * to do with what was hidden. Under the memory function those are different destinations,
     * and the old behaviour would have written the defaults over remembered values.
     *
     * With nothing outstanding it says so and touches nothing. See
     * [SettingsHiddenRunner.unhidePending] for why that differs from the tile.
     *
     * Launched on the application scope rather than [viewModelScope]: leaving the Favourites
     * tab — which is exactly what someone does after pressing this — would otherwise cancel
     * a revert that takes seconds, and can wait on adbd before it is finished.
     */
    fun unhideSettings() {
        appScope.launch { settingsHiddenRunner.unhidePending() }
    }
""",
        ),
    ],
    f"{APPS}/FavouriteAppsScreen.kt": [
        (
            "        onRevertToDefault = viewModel::revertToDefault,",
            "        onUnhideSettings = viewModel::unhideSettings,",
        ),
        (
            "    onRevertToDefault: () -> Unit,",
            "    onUnhideSettings: () -> Unit,",
        ),
        (
            """                FloatingActionButton(onClick = onRevertToDefault) {
                    Icon(
                        modifier = Modifier.size(24.dp),
                        painter = painterResource(designR.drawable.ic_revert_glyph),
                        contentDescription = stringResource(R.string.revert_to_default),
                    )
                }""",
            """                // ⚠ **The glyph stays and the description does not.** The author kept the
                // icon; the description is what TalkBack reads aloud, and "Revert to default"
                // stopped being true of this button when its job became unhiding.
                FloatingActionButton(onClick = onUnhideSettings) {
                    Icon(
                        modifier = Modifier.size(24.dp),
                        painter = painterResource(designR.drawable.ic_revert_glyph),
                        contentDescription = stringResource(R.string.unhide_settings),
                    )
                }""",
        ),
    ],
}

# Nothing may still name any of these once the round is done.
GONE = [
    "showRevertedToast",
    "showRevertShizukuFailedToast",
    "showRevertOverlayFailedToast",
    "showRevertShizukuAndOverlayFailedToast",
    "showShizukuWaitToast",
    "toast_auto_done_reverted",
    "toast_done_reverted_memory",
    "revert_failed_",
    "settings_manager_shizuku_wait",
]


def apply(path: Path, edits: list[tuple[str, str]], problems: list[str]) -> str | None:
    if not path.exists():
        problems.append(f"{path} is missing")

        return None

    text = path.read_text(encoding="utf-8")

    for old, new in edits:
        found = text.count(old)

        if found != 1:
            head = old.strip().splitlines()[0][:70] if old.strip() else old[:70]

            problems.append(f"{path.name}: {found} of {head!r}")

            continue

        text = text.replace(old, new, 1)

    return text


def main() -> int:
    problems: list[str] = []

    staged: dict[Path, str] = {}

    everything = {
        TOASTS: TOASTS_EDITS,
        RUNNER: RUNNER_EDITS,
        HIDDEN_RUNNER: HIDDEN_RUNNER_EDITS,
        **SIMPLE,
    }

    for name, edits in everything.items():
        path = ROOT / name

        before = set(path.read_text(encoding="utf-8").splitlines()) if path.exists() else set()

        text = apply(path=path, edits=edits, problems=problems)

        if text is None:
            continue

        staged[path] = text

        # ⚠ Only lines this edit **adds**. These files carry fully-qualified imports well past
        # 120 characters, which Kotlin allows and the project has always had; a guard that
        # counted those would refuse every round for something no round wrote. handover_3 §4.
        for line in set(text.splitlines()) - before:
            if len(line) > 120:
                problems.append(f"{path.name}: {len(line)} chars — {line.strip()[:60]}")

    for kotlin in sorted(ROOT.rglob("*.kt")):
        if "build" in kotlin.relative_to(ROOT).parts:
            continue

        body = staged.get(kotlin) or kotlin.read_text(encoding="utf-8")

        for name in GONE:
            if re.search(rf"\b{name}", body):
                problems.append(f"{kotlin.relative_to(ROOT)}: still names {name}")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")

    print(f"ok — {len(staged)} Kotlin files rewired; restored/reverted split, "
          f"failure toasts gone, Favourites button unhides")

    return 0


if __name__ == "__main__":
    sys.exit(main())
