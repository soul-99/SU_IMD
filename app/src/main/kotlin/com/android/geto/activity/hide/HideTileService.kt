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
package com.android.geto.activity.hide

import android.app.ActivityOptions
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.graphics.drawable.Icon
import android.os.Build
import android.service.quicksettings.Tile
import android.service.quicksettings.TileService
import androidx.annotation.RequiresApi
import com.android.geto.R
import com.android.geto.broadcastreceiver.HideToggle
import com.android.geto.broadcastreceiver.SettingsHiddenRunner
import com.android.geto.broadcastreceiver.buildHideTileOverlayFailedNotification
import com.android.geto.common.AppLocale
import com.android.geto.common.ApplicationScope
import com.android.geto.domain.common.Diagnostics
import com.android.geto.domain.model.settingsHidden
import com.android.geto.domain.repository.UserDataRepository
import com.android.geto.domain.usecase.SettingsWorkKind
import com.android.geto.domain.usecase.SettingsWorkTracker
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.HIDE_TILE_NOTIFICATION_ID
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import javax.inject.Inject
import com.android.geto.feature.apps.R as appsR

/**
 * The "Hide settings" Quick Settings tile.
 *
 * Unlike the other two tiles this one has a state to show rather than an action to fire, so
 * it follows the stored answer instead of flashing on for a second. That answer is written by
 * the hide and by every revert wherever it runs, which is what lets the tile show "visible"
 * again after a revert fired from a notification, an intent or a home-screen shortcut — none
 * of which know this tile exists.
 *
 * The direction of a press is decided in [SettingsHiddenRunner.toggle] rather than here. The
 * tile reads a flow and could always be a frame behind it; the runner re-reads the stored state
 * at the moment it runs, so the press cannot act on a state that has since changed.
 *
 * **The press runs here now, not in [HideActivity].** The window used to do the work, because
 * launching it was the only way to collapse the shade and the shade collapsed at the press. The
 * author wants the opposite: the shade open for the whole of it, so this tile is what the user
 * watches, and closed a second after a press that worked. That makes the collapse the *last*
 * thing rather than the first, and a window that is opened at the end cannot also be the thing
 * that runs. A press that fails leaves the shade open and says so in the shade — see
 * `HideTileNotification`.
 *
 * Long-pressing it opens the settings manager, routed through the shared preferences
 * trampoline like the other two.
 */
@RequiresApi(Build.VERSION_CODES.N)
@AndroidEntryPoint
class HideTileService : TileService() {
    // The chosen language, applied before anything reads a string. A no-op on Android 13
    // and up, where the platform has already applied it to this context.
    override fun attachBaseContext(newBase: Context) {
        super.attachBaseContext(AppLocale.wrap(newBase))
    }

    @Inject
    @ApplicationScope
    lateinit var appScope: CoroutineScope

    @Inject
    lateinit var userDataRepository: UserDataRepository

    @Inject
    lateinit var settingsWorkTracker: SettingsWorkTracker

    @Inject
    lateinit var settingsHiddenRunner: SettingsHiddenRunner

    @Inject
    lateinit var notificationManagerWrapper: AndroidNotificationManagerWrapper

    private var watch: Job? = null

    /**
     * Whether the panel is on screen with this tile in it.
     *
     * Read before the collapse, which happens a second after work that can itself take ten. By
     * then the user may have closed the shade themselves, and from Android 14 an app may only
     * start an activity from a tile while its panel is showing — so this is the difference
     * between skipping a collapse that has nothing left to collapse and throwing.
     */
    @Volatile
    private var listening: Boolean = false

    override fun onStartListening() {
        super.onStartListening()

        listening = true

        // Collected rather than read once, so a revert run from somewhere else while the
        // shade is open moves the tile there and then. The subscription lasts exactly as long
        // as the panel is showing it - see onStopListening.
        watch?.cancel()

        watch = appScope.launch {
            // Three things decide what the tile shows: what the device is, whether a press is
            // still being carried out, and which way that press is going. The second is what
            // stops the tile reading "visible" for the ten seconds a hide can spend waiting on
            // Shizuku - a stretch in which the old tile looked untouched and invited a second
            // press. The third is newer: busy alone said "Hiding settings" during a revert too,
            // which named the wrong direction for half of everything this tile does.
            combine(
                userDataRepository.userData.map { it.settingsHidden },
                settingsWorkTracker.inFlight,
                settingsWorkTracker.work,
            ) { hidden, busy, work -> Triple(hidden, busy, work) }
                .distinctUntilChanged()
                .collect { state ->
                    // ⚠ **On the main thread, and this is a fix rather than a tidy-up.**
                    // appScope is Dispatchers.Default, so every render before this ran on
                    // a background thread — and `qsTile` is a handle the framework swaps
                    // out around onStartListening and onStopListening. A render landing
                    // across that swap writes into a Tile the framework has already let
                    // go of and is dropped without a word, which leaves the tile showing
                    // whatever it was last told: dimmed, and reading "Unhiding settings"
                    // over a device that finished unhiding seconds ago. Intermittent by
                    // nature, and in whichever direction happened to be last. The other
                    // two tiles never had it — they only ever touch qsTile from a
                    // TileService callback, which is already the main thread.
                    withContext(Dispatchers.Main) {
                        render(
                            hidden = state.first,
                            busy = state.second,
                            work = state.third,
                        )
                    }
                }
        }
    }

