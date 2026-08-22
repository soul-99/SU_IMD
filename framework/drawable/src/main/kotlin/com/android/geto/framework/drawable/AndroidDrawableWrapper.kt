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

import android.graphics.drawable.Drawable

interface AndroidDrawableWrapper {
    /**
     * [size] is the square the icon is rasterised into. It defaults to the size the app
     * lists and shortcuts need; a picker showing a small row can ask for less rather than
     * paying for hundreds of full-size bitmaps it will only draw at 40dp.
     */
    suspend fun toByteArray(drawable: Drawable, size: Int = DEFAULT_ICON_SIZE): ByteArray

    companion object {
        /** 192px covers a 56dp icon at xxxhdpi and a notification large icon. */
        const val DEFAULT_ICON_SIZE = 192
    }
}
