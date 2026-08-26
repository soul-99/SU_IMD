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
 * The contract the Tasker / MacroDroid integration exposes, in one place so the receiver that
 * enforces it and the settings screen that documents it cannot drift.
 *
 * Three of the four functions are broadcasts, because they must run with no UI and with the
 * app not necessarily alive - a manifest receiver is what the system will start a process for.
 * The fourth, opening the services manager, is an ordinary activity launch instead: a
 * background receiver cannot bring an activity to the front on modern Android, and the manager
 * is exported for exactly this reason. It needs no key either - it only shows switches the
 * user then flips by hand, so there is no automatic change to guard.
 *
 * The action strings are duplicated verbatim in the broadcast-receiver manifest's
 * intent-filters. They are literal identifiers rather than anything derived, so a manifest can
 * name them; keep the two in step by hand.
 */
object TaskerIntegration {
    const val ACTION_REVERT_TO_DEFAULT = "com.soul_99.suIMD.tasker.REVERT_TO_DEFAULT"
    const val ACTION_REVERT_USING_MEMORY = "com.soul_99.suIMD.tasker.REVERT_USING_MEMORY"
    const val ACTION_HIDE_SETTINGS = "com.soul_99.suIMD.tasker.HIDE_SETTINGS"

    /** The intent extra every broadcast above must carry, holding the auth key. */
    const val EXTRA_AUTH_KEY = "auth_key"

    /**
     * The exported activity a caller launches to open the services manager. Shown in the
     * integration screen alongside the package, which is read from the app at runtime rather
     * than hard-coded here.
     */
    const val SERVICES_MANAGER_CLASS = "com.android.geto.activity.services.ServicesActivity"

    /** The action a services-manager launch intent uses - a plain view of the activity. */
    const val ACTION_VIEW = "android.intent.action.VIEW"

    /**
     * Whether a received broadcast is allowed to act.
     *
     * Three conditions, and the first two are the master switches: the integration must be
     * enabled, and a key must exist at all - a blank stored key means the user never set it
     * up, which also stops a broadcast carrying a blank key from matching a blank record. Only
     * then does an exact key match let the trigger through. The enable flag is checked here,
     * not just at the UI, so turning the switch off shuts the exported receiver whatever key a
     * caller still holds.
     */
    fun authorises(enabled: Boolean, storedKey: String, providedKey: String?): Boolean =
        enabled && storedKey.isNotBlank() && providedKey == storedKey
}
