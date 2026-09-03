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
package com.android.geto.framework.securesettings

import android.content.Context
import android.provider.Settings
import androidx.core.database.getLongOrNull
import androidx.core.database.getStringOrNull
import com.android.geto.domain.common.Diagnostics
import com.android.geto.domain.common.dispatcher.Dispatcher
import com.android.geto.domain.common.dispatcher.GetoDispatchers.IO
import com.android.geto.domain.framework.SecureSettingsWrapper
import com.android.geto.domain.model.SecureSetting
import com.android.geto.domain.model.SettingType
import com.android.geto.domain.model.SettingType.GLOBAL
import com.android.geto.domain.model.SettingType.SECURE
import com.android.geto.domain.model.SettingType.SYSTEM
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.withContext
import javax.inject.Inject

internal class DefaultSecureSettingsWrapper @Inject constructor(
    @param:Dispatcher(IO) private val ioDispatcher: CoroutineDispatcher,
    @param:ApplicationContext private val context: Context,
    private val writeSecureSettingsMonitor: WriteSecureSettingsMonitor,
) : SecureSettingsWrapper {

    private val contentResolver = context.contentResolver

    private val settingsProjection: Array<String> = arrayOf(
        Settings.NameValueTable._ID,
        Settings.NameValueTable.NAME,
        Settings.NameValueTable.VALUE,
    )

    // A synchronous PackageManager check behind a suspend signature, which the interface needs
    // because nothing else about this wrapper can be answered without leaving the caller's
    // thread. Cheap enough to ask at the top of every hide.
    override suspend fun hasWriteSecureSettingsPermission(): Boolean =
        writeSecureSettingsMonitor.hasPermission()

    override suspend fun canWriteSecureSettings(
        settingType: SettingType,
        key: String,
        value: String,
    ): Boolean = withContext(ioDispatcher) {
        // Every write in the app comes through here, which makes it the one place that can
        // notice the WRITE_SECURE_SETTINGS grant having gone away. Rethrown either way, so
        // the use cases still map it to AppSettingsResult.NoPermission exactly as before —
        // this only adds the reaction, it does not swallow the failure.
        try {
            // Bound to a name rather than left as the last expression, because it *is* the
            // return value - putString reports whether the row was written, and this whole
            // function is that Boolean. Logging after it without holding on to it made the
            // try block evaluate to Unit, which is exactly how this failed to compile once.
            val written = when (settingType) {
                SYSTEM -> Settings.System.putString(
                    contentResolver,
                    key,
                    value,
                )

                SECURE -> Settings.Secure.putString(
                    contentResolver,
                    key,
                    value,
                )

                GLOBAL -> Settings.Global.putString(
                    contentResolver,
                    key,
                    value,
                )
            }

            // The most useful line the diagnostic log carries, and the reason it is here
            // rather than in the use cases: they can say a hide failed, only this can say
            // which key it failed on. It reports what putString actually returned, so a
            // write that was refused outright and one that quietly did nothing read
            // differently in the log.
            Diagnostics.log(
                tag = "write",
                message = "$settingType.$key = $value -> " + if (written) "ok" else "not written",
            )

            written
        } catch (securityException: SecurityException) {
            // Before the rethrow, so the line exists whatever the use case above decides to
            // do with the exception - and so a run that ends in NoPermission names the key
            // it died on rather than only the fact that it died.
            Diagnostics.log(tag = "write", message = "$settingType.$key = $value -> refused")

            writeSecureSettingsMonitor.onWriteRefused()

            throw securityException
        }
    }

    override suspend fun getSecureSettingValue(
        settingType: SettingType,
        key: String,
    ): String? = withContext(ioDispatcher) {
        // Deliberately not getSecureSettings().find { }: that queries the whole table
        // through a cursor, and this runs once per setting every time a profile is applied.
        runCatching {
            when (settingType) {
                SYSTEM -> Settings.System.getString(contentResolver, key)
                SECURE -> Settings.Secure.getString(contentResolver, key)
                GLOBAL -> Settings.Global.getString(contentResolver, key)
            }
        }.getOrNull()
    }

    override suspend fun getSecureSettings(settingType: SettingType): List<SecureSetting> = withContext(ioDispatcher) {
        val cursor = when (settingType) {
            SYSTEM -> contentResolver.query(
                Settings.System.CONTENT_URI,
                settingsProjection,
                null,
                null,
                null,
            )

            SECURE -> contentResolver.query(
                Settings.Secure.CONTENT_URI,
                settingsProjection,
                null,
                null,
                null,
            )

            GLOBAL -> contentResolver.query(
                Settings.Global.CONTENT_URI,
                settingsProjection,
                null,
                null,
                null,
            )
        }

        cursor?.use {
            generateSequence { if (cursor.moveToNext()) cursor else null }.map {
                val idIndex =
                    cursor.getColumnIndex(Settings.NameValueTable._ID).takeIf { it != -1 }
                val nameIndex =
                    cursor.getColumnIndex(Settings.NameValueTable.NAME).takeIf { it != -1 }
                val valueIndex =
                    cursor.getColumnIndex(Settings.NameValueTable.VALUE).takeIf { it != -1 }

                val id = idIndex?.let { cursor.getLongOrNull(it) }
                val name = nameIndex?.let { cursor.getStringOrNull(it) }
                val value = valueIndex?.let { cursor.getStringOrNull(it) }

                SecureSetting(
                    settingType = settingType,
                    id = id,
                    name = name,
                    value = value,
                )
            }.sortedBy { it.name }.toList()
        } ?: emptyList()
    }
}
