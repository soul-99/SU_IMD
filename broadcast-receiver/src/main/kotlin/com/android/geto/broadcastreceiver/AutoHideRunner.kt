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
import android.content.Intent
import android.os.SystemClock
import com.android.geto.common.AutoHideDetection
import com.android.geto.common.AutoUnhideWatch
import com.android.geto.common.showAutoHidingToast
import com.android.geto.common.showHiddenToast
import com.android.geto.common.showRestoredToast
import com.android.geto.domain.common.Diagnostics
import com.android.geto.domain.framework.PackageManagerWrapper
import com.android.geto.domain.framework.ShizukuWrapper
import com.android.geto.domain.model.AppSettingsResult
import com.android.geto.domain.model.HidingFramework
import com.android.geto.domain.model.UnhidingFramework
import com.android.geto.domain.model.autoHideBlockedByHide
import com.android.geto.domain.model.autoHideFailureBackoffMillis
import com.android.geto.domain.model.effectiveSettingsToHide
import com.android.geto.domain.model.revertNamesApp
import com.android.geto.domain.repository.AppSettingsRepository
import com.android.geto.domain.repository.UserDataRepository
import com.android.geto.domain.usecase.ApplyAppSettingsUseCase
import com.android.geto.domain.usecase.ApplySettingsToHideUseCase
import com.android.geto.domain.usecase.DisableAutoHideServiceUseCase
import com.android.geto.domain.usecase.OverlayStart
import com.android.geto.domain.usecase.RevertAppSettingsUseCase
import com.android.geto.domain.usecase.SettingsWorkKind
import com.android.geto.domain.usecase.SettingsWorkTracker
import com.android.geto.domain.usecase.ShizukuStartTracker
import com.android.geto.domain.usecase.StartShizukuUseCase
import com.android.geto.framework.launcherapps.AndroidLauncherAppsWrapper
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.atomic.AtomicBoolean
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Auto-hide settings (IMD+), from the moment a watched app is noticed to the moment its revert
 * finishes.
 *
 * Both directions live together for the same reason [SettingsHiddenRunner]'s do: they are the
 * two halves of one state, and the failure that would hurt most is them disagreeing about what
 * "running" means.
 *
 * ### The run
 *
 * 0. **Is there anything to hide?** If not, there is no run: the app is not stopped, nothing is
 *    written, the detector is left alone and nothing is relaunched — the app opens exactly as it
 *    would with IMD+ switched off, and a popup says what to set and where. Steps 1 to 5 all
 *    assume the hide is going to hide something, and the one that assumes it hardest is step 4:
 *    reopening an app that was killed for nothing is a launch the detector then answers with
 *    another run. See [nothingConfiguredFor].
 * 1. **Kill the app.** The point of the whole feature: an app that objects to developer options
 *    reads them when it starts, so it has to be made to start again afterwards. Skipped when
 *    "Do not kill app on first launch" is ticked, and then nothing is relaunched either — the
 *    app is already in front and has already looked.
 * 2. **Hide.** Under "Revert to default", the device-wide "Settings to hide" list, exactly as a
 *    tile press would apply it. Under the **memory function**, the app's own per-app page,
 *    exactly as launching it from inside IMD would — which also means the revert puts back what
 *    that app changed and nothing else. Reading a different list is the whole of the difference
 *    between the two modes; every other step here is identical.
 * 3. **Switch off IMD's own detector**, before anything is launched. Without this the relaunch
 *    in step 4 is another app coming to the foreground, which is precisely what the detector
 *    listens for, and IMD+ would chase its own tail forever. See
 *    [DisableAutoHideServiceUseCase] — it is a state rather than a timer, so nothing depends
 *    on how long a kill or a launch takes on a given device.
 * 4. **Open the app again**, now that the settings it objects to are gone.
 * 5. **Post the IMD+ notification**, which is the way back.
 *
 * The order of 2 and 3 is the one place this departs from the shortest description of the
 * guard, and deliberately: a hide that fails, or finds nothing ticked, returns before the
 * detector is touched, so a run that changed nothing leaves IMD+ exactly as it found it — and
 * with nothing hidden there would be no revert coming to switch the detector back on. By the
 * time step 3 runs the hide has already recorded itself, which empties [watched] — so between
 * the two the detector is still on but has nothing left to react to.
 *
 * ### The revert
 *
 * Dismiss the notification, say so, and then follow whichever mode hid the settings. Under
 * "Revert to default" that is [RevertToDefaultRunner], which restores overlay access, the
 * accessibility services — IMD's own detector among them — and everything else. Under the
 * memory function it is that one app's own record, put back exactly and nothing else with it;
 * the app is named by the notification that was tapped, so nothing has to be stored.
 *
 * It closes nothing: an earlier draft force-stopped the watched apps first, which meant every
 * revert started Shizuku whether or not it had any other use for it.
 */
