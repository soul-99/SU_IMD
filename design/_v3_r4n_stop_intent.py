#!/usr/bin/env python3
"""v3-r4n — spec item 7: the stop intent stops waiting.

The author's spec, verbatim:

    "currently whenever IMD is trying to stop shizuku first it tries stop intent then it waits
     sometime and checks if shizuku stopped and if failed it disables USB, wireless debugging.
     Now make it so that just after sending shizuku stop intent, IMD also stops the USB
     debugging and within a split second turns USB and wireless debugging where it should be as
     per configuration of hiding or unhiding which ever is being performed at that point. The
     idea is that stop intent stops shizuku(thedjchi) to not turn on/off debugging and instead
     it will still be managed by IMD but the delay which occurs when intent is sent and IMD
     waits will be gone so we avoid the spinners for stopping shizuku. Also after this there is
     no need to display the notification that shizuku killed using adb one."

**This is the eight-second wait he hit while testing IMD+**, diagnosed at the top of this round:
`awaitStopped` polls `serviceWaitMillis / 500` times, and a deliberately wrong start intent
poisons the derived stop action, so it spent the whole budget twice.

## The two confirmations, in his words

* *"yes do that only, as stop intent is also sent shizuku wont try to restart"* — both USB **and**
  wireless debugging drop for the split second and then go where the configuration says.
* *"we are sending the stop intent so no worries"* — no confirmation poll afterwards. The stop
  reports that it ran, not that it was observed.

## What goes with it

`ShizukuFallbackNotifier.warnKilledViaUsbDebugging` and the notification behind it. The standing
warning in three handovers is that this comes out **with** item 7 and not before, because until
now cycling USB debugging really was a fallback the user could not see. Now it is the mechanism,
every time, and a notification that fired on every hide would be noise.

⚠ **The English strings and all eleven locale copies stay declared.** Translations are frozen for
the whole project, and deleting an English string whose translations remain is how
`check_translations` starts reporting orphans that nobody is allowed to fix. The r2i principle:
left declared, unused, with a comment saying why.

⚠ **`StopShizukuOutcome.StoppedViaUsb` and `NotStopped` become unreachable and are kept.** Same
principle, and there is a second reason here: `stopped` is what records the service against an
app so *that* app's revert restarts it, and a future round that reintroduces a check will want
the vocabulary intact rather than re-derived.

⚠ **The spinner goes with the wait.** `OverlayStart.StopShizuku` stops being raised from here.
The enum entry and the dialog's branch stay — `ShizukuStartingDialog`'s `when` must remain
exhaustive, and the settings manager can still stop the service from a screen of its own.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STOP = "domain/use-case/src/main/kotlin/com/android/geto/domain/usecase/StopShizukuServiceUseCase.kt"
DEVICE = "domain/use-case/src/main/kotlin/com/android/geto/domain/usecase/ApplySettingsToHideUseCase.kt"
PERAPP = "domain/use-case/src/main/kotlin/com/android/geto/domain/usecase/ApplyAppSettingsUseCase.kt"
NOTIFIER = "domain/framework/src/main/kotlin/com/android/geto/domain/framework/ShizukuFallbackNotifier.kt"
IMPL = "broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/DefaultShizukuFallbackNotifier.kt"
OUTCOME = "domain/model/src/main/kotlin/com/android/geto/domain/model/StopShizukuOutcome.kt"

EDITS: list[tuple[str, str, str, str]] = []


def edit(rel: str, name: str, old: str, new: str) -> None:
    EDITS.append((rel, name, old, new))


# ---------------------------------------------------------------------------------------
# 1 — the use case itself
# ---------------------------------------------------------------------------------------
edit(
    STOP,
    "the class KDoc",
    """/**
 * Stops the Shizuku service as part of a hide — gracefully if the fork answers a stop intent,
 * and by force if it does not.
 *
 * Stopping Shizuku before a launch is what keeps a fork's watchdog from flagging the app it
 * is about to open. The graceful path is the fork's own stop broadcast, which is what
 * [SetManualTargetUseCase] sends for [ManualRevertTarget.Shizuku]. Not every fork acts on one
 * — the stop action is derived from the start action and some forks ignore it — so this waits
 * a few seconds for the binder to go quiet, and when it does not, drops the transport the
 * service rides on by switching USB debugging off for a moment. That always works, because
 * the service cannot outlive adbd, but it is the blunt instrument: it cannot be undone as
 * cleanly on the way back, so the user is warned through [ShizukuFallbackNotifier] when it is
 * the path taken.
 *
 * Shared by the device-wide "Settings to hide" path and the per-app "Memory" profile so both
 * behave identically. It never throws for a hide to key off — a Shizuku that will not stop is
 * still, once USB debugging is cycled, a Shizuku that is not running.
 */""",
    """/**
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
 */""",
)

edit(
    STOP,
    "the parameter docs and the body",
    """    /**
     * @param usbFinalEnabled where USB debugging should be left if the fallback has to cycle
     *        it. The caller decides, and has to fold two things together: whether this run is
     *        hiding USB debugging anyway, and whether it was even on to begin with — restoring
     *        a setting the user had switched off would be this app enabling debugging on its
     *        own. Ignored when the graceful stop succeeds, since nothing is cycled then.
     * @param overlayHidden whether Display over other apps was hidden in this same run; only
     *        changes the wording of the fallback warning.
     */
    suspend operator fun invoke(
        usbFinalEnabled: Boolean,
        overlayHidden: Boolean,
    ): StopShizukuOutcome {""",
    """    /**
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
    ): StopShizukuOutcome {""",
)

edit(
    STOP,
    "the stop itself",
    """        // The graceful path: the fork's own stop broadcast, and a spinner over the wait for
        // it. By this point the overlay work is finished and its own spinner has gone, so
        // without this the launch simply stops dead for eight seconds with nothing on screen.
        setManualTargetUseCase(target = ManualRevertTarget.Shizuku, enabled = false)

        shizukuStartTracker.beginOverlay(OverlayStart.StopShizuku)

        val stopped = try {
            awaitStopped(userData = userData)
        } finally {
            shizukuStartTracker.endOverlay(OverlayStart.StopShizuku)
        }

        if (stopped) return StopShizukuOutcome.Stopped

        // The fork did not stop. Drop the transport it rides on: switching USB debugging off
        // takes adbd, and therefore Shizuku, down with it.
        setManualTargetUseCase(target = ManualRevertTarget.UsbDebugging, enabled = false)

        delay(FALLBACK_SETTLE_MILLIS)

        // Checked before USB debugging goes back, because restoring it is what could let a
        // fork come straight back up. A service on wireless debugging, or started as root,
        // outlives this - and reporting a stop that did not happen is worse than reporting
        // nothing: the app's revert would broadcast a start at a service already running, and
        // the warning would name a cause that was not the cause.
        val killed = !isShizukuRunning()

        // Put USB debugging back only where the caller says it belongs: off when this run is
        // hiding it anyway, and off when it was already off before any of this started.
        if (usbFinalEnabled) {
            setManualTargetUseCase(target = ManualRevertTarget.UsbDebugging, enabled = true)
        }

        if (!killed) return StopShizukuOutcome.NotStopped

        shizukuFallbackNotifier.warnKilledViaUsbDebugging(overlayHidden = overlayHidden)

        return StopShizukuOutcome.StoppedViaUsb
    }""",
    """        // The fork's own stop broadcast. It is what keeps the fork from switching debugging
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
    }""",
)

edit(
    STOP,
    "the polling helpers",
    """    /**
     * The binder ping on its own, not the full target-states read.
     *
     * [GetManualTargetStatesUseCase] answers for every row, and on a device with managed
     * overlay packages that includes an `appops query-op` shell round trip through the very
     * service being polled. Six of those inside a three-second budget is not a 500ms poll, and
     * this runs in the middle of a launch.
     */
    private suspend fun isShizukuRunning(): Boolean =
        runCatching { shizukuWrapper.isShizukuRunning() }.getOrDefault(false)

    /**
     * Polls for the service to go quiet after a stop broadcast, for as long as this fork is
     * given to answer - the same budget a start gets, because it is the same fork taking the
     * same kind of time over the same kind of broadcast.
     */
    private suspend fun awaitStopped(userData: UserData): Boolean {
        val polls = (userData.shizukuForkMode.serviceWaitMillis / STOP_CONFIRM_POLL_MILLIS).toInt()

        repeat(polls) {
            delay(STOP_CONFIRM_POLL_MILLIS)

            if (!isShizukuRunning()) return true
        }

        return false
    }

    private companion object {
        // The total wait is the fork's own (ShizukuForkMode.serviceWaitMillis); this is only
        // how often it is looked at.
        const val STOP_CONFIRM_POLL_MILLIS = 500L
        const val FALLBACK_SETTLE_MILLIS = 1_500L // let adbd drop before restoring USB debugging
    }""",
    """    private companion object {
        /**
         * The author's "split second" — long enough for adbd to drop the transport, short
         * enough that a launch does not visibly stop.
         *
         * ⚠ **Not `ShizukuForkMode.serviceWaitMillis`.** That is how long a fork is given to
         * *answer* a broadcast, and nothing here waits for an answer any more. Reading it here
         * is what made a hide stand still for eight seconds.
         */
        const val TRANSPORT_SETTLE_MILLIS = 300L
    }""",
)

# ---------------------------------------------------------------------------------------
# 2 — the two callers
# ---------------------------------------------------------------------------------------
edit(
    DEVICE,
    "the device-wide call",
    """        if (wanted[ManualRevertTarget.Shizuku] == true) {
            stopShizukuServiceUseCase(
                // Put back only if it was on to start with and this run is not hiding it.
                usbFinalEnabled = usbInitiallyOn &&
                    wanted[ManualRevertTarget.UsbDebugging] != true,
                overlayHidden = hidingOverlay,
            )""",
    """        if (wanted[ManualRevertTarget.Shizuku] == true) {
            stopShizukuServiceUseCase(
                // Put back only if it was on to start with and this run is not hiding it.
                usbFinalEnabled = usbInitiallyOn &&
                    wanted[ManualRevertTarget.UsbDebugging] != true,
                // ⚠ **The same question for wireless debugging, and it needs its own answer.**
                // Spec item 7 drops both transports, so both have to be put back deliberately
                // — and IMD's own rule is that it does not restore wireless debugging unless
                // asked, which `restoreWirelessDebugging` is. A hide that is not hiding
                // wireless debugging must still leave it exactly as it found it.
                wirelessFinalEnabled = wirelessInitiallyOn &&
                    wanted[ManualRevertTarget.WirelessDebugging] != true,
            )""",
)

edit(
    DEVICE,
    "the initial wireless reading",
    """        val usbInitiallyOn = before.isEnabled(ManualRevertTarget.UsbDebugging)""",
    """        val usbInitiallyOn = before.isEnabled(ManualRevertTarget.UsbDebugging)

        // ⚠ **And the same reading for wireless debugging, for the same reason** — since spec
        // item 7 the stop drops both transports, so both have to be put back only where they
        // were. Taken from the same snapshot, before anything below moves either of them.
        val wirelessInitiallyOn = before.isEnabled(ManualRevertTarget.WirelessDebugging)""",
)

edit(
    PERAPP,
    "the per-app call",
    """                    stopShizukuServiceUseCase(
                        // Put back only if it was on to start with and this profile is not
                        // hiding it itself.
                        usbFinalEnabled = usbInitiallyOn &&
                            !hidesUsbDebugging(enabledAppSettings),
                        overlayHidden = managesOverlay,
                    )""",
    """                    stopShizukuServiceUseCase(
                        // Put back only if it was on to start with and this profile is not
                        // hiding it itself.
                        usbFinalEnabled = usbInitiallyOn &&
                            !hidesUsbDebugging(enabledAppSettings),
                        // ⚠ **Its own answer since spec item 7**, which drops both transports.
                        // A profile that never mentions adb_wifi_enabled must end the launch
                        // with wireless debugging exactly where it found it.
                        wirelessFinalEnabled = wirelessInitiallyOn &&
                            !hidesWirelessDebugging(enabledAppSettings),
                    )""",
)

edit(
    PERAPP,
    "the per-app initial readings",
    """        val usbInitiallyOn = stoppingShizuku &&
            getManualTargetStatesUseCase().isEnabled(ManualRevertTarget.UsbDebugging)""",
    """        val usbInitiallyOn = stoppingShizuku &&
            getManualTargetStatesUseCase().isEnabled(ManualRevertTarget.UsbDebugging)

        // The same reading for wireless debugging: spec item 7's stop drops both transports,
        // so both have to be put back only where they were.
        val wirelessInitiallyOn = stoppingShizuku &&
            getManualTargetStatesUseCase().isEnabled(ManualRevertTarget.WirelessDebugging)""",
)

edit(
    PERAPP,
    "the wireless helper",
    """    private fun hidesUsbDebugging(appSettings: List<AppSetting>): Boolean = appSettings.any {
        it.enabled &&
            it.settingType == SettingType.GLOBAL &&
            it.key == AppSettingKeys.ADB_ENABLED &&
            it.valueOnLaunch == "0"
    }""",
    """    private fun hidesUsbDebugging(appSettings: List<AppSetting>): Boolean = appSettings.any {
        it.enabled &&
            it.settingType == SettingType.GLOBAL &&
            it.key == AppSettingKeys.ADB_ENABLED &&
            it.valueOnLaunch == "0"
    }

    /** The wireless half of the question above, asked since spec item 7 drops both. */
    private fun hidesWirelessDebugging(appSettings: List<AppSetting>): Boolean = appSettings.any {
        it.enabled &&
            it.settingType == SettingType.GLOBAL &&
            it.key == AppSettingKeys.ADB_WIFI_ENABLED &&
            it.valueOnLaunch == "0"
    }""",
)

# ---------------------------------------------------------------------------------------
# 3 — the warning that goes with it
# ---------------------------------------------------------------------------------------
edit(
    NOTIFIER,
    "the interface",
    """interface ShizukuFallbackNotifier {""",
    """@Deprecated(
    message = "v3 spec item 7 removed the USB fallback: dropping the transport is now the " +
        "mechanism rather than a fallback, so there is nothing exceptional to warn about. " +
        "Kept declared, with its strings and their eleven translations, because deleting an " +
        "English string whose locale copies remain is how check_translations starts reporting " +
        "orphans nobody is allowed to fix while translations are frozen.",
)
interface ShizukuFallbackNotifier {""",
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

    stop = staged[ROOT / STOP]

    # ⚠ **Nothing that waits for an answer may survive.** Spelled as the calls and constants
    # they can only be, never as bare words, because the replacement KDoc discusses the poll,
    # the fallback and the warning in prose — the comment trap.
    for spelling in (
        "awaitStopped(",
        "STOP_CONFIRM_POLL_MILLIS",
        "FALLBACK_SETTLE_MILLIS",
        "isShizukuRunning(",
        ".warnKilledViaUsbDebugging(",
        "beginOverlay(OverlayStart.StopShizuku)",
    ):
        if spelling in stop:
            print(f"REFUSED: {STOP} still carries {spelling!r}")
            return 1

    # And the injections behind them must go too, or check12 reports them and the constructor
    # asks Hilt for things it does not use.
    for gone in (
        "private val shizukuWrapper: ShizukuWrapper,",
        "private val shizukuFallbackNotifier: ShizukuFallbackNotifier,",
        "private val shizukuStartTracker: ShizukuStartTracker,",
    ):
        if gone in stop:
            stop = stop.replace(f"    {gone}\n", "", 1)

        if gone in stop:
            print(f"REFUSED: {STOP} still injects {gone!r}")
            return 1

    for gone_import in (
        "import com.android.geto.domain.framework.ShizukuFallbackNotifier\n",
        "import com.android.geto.domain.framework.ShizukuWrapper\n",
        "import com.android.geto.domain.model.UserData\n",
    ):
        stop = stop.replace(gone_import, "", 1)

        if gone_import in stop:
            print(f"REFUSED: {STOP} still imports {gone_import.strip()!r}")
            return 1

    staged[ROOT / STOP] = stop

    # ⚠ **Position, not presence.** The stop broadcast has to precede the transport drop, and
    # the settle has to sit between the drop and the restores — an edit that reordered them
    # would satisfy every count above and cycle the transport before asking the fork to stop.
    order = (
        "target = ManualRevertTarget.Shizuku, enabled = false",
        "target = ManualRevertTarget.UsbDebugging, enabled = false",
        "target = ManualRevertTarget.WirelessDebugging, enabled = false",
        "delay(TRANSPORT_SETTLE_MILLIS)",
        "target = ManualRevertTarget.UsbDebugging, enabled = true",
        "target = ManualRevertTarget.WirelessDebugging, enabled = true",
    )

    positions = []

    for needle in order:
        if needle not in stop:
            print(f"REFUSED: {STOP} does not carry {needle!r}")
            return 1

        positions.append(stop.index(needle))

    if positions != sorted(positions):
        print("REFUSED: the stop, the drop, the settle and the restores are out of order")
        return 1

    # Both callers must pass the new argument, and neither may still pass the old one.
    for rel in (DEVICE, PERAPP):
        text = staged[ROOT / rel]

        if "overlayHidden = " in text:
            print(f"REFUSED: {rel} still passes overlayHidden to the stop")
            return 1

        if "wirelessFinalEnabled = " not in text:
            print(f"REFUSED: {rel} does not pass wirelessFinalEnabled")
            return 1

    # The strings and their translations must all still be there — frozen, not deleted.
    english = (ROOT / "framework/notification-manager/src/main/res/values/strings.xml").read_text(
        encoding="utf-8",
    )

    for key in ("shizuku_usb_fallback_title", "shizuku_usb_fallback_text"):
        if f'<string name="{key}">' not in english:
            print(f"REFUSED: {key} was deleted; translations are frozen")
            return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")

    print(f"  ok        {STOP}  :: no wait, both transports, no warning")
    print(f"  ok        {DEVICE}  :: wirelessFinalEnabled")
    print(f"  ok        {PERAPP}  :: wirelessFinalEnabled + hidesWirelessDebugging")
    print(f"  ok        {NOTIFIER}  :: deprecated, kept declared")
    print("  ok        the fallback strings and all eleven translations are untouched")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
