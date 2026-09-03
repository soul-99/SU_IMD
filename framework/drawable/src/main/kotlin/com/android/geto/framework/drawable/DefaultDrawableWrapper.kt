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
package com.android.geto.framework.drawable

import android.graphics.Bitmap
import android.graphics.drawable.Drawable
import androidx.core.graphics.drawable.toBitmap
import com.android.geto.domain.common.IconStyleState
import com.android.geto.domain.common.dispatcher.Dispatcher
import com.android.geto.domain.common.dispatcher.GetoDispatchers
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.withContext
import java.io.ByteArrayOutputStream
import javax.inject.Inject

internal class DefaultDrawableWrapper @Inject constructor(
    @param:Dispatcher(GetoDispatchers.Default) private val defaultDispatcher: CoroutineDispatcher,
) : AndroidDrawableWrapper {
    /**
     * Renders an icon the system has already shaped exactly as it handed it over, and shapes
     * one it has not.
     *
     * An earlier version drew adaptive layers unmasked and clipped everything — adaptive
     * and legacy alike — to one squircle, so that every row in the app matched. It looked
     * worse, for two reasons that are worth writing down. Adaptive foregrounds are drawn
     * on a 108-unit canvas of which only the middle 72 is ever shown, so painting the
     * whole canvas into the tile renders every logo at two thirds of the size a launcher
     * shows it. And `LauncherActivityInfo.getIcon` already returns whatever treatment the
     * OEM launcher applies, which on many devices is a mask of its own — so the result was
     * a second mask over the first.
     *
     * ⚠ **Both of those are about icons that already arrive shaped, and neither is true of one
     * that does not.** A drawable that is not an `AdaptiveIconDrawable` on API 26+ has no 108-unit
     * canvas and has had no OEM treatment applied — it is a finished 48dp picture, which is why
     * the author saw legacy icons drawn raw beside shaped ones. [LegacyIconShaping] shapes only
     * those, and asks the platform for the mask rather than choosing a squircle, so the reverted
     * version's third problem — being right only on some devices — does not come back either.
     */
    override suspend fun toByteArray(drawable: Drawable, size: Int): ByteArray = withContext(defaultDispatcher) {
        val stream = ByteArrayOutputStream()

        // Always a fixed square, rather than the drawable's own intrinsic size capped at
        // it. A legacy icon whose intrinsic size is 48px was being rasterised at 48px and
        // then scaled up to a 50dp slot, which on a high-density screen is four times the
        // pixels it has — the icon read as small and soft next to its neighbours. Rendering
        // every icon at one size costs nothing extra for the ones that were already large.
        val rendered = drawable.toBitmap(width = size, height = size)

        // ⚠ **The user's Icon style, read from memory** — see IconStyleState for why it is
        // held rather than injected. False is "System icons": the drawable is handed over
        // exactly as the system gave it, which is what this app did before v3.
        val shaped = if (IconStyleState.shapeLegacyIcons && LegacyIconShaping.isLegacy(drawable)) {
            LegacyIconShaping.maskedInApp(source = rendered, size = size)
        } else {
            rendered
        }

        // The quality argument is ignored for PNG, which is lossless.
        shaped.compress(Bitmap.CompressFormat.PNG, 100, stream)

        stream.toByteArray()
    }
}