@Singleton
class AutoHideRunner @Inject constructor(
    @param:ApplicationContext private val context: Context,
    private val userDataRepository: UserDataRepository,
    private val appSettingsRepository: AppSettingsRepository,
    private val applySettingsToHideUseCase: ApplySettingsToHideUseCase,
    private val applyAppSettingsUseCase: ApplyAppSettingsUseCase,
    private val revertAppSettingsUseCase: RevertAppSettingsUseCase,
    private val disableAutoHideServiceUseCase: DisableAutoHideServiceUseCase,
    private val startShizukuUseCase: StartShizukuUseCase,
    private val shizukuWrapper: ShizukuWrapper,
    private val shizukuStartTracker: ShizukuStartTracker,
    private val settingsWorkTracker: SettingsWorkTracker,
    private val launcherAppsWrapper: AndroidLauncherAppsWrapper,
    private val packageManagerWrapper: PackageManagerWrapper,
    private val notificationManagerWrapper: AndroidNotificationManagerWrapper,
    private val revertToDefaultRunner: RevertToDefaultRunner,
    private val overlayRestoreRunner: OverlayRestoreRunner,
    private val revertOfferNotification: RevertOfferNotification,
) {
    /**
     * The packages a foregrounded app is checked against, or empty when IMD+ is not armed.
     *
     * A plain field rather than a read of the repository, because [onAppForegrounded] is called
     * for every window change on the device — every dialog, every keyboard, every notification
     * shade — and it has to be a set lookup and nothing more. The value is kept fresh by the
     * collector in [arm].
     */
    @Volatile
    private var watched: Set<String> = emptySet()

    /**
     * Which of the watched apps a run would currently find nothing to hide for.
     *
     * Beside [watched] and kept fresh by the same collector, for the same reason: deciding this
     * in [onAppForegrounded] has to be a field read rather than a datastore round trip.
     *
     * **A set rather than a flag, because the answer became per app.** Under "Revert to default"
     * there is one device-wide list, so it is all the watched apps or none of them. Under the
     * memory function each app answers for itself: one can have a page full of settings and the
     * next none at all, and IMD+ has to run for the first and explain itself for the second.
     *
     * A run in this state used to be the whole bug. It killed the app, hid nothing —
     * [ApplySettingsToHideUseCase] returns `NothingToHide` and touches no setting — and then
     * reopened the app, which the detector saw as another launch, which killed it again. The
     * detector is never switched off on that path, so nothing ever broke the circle: the app
     * opened and closed until the user gave up. Now there is no run at all.
     */
    @Volatile
    private var nothingConfiguredFor: Set<String> = emptySet()

    /**
     * When the "nothing to hide" popup was last raised for each watched package.
     *
     * **Per package, and that is the point.** Opening app 1 says its piece once and then leaves
     * app 1 alone for half an hour; opening app 2 in the meantime still gets told, because app 2
     * has its own entry and its own half hour. One shared timer would have silenced the second app for a
     * reason that had nothing to do with it.
     *
     * This replaced a "did the app arrive from somewhere else" test, which was meant to tell a
     * real launch from the popup's own echo — closing the popup puts the watched app back in
     * front, which is another foregrounding of the same package. It could not do it. One launch
     * produces several window changes, and a keyboard or a system dialog appearing inside the
     * app looks exactly like leaving and coming back, so the popup arrived three to five times
     * per launch. A clock does not have to guess: it does not matter how many events a launch
     * produces or what order they come in, because after the first one the app is simply not due
     * again.
     *
     * [SystemClock.elapsedRealtime] rather than the wall clock, so changing the device's time
     * zone or its clock cannot move the interval, and it cannot run backwards.
     *
     * In memory rather than in the DataStore, so it is lost if the process is killed and the
     * next launch of that app warns again. That is the right direction — the alternative is a
     * timestamp on disk that outlives the reason for it — and in practice the process stays
     * alive: IMD+ cannot detect anything at all unless its accessibility service is bound, which
     * is what keeps the process up.
     */
    private val nothingToHideShownAt = ConcurrentHashMap<String, Long>()

    /**
     * When a run for this app last hid nothing, and how many times in a row it has now done so.
     *
     * Package to state, exactly like [nothingToHideShownAt] beside it and for the same reason:
     * one app being broken says nothing about the next, and each is due again on its own clock.
     *
     * **The count is what stops a permanent fault costing a permanent loop.** A run that hides
     * nothing leaves the detector listening and ends by relaunching the app, and that relaunch
     * is another foregrounding — so for as long as the cause lasts the two chase each other with
     * a force-stop and a Shizuku start on every lap. The first failure is forgiven quickly
     * because most are transient; a cause that survives three tries is treated as standing, and
     * the app is left alone until it is looked at again.
     *
     * [SystemClock.elapsedRealtime] and in memory, both for the reasons given above.
     */
    private val failedRunAt = ConcurrentHashMap<String, RunFailure>()

    /**
     * Whether a run is already under way.
     *
     * One app coming to the front produces several window changes, so without this a single
     * launch would start several runs. Claimed before the window is asked for and released in
     * [run]'s `finally`, which is reached whatever the run does — and if the process dies in
     * between, an in-memory latch is gone with it.
     */
    private val inFlight = AtomicBoolean(false)

    /**
     * Starts listening, and keeps [watched] up to date for as long as the process lives.
     *
     * Called once from the application. The detector can deliver an event with nothing else of
     * this app running, so what it needs must already be in memory rather than waiting behind a
     * datastore read.
     */
    fun arm(scope: CoroutineScope) {
        scope.launch {
            combine(
                userDataRepository.userData,
                // The per-app pages, because under the memory function they are what IMD+
                // hides. Watched here rather than read inside a run for the same reason the
                // packages are: by the time a run is asked, the app is already on its way off
                // the screen, and a launch that would hide nothing must not reach the kill.
                appSettingsRepository.appSettingsFlow,
            ) { userData, appSettings ->
                // Armed only when IMD+ is on, nothing is hidden already, and no run is
                // outstanding. The second is what stops a watched app opened while settings
                // are hidden from starting a second run on top of the first; the third
                // survives a process restart, which the latch above does not.
                val armed = userData.autoHideEnabled &&
                    !userData.autoHideBlockedByHide &&
                    !userData.autoHideRunning

                val packages = if (armed) userData.autoHidePackages.toSet() else emptySet()

                val perApp = userData.hidingFramework == HidingFramework.PerApp

                // Which of the watched apps a run would find nothing to hide for, answered in
                // whichever sense the current mode means it. Under the memory function that is
                // per app — one watched app can be configured and the next not — which is
                // exactly why this is a set rather than the single flag it used to be.
                val nothing = when {
                    !perApp ->
                        if (userData.effectiveSettingsToHide.none { it.value }) packages
                        else emptySet()

                    else -> {
                        val configured = appSettings
                            .filter { it.enabled }
                            .map { it.componentName.substringBefore('/') }
                            .toSet()

                        packages - configured
                    }
                }

                Arming(packages = packages, nothingConfiguredFor = nothing)
            }
                .distinctUntilChanged()
                .collect { armed ->
                    watched = armed.packages

                    nothingConfiguredFor = armed.nothingConfiguredFor

                    // One line doing two jobs, both of them right. An app that is no longer
                    // watched keeps no timer, so re-adding it earns a fresh answer and this map
                    // cannot grow for as long as the process lives. And an app that has *just
                    // been configured* drops out of this set, so its timer goes with it — if
                    // the user empties that configuration again next week they are told
                    // promptly, rather than waiting out an interval that started before they
                    // fixed it.
                    nothingToHideShownAt.keys.retainAll(armed.nothingConfiguredFor)

                    // The same idea for the failure back-off, against the watched set rather
                    // than the unconfigured one: an app dropped from "Apps to watch" keeps no
                    // record, so adding it back earns a fresh attempt straight away.
                    //
                    // It is also the manual way out. Switching IMD+ off empties this set, so a
                    // user who has fixed whatever was wrong — granted the permission, brought
                    // Shizuku back — can switch it off and on again rather than waiting out the
                    // half hour. That is worth having, because most of the causes that reach
                    // here are fixed somewhere other than in IMD, and nothing about fixing them
                    // tells this class anything.
                    failedRunAt.keys.retainAll(armed.packages)
                }
        }

        AutoHideDetection.setHandler(::onAppForegrounded)
    }

    /**
     * What the collector in [arm] works out, in one value so the flow can tell when it changed.
     *
     * A declared type rather than a `Pair`, and not only for readability: `distinctUntilChanged`
     * on a pair of sets works, but `collect { (a, b) -> }` on one does not — component1/component2
     * fail to resolve against collect's overloads, which is the trap HideTileService hit.
     */
    private data class Arming(
        val packages: Set<String>,
        val nothingConfiguredFor: Set<String>,
    )

    /**
     * One app's record of runs that hid nothing — how many in a row, and when the last one was.
     *
     * A declared type for the same reason [Arming] is one, and because the count and the moment
     * are only ever read together: the count picks the wait and the moment says whether it has
     * passed.
     */
    private data class RunFailure(
        val count: Int,
        val atElapsed: Long,
        val result: AppSettingsResult,
    )

    /**
     * A window change, from the detector.
     *
     * Does as little as it possibly can: a set lookup, a latch, and an intent. Everything that
     * decides what a run means happens in [run], where there is a coroutine to do it in.
     */
    private fun onAppForegrounded(packageName: String) {
        if (packageName !in watched) return

        // There is nothing for a run to hide for this app, and it has already been told
        // recently, so there is not even a popup to raise. Stopped here rather than in [run] so
        // that the repeats cost nothing at all: every window change a launch produces would
        // otherwise start a window, look at the same answer, and close again.
        //
        // Safe to decide from the field: when there is nothing configured there is nothing a
        // run could do, so a moment's staleness here can only ever delay a popup, never skip a
        // hide.
        if (packageName in nothingConfiguredFor && !nothingToHidePopupDue(packageName)) return

        // The last run for this app hid nothing and left the detector listening, so the relaunch
        // it ended with is about to arrive back here as another window change. Without this the
        // two would chase each other for as long as the cause lasts — kill, start Shizuku, fail,
        // relaunch, detect, repeat — which is the open-and-close loop and the spinner that keeps
        // coming back.
        //
        // Stopped at the same place and for the same reason as the line above: before the latch
        // and before any window, so a repeat costs nothing at all.
        if (!runCooldownDue(packageName)) return

        if (!inFlight.compareAndSet(false, true)) return

        val intent = Intent()
            .setClassName(context, AutoHideDetection.ACTIVITY_CLASS_NAME)
            .putExtra(AutoHideDetection.EXTRA_PACKAGE_NAME, packageName)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK)

        // The window is what makes the rest possible — see AutoHideDetection.ACTIVITY_CLASS_NAME
        // for why a run cannot happen without one. If it will not start there is no run, so the
        // latch is given straight back rather than left standing until the process restarts.
        if (!runCatching { context.startActivity(intent) }.isSuccess) inFlight.set(false)
    }

    /**
     * The run itself, called by the window it opens.
     *
     * Every early return is a run that changed nothing and leaves IMD+ armed, so the next time
     * the app is opened it tries again. That is the right failure: the alternative is a feature
     * that silently switches itself off after one bad moment.
     *
     * Returns what the window should do. Anything other than [AutoHideOutcome.Done] is a run
     * that did not happen because there was nothing configured to hide — the one outcome worth
     * a word over the top of the app the user just opened, because it is the one they can do
     * something about. Everything else closes silently: the app itself is the confirmation.
     */
    suspend fun run(packageName: String): AutoHideOutcome {
        // Claimed here rather than left to the hide inside, because an IMD+ run starts long
        // before it reaches one: the kill can spend the whole Shizuku budget on its own. The
        // Hide settings tile is unavailable for all of it. Released in the finally below,
        // beside the latch, so no early return or throw can leave it standing.
        settingsWorkTracker.begin(kind = SettingsWorkKind.Hiding)

        try {
            val userData = userDataRepository.userData.first()

            // Read again here rather than trusted from the detection. Between the window change
            // and this line the user may have reverted, the tile may have hidden everything, or
            // another run may have finished — and each of those makes this run wrong.
            if (!userData.autoHideEnabled ||
                userData.autoHideBlockedByHide ||
                userData.autoHideRunning ||
                packageName !in userData.autoHidePackages
            ) {
                return AutoHideOutcome.Done
            }

            // **Which list of settings this run is about, and the whole of the difference
            // between the two notification functions.** Under the memory function it is the
            // app's own, saved from its per-app page; otherwise it is the one device-wide
            // "Settings to hide" list. Everything below — the toast, the kill, the guard, the
            // relaunch, the notification — is the same run either way, which is deliberate:
            // this is one feature reading a different list, not two features.
            val perApp = userData.hidingFramework == HidingFramework.PerApp

            val componentName = if (perApp) configuredComponentFor(packageName) else null

            // Nothing to hide, in whichever sense this mode means it. IMD+ does not start: the
            // app is not stopped, nothing is written, the detector is left alone and nothing is
            // relaunched — so the app the user tapped simply opens, as though IMD+ were not
            // installed, and a popup says what to set and where.
            //
            // Checked before the toast as well as before the kill. The toast announces a run,
            // and there is no run: saying "hiding settings" and then hiding nothing is how the
            // old behaviour looked from the outside even while it was killing the app.
            //
            // The device-wide reading is the second one — [nothingConfiguredFor] stopped the common
            // case a step earlier — and it is the authoritative one, taken from the same
            // snapshot as every other decision here rather than from a field that a moment's
            // staleness could have made wrong in either direction.
            val empty = when {
                perApp && componentName == null -> AutoHideOutcome.NoProfile

                !perApp && userData.effectiveSettingsToHide.none { it.value } ->
                    AutoHideOutcome.NothingToHide

                else -> null
            }

            // The popup is raised only when this app is actually due one, and the timer is
            // stamped here rather than where the popup is drawn: this is the moment the
            // decision is made, and a window that is dismissed, rotated or killed must not
            // change how long the app stays quiet for. One timer covers both popups — an app
            // can only ever be owed one of them at a time, and the mode is not something the
            // user changes between two launches of the same app.
            if (empty != null) {
                if (!nothingToHidePopupDue(packageName)) return AutoHideOutcome.Done

                nothingToHideShownAt[packageName] = SystemClock.elapsedRealtime()

                return empty
            }

            // Before the kill, because the kill is what takes the app off the screen: without a
            // word first, the app the user just tapped simply vanishes.
            context.showAutoHidingToast()

            val killing = !userData.autoHideNoKillOnLaunch

            // A kill that does not happen is not a reason to stop. The hide is still worth
            // doing — the app will read the settings next time it starts — and stopping here
            // would leave the user with a toast and nothing else.
            //
            // Shizuku failing to come up is the exception, and the author found it on the
            // device: the hide below needs the same service for its overlay step, so carrying
            // on spends a **second** full wait under the same spinner before failing anyway.
            // One eight-second wait, then a notification saying what is wrong.
            if (killing && kill(packages = setOf(packageName)) == AutoHideKill.ShizukuUnavailable) {
                recordRunFailure(packageName = packageName, result = AppSettingsResult.OverlayFailure)

                Diagnostics.log(
                    tag = "hide",
                    message = "route=imd+ pkg=$packageName abandoned: shizuku unavailable " +
                        "attempt=${failedRunAt[packageName]?.count ?: 0}",
                )

                notificationManagerWrapper.notify(
                    id = AndroidNotificationManagerWrapper.SHIZUKU_FALLBACK_NOTIFICATION_ID,
                    notification = buildAutoHideShizukuFailedNotification(context = context),
                )

                // Not relaunched. Shizuku never came up, so the force-stop never ran and the
                // app is still exactly where the user left it — in front, untouched. Starting
                // it again would be a second launch of something already open.
                return AutoHideOutcome.Done
            }

            // ⚠ **Armed before the hide, not after it, and the ordering is the whole point.**
            //
            // The hide is what writes `settingsHidden`, and that flag is what starts the auto
            // unhide service. The watch list is what tells that service whether this is an
            // app-launch session or a tile press. Arming afterwards left a window where the
            // service could start, find an empty list, call an IMD+ hide a tile press and
            // check it against the wrong "Used for" setting — which is exactly the notification
            // the author saw appear for IMD+ and not for a launch from inside IMD.
            //
            // Optimistic, and given back below if the hide turns out to have hidden nothing.
            // ⚠ **The same question the three launch routes ask**, through
            // `AutoUnhideWatch.armIfApplied`, and IMD+ used to ask a different one: it armed
            // per-app whenever the *hiding* framework was Per app. Under Per app + Revert to
            // default that left the launch routes arming device-wide — auto unhide waiting for
            // every app — while IMD+ armed per-app, so auto unhide reverted its app alone, from
            // a record, under a framework that says drive the defaults. Which app's record a
            // revert needs is the **unhiding** framework's question, and `revertNamesApp` is
            // where it is answered for everyone else.
            AutoUnhideWatch.arm(
                packageName = packageName,
                componentName = componentName.takeIf {
                    revertNamesApp(
                        hidingFramework = userData.hidingFramework,
                        unhidingFramework = userData.unhidingFramework,
                    )
                },
            )

            val result = if (componentName != null) {
                applyAppSettingsUseCase(componentName = componentName)
            } else {
                applySettingsToHideUseCase()
            }

            // Nothing was hidden: either the configuration is empty, or overlay access could
            // not be withdrawn and the hide gave up before touching anything. The detector has
            // not been switched off yet, so all that is owed is putting the app back — and only
            // if this run is what took it away.
            if (result != AppSettingsResult.Success && result != AppSettingsResult.Failure) {
                // This run hid nothing and the detector below was never reached, so it is still
                // listening — and the relaunch on the next line is a foregrounding it will see.
                // Recorded so that [onAppForegrounded] turns the next one away instead of
                // starting the same run again. Every result that lands here is one where the
                // cause outlives the run: a permission that is still revoked, a Shizuku that is
                // still unreachable, a profile that is still empty.
                recordRunFailure(packageName = packageName, result = result)

                // The optimistic arm above, given back. Watching an app whose settings were
                // never hidden would end a session that never began.
                AutoUnhideWatch.forget(packageName = packageName)

                Diagnostics.log(
                    tag = "hide",
                    message = "route=imd+ pkg=$packageName hid nothing result=$result " +
                        "attempt=${failedRunAt[packageName]?.count ?: 0}",
                )

                if (killing) launcherAppsWrapper.startPackage(packageName = packageName)

                // ⚠ **The one result here that is worth a word.** Every other way to land
                // in this branch is about this app or this run - an empty profile, a
                // Shizuku that would not start - and the app opening untouched is a fair
                // enough answer. A lost grant is not: it stops the tile, every launch,
                // every shortcut and IMD+ alike, and used to be swallowed here entirely.
                return if (result == AppSettingsResult.NoPermission) {
                    AutoHideOutcome.PermissionsLost
                } else {
                    AutoHideOutcome.Done
                }
            }

            // Something was hidden, so whatever was wrong before is not wrong now.
            clearRunFailure(packageName = packageName)

            Diagnostics.log(
                tag = "hide",
                message = "route=imd+ pkg=$packageName component=$componentName result=$result",
            )

            // The guard. Before the launch below, and after the hide above — see the class
            // comment for why that order is the safe one.
            disableAutoHideServiceUseCase()

            // Recorded before the launch, so a process death between the two still leaves the
            // notification's revert knowing that IMD+ is what hid these settings.
            //
            // **Only the device-wide mode records it.** Under the memory function the per-app
            // hold the apply just wrote *is* the record: `settingsHidden` reads true from it,
            // which is what disarms IMD+ and what the tile shows, so nothing here is missing.
            // Setting this as well would be actively wrong — a tile unhide routes on it
            // straight into [revert], which under the memory function needs to know *which*
            // app it is putting back and has no way to learn that from a tile press.
            if (componentName == null) {
                userDataRepository.updateAutoHideRunning(running = true)
            }

            if (killing) launcherAppsWrapper.startPackage(packageName = packageName)

            notificationManagerWrapper.notify(
                id = AndroidNotificationManagerWrapper.AUTO_HIDE_NOTIFICATION_ID,
                notification = buildAutoHideNotification(
                    context = context,
                    componentName = componentName,
                ),
            )

            // The author's completion toast, with the IMD+ prefix. Named for the app only
            // when this run read that app's own profile — componentName is non-null exactly
            // when it did, which is the same question `perApp` asked further up and is
            // already settled by here.
            context.showHiddenToast(
                appName = componentName?.let {
                    packageManagerWrapper.getActivityLabel(componentName = it)
                },
                autoHide = true,
            )

            return AutoHideOutcome.Done
        } finally {
            inFlight.set(false)

            settingsWorkTracker.end(kind = SettingsWorkKind.Hiding)
        }
    }

    /**
     * The IMD+ revert: what its notification, and the Hide settings tile while IMD+ is up, both
     * run.
     *
     * **It closes nothing.** An earlier draft force-stopped every watched app first, so none of
     * them would see its settings come back underneath it — but that meant every revert started
     * Shizuku, on every device, whether or not the revert had any other use for it. The revert
     * now hands straight over to [RevertToDefaultRunner], which starts Shizuku only if overlay
     * access actually has to be written and otherwise settles it at the very end, as the
     * "Revert to default" configuration asks. A revert that touches no overlay AppOps now
     * happens in a moment rather than after a ten second wait for a shell it never used.
     */
    // <Unit> is load-bearing. track returns whatever its block does, and the last expression
    // here is RevertToDefaultRunner's result - so without it this function silently stops
    // returning Unit and starts returning a RevertToDefaultResult that no caller asked for.
    suspend fun revert(componentName: String? = null) = settingsWorkTracker.track<Unit>(
        kind = SettingsWorkKind.Unhiding,
    ) {
        // First, so the shade is clear before anything else starts. RevertToDefaultRunner
        // clears every notification too, but that is a moment away.
        notificationManagerWrapper.cancel(
            id = AndroidNotificationManagerWrapper.AUTO_HIDE_NOTIFICATION_ID,
        )

        // The memory function's revert: put back exactly what this run hid for this one app,
        // which is what that app's own record holds. Nothing device-wide is touched, because
        // nothing device-wide was hidden — and `autoHideRunning` was never set, so there is
        // nothing to clear either.
        //
        // The app is named by the notification that was tapped rather than stored anywhere.
        // It has to survive process death and it does: the name rides in the PendingIntent,
        // which the system holds, and the repost receiver carries it into the rebuilt
        // notification when the user swipes one away. A stored field would have been a second
        // copy of the same fact, with the usual risk of the two disagreeing.
        if (componentName != null) {
            revertAppSettingsUseCase(componentName = componentName)

            // ⚠ Without this an IMD+ revert under the memory function reported nothing at all
            // when it could not put overlay access back — the author found it on the device.
            // The overlay step is deliberately allowed to fail without failing the rest of the
            // profile, so this is the only place its outcome is ever reported on this route.
            // The ordinary memory sweep asks the same question in SettingsHiddenRunner.unhide.
            // Shizuku is not a target of a per-app revert, so only the one message applies.
            // ⚠ **This branch used to say nothing at all, and it was the author's report.**
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
            // ⚠ **The shared offer, which this branch never took down.** The cancel at
            // the top of this function names AUTO_HIDE_NOTIFICATION_ID - IMD+'s own - and
            // this branch returns below, before the hand-over to RevertToDefaultRunner that
            // sweeps the shade on the device-wide path. So a launch's "tap to revert" offer,
            // posted under the one fixed id every hide shares, sat over a device IMD+ had
            // just restored. The author's second report.
            //
            // Conditional inside: another app may still be hidden, and one notification now
            // serves them all.
            revertOfferNotification.clearIfSettled()

            if (!overlayRestoreRunner.reportIfFailed()) {
                context.showRestoredToast(
                    fromMemory = true,
                    appName = packageManagerWrapper.getActivityLabel(
                        componentName = componentName,
                    ),
                )
            }

            return@track
        }

        // Cleared before the revert rather than after it. The revert re-enables IMD's own
        // detector as part of putting the accessibility services back, and a detector that
        // came up while this still read "running" would find IMD+ disarmed.
        userDataRepository.updateAutoHideRunning(running = false)

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
    }

    /**
     * Which per-app configuration IMD+ should apply for a watched app, or null if it has none.
     *
     * The two sides of this speak slightly different languages and that is the whole of the
     * work here. IMD+ watches **apps** — the picker stores package names, and the detector
     * reports a package name. Per-app settings are saved against a **launcher icon**, so their
     * key is a flattened component name, `package/class`. Matching on the part before the
     * slash is what turns one into the other.
     *
     * Only rows the user actually enabled count. An app with a page full of switches all left
     * off has nothing configured to be hidden, which from where the user is standing is the
     * same as having no page at all — and it raises the same popup.
     *
     * ⚠ An app with **two** configured launcher icons is ambiguous, and the lowest component
     * name wins so that at least the answer is stable rather than arbitrary. The author's
     * position is that settings belong to the app rather than to the icon, so this should not
     * arise; if it ever does, the real fix is to key the per-app page by package, which is a
     * database migration rather than a change here.
     */
    private suspend fun configuredComponentFor(packageName: String): String? =
        appSettingsRepository.appSettingsFlow.first()
            .filter { it.enabled && it.componentName.substringBefore('/') == packageName }
            .map { it.componentName }
            .minOrNull()

    /**
     * Whether this app is owed the "nothing to hide" popup, or has already had it recently.
     *
     * An app with no entry has never been told, so it is due. See [nothingToHideShownAt] for why
     * the answer is a clock rather than a reading of what the user just did.
     */
    private fun nothingToHidePopupDue(packageName: String): Boolean {
        val shown = nothingToHideShownAt[packageName] ?: return true

        return SystemClock.elapsedRealtime() - shown >= NOTHING_TO_HIDE_INTERVAL_MILLIS
    }

    /**
     * Whether this app may be run for again, after a run that hid nothing.
     *
     * An app with no entry has never failed, so it is due — which is every app, every time,
     * until something goes wrong. See [failedRunAt] for why this is a clock rather than a count
     * of window changes.
     */
    private fun runCooldownDue(packageName: String): Boolean {
        val failure = failedRunAt[packageName] ?: return true

        val wait = autoHideFailureBackoffMillis(failures = failure.count)

        return SystemClock.elapsedRealtime() - failure.atElapsed >= wait
    }

    /**
     * Records a run that hid nothing, moving this app one step further down the back-off.
     *
     * The result is kept only so the diagnostic log can say which cause is repeating; nothing
     * branches on it. Every result that reaches here has the same shape — the detector is still
     * listening and the app is about to be relaunched into it.
     */
    private fun recordRunFailure(packageName: String, result: AppSettingsResult) {
        val previous = failedRunAt[packageName]

        failedRunAt[packageName] = RunFailure(
            count = (previous?.count ?: 0) + 1,
            atElapsed = SystemClock.elapsedRealtime(),
            result = result,
        )
    }

    /** Forgets an app's failures, so the next fault starts again at the shortest wait. */
    private fun clearRunFailure(packageName: String) {
        failedRunAt.remove(packageName)
    }

    /**
     * Force-stops the app a run was started for, bringing Shizuku up first if it is not
     * already there.
     *
     * The one place IMD+ asks Shizuku for anything on its own account — which is why the
     * "Do not close the app on the first launch" checkbox is the whole of the Shizuku
     * question on the IMD+ page.
     *
     * The start is announced to the tracker as an overlay hide, which is what puts the same
     * spinner over the run that a shortcut launch shows while Shizuku is coming up. It is not
     * an overlay hide, but it is the same wait for the same reason, and inventing a third
     * spinner for it would say nothing the user does not already understand.
     *
     * ⚠ **Three outcomes, not two, and the distinction is what stops a doomed run costing
     * sixteen seconds of spinner.** A force-stop that did not take is worth carrying on from —
     * hiding the settings is still worth doing. Shizuku failing to come up is not: the hide
     * behind this needs the same service for its overlay step and will spend another whole
     * wait discovering the same thing, under the same spinner, before failing anyway.
     */
    private suspend fun kill(packages: Set<String>): AutoHideKill {
        if (packages.isEmpty()) return AutoHideKill.Killed

        val running = runCatching { shizukuWrapper.isShizukuRunning() }.getOrDefault(false)

        if (!running) {
            shizukuStartTracker.beginOverlay(OverlayStart.Hide)

            val started = try {
                startShizukuUseCase()
            } finally {
                shizukuStartTracker.endOverlay(OverlayStart.Hide)
            }

            if (!started) return AutoHideKill.ShizukuUnavailable
        }

        val permitted = runCatching {
            shizukuWrapper.hasShizukuPermission() || shizukuWrapper.requestShizukuPermission()
        }.getOrDefault(false)

        // Permission refused is the same shape as a service that will not start: nothing
        // Shizuku is asked for later in this run can succeed either.
        if (!permitted) return AutoHideKill.ShizukuUnavailable

        // Each package independently, and all of them attempted: one app that has been
        // uninstalled since it was chosen must not stop the rest being stopped.
        val stopped = packages.map { packageName ->
            runCatching { shizukuWrapper.forceStop(packageName = packageName) }
                .getOrDefault(false)
        }.all { it }

        return if (stopped) AutoHideKill.Killed else AutoHideKill.NotKilled
    }
}

