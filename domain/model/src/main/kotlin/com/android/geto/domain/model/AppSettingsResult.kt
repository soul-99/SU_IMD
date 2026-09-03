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
package com.android.geto.domain.model

enum class AppSettingsResult {
    Success,
    Failure,

    /**
     * Hiding "Display over other apps" needs a running Shizuku service, and it could not be
     * reached. Kept apart from [Failure] because it is the one failure with a specific,
     * actionable cause: every other failure is a settings write that did not take, whereas
     * this one is answered by granting IMD permission in Shizuku or fixing the fork
     * configuration, and the user cannot guess that from "could not apply settings".
     */
    OverlayFailure,

    /**
     * The device-wide "Settings to hide" configuration has nothing ticked, so launching the
     * app would hide nothing.
     *
     * Not a failure, and not success either. Nothing has gone wrong and nothing needs
     * retrying — the app simply has not been told what to hide yet, which since v2.1 is the
     * state every fresh install starts in. Launching anyway would open the app with every
     * setting it objects to still switched on, which looks exactly like this app not working;
     * saying so, and where to fix it, is the only useful thing left to do.
     *
     * Only [ApplySettingsToHideUseCase] returns it. A per-app profile with nothing in it is
     * [EmptyAppSettings], which is the same idea one scope down.
     */
    NothingToHide,

    /**
     * Everything this launch would have hidden is already hidden, so the app is simply opened.
     *
     * The ordinary state while Auto-hide settings (IMD+) is holding the device down: IMD+ has
     * applied the device-wide list, and a launch from inside IMD then finds there is nothing
     * left for it to do. Distinct from [Success] on one point that matters — **no revert
     * notification is posted**. This launch created no debt, and a notification offering to
     * undo it would offer to undo IMD+'s run instead, from a button that does not know how.
     *
     * It also covers the plain case with IMD+ out of the picture: a launch whose settings are
     * all off already changes nothing and needs no way back.
     */
    AlreadyHidden,

    /**
     * A per-app profile asks for something the outstanding hide does not cover, and cannot be
     * satisfied without changing what that hide is holding.
     *
     * Only reachable while IMD+ is running. Hiding the extra settings would leave a device that
     * neither mechanism's revert puts back: IMD+'s revert restores what IMD+ hid, this app's
     * revert restores what this app hid, and nothing owns the overlap. So the launch is refused
     * and the dialog says why — see [autoHideCoversProfile].
     */
    AutoHideConflict,
    NoPermission,
    InvalidValues,
    EmptyAppSettings,
    DisabledAppSettings,

    /**
     * Settings are still hidden from a run of IMD that is no longer alive.
     *
     * Nothing was written and nothing was launched: the hide stops before it touches anything,
     * so that the user can choose between putting the old state back and letting go of it. See
     * [com.android.geto.domain.common.PriorHide] for how "no longer alive" is known.
     *
     * ⚠ **Not a failure**, and it must not be treated as one. Every other value in this enum
     * that stops a launch describes something wrong with the configuration or the device; this
     * one describes a device that is working exactly as asked and a user who has not been told.
     */
    HiddenFromPreviousUse,
}
