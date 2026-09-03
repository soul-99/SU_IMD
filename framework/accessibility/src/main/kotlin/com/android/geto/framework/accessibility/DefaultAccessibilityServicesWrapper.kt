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
package com.android.geto.framework.accessibility

import android.accessibilityservice.AccessibilityServiceInfo
import android.content.ComponentName
import android.content.Context
import android.provider.Settings
import android.view.accessibility.AccessibilityManager
import com.android.geto.common.AutoHideDetection
import com.android.geto.domain.common.dispatcher.Dispatcher
import com.android.geto.domain.common.dispatcher.GetoDispatchers.IO
import com.android.geto.domain.framework.AccessibilityServicesWrapper
import com.android.geto.domain.model.AccessibilityServiceData
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.withContext
import javax.inject.Inject

private const val SERVICES_SEPARATOR = ":"

internal class DefaultAccessibilityServicesWrapper @Inject constructor(
    @param:Dispatcher(IO) private val ioDispatcher: CoroutineDispatcher,
    @param:ApplicationContext private val context: Context,
) : AccessibilityServicesWrapper {

    private val contentResolver = context.contentResolver

    private val accessibilityManager
        get() = context.getSystemService(Context.ACCESSIBILITY_SERVICE) as AccessibilityManager

    override suspend fun getAccessibilityServices(): List<AccessibilityServiceData> = withContext(ioDispatcher) {
        val enabled = readEnabledComponents().toSet()

        val packageManager = context.packageManager

        val installed = runCatching {
            accessibilityManager.installedAccessibilityServiceList
        }.getOrDefault(emptyList())

        val services = installed.mapNotNull { serviceInfo ->
            val resolveInfo = serviceInfo.resolveInfo ?: return@mapNotNull null

            val componentName = ComponentName(
                resolveInfo.serviceInfo.packageName,
                resolveInfo.serviceInfo.name,
            )

            AccessibilityServiceData(
                id = componentName.flattenToString(),
                packageName = componentName.packageName,
                label = runCatching {
                    resolveInfo.loadLabel(packageManager).toString()
                }.getOrDefault(componentName.className.substringAfterLast('.')),
                enabled = componentName in enabled,
            )
        }

        val known = services.map { it.id }.toSet()

        // A service can sit in the enabled list after its app is gone. Surfacing it
        // rather than hiding it is the only way the user can clear it out.
        val orphans = enabled.filterNot { it.flattenToString() in known }.map {
            AccessibilityServiceData(
                id = it.flattenToString(),
                packageName = it.packageName,
                label = it.className.substringAfterLast('.'),
                enabled = true,
            )
        }

        services + orphans
    }

    override suspend fun getEnabledAccessibilityServices(): List<String> = withContext(ioDispatcher) {
        readEnabledComponents().map { it.flattenToString() }
    }

    override suspend fun setEnabledAccessibilityServices(components: List<String>): Boolean = withContext(ioDispatcher) {
        val normalised = components.mapNotNull { ComponentName.unflattenFromString(it) }
            .distinct()
            .joinToString(SERVICES_SEPARATOR) { it.flattenToString() }

        val wroteServices = Settings.Secure.putString(
            contentResolver,
            Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES,
            normalised,
        )

        // The framework keys off both values. Leaving accessibility_enabled at 1 with an
        // empty list, or at 0 with a populated one, produces a state the Settings app
        // itself renders inconsistently.
        val wroteMasterFlag = Settings.Secure.putString(
            contentResolver,
            Settings.Secure.ACCESSIBILITY_ENABLED,
            if (normalised.isEmpty()) "0" else "1",
        )

        wroteServices && wroteMasterFlag
    }

    override fun autoHideServiceComponent(): String = ComponentName(
        context.packageName,
        AutoHideDetection.SERVICE_CLASS_NAME,
    ).flattenToString()

    override suspend fun isAutoHideServiceRunning(): Boolean = withContext(ioDispatcher) {
        val component = ComponentName(context.packageName, AutoHideDetection.SERVICE_CLASS_NAME)

        // The system's list of services it has actually bound, not the setting that asks for
        // them. On Android 13+ a sideloaded service can be in the setting and never bound.
        val bound = runCatching {
            accessibilityManager.getEnabledAccessibilityServiceList(
                AccessibilityServiceInfo.FEEDBACK_ALL_MASK,
            )
        }.getOrNull().orEmpty().any {
            it.resolveInfo?.serviceInfo?.let { info ->
                info.packageName == component.packageName && info.name == component.className
            } == true
        }

        // The service's own report is the tie-breaker rather than the answer. The manager's
        // list is authoritative but can lag a bind by a moment, and this is polled straight
        // after asking for one — so a service that has already said "connected" counts.
        bound || AutoHideDetection.isRunning
    }

    /**
     * The stored value mixes short ("pkg/.Service") and long ("pkg/pkg.Service") forms
     * depending on who wrote it, so everything is unflattened before it is compared.
     */
    private fun readEnabledComponents(): List<ComponentName> {
        val raw = Settings.Secure.getString(
            contentResolver,
            Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES,
        ).orEmpty()

        return raw.split(SERVICES_SEPARATOR)
            .filter { it.isNotBlank() }
            .mapNotNull { ComponentName.unflattenFromString(it.trim()) }
            .distinct()
    }
}