    override fun onStopListening() {
        listening = false

        watch?.cancel()

        watch = null

        super.onStopListening()
    }

    override fun onDestroy() {
        listening = false

        watch?.cancel()

        watch = null

        super.onDestroy()
    }

    private fun render(hidden: Boolean, busy: Boolean, work: SettingsWorkKind?) {
        // Cancelling a job only *asks* it to stop, so a collector cancelled by
        // onStopListening can still deliver one last emission. There is no tile to draw
        // on by then and qsTile is somebody else's now, so this is the moment to stop.
        if (!listening) return

        // Which way a busy tile is going, with a fallback for the one moment nothing has said.
        //
        // `work` is null between the press claiming the tracker and the use case underneath it
        // claiming again *with* a direction - a couple of datastore reads, but a couple of reads
        // in which the label would otherwise still read "Hiding settings" on the way out of a
        // hide. In that window `hidden` decides it, and cannot be wrong: the only claim that
        // omits a direction is this tile's own press, and SettingsHiddenRunner.toggle reads this
        // very value to pick one. Every other path - IMD+, a launch, a notification, the
        // settings manager - names its direction from its first moment, and a named one wins.
        val unhiding = work == SettingsWorkKind.Unhiding || (work == null && hidden)

        qsTile?.apply {
            // UNAVAILABLE while the press is being carried out: the platform draws that
            // dimmed and refuses the tap for us, which is exactly "visibly unclickable".
            // The state is not moved until the work that decides it has finished, so the
            // tile never shows an answer the device has not reached yet.
            state = when {
                busy -> Tile.STATE_UNAVAILABLE

                hidden -> Tile.STATE_ACTIVE

                else -> Tile.STATE_INACTIVE
            }

            // The label as well as the icon, because a tile in a collapsed panel shows the
            // icon alone and one in the expanded panel shows both - and "Settings
            // visible/hidden" would then be describing the switch rather than saying which
            // way it is set.
            //
            // While busy it says so rather than keeping the old label: a dimmed tile still
            // reading "Settings visible" says the press was refused, which is the opposite of
            // what is happening. And it now says which of the two is being carried out - a
            // revert dimming the tile under "Hiding settings" was naming the wrong one.
            label = getString(
                when {
                    busy && unhiding -> R.string.hide_tile_unhiding

                    busy -> R.string.hide_tile_working

                    hidden -> R.string.hide_tile_hidden

                    else -> R.string.hide_tile_visible
                },
            )

            icon = Icon.createWithResource(
                this@HideTileService,
                if (hidden) R.drawable.ic_hidden_tile else R.drawable.ic_hide_tile,
            )

            updateTile()

            // What the tile was last told, which is the one thing a report of a stuck
            // label cannot be settled without: it separates "the tile was told the
            // wrong thing" from "the tile was told the right thing and did not show
            // it". One line per change, not per second — the collector is distinct-until-
            // changed, so nothing is written while the tile is sitting still.
            Diagnostics.log(
                tag = "tile",
                message = "hide tile hidden=$hidden busy=$busy work=$work",
            )
        }
    }

