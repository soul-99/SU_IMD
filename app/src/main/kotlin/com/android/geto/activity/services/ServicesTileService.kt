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
package com.android.geto.activity.services

import android.app.PendingIntent
import android.content.Intent
import android.os.Build
import android.service.quicksettings.Tile
import android.service.quicksettings.TileService
import androidx.annotation.RequiresApi

/**
 * The Quick Settings tile.
 *
 * Opens the manager rather than toggling anything itself. There are five separate switches
 * behind it and no honest way to collapse them into one tile state — a tile that claimed
 * "on" while two of them were off would be the same lie the Shizuku switch used to tell.
 *
 * The tile therefore stays inactive and behaves as a shortcut, which is a supported use:
 * the panel collapses and the manager appears over whatever was on screen.
 */
@RequiresApi(Build.VERSION_CODES.N)
class ServicesTileService : TileService() {
    override fun onStartListening() {
        super.onStartListening()

        qsTile?.apply {
            // Never ACTIVE: see the class comment. INACTIVE reads as "a thing you can
            // open", which is what it is.
            state = Tile.STATE_INACTIVE

            updateTile()
        }
    }

    override fun onClick() {
        super.onClick()

        // No CLEAR_TOP: the activity has its own task affinity, so there is nothing above
        // it to clear, and the flag only ever mattered when it shared the app's task.
        val intent = Intent(this, ServicesActivity::class.java)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)

        // From Android 14 the panel refuses to launch a bare intent from a tile; it wants
        // a PendingIntent so the launch is attributable. Below that, the intent overload
        // is the only one that exists.
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
            startActivityAndCollapse(
                PendingIntent.getActivity(
                    this,
                    0,
                    intent,
                    PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
                ),
            )
        } else {
            @Suppress("DEPRECATION")
            startActivityAndCollapse(intent)
        }
    }
}
