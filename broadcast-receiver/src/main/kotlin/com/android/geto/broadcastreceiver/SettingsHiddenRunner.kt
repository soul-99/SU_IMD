/*
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
package com.android.geto.broadcastreceiver

import android.content.Context
import com.android.geto.common.AutoRevertPending
import com.android.geto.common.AutoUnhideWatch
import com.android.geto.common.showHiddenToast
import com.android.geto.common.showNothingToRestoreToast
import com.android.geto.common.showRestoredToast
import com.android.geto.domain.common.Diagnostics
import com.android.geto.domain.model.AppSettingsResult
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.settingsHidden
import com.android.geto.domain.repository.UserDataRepository
import com.android.geto.domain.usecase.ApplySettingsToHideUseCase
import com.android.geto.domain.usecase.GetSettingsHiddenUseCase
import com.android.geto.domain.model.UnhidingFramework
import com.android.geto.domain.common.PriorHide
import com.android.geto.domain.usecase.DiscardPendingRevertsUseCase
import com.android.geto.domain.usecase.RevertAllMemoryUseCase
import com.android.geto.domain.usecase.SettingsWorkKind
import com.android.geto.domain.usecase.SettingsWorkTracker
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.REVERT_TO_DEFAULT_NOTIFICATION_ID
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.first
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Both directions of the "Hide settings" toggle, with no app involved.
 *
 * The tile is the one surface that hides and unhides on its own account rather than around a
 * launch, so both halves live together here: they are the two ends of one switch, and the
 * thing most likely to go wrong is them disagreeing about what "hidden" means.
 *
 * The hide is always the device-wide "Settings to hide" list, whichever mechanism is chosen.
 * That is not an oversight about the memory function - the memory function hides what *one
 * app* asks to be hidden, and a tile press names no app, so there is nothing for it to read.
 * The settings screen says as much next to the list when the memory function is on.
 */
