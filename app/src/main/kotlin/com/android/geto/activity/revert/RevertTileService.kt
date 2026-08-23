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
package com.android.geto.activity.revert

import android.app.PendingIntent
import android.content.Intent
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.service.quicksettings.Tile
import android.service.quicksettings.TileService
import androidx.annotation.RequiresApi

/**
 * How long the tile shows as on after a press.
 *
 * "Revert to default" is an action, not a state, so there is nothing for a tile to stay on
 * for. The flash exists only to acknowledge the press — without it the panel collapses and
 * nothing visibly happens, which reads as a tile that did not register the tap.
 */
private const val ACTIVE_FLASH_MILLIS = 1_000L

/**
 * The "Revert to default" Quick Settings tile.
 *
 * Long-pressing it opens the settings manager, routed through [TilePreferencesActivity] —
 * see there for why that is a trampoline rather than two separate activities.
 */
@RequiresApi(Build.VERSION_CODES.N)
class RevertTileService : TileService() {

    private val handler = Handler(Looper.getMainLooper())

    override fun onStartListening() {
        super.onStartListening()

        // Reset on every listen rather than relying on the delayed reset below. The panel
        // usually collapses before that runs and this service is unbound with it, so this
        // is what actually guarantees the tile is never found stuck on.
        qsTile?.apply {
            state = Tile.STATE_INACTIVE

            updateTile()
        }
    }

    override fun onStopListening() {
        handler.removeCallbacksAndMessages(null)

        super.onStopListening()
    }

    override fun onClick() {
        super.onClick()

        qsTile?.apply {
            state = Tile.STATE_ACTIVE

            updateTile()
        }

        handler.postDelayed(
            {
                qsTile?.apply {
                    state = Tile.STATE_INACTIVE

                    updateTile()
                }
            },
            ACTIVE_FLASH_MILLIS,
        )

        val intent = Intent(this, RevertActivity::class.java).addFlags(
            Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP,
        )

        // The revert itself happens in RevertActivity. Doing it here instead would leave the
        // shade open — collapsing it is only possible by launching something, and this is
        // the launch. From Android 14 the panel wants a PendingIntent so the launch is
        // attributable; below that the intent overload is the only one that exists.
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
