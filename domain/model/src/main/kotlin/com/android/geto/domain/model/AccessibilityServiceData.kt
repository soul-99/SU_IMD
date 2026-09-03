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
 * One accessibility service installed on the device.
 *
 * [id] is the flattened component name ("pkg/com.example.MyService") exactly as it
 * appears in Settings.Secure.enabled_accessibility_services, and is the only value
 * ever persisted. Labels are resolved fresh each time so a renamed or updated app
 * never leaves a stale entry behind.
 */
data class AccessibilityServiceData(
    val id: String,
    val packageName: String,
    val label: String,
    val enabled: Boolean,
    /**
     * The owning app's icon, or null when it has none, could not be decoded, or was not asked
     * for — an orphan row whose app is gone has no icon and is still worth showing.
     */
    val icon: ByteArray? = null,
) {
    // ⚠ **ByteArray compares by identity**, so a data-class equals holding one would report a
    // change on every re-read of this list and re-render the picker under the user's finger.
    // The same fix InstalledAppData already carries.
    //
    // `enabled` stays in: it is what the row's supporting line reports, so a service being
    // switched off has to read as a change. Only the bytes are left out, and only because they
    // cannot compare.
    override fun equals(other: Any?): Boolean = this === other ||
        (
            other is AccessibilityServiceData &&
                id == other.id &&
                packageName == other.packageName &&
                label == other.label &&
                enabled == other.enabled
            )

    override fun hashCode(): Int {
        var result = id.hashCode()

        result = 31 * result + packageName.hashCode()

        result = 31 * result + label.hashCode()

        result = 31 * result + enabled.hashCode()

        return result
    }
}

/**
 * Which services the "Accessibility services to hide" picker should list.
 *
 * The author's rule for v3 is "only show the enabled ones", and taken literally that has a bug
 * in it: **a service IMD has switched off is no longer enabled**, so during the very hide the
 * picker exists to configure, every service it manages would vanish from the list. Someone
 * opening it mid-hide would see an empty page and reasonably conclude their configuration had
 * been lost — which this project has already been bitten by once, with the IMD+ row that looked
 * absent until a clear-data.
 *
 * So the rule is enabled **or** currently held down by IMD. Everything IMD turned off is
 * something it owes back, which is exactly what the first line of the dialog now promises, and
 * a promise about services you cannot see is worth nothing.
 *
 * ⚠ **Or selected**, which closes the hole the two above leave between them. "Held" only covers a
 * service IMD switched off *and still has a record of*. A service the user switched off in the
 * system settings themselves, or one whose record was discarded, is selected, off and unheld —
 * and vanishes from the picker for as long as that lasts, taking with it the only control that
 * could unselect it. The selection is the user's own answer and is always worth showing; the
 * `enabled` flag on the row goes on telling the truth about the device.
 *
 * [ownDetector] is kept whatever its state: it is drawn ticked and unclickable while IMD+ is on,
 * and it explains itself there. Blank when IMD+ is off, which matches nothing and drops it.
 *
 * Order is preserved, so the caller's sort survives.
 */
fun accessibilityServicesForPicker(
    services: List<AccessibilityServiceData>,
    heldAccessibilityServices: Map<String, List<String>>,
    ownDetector: String = "",
    managedAccessibilityServices: List<String> = emptyList(),
): List<AccessibilityServiceData> {
    val held = heldAccessibilityServices.values.flatten().toSet()

    val selected = managedAccessibilityServices.toSet()

    return services.filter { service ->
        service.enabled ||
            service.id in held ||
            service.id in selected ||
            (ownDetector.isNotBlank() && service.id == ownDetector)
    }
}
