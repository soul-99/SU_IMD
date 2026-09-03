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
 * How stopping the Shizuku service went, so a caller can decide whether to record it against
 * an app (for a later revert) and word its warning correctly.
 */
enum class StopShizukuOutcome {
    /** No stop action to derive — Shizuku is not configured in IMD settings, so this is a no-op. */
    NotConfigured,

    /** Nothing was running, so nothing was stopped. */
    NotRunning,

    /** The fork answered its stop intent and the service went quiet. */
    Stopped,

    /** The fork ignored the stop intent, so USB debugging was cycled to take the service down. */
    StoppedViaUsb,

    /**
     * Neither route worked and the service is still running — a fork riding wireless debugging
     * or started as root outlives the USB transport being cycled. Nothing is recorded against
     * the app and no warning is raised, because nothing was stopped: claiming otherwise would
     * make the app's revert broadcast a start at a service that never went down.
     */
    NotStopped,
    ;

    /** True when a running service was actually taken down by this call, either way. */
    val stopped: Boolean get() = this == Stopped || this == StoppedViaUsb
}
