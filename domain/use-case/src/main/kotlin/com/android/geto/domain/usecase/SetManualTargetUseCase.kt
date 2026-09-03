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
package com.android.geto.domain.usecase

import com.android.geto.domain.common.dispatcher.Dispatcher
import com.android.geto.domain.common.dispatcher.GetoDispatchers
import com.android.geto.domain.framework.AccessibilityServicesWrapper
import com.android.geto.domain.framework.PackageManagerWrapper
import com.android.geto.domain.framework.SecureSettingsWrapper
import com.android.geto.domain.framework.ShizukuWrapper
import com.android.geto.domain.model.AccessibilityServicePlan
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.SettingType
import com.android.geto.domain.model.ShizukuForkDefaults
import com.android.geto.domain.model.isShizukuConfigured
import com.android.geto.domain.model.settingsHidden
import com.android.geto.domain.repository.UserDataRepository
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withContext
import javax.inject.Inject

private const val ON = "1"

private const val OFF = "0"

/**
 * Switches one row of the settings manager on or off.
 *
 * The manager dialog's per-row switches, and the only path that writes these settings by
 * hand. An earlier version could only ever put things back — one direction, behind a batch
 * button — which meant the dialog could rescue a device but never simply manage it.
 *
 * Switching **off** is deliberately narrow. Accessibility services removes only the
 * components this app manages, and Shizuku sends the fork's own stop action rather than
 * killing anything — neither reaches beyond what the app put in place itself.
 */