/**
 * How long the "nothing to hide" popup stays quiet for an app after it has been raised for it.
 *
 * Thirty minutes, which the author chose, and the shape of the rule matters more than the number:
 * this popup is a standing fact about the configuration rather than news about this particular
 * launch. Once told, a person does not need telling again on the next tap - and if they have not
 * fixed it half an hour later, they may well have forgotten.
 *
 * Counted per package. See [AutoHideRunner.nothingToHideShownAt].
 */
private const val NOTHING_TO_HIDE_INTERVAL_MILLIS = 30L * 60L * 1000L

/**
 * What the force-stop at the start of an IMD+ run managed to do.
 *
 * Top level rather than nested, because `check16_when` cannot read an indented enum — it needs
 * the closing brace at column 0, and this project has already moved one declaration out of a
 * class for exactly that.
 */
private enum class AutoHideKill {
    /** The app was stopped, or there was nothing to stop. */
    Killed,

    /**
     * Shizuku was there and permitted, but the stop did not take.
     *
     * Carried on from deliberately: the settings are still worth hiding, and a kill that
     * failed is indistinguishable from one that worked by the time the app is relaunched.
     */
    NotKilled,

    /**
     * Shizuku would not start, or refused permission.
     *
     * The run stops here. Everything after this needs the same service — and the hide's own
     * overlay step would spend a second full wait finding that out under the same spinner.
     */
    ShizukuUnavailable,
}


