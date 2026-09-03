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
package com.android.geto.domain.common

/**
 * Where a diagnostic line ends up. Implemented on the Android side, which owns the file.
 *
 * An interface here rather than the writer itself, because the callers are spread across every
 * module in the app — the hide use cases, the runners, the watcher, the framework wrappers —
 * and most of them have no business knowing that a file exists.
 */
interface DiagnosticSink {
    fun write(tag: String, message: String)
}

/**
 * The diagnostic log, as seen by everything that writes to it.
 *
 * **This is deliberately not a service, a poller or anything with a lifetime.** There is no
 * diagnostics process to run: a log line is an append that happens on a code path which was
 * running anyway. With nothing hidden and IMD+ switched off, nothing in the app calls [log],
 * so the whole feature costs exactly nothing — switched on or not.
 *
 * **The gate is one volatile read.** [enabled] is an in-memory flag, never a datastore lookup,
 * so a disabled logger is a branch and a return rather than any kind of work. That matters
 * because some of the call sites are hot: the watcher's tick, the settings observer's
 * callback.
 *
 * **An object rather than an injected singleton**, for the reason [SettingsObservationGate] is
 * one: the writers are scattered across modules that would otherwise need a dependency each,
 * and several of them — the two hide use cases especially — are pure Kotlin with no Android
 * on the classpath and no injector in reach.
 */
object Diagnostics {

    @Volatile
    private var sink: DiagnosticSink? = null

    /**
     * Whether anything is being recorded.
     *
     * Public and volatile so a caller with an expensive message to build can skip building it:
     * `if (Diagnostics.enabled) Diagnostics.log(...)` costs one read when it is off.
     */
    @Volatile
    var enabled: Boolean = false

    /** Installed once, by the application, and kept in step with the stored preference. */
    fun install(sink: DiagnosticSink?) {
        this.sink = sink
    }

    /**
     * One line, if recording is on.
     *
     * [tag] is a short fixed word — `hide`, `revert`, `unhide`, `tick`, `svc`, `state` — so a
     * reader can find one kind of event in a long file without a filter. Never throws: a
     * diagnostic that could break the thing it is diagnosing would be worse than no diagnostic
     * at all.
     */
    fun log(tag: String, message: String) {
        if (!enabled) return

        runCatching { sink?.write(tag = tag, message = message) }
    }
}
