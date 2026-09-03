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
package com.android.geto.domain.model

/**
 * Which family of Shizuku fork the start-service broadcast is aimed at.
 *
 * The families do not share a contract. thedjchi's fork listens for a broadcast carrying
 * an "auth" token copied out of its own *View intents* screen; Shevery and the forks that
 * grew alongside it expose a start action with no token at all. Neither complains when it
 * receives the other's shape — the broadcast is simply ignored — so the user names the
 * family and the fields follow from it, rather than the app guessing.
 *
 * [Unset] exists because there is no safe default. Guessing produces the one outcome worth
 * avoiding: a toggle that looks configured and silently does nothing.
 */
enum class ShizukuForkMode {
    Unset,
    Thedjchi,
    Other,
    ;

    /** Only thedjchi's fork authenticates the broadcast. */
    val requiresAuthKey: Boolean get() = this == Thedjchi

    /**
     * Whether this family can be started and stopped by broadcasting an intent at it.
     *
     * Only thedjchi's can. Shevery has no start or stop action to send: what brings its
     * service back is Shevery's own **ErrorProtect** watchdog, which polls every ten seconds
     * and starts the server itself the moment the debugging transport is available again. So
     * IMD does not drive Shevery at all — it gives debugging back and waits, and it stops
     * Shevery by taking debugging away. Every screen that offers to toggle the service, and
     * every code path that would send it an intent, has to know which of the two it is
     * talking to.
     */
    val supportsIntents: Boolean get() = this == Thedjchi

    /**
     * Shevery and the forks alongside it: driven indirectly, through the debugging transport,
     * because there is no intent contract to use.
     */
    val isShevery: Boolean get() = this == Other

    /**
     * How long to wait for the service to appear after asking for it, in milliseconds.
     *
     * Two different numbers because two different things are being waited on. thedjchi's fork
     * is answering a broadcast this app just sent, so the wait covers only its own start-up —
     * eight seconds is generous for that. Shevery is not answering anything: the wait is for
     * its ErrorProtect watchdog to come round again, notice the transport is back and start
     * the server itself. That poll is on a ten-second cycle, so anything at or under ten
     * seconds can miss a whole revolution.
     *
     * ⚠ **Forty seconds for Shevery, the author's number in v3**, up from thirteen. Thirteen
     * left room for one cycle plus the server's own start-up and nothing more, so a watchdog
     * that had just gone round when the transport came back was already outside the window.
     *
     * [Unset] never waits, because nothing was ever asked.
     */
    val serviceWaitMillis: Long
        get() = when (this) {
            Unset -> 0L
            Thedjchi -> 8_000L
            Other -> 40_000L
        }
}

/**
 * Whether enough has been filled in for a start broadcast to be worth sending.
 *
 * One definition for the switch that gates the feature, the automatic restart on revert
 * and the manual re-enable button, so the three can never disagree about what "set up"
 * means. The auth key is required only where the chosen fork actually reads it.
 */
val UserData.isShizukuConfigured: Boolean
    get() = shizukuForkMode != ShizukuForkMode.Unset &&
        shizukuPackageName.isNotBlank() &&
        shizukuStartAction.isNotBlank() &&
        (!shizukuForkMode.requiresAuthKey || shizukuAuthKey.isNotBlank())

/**
 * Whether IMD is managing Shizuku right now — the master switch as the UI must read it.
 *
 * [UserData.manageShizuku] is the user's stored answer; this is that answer **and** a Shizuku
 * configuration complete enough to act on. The author's rule is that the switch "gets
 * automatically toggled off if any field below is blank, but remembers the previous state in
 * case a field below is emptied and filled again" — which is this expression exactly, with
 * nothing written on the way through.
 *
 * ⚠ **Every gate in the app reads this, never the stored field.** A row that asked
 * [UserData.manageShizuku] alone would offer to drive a Shizuku IMD cannot reach.
 */
val UserData.manageShizukuEffective: Boolean
    get() = manageShizuku && isShizukuConfigured