@Singleton
class SettingsHiddenRunner @Inject constructor(
    @param:ApplicationContext private val context: Context,
    private val getSettingsHiddenUseCase: GetSettingsHiddenUseCase,
    private val applySettingsToHideUseCase: ApplySettingsToHideUseCase,
    private val revertAllMemoryUseCase: RevertAllMemoryUseCase,
    private val discardPendingRevertsUseCase: DiscardPendingRevertsUseCase,
    private val revertToDefaultRunner: RevertToDefaultRunner,
    private val autoHideRunner: AutoHideRunner,
    private val overlayRestoreRunner: OverlayRestoreRunner,
    private val userDataRepository: UserDataRepository,
    private val notificationManagerWrapper: AndroidNotificationManagerWrapper,
    private val settingsWorkTracker: SettingsWorkTracker,
    private val revertOfferNotification: RevertOfferNotification,
) {
    /**
     * A whole tile press: read which way the switch is set, move it the other way, and say
     * what came of it.
     *
     * **Moved here from the tile's window, which used to run it.** That window could only be
     * opened by the call that collapses the shade, so as long as the work lived inside it the
     * shade had to collapse before the work began — and the author wants it to stay open,
     * showing the tile working, until a second after the work is done. The window is now
     * launched at the end for exactly that collapse, so it cannot also be the thing that runs.
     *
     * ⚠ **The direction is read here rather than in the tile.** The tile follows a flow and
     * can be a frame behind: a revert that landed between the panel opening and the press would
     * leave it showing "hidden", and the press would then try to unhide a visible device.
     *
     * The tracker is claimed twice, and both claims earn their place. The outer one covers the
     * read below, so the tile is drawn unavailable from the press rather than from the first
     * write, and it cannot name a direction because the read is what decides one. The inner one
     * names it and holds it for the rest of the press. See `SettingsWorkTracker` and
     * `HideTileService.render`.
     */
    suspend fun toggle(): HideToggle = settingsWorkTracker.track<HideToggle> {
        val hidden = userDataRepository.userData.first().settingsHidden

        // ⚠ **Claimed again, now with a direction, and the second claim is not decoration.**
        // The outer one above cannot name a direction — it is taken before the read that
        // decides one — and the use cases underneath name theirs only for as long as they run.
        // Between the inner one ending and the outer one being released the tracker was
        // therefore busy with no direction at all, and the tile's fallback for that window
        // reads `settingsHidden`, which the revert has by then already written false. So every
        // tile revert ended with a flash of "Hiding settings" over a device that had just
        // finished unhiding. This holds the direction for the whole press instead.
        settingsWorkTracker.track(
            kind = if (hidden) SettingsWorkKind.Unhiding else SettingsWorkKind.Hiding,
        ) {
            toggle(hidden = hidden)
        }
    }

    private suspend fun toggle(hidden: Boolean): HideToggle {
        if (hidden) {
            unhide()

            return HideToggle.Done
        }

        return when (hide()) {
            AppSettingsResult.NothingToHide -> HideToggle.NothingToHide

            AppSettingsResult.OverlayFailure -> HideToggle.OverlayFailure

            AppSettingsResult.NoPermission -> HideToggle.PermissionsLost

            // Everything else either hid something or hid part of it, and both are states the
            // tile now shows for itself. A partial failure is deliberately silent: the settings
            // that did not move are named in the settings manager, and the one failure with a
            // cause outside this app — Shizuku having to be killed through USB debugging —
            // raises its own notification from inside the stop, wherever that stop came from.
            else -> HideToggle.Done
        }
    }

    /**
     * Hide, and post the notification that offers the way back.
     *
     * The device-wide notification whichever framework is chosen, because that is the shape
     * of what was applied: the device-wide list, with no app to name. The memory function's
     * per-app notification would be offering to restore an app that was never launched.
     *
     * ⚠ **Its button is not "Revert to default" any more.** It runs the framework-following
     * unhide — see RevertToDefaultBroadcastReceiver — so under UnhidingFramework.Memory this
     * notification puts back what the hide measured rather than driving the configured
     * defaults. The notification is the way back from *this* hide; the named Revert to
     * default function is a different thing and still lives on the tile, the shortcut, the
     * manager, the Favourites button and its intent.
     *
     * The result is returned rather than acted on, because the two outcomes worth saying
     * something about — nothing configured to hide, and Shizuku refusing to start — need a
     * dialog and a window to put it in, and this has neither.
     */
    suspend fun hide(): AppSettingsResult {
        val result = applySettingsToHideUseCase()

        Diagnostics.log(tag = "hide", message = "route=tile result=$result")

        // Only where the device may actually have changed. NothingToHide changed nothing by
        // definition, and an overlay failure abandons the hide before touching anything, so
        // posting "settings hidden, tap to revert" after either would be an offer to undo
        // something that never happened.
        if (result == AppSettingsResult.Success || result == AppSettingsResult.Failure) {
            notificationManagerWrapper.notify(
                id = REVERT_TO_DEFAULT_NOTIFICATION_ID,
                notification = buildRevertToDefaultNotification(context = context),
            )
        }

        // The author's completion toast. Said only where the device may actually have
        // changed, on the same test as the notification above: "Settings hidden" after a run
        // that hid nothing is how somebody goes on trusting a tile that has quietly stopped
        // working. No app name — a tile press names none.
        if (result == AppSettingsResult.Success || result == AppSettingsResult.Failure) {
            context.showHiddenToast()
        }

        return result
    }

    /**
     * Unhide whatever is actually outstanding — which can be one debt or both.
     *
     * The two are undone by different reverts and a device can owe both at once: the tile
     * hides device-wide whichever mechanism is chosen, so pressing it and then launching an
     * app under the memory function leaves one of each. Running only the revert that matches
     * the chosen mechanism would leave the other standing, with the tile switched off and
     * nothing left on screen pointing at it.
     *
     * Memory first, then default. The memory sweep puts each app's own remembered values
     * back; the revert to default then drives everything to the state the user nominated as
     * normal, and that is the one that should have the last word — it is the answer to "what
     * should this device look like", where the snapshots are only "what was it before".
     */
    suspend fun unhide() = unhide(fallbackToDefault = true)

    /**
     * Settles every debt that actually exists, and does nothing at all if none does.
     *
     * What a change of hiding-unhiding mechanism runs before it takes effect. The two
     * mechanisms are undone by different reverts and each has routes the other does not, so a
     * debt carried across the change can end up with nothing left that clears it — most
     * plainly a pile of per-app memory records under a mechanism that no longer writes or
     * reads them.
     *
     * The difference from a tile press is the empty case. A press has to do something, or the
     * tile reads as broken; this runs whether or not there is anything outstanding, so on a
     * device with nothing hidden it must leave the settings alone rather than quietly applying
     * the user's defaults to a device that never asked.
     */
    suspend fun flushPendingReverts(): Boolean = unhide(fallbackToDefault = false)

    /**
     * Forget every outstanding revert and take the device as it stands.
     *
     * What `'Ignore all previous reverts'` runs. The use case clears the five stored debts; the
     * two in-memory ones are cleared here, because they live in `:common` where a domain use
     * case cannot see them.
     *
     * ⚠ **[PriorHide.settled] last**, after the debt is genuinely gone: it is the flag the
     * popup's trigger reads, and clearing it while a record still stood would leave the next
     * launch warning about a debt this call was supposed to have ended.
     */
    /**
     * Takes the offer to undo a hide out of the shade, once there is no hide left to undo.
     *
     * ⚠ **One notification serves every hide now**, under
     * [AndroidNotificationManagerWrapper.REVERT_TO_DEFAULT_NOTIFICATION_ID] - r3 replaced the
     * per-app notifications with a single fixed id. The per-app revert paths were still
     * cancelling `componentName.hashCode()`, which nothing has posted under since, so they
     * restored the device and left the offer standing. This is what they call instead.
     *
     * ⚠ **Conditional, and it has to stay that way.** One shared notification means cancelling
     * it while a second app is still hidden would take away that app's only way back from the
     * shade. Asked of the records rather than of what this particular revert did, because a
     * memory sweep and a single profile revert both end here and only the records know whether
     * anything is left.
     *
     * `cancelAll` rather than the one id: an install upgrading from before r3 can still have
     * per-app notifications keyed on hashes this cannot compute, and they describe a device
     * that no longer exists either. A foreground service's own notification survives it.
     *
     * Returns whether it cleared, so a caller that also wants to stop can use the same answer.
     */
    suspend fun clearRevertOfferIfSettled(): Boolean =
        revertOfferNotification.clearIfSettled()

    suspend fun discardPendingReverts() {
        discardPendingRevertsUseCase()

        notificationManagerWrapper.cancelAll()

        AutoUnhideWatch.clear()

        AutoRevertPending.clear()

        PriorHide.settled()
    }

    /**
     * Whether nothing at all is outstanding right now.
     *
     * Read after a revert rather than returned by it, and that is the point: `'Restore settings
     * first'` has to know whether to go on and hide, and threading a result back through
     * `AutoHideRunner.revert`, `RevertAllMemoryUseCase` and both branches below would be four
     * new return types for a question the stored records already answer.
     */
    private suspend fun nothingOutstanding(): Boolean {
        val hidden = getSettingsHiddenUseCase()

        return !userDataRepository.userData.first().autoHideRunning &&
            !hidden.memory &&
            !hidden.deviceWide
    }

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

    /**
     * The named `Revert to default`, and everything that has to be settled before it.
     *
     * ⚠ **Four steps, and the first three are the author's bug report.** `RevertToDefaultRunner`
     * cancels every notification and touches neither [AutoUnhideWatch] nor [AutoRevertPending],
     * so an explicit revert used to put the settings back and leave the auto unhide session
     * standing — service running, notification in the shade, still armed to revert a device
     * that had already been reverted — and leave the per-app records behind it, which is why
     * the Hide settings tile still read "hidden" afterwards.
     *
     * The author's rule: *clear all pending reverts first including IMD+, clear the auto unhide
     * service, and then revert to default.*
     *
     * ⚠ **The IMD+ flag rather than [AutoHideRunner.revert].** That call's device-wide branch is
     * three things — cancel its own notification, clear `autoHideRunning`, run
     * [RevertToDefaultRunner] — and the third is step four below. Calling it would revert twice
     * and speak twice, two toasts for one press. Cleared **before** the revert for the reason
     * its own comment gives: the revert re-enables IMD's detector as part of putting the
     * accessibility services back, and a detector coming up while this still read "running"
     * would find IMD+ disarmed.
     *
     * ⚠ **IMD+ is re-armed by the revert itself**, in `RevertToDefaultUseCase` — nothing here
     * has to do it, and doing it here as well would race that.
     *
     * ⚠ **Here rather than in [RevertToDefaultRunner].** `AutoHideRunner` injects that runner,
     * so a runner reaching back for `AutoHideRunner` would be a Dagger cycle. This class already
     * holds every piece, and one method beats the same four-step recipe written into each of
     * the three explicit routes — the r1 lesson about eight hide routes, applied again.
     *
     * Tracked as one piece of work for the whole press, like [toggle]: the four steps claim the
     * tracker separately underneath, and without this the tile would flicker between them.
     */
    suspend fun revertToDefault() = settingsWorkTracker.track(
        kind = SettingsWorkKind.Unhiding,
    ) {
        if (userDataRepository.userData.first().autoHideRunning) {
            Diagnostics.log(tag = "revert", message = "explicit: clearing IMD+ hold")

            userDataRepository.updateAutoHideRunning(running = false)
        }

        // Every per-app record, whatever hid them — a launch, a shortcut or IMD+ under Per app
        // configuration. The defaults go on top afterwards, which is r2's extras-before-defaults
        // ordering: anything a profile hid outside the six revert targets is put back by this,
        // and the six themselves are then driven wherever the configuration says.
        if (getSettingsHiddenUseCase().memory) {
            Diagnostics.log(tag = "revert", message = "explicit: sweeping memory records")

            // Each per-app Revert notification is about to describe a device that no longer
            // exists. The runner below cancels them too, a moment later; this is early enough
            // that none can be tapped in between.
            notificationManagerWrapper.cancelAll()

            revertAllMemoryUseCase()
        }

        // The session is over however it ended. Clearing the watch is what lets the service
        // settle and take its notification with it; clearing the pending record is
        // AutoRevertPending's own case — "the user reverts by hand first ... firing again on
        // return would be a second revert of nothing".
        AutoUnhideWatch.clear()

        AutoRevertPending.clear()

        revertToDefaultRunner(explicit = true)
    }

    /**
     * Returns whether the device is actually clear afterwards.
     *
     * ⚠ **Both signals, because either alone can lie.** A revert can report success having
     * cleared a debt it never fully wrote, and a debt can clear while Shizuku was left down. So
     * the answer is what the revert *reported* **and** what the records *say* — and only the
     * device-wide branch has a report to give, which is why the other two fall back to the
     * records alone.
     */
    private suspend fun unhide(fallbackToDefault: Boolean): Boolean {
        // An IMD+ run put the device here, so its own revert is the one that undoes it: that
        // revert force-stops the watched apps before restoring anything, so none of them sees
        // its settings come back while it is running. Running the plain revert-to-default from
        // the tile would put the settings back underneath a watched app that is very likely
        // still on screen - which is the one thing IMD+ exists to prevent.
        //
        // It ends by running RevertToDefaultRunner, so everything below happens anyway.
        if (userDataRepository.userData.first().autoHideRunning) {
            Diagnostics.log(tag = "revert", message = "route=imd+ (autoHideRunning)")

            autoHideRunner.revert()

            return nothingOutstanding()
        }

        val hiddenState = getSettingsHiddenUseCase()

        val memory = hiddenState.memory

        val deviceWide = hiddenState.deviceWide

        Diagnostics.log(
            tag = "revert",
            message = "unhide memory=$memory deviceWide=$deviceWide fallback=$fallbackToDefault",
        )

        if (memory) {
            // Every per-app Revert notification is about to describe a device that no longer
            // exists. RevertToDefaultRunner does this for itself; the memory sweep has no
            // notification handling of its own, and its notifications are ongoing now, so
            // without this they would sit there un-swipeable with nothing left to revert.
            notificationManagerWrapper.cancelAll()

            revertAllMemoryUseCase()

            // Only when this is the whole story. Otherwise the revert below says its own
            // piece, and two toasts in a row for one press reads as two things happening.
            // Device-wide, with no app named: this sweep settles every outstanding per-app
            // record at once, so naming one of them would be picking a winner. The per-app
            // sentence belongs to the routes that revert exactly one app.
            //
            // ⚠ **The overlay step's outcome is reported here or nowhere on this route.** It
            // is allowed to fail without failing the rest of a profile, and until r3 the only
            // caller that asked after a sweep was the per-app notification's own receiver,
            // which r3 deleted. Without this a sweep that could not put Display over other
            // apps back said "restored from memory" and nothing else — and that was already
            // true of the Favourites Unhide button and a framework change, which reach this
            // same branch through flushPendingReverts.
            //
            // Nothing is said when the report fires: the failure raises a notification of its
            // own and the completion sentence would be untrue over it. Same shape as
            // AutoRevertRunner's memory branch, deliberately.
            if (!deviceWide && !overlayRestoreRunner.reportIfFailed()) {
                context.showRestoredToast(fromMemory = true)
            }
        }

        // The second arm is belt and braces for the tile: a press arrives here only while it
        // is showing "hidden", so at least one debt is supposed to exist, and if neither does
        // the safe reading of the press is still "put the device back to normal" - a tile that
        // did nothing at all would leave the user pressing it again. A mechanism change asks
        // for the opposite and passes false, because there nobody pressed anything that means
        // "revert", and reverting a device with nothing hidden would be this app changing
        // settings on its own.
        if (deviceWide || (fallbackToDefault && !memory)) {
            // ⚠ **Which destination a device-wide hide comes back to is the Unhiding
            // framework's question, and this is the only place that asks it.** Under
            // UnhidingFramework.Memory the keyed targets go back to what the hide measured, so
            // a setting the user never had on before the hide is not switched on by the
            // revert. Under RevertToDefault they are driven to the configured list, which is
            // what every version before v3 did for a device-wide hide whatever mechanism was
            // chosen.
            //
            // The explicit `Revert to default` routes do not come through here at all — they
            // call RevertToDefaultRunner directly and so always drive the defaults, which is
            // the author's rule that Revert to default always means the defaults.
            val fromMemory = userDataRepository.userData.first().unhidingFramework ==
                UnhidingFramework.Memory

            val result = revertToDefaultRunner(fromMemory = fromMemory)

            return !result.overlayRestoreFailed &&
                ManualRevertTarget.Shizuku !in result.failed &&
                nothingOutstanding()
        }

        return nothingOutstanding()
    }
}

/**
 * What a tile press came to.
 *
 * Four outcomes rather than the ten [AppSettingsResult] has, because the tile only needs to know
 * whether to close the shade and which of three things to say: everything that hid *anything* is
 * one answer, and an unhide is always that answer too.
 *
 * Top level rather than nested, for the same mundane reason `SettingsWorkKind` is: `check16_when`
 * cannot read an indented enum — it needs the closing brace at column 0.
 */
enum class HideToggle {
    /** It did what it was pressed to do. The shade closes a second later. */
    Done,

    /** Nothing is ticked in "Settings to hide", so there was nothing a press could do. */
    NothingToHide,

    /** Overlay access needed Shizuku and Shizuku did not come up. Nothing was hidden. */
    OverlayFailure,

    /**
     * `WRITE_SECURE_SETTINGS` is no longer granted, so nothing could be written at all.
     *
     * Apart from [OverlayFailure] because the two send the user to different places: that
     * one is fixed in Shizuku, this one by re-granting a permission over adb. And apart
     * from [Done] because nothing was hidden — the hide stops before it touches anything,
     * and undoes itself if the grant goes during the run.
     */
    PermissionsLost,
}
