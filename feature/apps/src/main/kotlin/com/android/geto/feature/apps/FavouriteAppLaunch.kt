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
package com.android.geto.feature.apps

import com.android.geto.domain.model.AppSettingsResult
import com.android.geto.domain.model.NotificationFunction

/**
 * The outcome of applying a favourite's settings, on its way to the UI so it can post the
 * revert notification and open the app.
 *
 * Not a data class: [icon] is a ByteArray, whose equality is identity-based, and the state
 * is cleared to null after handling anyway — so structural equality would buy nothing and
 * mislead anyone who assumed it worked.
 */
class FavouriteAppLaunch(
    val componentName: String,
    val result: AppSettingsResult,
    val icon: ByteArray?,
    /**
     * Read when the settings were applied rather than when the notification is posted, so a
     * launch cannot be applied under one function and announced under the other if the
     * preference changes in the moment between.
     */
    val notificationFunction: NotificationFunction,
)
