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
 * The arithmetic behind Settings.Secure.enabled_accessibility_services, kept as pure
 * functions so it can be reasoned about and tested without a device.
 *
 * Two rules this exists to enforce:
 *
 * 1. Only ever add or remove the specific components this app is responsible for. The
 *    enabled-services string is never saved and restored wholesale, because a service the
 *    user enables or disables elsewhere while the target app is open would otherwise be
 *    silently dropped or resurrected on revert.
 *
 * 2. A service stays off until *every* app that asked for it to be off has been reverted.
 *    Holds are tracked per target app, so reverting one app cannot switch a service back
 *    on underneath another app that is still in the foreground.
 */
object AccessibilityServicePlan {

    private const val SEPARATOR = ":"

    /** Hold key used by the device-wide "Settings to hide" accessibility target. */
    const val DEVICE_WIDE_HOLD = "__device_wide_settings_to_hide__"

    data class Hold(
        /** The new value for enabled_accessibility_services. */
        val enabledAfter: List<String>,
        /** Components this app is now holding down, to be recorded against it. */
        val held: List<String>,
        /** Whether the enabled list actually needs writing. */
        val listChanged: Boolean,
    )

    data class Release(
        val enabledAfter: List<String>,
        val restored: List<String>,
    ) {
        val listChanged: Boolean get() = restored.isNotEmpty()
    }

    /**
     * Switches off the managed services that are currently on, and claims a hold on every
     * managed service that is either on now or already being held down by another app.
     *
     * Claiming the already-held ones matters: without it, app A holds a service, app B
     * launches and finds it already off so records nothing, then A's revert switches it
     * back on while B is still open.
     */
    fun hold(
        managed: List<String>,
        currentlyEnabled: List<String>,
        heldByOthers: List<String>,
    ): Hold {
        val managedSet = managed.toSet()

        val enabledSet = currentlyEnabled.toSet()

        val othersSet = heldByOthers.toSet()

        val held = managed.distinct().filter { it in enabledSet || it in othersSet }

        val enabledAfter = currentlyEnabled.filterNot { it in managedSet }

        return Hold(
            enabledAfter = enabledAfter,
            held = held,
            listChanged = enabledAfter.size != currentlyEnabled.size,
        )
    }

    /**
     * Puts back the services this app was holding, skipping any that another app is still
     * holding and any the user has since re-enabled by hand, so the list never grows a
     * duplicate and never re-enables something another app still needs off.
     */
    fun release(
        released: List<String>,
        stillHeldByOthers: List<String>,
        currentlyEnabled: List<String>,
    ): Release {
        val blocked = stillHeldByOthers.toSet()

        val enabledSet = currentlyEnabled.toSet()

        val restored = released.distinct().filterNot { it in blocked || it in enabledSet }

        return Release(
            enabledAfter = currentlyEnabled + restored,
            restored = restored,
        )
    }

    /**
     * The enabled list after releasing *every* hold, whoever placed it, and the record that
     * remains once they are all gone - which is nothing.
     *
     * This is what "turn accessibility services on" from the services manager and "Revert to
     * default" both use, and the difference from [release] is the whole point of the reported
     * bug. [release] restores one holder's services and treats every other holder as a reason
     * to keep a service off. That is right for a per-app revert - another app may still need
     * the service down - but wrong for these two, where the user is asking for their services
     * back full stop. Because a launch claims a service that the manager already switched off,
     * every device-wide hold ends up shadowed by a per-app one, and a [release] of just the
     * device-wide holder then finds them all "held by others" and restores nothing.
     *
     * Releasing everything is also what makes a revert cumulative: services switched off from
     * the manager and services switched off across any number of launches all come back
     * together, because all their holders are cleared at once.
     *
     * The per-app memory revert deliberately does not come here - it releases its own holder
     * and leaves the others - which is what keeps it from undoing a manager hide or another
     * app's.
     */
    fun releaseAll(
        held: Map<String, List<String>>,
        currentlyEnabled: List<String>,
    ): Release = release(
        released = held.values.flatten().distinct(),
        stillHeldByOthers = emptyList(),
        currentlyEnabled = currentlyEnabled,
    )

    /**
     * The enabled list after switching [wanted] on, whatever state they were in before.
     *
     * This is what the manual Re-enable control uses, and it is deliberately not
     * [release]: release only restores what this app is recorded as having switched off,
     * whereas the user pressing Re-enable is asking for their chosen services to be on
     * full stop — including ones no hold was ever recorded for, which is exactly the
     * situation that arises when the record was lost.
     *
     * Order is preserved and duplicates are impossible: the system setting is a plain
     * colon-joined list and a repeated component would be written back verbatim.
     */
    fun enable(
        wanted: List<String>,
        currentlyEnabled: List<String>,
    ): List<String> {
        val enabled = currentlyEnabled.toSet()

        return currentlyEnabled + wanted.distinct().filterNot { it in enabled }
    }

    /**
     * [currentlyEnabled] with [unwanted] taken out, order otherwise untouched.
     *
     * The mirror of [enable], for the manager dialog's off switch. Same rule as everywhere
     * else here: only the components this app is responsible for are removed, so a service
     * the user turned on themselves is never swept up by switching the app's own set off.
     */
    fun disable(
        unwanted: List<String>,
        currentlyEnabled: List<String>,
    ): List<String> {
        val remove = unwanted.toSet()

        return currentlyEnabled.filterNot { it in remove }
    }

    /**
     * Whether every one of [wanted] is currently on.
     *
     * All of them, not any: the dialog's accessibility row stands for a set, and a row that
     * reads "on" while two of five services are off would be a lie in the direction that
     * matters — the user would believe the device was back to normal when it was not.
     *
     * An empty [wanted] is reported as on. Nothing is being held down, so there is nothing
     * for the switch to put back, and showing it off would invite a press that does nothing.
     */
    fun allEnabled(
        wanted: List<String>,
        currentlyEnabled: List<String>,
    ): Boolean {
        if (wanted.isEmpty()) return true

        val enabled = currentlyEnabled.toSet()

        return wanted.distinct().all { it in enabled }
    }

    /** Everything held by apps other than [exceptComponentName]. */
    fun heldByOthers(
        held: Map<String, List<String>>,
        exceptComponentName: String,
    ): List<String> = held.entries
        .filter { it.key != exceptComponentName }
        .flatMap { it.value }
        .distinct()

    /** Drops empty entries so a reverted app leaves no residue in the record. */
    fun withHold(
        held: Map<String, List<String>>,
        componentName: String,
        services: List<String>,
    ): Map<String, List<String>> = if (services.isEmpty()) {
        held - componentName
    } else {
        held + (componentName to services.distinct())
    }

    /**
     * The record is stored as a proto map of strings, so each app's list is flattened with
     * the same separator the system setting itself uses.
     */
    fun encode(services: List<String>): String = services.joinToString(SEPARATOR)

    fun decode(value: String): List<String> = value.split(SEPARATOR).filter { it.isNotBlank() }
}
