/*
 *
 *   Copyright 2026 soul_99 (suIMD)
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
package com.android.geto.domain.usecase

import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.StopShizukuOutcome
import com.android.geto.domain.model.isShizukuConfigured
import com.android.geto.domain.repository.UserDataRepository
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.first
import javax.inject.Inject

/**
 * Stops the Shizuku service as part of a hide: the stop broadcast, and the transport dropped
 * underneath it in the same breath.
 *
 * Stopping Shizuku before a launch is what keeps a fork's watchdog from flagging the app it is
 * about to open. The stop broadcast is the fork's own, which [SetManualTargetUseCase] sends for
 * [ManualRevertTarget.Shizuku] — and immediately after it, USB and wireless debugging are
 * switched off and then put back where this run's configuration says they belong.
 *
 * ⚠ **No wait, and that is v3 spec item 7.** This used to poll for the binder to go quiet for
 * as long as the fork's whole start budget — eight seconds on Thedjchi — and only cycle the
 * transport if it had not. The author's instruction: *"just after sending shizuku stop intent,
 * IMD also stops the USB debugging and within a split second turns USB and wireless debugging
 * where it should be … so we avoid the spinners for stopping shizuku."*
 *
 * The two paths did the same thing in the end; the poll only decided how long a launch stood
 * still first, and how it was described afterwards. A hide the user is waiting on is the wrong
 * place to spend eight seconds confirming something the next line makes true anyway: the
 * service cannot outlive adbd.
 *
 * ⚠ **Both transports, because dropping USB alone does not always do it.** A fork riding
 * wireless debugging outlives a USB cycle — that is what the old fallback's own confirmation
 * poll was for. With no poll left, the answer is to drop both and let the configuration put
 * back whichever of them this run means to leave on.
 *
 * ⚠ **No confirmation, at the author's decision** — *"we are sending the stop intent so no
 * worries"*. [StopShizukuOutcome.Stopped] therefore means "the stop ran", not "the stop was
 * observed to work"; [StopShizukuOutcome.StoppedViaUsb] and [StopShizukuOutcome.NotStopped] are
 * no longer reachable and are kept for the vocabulary.
 *
 * Shared by the device-wide "Settings to hide" path and the per-app "Memory" profile so both
 * behave identically. It never throws for a hide to key off.
 */
class StopShizukuServiceUseCase @Inject constructor(
    private val userDataRepository: UserDataRepository,
    private val getManualTargetStatesUseCase: GetManualTargetStatesUseCase,
    private val setManualTargetUseCase: SetManualTargetUseCase,
) {
    /**
     * @param usbFinalEnabled where USB debugging is left after the cycle. The caller decides,
     *        and has to fold two things together: whether this run is hiding USB debugging
     *        anyway, and whether it was even on to begin with — restoring a setting the user
     *        had switched off would be this app enabling debugging on its own.
     * @param wirelessFinalEnabled the same question for wireless debugging. ⚠ **Its own
     *        parameter, not inferred from [usbFinalEnabled]**: the two are configured
     *        separately, and IMD's default is to hide wireless debugging without restoring it
     *        — see `restoreWirelessDebugging`, which the caller has already folded in.
     */
    suspend operator fun invoke(
        usbFinalEnabled: Boolean,
        wirelessFinalEnabled: Boolean,
    ): StopShizukuOutcome {
        val userData = userDataRepository.userData.first()

        // The toggle only means anything once Shizuku is configured: there is no stop action
        // to derive otherwise, and nothing this app can manage. Treated as a no-op rather than
        // a failure so a launch is never cancelled over it.
        if (!userData.isShizukuConfigured) return StopShizukuOutcome.NotConfigured

        // Nor for a fork with no stop intent. Shevery goes down with the debugging transport,
        // which the hide rules already decide, so there is nothing for this to send and the
        // Shizuku row is not offered on that fork in the first place.
        if (!userData.shizukuForkMode.supportsIntents) return StopShizukuOutcome.NotConfigured

        // Nothing running, nothing to stop. A hide that started Shizuku to hide the overlay
        // will have left it running, which is exactly the case this then takes back down.
        if (!getManualTargetStatesUseCase().isEnabled(ManualRevertTarget.Shizuku)) {
            return StopShizukuOutcome.NotRunning
        }

        // The fork's own stop broadcast. It is what keeps the fork from switching debugging
        // on or off on its own account while IMD is deciding where both should be.
        setManualTargetUseCase(target = ManualRevertTarget.Shizuku, enabled = false)

        // ⚠ **Straight after it, and with no wait in between** - spec item 7. Both transports
        // drop: the service cannot outlive adbd, and a fork riding wireless debugging would
        // outlive USB going down alone.
        setManualTargetUseCase(target = ManualRevertTarget.UsbDebugging, enabled = false)

        setManualTargetUseCase(target = ManualRevertTarget.WirelessDebugging, enabled = false)

        // The author's "within a split second". Long enough for adbd to notice the transport
        // has gone, short enough that nothing on screen has time to describe it.
        delay(TRANSPORT_SETTLE_MILLIS)

        // And back where this run's configuration says they belong. Off is already true, so
        // only the restores are written - a second write of a setting that is already right
        // is a shell round trip in the middle of a launch.
        if (usbFinalEnabled) {
            setManualTargetUseCase(target = ManualRevertTarget.UsbDebugging, enabled = true)
        }

        if (wirelessFinalEnabled) {
            setManualTargetUseCase(target = ManualRevertTarget.WirelessDebugging, enabled = true)
        }

        return StopShizukuOutcome.Stopped
    }

    private companion object {
        /**
         * The author's "split second" — long enough for adbd to drop the transport, short
         * enough that a launch does not visibly stop.
         *
         * ⚠ **Not `ShizukuForkMode.serviceWaitMillis`.** That is how long a fork is given to
         * *answer* a broadcast, and nothing here waits for an answer any more. Reading it here
         * is what made a hide stand still for eight seconds.
         */
        const val TRANSPORT_SETTLE_MILLIS = 300L
    }
}
