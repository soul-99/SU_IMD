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

import android.content.ComponentName
import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import com.android.geto.activity.main.MainActivity
import com.android.geto.activity.services.ServicesActivity

/**
 * Where a long press on either Quick Settings tile lands.
 *
 * Android allows an app exactly one long-press target, declared with the
 * QS_TILE_PREFERENCES intent filter, no matter how many tiles it publishes — so two tiles
 * that want to open different things have to share one activity and sort themselves out
 * here. The system says which tile was pressed in [Intent.EXTRA_COMPONENT_NAME]; this reads
 * it, starts the right thing and gets out of the way.
 *
 * The two destinations are deliberately crossed over. Long-pressing *Revert to default*
 * opens the settings manager, because the question after a revert is "what state is
 * everything in now", and the manager is the screen that answers it. Long-pressing the
 * *manager* tile opens the app itself, which is the only route to the Favourites list the
 * manager cannot show.
 */
class TilePreferencesActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        startActivity(destinationFor(pressedTile()))

        finish()
    }

    /**
     * `getParcelableExtra` without a class argument is deprecated from API 33, but the typed
     * replacement only exists from 33 — and there is no core-ktx compat helper in this
     * project's dependency set. One deprecated call is better than a version branch around
     * two lines.
     */
    @Suppress("DEPRECATION")
    private fun pressedTile(): ComponentName? =
        intent?.getParcelableExtra(Intent.EXTRA_COMPONENT_NAME)

    private fun destinationFor(tile: ComponentName?): Intent {
        if (tile?.className == RevertTileService::class.java.name) {
            return Intent(this, ServicesActivity::class.java)
        }

        // Clearing the task is what actually guarantees the Favourites tab: the tab is the
        // home graph's start destination, so a freshly created MainActivity lands on it,
        // whereas merely bringing the app forward would show whatever tab it was left on.
        // The cost is discarding an app screen the user had open — acceptable here, since
        // per-app settings are written to the database as they are edited rather than held
        // unsaved on screen.
        return Intent(this, MainActivity::class.java).addFlags(
            Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK,
        )
    }
}