/**
 * What an IMD+ run decided, as far as the window that opened it needs to care.
 *
 * Only the two "nothing configured" cases are distinguished, and only because they are answered
 * by two different popups pointing at two different screens. Every other outcome — hidden and
 * relaunched, a kill that failed, a hide that could not withdraw overlay access — is [Done],
 * because the window's job in all of them is the same: close and let the app the user asked for
 * be the answer.
 */
enum class AutoHideOutcome {
    /** Nothing to say. The window closes. */
    Done,

    /** Revert-to-default mode, and the device-wide "Settings to hide" list has nothing ticked. */
    NothingToHide,

    /** Memory function, and this app has no settings of its own configured to be hidden. */
    NoProfile,

    /**
     * `WRITE_SECURE_SETTINGS` has gone, so IMD+ could not write a single setting.
     *
     * Its own value rather than folding into [Done], because Done means "nothing to say"
     * and this run has the one thing in the app most worth saying: every route is broken
     * until somebody re-grants the permission. It used to be swallowed here — the app was
     * relaunched with its settings untouched and nothing anywhere explained why.
     */
    PermissionsLost,

    /**
     * Settings are down from a run of IMD that is no longer alive.
     *
     * Raised by [com.android.geto.activity.autohide.AutoHideViewModel] **before** the runner is
     * asked to do anything, at the author's instruction — so that both of the popup's answers
     * have a run left to carry on with. A value here rather than a flag on the activity because
     * `AutoHideActivity` already draws every one of these and knows nothing else about them.
     */
    HiddenFromPreviousUse,
}
