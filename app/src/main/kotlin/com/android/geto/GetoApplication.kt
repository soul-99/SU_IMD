/*
 *
 *   Copyright 2023 Einstein Blanco
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
package com.android.geto

import android.app.Application
import android.app.NotificationManager
import android.content.ComponentName
import android.content.Context
import android.os.Build
import android.service.quicksettings.TileService
import com.android.geto.activity.autounhide.AutoUnhideService
import com.android.geto.activity.hide.HideTileService
import com.android.geto.broadcastreceiver.AutoHideRunner
import com.android.geto.broadcastreceiver.DiagnosticStateReporter
import com.android.geto.activity.hide.DrawerShortcuts
import com.android.geto.common.AppLocale
import com.android.geto.common.ApplicationScope
import com.android.geto.diagnostics.DefaultDiagnosticLogStore
import com.android.geto.domain.common.Diagnostics
import com.android.geto.domain.common.IconStyleState
import com.android.geto.domain.model.IconStyle
import com.android.geto.domain.model.settingsHidden
import com.android.geto.domain.repository.UserDataRepository
import com.android.geto.domain.usecase.DetectShizukuForkUseCase
import com.android.geto.domain.usecase.MigrateFrameworksUseCase
import com.android.geto.broadcastreceiver.DeveloperNoteNotification
import com.android.geto.activity.main.SETTINGS_NOTICE_REVISION
import com.android.geto.domain.usecase.MigrateAutoUnhideUseCase
import com.android.geto.domain.usecase.MigrateManageShizukuUseCase
import com.android.geto.domain.usecase.MigrateNotificationFunctionUseCase
import com.android.geto.domain.usecase.MigrateRevertDefaultsUseCase
import com.android.geto.domain.usecase.SyncAutoHideDetectorSelectionUseCase
import com.android.geto.domain.usecase.SettingsWorkTracker
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper
import dagger.hilt.android.HiltAndroidApp
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.drop
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.launch
import javax.inject.Inject
import com.android.geto.framework.notificationmanager.R as notificationR

@HiltAndroidApp
class GetoApplication : Application() {
    @Inject
    lateinit var notificationManagerWrapper: AndroidNotificationManagerWrapper

    @Inject
    lateinit var developerNoteNotification: DeveloperNoteNotification

    @Inject
    lateinit var migrateNotificationFunctionUseCase: MigrateNotificationFunctionUseCase

    @Inject
    lateinit var migrateFrameworksUseCase: MigrateFrameworksUseCase

    @Inject
    lateinit var migrateManageShizukuUseCase: MigrateManageShizukuUseCase

    @Inject
    lateinit var migrateAutoUnhideUseCase: MigrateAutoUnhideUseCase

    @Inject
    lateinit var migrateRevertDefaultsUseCase: MigrateRevertDefaultsUseCase

    @Inject
    lateinit var syncAutoHideDetectorSelectionUseCase: SyncAutoHideDetectorSelectionUseCase

    @Inject
    lateinit var detectShizukuForkUseCase: DetectShizukuForkUseCase

    @Inject
    lateinit var autoHideRunner: AutoHideRunner

    @Inject
    lateinit var userDataRepository: UserDataRepository

    @Inject
    lateinit var diagnosticLogStore: DefaultDiagnosticLogStore

    @Inject
    lateinit var diagnosticStateReporter: DiagnosticStateReporter

    @Inject
    lateinit var settingsWorkTracker: SettingsWorkTracker

    @Inject
    lateinit var drawerShortcuts: DrawerShortcuts

    @Inject
    @ApplicationScope
    lateinit var appScope: CoroutineScope

    // Wrapping here is what puts the chosen language on the application context, which is
    // the context Hilt injects everywhere and the one every notification is built from.
    // A no-op on Android 13 and up, where the platform applies it before the process starts.
    override fun attachBaseContext(base: Context) {
        super.attachBaseContext(AppLocale.wrap(base))
    }

    override fun onCreate() {
        super.onCreate()

        // Here rather than in MainActivity, because most of what this app does happens
        // with the app not open: a Quick Settings tile, a pinned shortcut and a notification
        // action all run in this process without any activity being created. Migrating on
        // first launch of the UI would leave those reading the old preference for as long as
        // the user never opened the app.
        // ⚠ **One block, in order, and it used to be two launches.** The comment below has
        // always said the order is the whole of it, and two `appScope.launch` calls do not
        // order anything. It bites only an install arriving from below v1.6 - anyone above it
        // already carries the reset's marker, so it returns early and the pairing reads their
        // real mechanism - but there the result depended on which coroutine won.
        appScope.launch {
            migrateNotificationFunctionUseCase()

            // v3 reads whatever the old mechanism finally settled on, so the v1.6 reset has to
            // have run first or an install arriving from below v1.6 would be split on a value
            // about to change.
            migrateFrameworksUseCase()
        }

        // Independent of the frameworks migration above, so the order between them does not
        // matter: this one reads only the Shizuku configuration fields, which no migration
        // writes.
        appScope.launch { migrateManageShizukuUseCase() }

        // ⚠ **Collected for the life of the process, not run once.** The Hide/unhide entry's
        // icon has to follow the hidden state, and that state changes from a tile, a
        // notification action, a Tasker broadcast or the drawer entry itself - all of them in
        // this process, none of them through an activity. A one-shot here would leave the
        // drawer showing an open eye over a hidden device until something else restarted IMD.
        appScope.launch {
            drawerShortcuts.states.collect {
                drawerShortcuts.apply(userDataRepository.userData.first())
            }
        }

        // Independent of every other migration: it writes only auto unhide's own triggers and
        // conditions, which nothing else touches. Here rather than on the settings screen for
        // the same reason as the rest — the watcher can be started by a tile or a shortcut in
        // a process where no activity ever exists.
        appScope.launch { migrateAutoUnhideUseCase() }

        // ⚠ **One call for all five of the author's triggers.** He asked for the note on first
        // app launch, first hide from a shortcut or IMD+, the settings manager, a toggle and an
        // intent. The first four open an activity and get the dialog; the Hide settings tile
        // and the Tasker intents have no window at all. Every one of them starts *this
        // process*, so posting here covers the two that cannot show a dialog without a call at
        // each site — and the moment an activity appears, MainActivity shows the dialog and
        // acknowledging it takes the notification down.
        appScope.launch {
            developerNoteNotification.postIfUnread(currentRevision = SETTINGS_NOTICE_REVISION)
        }

        // Both default configurations - what a Revert restores and what a launch hides - and
        // the same reason neither can wait for the UI: a tile or a shortcut can fire a Revert,
        // or launch an app, in this process without an activity ever existing, and both must
        // already be reading the configuration this install has always had.
        appScope.launch { migrateRevertDefaultsUseCase() }

        // IMD+'s own detector is an ordinary entry in the managed accessibility list since r9,
        // where it used to be a tick the picker drew by itself and stored nowhere. An install
        // that already had IMD+ on has an empty list and no event coming to fix it - that is
        // what left the manager's Accessibility row greyed - so it is brought into line once,
        // here, and kept there by the IMD+ switch afterwards.
        //
        // Behind the flag rather than run every start: the sync is idempotent and would write
        // nothing anyway, but "this has already been done" is worth being a fact rather than a
        // re-derivation, and it matches every other one-shot in this block.
        appScope.launch {
            if (!userDataRepository.userData.first().autoHideDetectorManagedV3) {
                syncAutoHideDetectorSelectionUseCase()

                userDataRepository.updateAutoHideDetectorManagedV3(done = true)
            }
        }

        // Only writes when nobody has chosen a fork family yet, so it fills in a fresh
        // install and leaves every other one alone. Here rather than on the settings
        // screen because the guess should already be made by the time somebody opens it.
        appScope.launch { detectShizukuForkUseCase() }

        // The diagnostic log's writing end, and the in-memory flag every caller checks before
        // it builds a message. Installed here because the sink has to exist before the first
        // line, and a line can be written by a tile press in a process with no activity in it.
        //
        // Nothing starts because of this. The flag is read and returned on when recording is
        // off, and when it is on the only cost is an append from code that was already running
        // - there is no thread, no timer and no service behind it.
        Diagnostics.install(sink = diagnosticLogStore)

        appScope.launch {
            userDataRepository.userData
                .map { it.diagnosticsEnabled }
                .distinctUntilChanged()
                .collect { enabled ->
                    Diagnostics.enabled = enabled

                    // The baseline every delta below is a difference from. This transition is
                    // the only moment a file has none: the store has just created it and
                    // written "recording started", and without a full block behind them a
                    // later "work: permissions writeSecure=no" would describe a change from a
                    // value the reader never saw.
                    if (enabled) {
                        diagnosticStateReporter.report(
                            reason = "recording started",
                            full = true,
                        )
                    }
                }
        }

        // What IMD was configured to do, and allowed to do, at the start and the end of every
        // hide and every revert — whichever of the eighteen routes began it.
        //
        // ⚠ **The tracker rather than the routes, for the reason the tracker itself gives.**
        // Those eighteen call sites sit on four use cases, and every one of them claims this
        // before it touches anything, so a path cannot start work without appearing here. A
        // reporter wired into the routes would have eighteen chances to miss one and would
        // silently not cover the nineteenth.
        //
        // ⚠ **`distinctUntilChanged` is what makes this one report rather than three.** The
        // claims genuinely nest — the tile takes two, an IMD+ revert takes one around the use
        // case's own — and the flow only speaks when the answer changes.
        //
        // ⚠ **`drop(1)`** discards the replayed `false` a StateFlow hands every new collector,
        // which at this point in `onCreate` is "nothing has ever run" rather than "something
        // just settled". Nothing can be in flight before this line, so it can never drop a
        // real emission.
        //
        // Costs nothing with recording off: the reporter's first act is one volatile read.
        appScope.launch {
            settingsWorkTracker.inFlight
                .drop(1)
                .collect { running ->
                    diagnosticStateReporter.report(
                        reason = if (running) "work" else "settled",
                    )
                }
        }

        // ⚠ **The Icon style, into the memory holder the two renderers read.** They are in
        // `:framework` and cannot reach the preferences — see IconStyleState. One collector
        // rather than a read at each icon: a few hundred icons are decoded per list.
        appScope.launch {
            userDataRepository.userData
                .map { it.iconStyle }
                .distinctUntilChanged()
                .collect { style ->
                    IconStyleState.shapeLegacyIcons = style == IconStyle.SmartAdaptive
                }
        }

        // Auto-hide settings (IMD+) starts listening here, and only here. The accessibility
        // service can deliver an event with nothing else of this app running, so what it needs
        // to decide has to be in memory before the first event rather than behind a datastore
        // read - which is what arm() keeps up to date.
        autoHideRunner.arm(scope = appScope)

        // The auto unhide watcher runs for exactly as long as something is hidden and the
        // feature is switched on, and not one moment longer - a foreground service and its
        // notification with nothing to watch would be a battery cost and a shade entry in
        // exchange for nothing.
        //
        // Driven from the stored state rather than started at each of the six places a hide
        // can begin. The state outlives the process, so a service the system reclaims comes
        // back with it, and a seventh hide route added later is covered without anyone
        // remembering to wire it up.
        appScope.launch {
            userDataRepository.userData
                .map { it.autoUnhideEnabled && it.settingsHidden }
                .distinctUntilChanged()
                .collect { needed ->
                    if (needed) {
                        AutoUnhideService.start(this@GetoApplication)
                    } else {
                        AutoUnhideService.stop(this@GetoApplication)
                    }
                }
        }

        // ⚠ **Telling the system the Hide settings tile has something new to say.**
        //
        // A tile only hears from its own service while its panel is on screen. Every hide
        // and every revert that does not come from the tile itself — a launch from inside
        // IMD, a pinned shortcut, IMD+, an automation intent, the revert notification —
        // happens with the shade shut, so the tile is told nothing at all and goes on
        // showing whatever it was last told until somebody opens the panel and the
        // collector inside the service has caught up. That is the few seconds the author
        // saw after launching an app from inside IMD, and why a tile press looked fixed
        // while everything else did not: a press keeps the shade open, so its service is
        // listening for the whole of it.
        //
        // `requestListeningState` is the platform's answer to exactly this — it binds the
        // tile service and calls onStartListening with the panel closed, so the update
        // happens before anybody looks rather than after. **It has never been called
        // anywhere in this app.**
        //
        // On the settled state only. Which way the work is going is worth drawing while
        // somebody is watching the tile, and nobody is watching a closed shade; asking
        // the system to bind a service for that would be spending a wake-up on a frame
        // no one sees. The system rate-limits these requests in any case.
        appScope.launch {
            userDataRepository.userData
                .map { it.settingsHidden }
                .distinctUntilChanged()
                .collect {
                    // Wrapped because this is a request to the system about a tile the
                    // user may never have added to their panel, and OEM shades vary in
                    // what they do with one. A refused refresh is not worth a crash in
                    // Application.onCreate's scope.
                    runCatching {
                        TileService.requestListeningState(
                            this@GetoApplication,
                            ComponentName(this@GetoApplication, HideTileService::class.java),
                        )
                    }
                }
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            notificationManagerWrapper.createNotificationChannel(
                channelId = AndroidNotificationManagerWrapper.NOTIFICATION_CHANNEL_ID,
                name = getString(R.string.app_name),
                importance = NotificationManager.IMPORTANCE_DEFAULT,
            )

            // Separate and louder, for failures that leave the device changed in a way the
            // user cannot see. Registering it here rather than on first use means the channel
            // exists in system settings before anything has gone wrong, so it can be tuned
            // down in advance by anyone who would rather it did not interrupt.
            notificationManagerWrapper.createNotificationChannel(
                channelId = AndroidNotificationManagerWrapper.ALERT_NOTIFICATION_CHANNEL_ID,
                name = getString(notificationR.string.alert_notification_channel),
                importance = NotificationManager.IMPORTANCE_HIGH,
            )

            // The channel for the one ongoing notification a hide leaves behind, so it can
            // be silenced or sorted without touching anything else. Registered whichever
            // framework is in use: a channel is invisible in Android's settings until
            // something has been posted to it, and creating one lazily would mean the first
            // post arriving before its channel existed.
            notificationManagerWrapper.createNotificationChannel(
                channelId = AndroidNotificationManagerWrapper.REVERT_TO_DEFAULT_CHANNEL_ID,
                name = getString(notificationR.string.revert_to_default),
                importance = NotificationManager.IMPORTANCE_DEFAULT,
            )

            // ⚠ **The per-app revert channel, deleted rather than merely left uncreated.** r3
            // replaced the per-app notification with the single generic one, so nothing posts
            // here any more - but a device that ever saw one carries this channel in Android's
            // settings, and an entry that can never hold a notification again is worse than no
            // entry at all. Same treatment as AUTO_UNHIDE_CHANNEL_ID_LOW below, for the same
            // reason.
            notificationManagerWrapper.deleteNotificationChannel(
                channelId = AndroidNotificationManagerWrapper.REVERT_MEMORY_CHANNEL_ID,
            )

            // And one for Auto-hide settings (IMD+), whose notification is the only one a
            // user can meet without having opened this app - it appears because an app they
            // tapped was on the watched list. Its own channel so it can be turned down without
            // silencing the route back from a hide they asked for deliberately.
            notificationManagerWrapper.createNotificationChannel(
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
            )

            // And one for the auto unhide watcher's own service notification, at
            // IMPORTANCE_MIN - Android's own "Minimise" - so it is silent, unbadged, at the
            // bottom of the shade and, the point of the exercise, absent from the status bar.
            //
            // r12 registered this at LOW, which does put an icon up there. Importance cannot
            // be edited after a channel exists, so this is a new id and the old one is
            // deleted below rather than left behind as a dead entry in Android's settings.
            notificationManagerWrapper.createNotificationChannel(
                channelId = AndroidNotificationManagerWrapper.AUTO_UNHIDE_CHANNEL_ID,
                name = getString(notificationR.string.auto_unhide_channel),
                importance = NotificationManager.IMPORTANCE_MIN,
            )

            notificationManagerWrapper.deleteNotificationChannel(
                channelId = AndroidNotificationManagerWrapper.AUTO_UNHIDE_CHANNEL_ID_LOW,
            )
        }
    }
}
