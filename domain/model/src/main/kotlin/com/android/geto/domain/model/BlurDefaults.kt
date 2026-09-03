/*
 *
 *   Copyright 2026 soul_99 (suIMD)
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
 * What the author's three blur sliders default to, and how far each of them travels.
 *
 * ⚠ **Here rather than in `:design-system`, where the drawing is, and the module graph is why.**
 * Four places need these numbers: the datastore, which resolves an install that has never opened
 * the dialog; the dialog itself, which needs the slider ranges; the page modifier; and the frosted
 * window. The first of those is a data module and must not depend on a UI one — a `:data` module
 * reaching into `:design-system` is the dependency arrow pointing the wrong way, and it would work
 * right up until something in the design system wanted a repository. `:domain:model` depends on
 * nothing and everything depends on it, which is exactly what a shared constant wants.
 *
 * ⚠ **Stored, shown and drawn in the same units.** A dp of radius, a percent of tint, a dp of ramp
 * — the number on the slider is the number in the proto is the number in the draw, so there is no
 * conversion between them to get backwards.
 */

/** The author's own number, r23, after living with the sliders. */
const val DEFAULT_RADIUS_DP = 15

/**
 * ⚠ **Down from 50 to 15 in r23, at the author's word, and it is a change of mind worth keeping
 * a note of.** r20 argued the tint upward because a band that is only blurred reads as a smudge.
 * With the frosted manager window taking the same number, a heavy tint is a card you cannot see
 * through — and once the window existed the author wanted the glass, not the paint.
 */
const val DEFAULT_TINT_PERCENT = 15

/**
 * Long enough that the eye cannot find where the ramp stops, short enough that the untouched
 * middle of a phone screen is still most of it. The author's own 120 dp, r23 — a longer ramp
 * than r20 chose, which is the right direction now the tint is light.
 */
const val DEFAULT_FADE_DP = 120

/**
 * The slider travel, which is also what the store clamps to.
 *
 * ⚠ **The floors are not zero, and the ceilings are not generous.** Below about two dp a blur is
 * indistinguishable from none and some drivers report an error rather than drawing the source
 * unchanged; above forty it is a frame budget rather than a preference. The tint stops at ninety
 * because a hundred is an opaque bar across the page with the list behind it deleted.
 */
val BLUR_RADIUS_RANGE = 2..40

val BLUR_TINT_RANGE = 0..90

val BLUR_FADE_RANGE = 16..200