class SetManualTargetUseCase @Inject constructor(
    private val secureSettingsWrapper: SecureSettingsWrapper,
    private val accessibilityServicesWrapper: AccessibilityServicesWrapper,
    private val shizukuWrapper: ShizukuWrapper,
    private val packageManagerWrapper: PackageManagerWrapper,
    private val userDataRepository: UserDataRepository,
    private val startShizukuUseCase: StartShizukuUseCase,
    // The detector's lifecycle is theirs, not this class's. Reusing them rather than weaving
    // the detector into the plan below keeps one owner for "IMD+ off" and "IMD+ back", and
    // means this switch cannot invent a third way of recording the same hold.
    private val disableAutoHideServiceUseCase: DisableAutoHideServiceUseCase,
    private val restoreAutoHideServiceUseCase: RestoreAutoHideServiceUseCase,
    @param:Dispatcher(GetoDispatchers.Default) private val defaultDispatcher: CoroutineDispatcher,
) {
    /**
     * False for a target that could not be written, and never an exception.
     *
     * The false-versus-throw distinction is the whole contract, because every caller that
     * matters is part-way through changing the device when it asks. A revert writes overlay
     * access, then four settings, then Shizuku; a thrown exception out of the first of those
     * skips the other five and leaves the device in the half-reverted state the revert
     * exists to prevent - with no notification either, since the caller never reaches the
     * line that raises one.
     *
     * The overlay and Shizuku branches are the ones that made this real rather than
     * theoretical: both end in a binder call to a service that can die between the check
     * that it is alive and the call itself, and a dead binder throws rather than returning.
     */
    suspend operator fun invoke(
        target: ManualRevertTarget,
        enabled: Boolean,
        /**
         * A person pressing this row's switch in the settings manager, as opposed to a hide, a
         * revert, IMD+ or Tasker.
         *
         * ⚠ **Read on the `enabled = true` paths only**, and it is the difference between
         * "release what IMD is holding" and "put my chosen services back on". The second is what
         * the switch has always claimed to do and could not: with no debt recorded — after a
         * discard, or after the user switched something off in the system settings themselves —
         * both branches found nothing to release, reported success, and wrote nothing. The row
         * then re-read the device, found it unchanged, and looked stuck.
         *
         * ⚠ **False everywhere else, and that default is load-bearing.** A revert forcing the
         * selection on would switch on services the user had turned off by hand since the hide,
         * which is not what "put it back the way it was" means.
         */
        manual: Boolean = false,
    ): Boolean = withContext(defaultDispatcher) {
        // Same reasoning as the manual revert: a half-applied change to developer options
        // is worse than none, so navigating away must not cancel it mid-write.
        withContext(NonCancellable) {
            runCatching {
                set(target = target, enabled = enabled, manual = manual)
            }.getOrDefault(false)
        }
    }

    private suspend fun set(
        target: ManualRevertTarget,
        enabled: Boolean,
        manual: Boolean,
    ): Boolean {
        target.globalSettingKey?.let { key ->
            return runCatching {
                secureSettingsWrapper.canWriteSecureSettings(
                    settingType = SettingType.GLOBAL,
                    key = key,
                    value = if (enabled) ON else OFF,
                )
            }.getOrDefault(false)
        }

        return when (target) {
            ManualRevertTarget.AccessibilityServices -> setAccessibilityServices(
                enabled = enabled,
                manual = manual,
            )

            ManualRevertTarget.Shizuku -> setShizuku(running = enabled)

            ManualRevertTarget.DisplayOverOtherApps -> setOverlayPermission(
                enabled = enabled,
                manual = manual,
            )
            else -> false
        }
    }

    /**
     * The device-wide half of overlay access, scoped to the user's selection.
     *
     * A near-copy of [setAccessibilityServices] below, and deliberately so: both manage a
     * chosen subset of something the whole system shares, both have to survive two apps
     * holding the same item down at once, and both are wrong in exactly the same way if they
     * take everything they find rather than everything the user picked.
     */
    private suspend fun setOverlayPermission(enabled: Boolean, manual: Boolean): Boolean {
        val userData = userDataRepository.userData.first()

        val held = userData.heldOverlayPackages
        val holdKey = AccessibilityServicePlan.DEVICE_WIDE_HOLD

        if (enabled) {
            val released = held[holdKey].orEmpty()

            // The early return is kept for every automatic caller: with nothing owed there is
            // nothing for a revert to put back, and saying so costs no binder call.
            if (released.isEmpty() && !manual) return true

            val stillHeld = AccessibilityServicePlan.heldByOthers(
                held = held,
                exceptComponentName = holdKey,
            )

            // Only what this holder took, minus anything another profile is still holding
            // down. Identities are checked because an app uninstalled or replaced since has
            // no permission of ours to give back.
            val identities: Map<String, String> = userData.heldOverlayIdentities
            val current: Map<String, String> =
                packageManagerWrapper.getPackageIdentities(released.toSet())
            val toRestore = released
                .filterNot { it in stillHeld }
                .filter { current[it] != null && current[it] == identities[it] }
                .toSet()

            // Everything the user selected that is off right now and that nothing else is
            // holding down. Only asked for on the manual path, because it costs a live AppOp
            // read, and only there does the answer change anything.
            //
            // A null answer is Shizuku out of reach, which is not the same as "nothing to do":
            // the debt below is still released on the author's own record, and the forced part
            // is simply skipped rather than guessed at.
            val forced: Set<String> = if (manual) {
                val allowed = runCatching {
                    shizukuWrapper.getAllowedOverlayPackages()
                }.getOrNull()

                if (allowed == null) {
                    emptySet()
                } else {
                    userData.managedOverlayPackages
                        .filterNot { it in stillHeld || it in allowed }
                        .toSet()
                }
            } else {
                emptySet()
            }

            val wanted = toRestore + forced

            val restored = if (wanted.isEmpty()) {
                emptySet()
            } else {
                shizukuWrapper.setOverlayPermission(packages = wanted, allowed = true)
                    ?: emptySet()
            }

            // Anything neither restored nor restorable leaves this holder's debt; a package
            // whose app is gone is dropped, because there is nothing left to give it back to.
            val outstanding = released.filter {
                it !in restored && (it in stillHeld || current[it] == identities[it])
            }

            val remaining = AccessibilityServicePlan.withHold(
                held = held,
                componentName = holdKey,
                services = outstanding,
            )

            val stillOwed = remaining.values.flatten().toSet()

            userDataRepository.updateHeldOverlayPackages(
                held = remaining,
                identities = identities.filterKeys { it in stillOwed },
            )

            // The debt is what remembers that overlay access is still withdrawn. The flag is
            // separate: a non-empty debt is the ordinary state between hiding and reverting,
            // whereas this says a restore was tried and did not work, which is what earns a
            // red row and a notification.
            val restoredEverything = outstanding.none { it !in stillHeld }

            // The flag stays a statement about the **debt** only. A forced grant that Shizuku
            // refused is a switch that did not move, not a revert that failed, and raising the
            // red row and its notification for it would be reporting a debt that never existed.
            if (userData.overlayRestoreFailed == restoredEverything) {
                userDataRepository.updateOverlayRestoreFailed(failed = !restoredEverything)
            }

            // The caller is told about both, because the manager's switch has to spring back
            // if what the user pressed it for did not happen.
            return restoredEverything && forced.all { it in restored }
        }

        val selected = userData.managedOverlayPackages

        if (selected.isEmpty()) return true

        val allowed = shizukuWrapper.getAllowedOverlayPackages() ?: return false

        val heldByOthers = AccessibilityServicePlan.heldByOthers(
            held = held,
            exceptComponentName = holdKey,
        )

        // Claim a selected package that is allowed now, and one another profile is already
        // holding down - without the second, that profile's revert would hand overlay access
        // back while the device-wide hide is still meant to be in force.
        val toClaim = selected.filter { it in allowed || it in heldByOthers }

        val toDisable = toClaim.filter { it in allowed }.toSet()

        if (toClaim.isEmpty()) return true

        val identities: Map<String, String> =
            packageManagerWrapper.getPackageIdentities(toDisable)

        // Written before the shell command, and extending rather than replacing: a second
        // launch must not lose the first one's debt, and a multi-package command can fail
        // after changing an earlier package.
        val provisional = AccessibilityServicePlan.withHold(
            held = held,
            componentName = holdKey,
            services = held[holdKey].orEmpty() + toClaim,
        )

        userDataRepository.updateHeldOverlayPackages(
            held = provisional,
            identities = userData.heldOverlayIdentities + identities,
        )

        if (toDisable.isEmpty()) return true

        val disabled = shizukuWrapper.setOverlayPermission(
            packages = toDisable,
            allowed = false,
        ) ?: emptySet()

        // Narrow the crash-safe provisional debt to what the shell actually changed. Every
        // candidate was allowed before this attempt, so a process death before this cleanup
        // can only re-allow something that never stopped being allowed.
        val settled = held[holdKey].orEmpty() + toClaim.filter {
            it in disabled || it in heldByOthers
        }

        userDataRepository.updateHeldOverlayPackages(
            held = AccessibilityServicePlan.withHold(
                held = held,
                componentName = holdKey,
                services = settled,
            ),
            identities = userData.heldOverlayIdentities + identities.filterKeys { it in disabled },
        )

        return disabled == toDisable
    }

    private suspend fun setAccessibilityServices(enabled: Boolean, manual: Boolean): Boolean {
        val userData = userDataRepository.userData.first()

        val held = userData.heldAccessibilityServices
        val holdKey = AccessibilityServicePlan.DEVICE_WIDE_HOLD

        val currentlyEnabled = runCatching {
            accessibilityServicesWrapper.getEnabledAccessibilityServices()
        }.getOrNull() ?: return false

        if (enabled) {
            // A full restore, not a scoped one. This runs for the manager's own toggle and
            // for "Revert to default", and both mean "put my accessibility services back" -
            // so every hold IMD is carrying is released, whoever placed it, and the record is
            // cleared. Scoping this to the device-wide holder, as an earlier build did, is the
            // reported bug: a launch always claims a service the manager already switched off,
            // so the device-wide hold was shadowed by a per-app one and releasing only the
            // device-wide holder found everything "held by others" and restored nothing.
            //
            // The per-app memory revert does not come through here - RevertAppSettingsUseCase
            // releases one app's holder and leaves the rest - which is what keeps a per-app
            // revert from undoing a manager hide, exactly as asked.
            // IMD's own IMD+ detector is deliberately left out, in both directions. This
            // switch stands for the services the *user* picked, and the detector is not one
            // of them: it is switched off by every hide whatever the selection says, and put
            // back by a revert - see RestoreAutoHideServiceUseCase. A manager switch that
            // moved it as well would let someone turn IMD+'s detector on in the middle of a
            // hide, which is exactly the state the hide exists to prevent.
            val ownHold = held.filterKeys { it == AccessibilityServicePlan.AUTO_HIDE_HOLD }

            val plan = AccessibilityServicePlan.releaseAll(
                held = held - AccessibilityServicePlan.AUTO_HIDE_HOLD,
                currentlyEnabled = currentlyEnabled,
            )

            // Releasing the debt, and then — for the manager's own switch only — switching on
            // whatever of the user's selection is *still* off afterwards. See
            // AccessibilityServicePlan.enable, which was written for this case and describes it
            // exactly: "including ones no hold was ever recorded for, which is exactly the
            // situation that arises when the record was lost".
            //
            // After releaseAll rather than instead of it, so the two cannot disagree about the
            // order of the list, and so a service held by a per-app profile is released by the
            // step that knows about holders rather than forced past it by the step that does not.
            val enabledAfter = if (manual) {
                AccessibilityServicePlan.enable(
                    wanted = userData.managedAccessibilityServices,
                    currentlyEnabled = plan.enabledAfter,
                )
            } else {
                plan.enabledAfter
            }

            val written = runCatching {
                accessibilityServicesWrapper.setEnabledAccessibilityServices(enabledAfter)
            }.getOrDefault(false)

            // The detector's hold survives, so whatever put it down still owes it back.
            if (written && held.isNotEmpty()) {
                userDataRepository.updateHeldAccessibilityServices(held = ownHold)
            }

            // ...unless nothing is hidden, in which case the only thing that can be holding it
            // is this switch being turned off a moment ago, and the author asked for that to be
            // symmetrical.
            //
            // ⚠ **Guarded on the hidden state, and that guard is the whole reason this is safe.**
            // The comment above is still true while a hide is standing: handing the detector
            // back then would let IMD+ notice an app and start a run on top of settings that are
            // already down, which is precisely the state a hide exists to prevent. With nothing
            // hidden there is no run to interfere with, so there is nothing left to protect.
            //
            // [settingsHidden] cannot be tripped by this switch's own work: a device-wide
            // accessibility hold is one of [AccessibilityServicePlan.INTERNAL_HOLDS], which
            // [memoryHeldComponents] filters out, and nothing here writes
            // `settingsHiddenDeviceWide`.
            if (written && !userData.settingsHidden) {
                restoreAutoHideServiceUseCase()
            }

            return written
        }

        val heldByOthers = AccessibilityServicePlan.heldByOthers(
            held = held,
            exceptComponentName = holdKey,
        )
        // Only the services the user picked in IMD settings are ever touched. Taking the
        // whole live enabled list instead would switch off services the user never chose and
        // had no way to exempt, which is the one thing this app has always refused to do to a
        // device — see the rule at the top of AccessibilityServicePlan.
        //
        // IMD's own IMD+ detector is not in here either. It is switched off by every hide
        // through DisableAutoHideServiceUseCase, whatever this selection says, and it is
        // recorded under its own holder so that neither this switch nor a per-app revert can
        // hand it back while a hide is still standing.
        val managed = userData.managedAccessibilityServices

        val selected = managed.toSet()

        val plan = AccessibilityServicePlan.hold(
            // Services already held for this target are re-claimed so a repeat launch
            // extends the existing debt, and a service a per-app profile is holding is
            // claimed too — but only within the selection, so the profile's Revert cannot
            // bring one back while the device-wide restricted app is still open.
            managed = held[holdKey].orEmpty() + managed +
                heldByOthers.filter { it in selected },
            currentlyEnabled = currentlyEnabled,
            heldByOthers = heldByOthers,
        )

        if (plan.held.isEmpty() && !plan.listChanged) {
            // Nothing of the user's selection needed touching — every service was already off,
            // or none was selected. Still a switch turned off, so the detector goes with it.
            //
            // ⚠ Safe to do here precisely because there is no plan write on this path. On the
            // path below it has to wait until after the write: `plan.enabledAfter` is computed
            // from the `currentlyEnabled` snapshot taken at the top, which still lists the
            // detector, so writing that list *after* disabling it would switch it straight back
            // on.
            disableAutoHideServiceUseCase()

            return true
        }

        val updatedHeld = AccessibilityServicePlan.withHold(
            held = held,
            componentName = holdKey,
            // A second device-wide launch must extend the existing debt rather than
            // replacing it. Services from the first launch are already off, so hold()
            // cannot rediscover them from the live enabled list.
            services = held[holdKey].orEmpty() + plan.held,
        )

        // Persist before writing so process death cannot leave a service disabled with no
        // record capable of restoring it.
        userDataRepository.updateHeldAccessibilityServices(held = updatedHeld)

        val written = runCatching {
            accessibilityServicesWrapper.setEnabledAccessibilityServices(
                plan.enabledAfter,
            )
        }.getOrDefault(false)

        if (!written) {
            userDataRepository.updateHeldAccessibilityServices(held = held)

            return false
        }

        // IMD+'s own detector goes off with them, which is new in v3 and the author's rule:
        // "whenever accessibility services are turned off by IMD from IMD services manager,
        // always also disable IMD+ accessibility service."
        //
        // Left to [DisableAutoHideServiceUseCase] rather than folded into the plan above, so
        // that the detector is recorded under its own holder exactly as a hide records it —
        // one shape of that record, written in one place. It early-returns while IMD+ is
        // switched off, so there is nothing to guard here.
        //
        // After the write, not before: a plan that failed to land should not take the detector
        // with it, and the early return above is what makes that true.
        disableAutoHideServiceUseCase()

        return true
    }

    private suspend fun setShizuku(running: Boolean): Boolean {
        // Starting goes through the shared use case, which waits to find out whether Shizuku
        // actually came up. Sending the broadcast and reporting success was the old
        // behaviour, and it is why a switch could report "on" for a service that never
        // started.
        if (running) return startShizukuUseCase()

        val userData = userDataRepository.userData.first()

        if (!userData.isShizukuConfigured) return false

        val startAction = userData.shizukuStartAction.ifBlank {
            userData.shizukuPackageName + ShizukuWrapper.ACTION_START_SUFFIX
        }

        // No stop action can be derived from a start action with no "START" in it. Better
        // to report failure than to broadcast something invented.
        val stopAction = ShizukuForkDefaults.stopActionFor(startAction = startAction)

        if (stopAction.isBlank()) return false

        return shizukuWrapper.stopShizuku(
            packageName = userData.shizukuPackageName,
            action = stopAction,
            authKey = userData.shizukuAuthKey,
        )
    }
}
