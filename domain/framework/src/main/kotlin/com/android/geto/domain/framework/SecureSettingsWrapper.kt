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
package com.android.geto.domain.framework

import com.android.geto.domain.model.SecureSetting
import com.android.geto.domain.model.SettingType

interface SecureSettingsWrapper {
    suspend fun canWriteSecureSettings(
        settingType: SettingType,
        key: String,
        value: String,
    ): Boolean

    /**
     * Whether `WRITE_SECURE_SETTINGS` is still granted — asked *before* a hide, not after it.
     *
     * The grant is given once over adb and can be taken away again: by hand, or by Android's
     * own automatic revocation of permissions belonging to an app nobody has opened for
     * months. Without it every write in this app fails, and it fails in the least legible way
     * possible — a settings row that will not move, with nothing saying why.
     *
     * **Asked first because it makes the answer free.** The permission that switches a setting
     * off is the same one needed to switch it back on, so a hide that discovers the loss
     * halfway has, by definition, hidden nothing through it — but it may already have withdrawn
     * Display over other apps through Shizuku, which does not use this permission at all. Asking
     * up front means the usual case never reaches that state and has nothing to undo.
     */
    suspend fun hasWriteSecureSettingsPermission(): Boolean

    suspend fun getSecureSettings(settingType: SettingType): List<SecureSetting>

    /**
     * The current value of one setting, or null when it has never been written.
     *
     * Null is a real answer and not an error: reverting to "unset" is not something the
     * settings API can express, so the caller has to know the difference between a setting
     * that was empty and one that was never there.
     */
    suspend fun getSecureSettingValue(settingType: SettingType, key: String): String?
}
