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
package com.android.geto.framework.shortcutmanager

import android.content.ComponentName
import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.drawable.AdaptiveIconDrawable
import android.graphics.drawable.Drawable
import android.os.Build
import android.util.Log
import androidx.annotation.RequiresApi
import androidx.core.graphics.drawable.IconCompat
import com.android.geto.domain.common.IconStyleState
import com.android.geto.framework.drawable.LegacyIconShaping
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject

private const val TAG = "ShortcutIconFactory"

/**
 * Fallback bitmap edge in pixels. 288px is 108dp at xxxhdpi, the largest size any launcher
 * asks for, and downscaling looks better than upscaling.
 */
private const val ADAPTIVE_BITMAP_SIZE = 288

/**
 * Builds the icon for a pinned shortcut so that it is rendered the same way the launcher
 * renders the target app's own icon.
 *
 * Upstream rendered the icon to a PNG and handed it over as `IconCompat.createWithBitmap`.
 * That tells the launcher "this is a finished picture, do not touch it", which defeats
 * everything adaptive icons do: the launcher cannot apply its own mask, cannot apply the
 * standard inset, and cannot render a themed variant. The shortcut ends up a different
 * shape and size from the icon sitting next to it on the home screen.
 *
 * The obvious fix — a TYPE_RESOURCE icon pointing at the target app's own drawable — is not
 * available. ShortcutService.injectValidateIconResPackage rejects any resource icon whose
 * package is not the shortcut owner's ("Icon resource must reside in shortcut owner
 * package"), and it throws from the system server on both requestPinShortcut and
 * updateShortcuts. So:
 *
 * 1. **Full-bleed adaptive bitmap.** Draw the adaptive drawable's background and foreground
 *    layers unmasked onto a square bitmap and hand it over as an adaptive bitmap. The
 *    launcher then applies its own mask and inset, which is what makes the shortcut match
 *    the app icon beside it.
 * 2. **Plain bitmap**, from the bytes the caller already had — for legacy non-adaptive
 *    icons and for apps whose icon cannot be read at all.
 */
internal class ShortcutIconFactory @Inject constructor(
    @param:ApplicationContext private val context: Context,
) {

    fun create(componentName: String, icon: ByteArray?): IconCompat? {
        val component = ComponentName.unflattenFromString(componentName)

        if (component != null && Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            adaptiveBitmapIcon(component)?.let { return it }
        }

        return legacyBitmapIcon(icon)
    }

    @RequiresApi(Build.VERSION_CODES.O)
    private fun adaptiveBitmapIcon(component: ComponentName): IconCompat? = runCatching {
        val drawable = context.packageManager.getActivityIcon(component)

        if (drawable !is AdaptiveIconDrawable) return@runCatching null

        val size = drawable.intrinsicWidth.coerceAtLeast(ADAPTIVE_BITMAP_SIZE)

        val bitmap = Bitmap.createBitmap(size, size, Bitmap.Config.ARGB_8888)

        val canvas = Canvas(bitmap)

        // Drawing the layers rather than the AdaptiveIconDrawable itself is deliberate:
        // drawing the drawable would apply the system mask, and the launcher would then
        // mask an already-masked icon. createWithAdaptiveBitmap expects the full unmasked
        // square and does the insetting and masking itself.
        drawable.background?.drawInto(canvas, size)

        drawable.foreground?.drawInto(canvas, size)

        IconCompat.createWithAdaptiveBitmap(bitmap)
    }.onFailure {
        Log.w(TAG, "Could not build an adaptive icon for $component", it)
    }.getOrNull()

    private fun legacyBitmapIcon(icon: ByteArray?): IconCompat? {
        if (icon == null || icon.isEmpty()) return null

        val bitmap = BitmapFactory.decodeByteArray(icon, 0, icon.size) ?: return null

        // ⚠ **An adaptive bitmap, not a plain one, and that is the author's report.**
        // createWithBitmap says "this is a finished picture, do not touch it", so the launcher
        // could not mask it and a legacy shortcut sat square beside round neighbours. Handing
        // over a full-bleed square instead lets the launcher apply its own shape and inset -
        // the same route the adaptive branch above already takes, which is why that one has
        // always looked right.
        //
        // Below API 26 there is no adaptive icon to match, so the finished picture is still the
        // honest answer there.
        //
        // ⚠ **And when the user has chosen System icons**, which is what that choice means on
        // this path: hand the launcher a finished picture and let it sit unshaped, exactly as
        // every build before v3 did. See IconStyleState.
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O || !IconStyleState.shapeLegacyIcons) {
            return IconCompat.createWithBitmap(bitmap)
        }

        return IconCompat.createWithAdaptiveBitmap(
            LegacyIconShaping.adaptiveCanvas(source = bitmap, size = ADAPTIVE_BITMAP_SIZE),
        )
    }

    private fun Drawable.drawInto(canvas: Canvas, size: Int) {
        setBounds(0, 0, size, size)

        draw(canvas)
    }
}
