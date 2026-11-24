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

private const val ON = "1"

private const val OFF = "0"

/**
 * What "on" is written as for [ManualRevertTarget.Location].
 *
 * 3 is Android's `LOCATION_MODE_HIGH_ACCURACY`: GPS, network and sensors together, which is
 * what the system's own toggle is on and what an app asking for a location is asking for. 1
 * and 2 are the battery-saving modes and are written by the system itself when a saver turns
 * them on; IMD only ever needs the fully-on value, and 0 to turn it off again.
 */
private const val LOCATION_MODE_ON = "3"

/**
 * Something the user can put back by hand from the Favourites tab.
 *
 * The ongoing notification is the normal way back, but it can be swiped away, and on some
 * devices it is culled by the launcher or a battery optimiser. Without this the only
 * remaining route is Android's own developer-options screen, which is exactly the screen
 * that is switched off.
 *
 * [settingKey] is the Settings row this target stands for, and [settingType], [valueOn] and
 * [valueOff] are how it is written. Targets that are not a single settings row carry a null
 * key and are handled specifically.
 *
 * ⚠ **The value pair is not decoration.** Every row this app managed until Location was a
 * flag in the Global table, so "on" was "1" and "off" was "0" and both could be written
 * literally. Location is a **mode** in the Secure table: 0 is off and any non-zero value is
 * on, with 3 meaning on at full accuracy. Writing "1" there would be setting the mode to
 * "sensors only", and reading `== "1"` would report a perfectly working GPS as off.
 */
enum class ManualRevertTarget(
    val settingKey: String?,
    val settingType: SettingType = SettingType.GLOBAL,
    val valueOn: String = ON,
    val valueOff: String = OFF,
) {
    DeveloperSettings(AppSettingKeys.DEVELOPMENT_SETTINGS_ENABLED),
    UsbDebugging(AppSettingKeys.ADB_ENABLED),
    WirelessDebugging(AppSettingKeys.ADB_WIFI_ENABLED),
    AccessibilityServices(null),
    Shizuku(null),
    DisplayOverOtherApps(null),

    /**
     * Location services.
     *
     * ⚠ **The one row whose useful direction is on.** Every other target exists to be switched
     * off while a restrictive app is in front, and the settings manager switches it back on.
     * Location is the reverse: plenty of apps refuse to work without it, and the user's normal
     * state is off. So it is managed as an ordinary row — live state, one switch, an arrow out to
     * Android's own screen — and its "Revert to default" state is **off**, which is what makes a
     * revert (or auto unhide, or the end of a session) put location back the way it was found
     * rather than leaving it on for ever.
     *
     * ⚠ **Ticked in [SettingsToHide] to switch it ON, and that is the whole of the design.** A hide
     * drives every target it names to [stateWhileHidden], which for this row is true: the row
     * exists for the length of a session, and the session starts when one of the user's apps is
     * opened through IMD. Unticked, nothing touches location at all — on a fresh install and on an
     * upgrade, which is what keeps a privileged change out of an install nobody configured.
     */
    Location(
        settingKey = AppSettingKeys.LOCATION_MODE,
        settingType = SettingType.SECURE,
        valueOn = LOCATION_MODE_ON,
        valueOff = OFF,
    ),
    ;

    /**
     * The Global settings row behind this target, or null when it is not one.
     *
     * Kept as the question the revert's own bookkeeping asks — which settings a configured
     * default can drive, and which a per-app record has to carry itself. Location is answered
     * null by it despite having a key, because every one of those callers assumes the Global
     * table and the "1"/"0" pair; a target that is neither is a target they have to be told
     * about rather than one they can derive.
     */
    val globalSettingKey: String?
        get() = settingKey.takeIf { settingType == SettingType.GLOBAL }

    /**
     * The state a **hide** drives this target to.
     *
     * Off for every row but one, because a hide is what makes a device uninteresting to a
     * restrictive app: developer options, debugging, accessibility services, Shizuku and
     * overlay access all go away on the way in.
     *
     * ⚠ **Location goes the other way, and this property is what makes that one fact rather
     * than a special case in three loops.** Those apps object to debugging surfaces and to
     * nothing else; a great many of them refuse to run without a position, which is why the
     * author asked for location to come on when one of his selected apps opens and go off when
     * it closes. So the row's *hidden* state is **on**: ticking it in Settings to hide means
     * "location on while an app is in front", the revert puts it back to the value measured
     * before the hide, and a user who never ticks it keeps location exactly as they left it.
     */
    val stateWhileHidden: Boolean
        get() = this == Location

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
 * ⚠ **Location last on the way on and therefore first on the way off**, and it is the one
 * member of this list with no dependency on any other. It is put at the end because every other
 * position in this list is a claim about ordering and location has no claim to make: nothing
 * disturbs it and it disturbs nothing. Read backwards that makes it the first thing switched
 * off when a session ends, which is also the harmless end to be wrong at.
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
    ManualRevertTarget.Location,
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
