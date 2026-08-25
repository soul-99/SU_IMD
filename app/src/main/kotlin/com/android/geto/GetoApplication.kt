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
package com.android.geto

import android.app.Application
import android.app.NotificationManager
import android.content.Context
import android.os.Build
import com.android.geto.common.AppLocale
import com.android.geto.common.ApplicationScope
import com.android.geto.domain.usecase.DetectShizukuForkUseCase
import com.android.geto.domain.usecase.MigrateNotificationFunctionUseCase
import com.android.geto.domain.usecase.MigrateRevertDefaultsUseCase
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper
import dagger.hilt.android.HiltAndroidApp
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltAndroidApp
class GetoApplication : Application() {
    @Inject
    lateinit var notificationManagerWrapper: AndroidNotificationManagerWrapper

    @Inject
    lateinit var migrateNotificationFunctionUseCase: MigrateNotificationFunctionUseCase

    @Inject
    lateinit var migrateRevertDefaultsUseCase: MigrateRevertDefaultsUseCase

    @Inject
    lateinit var detectShizukuForkUseCase: DetectShizukuForkUseCase

    @Inject
    @ApplicationScope
    lateinit var appScope: CoroutineScope

    // Wrapping here is what puts the chosen language on the application context, which is
    // the context Hilt injects everywhere and the one every notification is built from.
    // A no-op on Android 13 and up, where the platform applies it before the process starts.
    override fun attachBaseContext(base: Context) {
        super.attachBaseContext(AppLocale.wrap(base))
    }

    override fun onCreate() {
        super.onCreate()

        // Here rather than in MainActivity, because most of what this app does happens
        // with the app not open: a Quick Settings tile, a pinned shortcut and a notification
        // action all run in this process without any activity being created. Migrating on
        // first launch of the UI would leave those reading the old preference for as long as
        // the user never opened the app.
        appScope.launch { migrateNotificationFunctionUseCase() }

        // Same reasoning as above, and the same reason it cannot wait for the UI: a tile or
        // a shortcut can fire a Revert in this process without an activity ever existing,
        // and that Revert must already be reading the narrowed configuration.
        appScope.launch { migrateRevertDefaultsUseCase() }

        // Only writes when nobody has chosen a fork family yet, so it fills in a fresh
        // install and leaves every other one alone. Here rather than on the settings
        // screen because the guess should already be made by the time somebody opens it.
        appScope.launch { detectShizukuForkUseCase() }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            notificationManagerWrapper.createNotificationChannel(
                channelId = AndroidNotificationManagerWrapper.NOTIFICATION_CHANNEL_ID,
                name = getString(R.string.app_name),
                importance = NotificationManager.IMPORTANCE_DEFAULT,
            )
        }
    }
}
