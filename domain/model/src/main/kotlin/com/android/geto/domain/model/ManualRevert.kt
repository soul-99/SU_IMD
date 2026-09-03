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
 * Something the user can put back by hand from the Favourites tab.
 *
 * The ongoing notification is the normal way back, but it can be swiped away, and on some
 * devices it is culled by the launcher or a battery optimiser. Without this the only
 * remaining route is Android's own developer-options screen, which is exactly the screen
 * that is switched off.
 *
 * [globalSettingKey] is the Global setting written back to "1"; targets that are
 * not a single settings row carry null and are handled specifically.
 */
enum class ManualRevertTarget(val globalSettingKey: String?) {
    DeveloperSettings(AppSettingKeys.DEVELOPMENT_SETTINGS_ENABLED),
    UsbDebugging(AppSettingKeys.ADB_ENABLED),
    WirelessDebugging(AppSettingKeys.ADB_WIFI_ENABLED),
    AccessibilityServices(null),
    Shizuku(null),
    DisplayOverOtherApps(null),
    ;

    companion object {
        /**
         * What the dialog starts out with. All of them: the situation this exists for is
         * "the notification is gone and I do not know what is still switched off", and
         * putting everything back is both safe and what was wanted.
         *
         * This is also what an empty stored selection falls back to. Storing "nothing
         * ticked" is not worth distinguishing from "never opened" — with nothing ticked
         * the Revert button does nothing anyway.
         */
        val Default: Set<ManualRevertTarget> = entries.toSet()

        fun encode(targets: Set<ManualRevertTarget>): List<String> =
            entries.filter { it in targets }.map { it.name }

        /** Unknown names are dropped, so a downgrade cannot poison the stored set. */
        fun decode(names: List<String>): Set<ManualRevertTarget> {
            val byName = entries.associateBy { it.name }

            val decoded = names.mapNotNull { byName[it] }.toSet()

            return decoded.ifEmpty { Default }
        }
    }
}

/**
 * Per-target outcome, so the user is told which parts of a multi-target revert did not
 * take rather than a flat "failed".
 */
data class ManualRevertResult(
    val reverted: Set<ManualRevertTarget> = emptySet(),
    val failed: Set<ManualRevertTarget> = emptySet(),
    val noPermission: Boolean = false,
) {
    val isSuccess: Boolean get() = !noPermission && failed.isEmpty() && reverted.isNotEmpty()

    val isEmpty: Boolean get() = !noPermission && failed.isEmpty() && reverted.isEmpty()
}

/**
 * The order the settings manager's master pill switches targets **on** in; off is the exact
 * reverse.
 *
 * ⚠ **Not [ManualRevertTarget.entries], and the difference is a dependency graph rather than a
 * preference:**
 *
 *  * developer options first, because USB debugging depends on it;
 *  * Shizuku before Display over other apps, whose AppOps can only be written while Shizuku is
 *    running;
 *  * wireless debugging **last**, because starting a Shizuku fork brings the debugging
 *    transport up using its own WRITE_SECURE_SETTINGS and moves wireless debugging on the way.
 *    Settled any earlier, the fork overrules the press.
 *
 * Reversed on the way off, which puts Display over other apps before Shizuku stops and leaves
 * developer options until last — the same three reasons read backwards.
 *
 * Lives here rather than in the ViewModel that uses it so the host tests can assert it still
 * covers every target: a seventh one added later would otherwise be silently skipped by the
 * pill, with nothing in the audit suite able to see it.
 */
val masterPillOnOrder: List<ManualRevertTarget> = listOf(
    ManualRevertTarget.DeveloperSettings,
    ManualRevertTarget.UsbDebugging,
    ManualRevertTarget.AccessibilityServices,
    ManualRevertTarget.Shizuku,
    ManualRevertTarget.DisplayOverOtherApps,
    ManualRevertTarget.WirelessDebugging,
)

/**
 * The targets the master pill should move, in the order it should move them.
 *
 * [usable] is the dialog's own per-row test, handed over rather than recomputed — the pill's
 * promise is that it moves exactly the rows the user could have moved by hand.
 */
fun masterPillOrder(
    enabled: Boolean,
    usable: List<ManualRevertTarget>,
): List<ManualRevertTarget> = masterPillOnOrder.filter { it in usable }.let {
    if (enabled) it else it.reversed()
}