    override fun onClick() {
        super.onClick()

        // The platform will not deliver a tap on an UNAVAILABLE tile, but the state it is
        // drawn in and the state it is in can be a frame apart - and the one press that must
        // never get through twice is this one. Cheap, and it closes the gap.
        if (settingsWorkTracker.inFlightNow) return

        // The application context rather than this service, and read before the work rather
        // than after it. A press can take ten seconds; this service may not outlive it, and a
        // notification built from a destroyed service is a notification that never appears.
        // It also carries the chosen language, which GetoApplication put on it.
        val context = applicationContext

        // On the application scope, so the press finishes whether or not this service does -
        // the panel closing must not cut a revert in half. Nothing here holds the tracker; the
        // runner claims it for the whole toggle, which is what keeps the tile dimmed.
        appScope.launch {
            when (settingsHiddenRunner.toggle()) {
                // A second to see the tile land on its new state, then the shade closes. The
                // delay is the whole point of it - the collapse could happen the moment the
                // work returns, and then the answer the user was watching for would leave with
                // the shade that was showing it.
                HideToggle.Done -> {
                    delay(COLLAPSE_DELAY_MILLIS)

                    withContext(Dispatchers.Main) { collapseShade() }
                }

                // Nothing ticked to hide keeps the behaviour it always had, on the author's
                // instruction: the shade closes and the dialog says what to configure. No
                // second in front of it - this returns in a moment and the tile does not move,
                // so there is nothing to hold the shade open to watch. It is also not a
                // failure; nothing went wrong, there was simply nothing set up to do.
                HideToggle.NothingToHide -> withContext(Dispatchers.Main) {
                    collapseShade(dialog = HideDialog.NothingToHide)
                }

                // ⚠ **This failure does collapse, unlike the one below, and the author
                // asked for exactly that.** Nothing was hidden here either, but this is
                // not a problem with the press - it is the whole app unable to write a
                // single setting until somebody re-grants a permission over adb, and the
                // notification shade is not where a person should have to read that.
                HideToggle.PermissionsLost -> withContext(Dispatchers.Main) {
                    collapseShade(dialog = HideDialog.PermissionsLost)
                }

                // ⚠ **No collapse on a failure, on the author's instruction.** Nothing was
                // hidden, so there is nothing to go and look at, and closing the shade would
                // take away the tile that is still reading "Settings visible" - the clearest
                // statement that the press did not land.
                HideToggle.OverlayFailure -> notificationManagerWrapper.notify(
                    id = HIDE_TILE_NOTIFICATION_ID,
                    notification = buildHideTileOverlayFailedNotification(
                        context = context,
                        title = context.getString(appsR.string.overlay_failure_title),
                        text = overlayFailureText(context = context),
                    ),
                )
            }
        }
    }

    /**
     * The overlay dialog's three sentences, one per line.
     *
     * The dialog draws its two points as bulleted rows, with the marker supplied by the
     * composable rather than typed into the string — so that a translation cannot lose it and a
     * right-to-left language gets it on the correct side. A notification has no such composable,
     * and hard-coding a bullet here would reintroduce exactly the problem that avoided, so the
     * lines are simply lines.
     */
    private fun overlayFailureText(context: Context): String = listOf(
        appsR.string.overlay_failure_check,
        appsR.string.overlay_failure_point_permission,
        appsR.string.overlay_failure_point_configuration,
    ).joinToString(separator = "\n") { context.getString(it) }

    /**
     * Closes the shade, which since Android 12 an app can only do by launching an activity.
     *
     * [HideActivity] is that activity, and for an ordinary press it opens and closes again
     * without drawing anything. It used to run the press as well, which it could because the
     * collapse happened first; now that the collapse happens last, a window opened at the end
     * cannot be the window the work happens in.
     *
     * [dialog] is the two cases where it still draws: nothing ticked to hide, which names
     * what to configure and is what such a press has always shown, and the lost grant.
     *
     * Refused rather than obeyed if the panel has already gone, and that is the right answer:
     * there is nothing left to collapse. Wrapped anyway, because from Android 14 the platform
     * throws rather than ignoring a start from a tile whose panel is not showing, and this runs
     * a second after work that can take ten.
     */
    private fun collapseShade(dialog: HideDialog? = null) {
        if (!listening) return

        val intent = Intent(this, HideActivity::class.java).putExtra(
            HIDE_EXTRA_DIALOG,
            dialog?.name,
        ).addFlags(
            // NO_ANIMATION is the third half of being invisible, and the one the theme cannot
            // supply. Theme.Geto.Tile switches off this window's *own* animation, but the
            // transition that plays when an activity is launched belongs to the launch, not to
            // the window - it is chosen by whoever starts it. Nothing was choosing, so the
            // system used its default and a press that draws nothing still showed a moment of
            // an app opening. Purely cosmetic: this flag cannot stop the activity starting or
            // change anything it does.
            Intent.FLAG_ACTIVITY_NEW_TASK or
                Intent.FLAG_ACTIVITY_CLEAR_TOP or
                Intent.FLAG_ACTIVITY_NO_ANIMATION,
        )

        runCatching {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
                // The same "no animation" said the other way it can be said. From Android 14
                // the shade hands the start to the system through a PendingIntent, and the
                // options baked into that are what the system reads when it picks a transition
                // - so the flag above is stated here as well rather than trusted to survive the
                // handover. Two zeroes mean "no enter animation, no exit animation".
                val options = ActivityOptions.makeCustomAnimation(this, 0, 0).toBundle()

                startActivityAndCollapse(
                    PendingIntent.getActivity(
                        this,
                        0,
                        intent,
                        PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
                        options,
                    ),
                )
            } else {
                @Suppress("DEPRECATION")
                startActivityAndCollapse(intent)
            }
        }
    }

    companion object {
        /**
         * How long the shade stays open after a press that worked.
         *
         * A second, which the author asked for and which is about right: long enough to read
         * the tile settling on "Settings hidden" or "Settings visible", short enough that it
         * still feels like the press closed the shade rather than the user having to.
         */
        private const val COLLAPSE_DELAY_MILLIS = 1_000L
    }
}
