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
