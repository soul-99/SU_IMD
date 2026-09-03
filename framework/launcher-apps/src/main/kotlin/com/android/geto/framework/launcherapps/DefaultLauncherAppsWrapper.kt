/*
 *
 *   Copyright 2023 Einstein Blanco
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
package com.android.geto.framework.launcherapps

import android.content.ActivityNotFoundException
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.pm.LauncherActivityInfo
import android.content.pm.LauncherApps
import android.os.Handler
import android.os.Looper
import android.os.Process.myUserHandle
import android.os.UserHandle
import com.android.geto.domain.common.IconStyleState
import com.android.geto.domain.common.dispatcher.Dispatcher
import com.android.geto.domain.common.dispatcher.GetoDispatchers.Default
import com.android.geto.domain.framework.LauncherAppsWrapper
import com.android.geto.domain.framework.PackageManagerWrapper
import com.android.geto.domain.model.LauncherAppsActivityInfo
import com.android.geto.framework.drawable.AndroidDrawableWrapper
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.drop
import kotlinx.coroutines.flow.flowOn
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.launch
import java.util.concurrent.ConcurrentHashMap
import javax.inject.Inject

internal class DefaultLauncherAppsWrapper @Inject constructor(
    @param:Dispatcher(Default) private val defaultDispatcher: CoroutineDispatcher,
    @param:ApplicationContext private val context: Context,
    private val androidDrawableWrapper: AndroidDrawableWrapper,
    private val packageManagerWrapper: PackageManagerWrapper,
) : LauncherAppsWrapper,
    AndroidLauncherAppsWrapper {
    private val launcherApps =
        context.getSystemService(Context.LAUNCHER_APPS_SERVICE) as LauncherApps

    /**
     * Rendered icons, keyed by component name and the package's last update time.
     *
     * Rasterising an icon means loading the drawable, drawing two layers, masking and
     * PNG-encoding it. The list is rebuilt on every package added / removed / changed /
     * available / unavailable callback, and `onPackageChanged` fires for routine things
     * like an app being enabled or its components toggled — so without this, a few hundred
     * icons were re-rendered for a change to one of them.
     *
     * Replaced wholesale on each rebuild rather than added to, so uninstalled apps do not
     * accumulate: the map is never larger than the current launcher list.
     */
    private val iconCache = ConcurrentHashMap<String, ByteArray>()

    override fun getActivityListFlow(): Flow<List<LauncherAppsActivityInfo>> = callbackFlow {
        suspend fun getActivityList() {
            // Fetched once for the whole list rather than per app: this used to be a
            // binder round trip inside the map below, so a device with a few hundred
            // launcher entries paid a few hundred IPCs before the list could appear.
            val lastUpdateTimes = packageManagerWrapper.getLastInstallTimes()

            val icons = HashMap<String, ByteArray>()

            val activities =
                launcherApps.getActivityList(null, myUserHandle()).map { launcherActivityInfo ->
                    currentCoroutineContext().ensureActive()

                    val key = launcherActivityInfo.iconKey(lastUpdateTimes)

                    val icon = iconCache[key]
                        ?: androidDrawableWrapper.toByteArray(launcherActivityInfo.getIcon(0))

                    icons[key] = icon

                    launcherActivityInfo.toLauncherAppsActivityInfo(lastUpdateTimes, icon)
                }

            // Pruned to what is installed now, then refilled: the favourites path adds
            // entries of its own, so the map cannot simply be replaced.
            iconCache.keys.retainAll(icons.keys)

            iconCache.putAll(icons)

            trySend(activities)
        }

        getActivityList()

        // ⚠ **The Icon style changed, so every cached picture is wrong.** The cache above is
        // keyed by component name and package update time — the right key for the package
        // events this flow was built to survive, and blind to this one, because changing a style
        // changes no package's update time. Clearing it is what makes the rebuild produce
        // different bytes rather than handing back the same ones.
        //
        // drop(1) discards the value every new collector is replayed: at this point it means
        // "nothing has changed yet", and acting on it would rebuild the list a second time for
        // no reason on every subscription.
        launch {
            IconStyleState.revision.drop(1).collect {
                iconCache.clear()

                getActivityList()
            }
        }

        val callback = object : LauncherApps.Callback() {

            override fun onPackageAdded(
                packageName: String?,
                user: UserHandle?,
            ) {
                launch {
                    getActivityList()
                }
            }

            override fun onPackageRemoved(
                packageName: String?,
                user: UserHandle?,
            ) {
                launch {
                    getActivityList()
                }
            }

            override fun onPackageChanged(
                packageName: String?,
                user: UserHandle?,
            ) {
                launch {
                    getActivityList()
                }
            }

            override fun onPackagesAvailable(
                packageNames: Array<out String>?,
                user: UserHandle?,
                replacing: Boolean,
            ) {
                launch {
                    getActivityList()
                }
            }

            override fun onPackagesUnavailable(
                packageNames: Array<out String>?,
                user: UserHandle?,
                replacing: Boolean,
            ) {
                launch {
                    getActivityList()
                }
            }
        }

        launcherApps.registerCallback(
            callback,
            Handler(Looper.getMainLooper()),
        )

        awaitClose {
            launcherApps.unregisterCallback(callback)
        }
    }.distinctUntilChanged().flowOn(defaultDispatcher)

    /**
     * Component, update time **and Icon style**: those are the three things that change an icon.
     *
     * ⚠ The style was missing until r4y, and the collector below cleared the whole cache to work
     * around it. The clear stays — it frees the bytes of a style nobody is looking at any more —
     * but this is what makes the key correct rather than merely emptied at the right moment.
     */
    private fun LauncherActivityInfo.iconKey(lastUpdateTimes: Map<String, Long>): String =
        componentName.flattenToString() + "@" +
            (lastUpdateTimes[applicationInfo.packageName] ?: 0L) + "@" +
            IconStyleState.revision.value

    private fun LauncherActivityInfo.toLauncherAppsActivityInfo(
        lastUpdateTimes: Map<String, Long>,
        icon: ByteArray,
    ): LauncherAppsActivityInfo = LauncherAppsActivityInfo(
        componentName = componentName.flattenToString(),
        packageName = applicationInfo.packageName,
        activityIcon = icon,
        activityLabel = label.toString(),
        firstInstallTime = firstInstallTime,
        lastUpdateTime = lastUpdateTimes[applicationInfo.packageName] ?: 0L,
        isSystem = packageManagerWrapper.isSystem(flags = applicationInfo.flags),
        // Read at render time, so the value travels with the picture it describes.
        iconRevision = IconStyleState.revision.value,
    )

    override fun getActivityInfosFlow(
        componentNames: Flow<List<String>>,
    ): Flow<List<LauncherAppsActivityInfo>> = combine(
        componentNames.distinctUntilChanged(),
        packageChanges(),
    ) { names, _ ->
        names
    }.map { names ->
        resolveActivityInfos(componentNames = names)
    }.distinctUntilChanged().flowOn(defaultDispatcher)

    /** Emits once immediately, then again whenever a package on the device changes. */
    private fun packageChanges(): Flow<Unit> = callbackFlow {
        trySend(Unit)

        val callback = object : LauncherApps.Callback() {
            override fun onPackageAdded(packageName: String?, user: UserHandle?) {
                trySend(Unit)
            }

            override fun onPackageRemoved(packageName: String?, user: UserHandle?) {
                trySend(Unit)
            }

            override fun onPackageChanged(packageName: String?, user: UserHandle?) {
                trySend(Unit)
            }

            override fun onPackagesAvailable(
                packageNames: Array<out String>?,
                user: UserHandle?,
                replacing: Boolean,
            ) {
                trySend(Unit)
            }

            override fun onPackagesUnavailable(
                packageNames: Array<out String>?,
                user: UserHandle?,
                replacing: Boolean,
            ) {
                trySend(Unit)
            }
        }

        launcherApps.registerCallback(callback, Handler(Looper.getMainLooper()))

        awaitClose { launcherApps.unregisterCallback(callback) }
    }

    /**
     * One `getActivityList(packageName, user)` per favourite rather than one call for the
     * whole device. A component that no longer resolves is dropped — an uninstalled
     * favourite should disappear from the tab rather than show as a dead tile — but its
     * stored entry is kept elsewhere, so an app that is merely unavailable right now comes
     * back on its own.
     */
    private suspend fun resolveActivityInfos(
        componentNames: List<String>,
    ): List<LauncherAppsActivityInfo> {
        if (componentNames.isEmpty()) return emptyList()

        val lastUpdateTimes = packageManagerWrapper.getLastInstallTimes()

        return componentNames.mapNotNull { flattened ->
            currentCoroutineContext().ensureActive()

            val component = ComponentName.unflattenFromString(flattened) ?: return@mapNotNull null

            val info = runCatching {
                launcherApps.getActivityList(component.packageName, myUserHandle())
                    .firstOrNull { it.componentName == component }
            }.getOrNull() ?: return@mapNotNull null

            val key = info.iconKey(lastUpdateTimes)

            val icon = iconCache[key]
                ?: androidDrawableWrapper.toByteArray(info.getIcon(0))
                    .also { iconCache[key] = it }

            info.toLauncherAppsActivityInfo(lastUpdateTimes, icon)
        }
    }

    override fun startMainActivity(componentName: String) {
        // Tap-to-launch is the default gesture on the Favourites tab, so this runs against
        // a component that may have been uninstalled between the list emission and the
        // tap. ActivityNotFoundException is as likely here as SecurityException, and
        // neither is worth crashing over.
        try {
            launcherApps.startMainActivity(
                ComponentName.unflattenFromString(componentName),
                myUserHandle(),
                null,
                null,
            )
        } catch (e: SecurityException) {
            e.printStackTrace()
        } catch (e: ActivityNotFoundException) {
            e.printStackTrace()
        } catch (e: IllegalArgumentException) {
            e.printStackTrace()
        }
    }

    /**
     * The launcher's own entry for the package, and the package manager's answer if it has
     * none that LauncherApps will admit to.
     *
     * Two routes because they fail on different devices. LauncherApps is the right one — it is
     * profile-aware and it is what the rest of this class uses — but it lists only apps with a
     * launcher category, and an app that IMD+ was asked to watch may have been started some
     * other way. The launch intent covers that case, and it is also what every launcher on the
     * device would do.
     */
    override fun startPackage(packageName: String): Boolean {
        val component = runCatching {
            launcherApps.getActivityList(packageName, myUserHandle()).firstOrNull()?.componentName
        }.getOrNull()

        if (component != null) {
            val started = runCatching {
                launcherApps.startMainActivity(component, myUserHandle(), null, null)
            }.isSuccess

            if (started) return true
        }

        val intent = runCatching {
            context.packageManager.getLaunchIntentForPackage(packageName)
        }.getOrNull() ?: return false

        // NEW_TASK because this can be started from a context that is not an activity — the
        // app has just been force-stopped and the window IMD+ was standing in may be gone.
        return runCatching {
            context.startActivity(intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
        }.isSuccess
    }
}
