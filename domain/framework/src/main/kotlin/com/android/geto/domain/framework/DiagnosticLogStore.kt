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
package com.android.geto.domain.framework

/**
 * The diagnostic log as seen by the screen that shows it.
 *
 * Separate from [com.android.geto.domain.common.DiagnosticSink], which is the writing half.
 * The two are used by completely different code — every module writes, one dialog reads — and
 * a single interface would have put a file-reading method on the classpath of forty call sites
 * that only ever append.
 */
interface DiagnosticLogStore {

    /**
     * Everything recorded so far, oldest first, or empty when nothing has been.
     *
     * The whole file rather than a page of it: it is capped at a few megabytes and the reader
     * is a person scrolling for the moment something went wrong, which is as likely to be at
     * the top as the bottom.
     */
    suspend fun read(): String

    /** Drops everything and starts again, including the file's own age. */
    suspend fun clear()

    /**
     * Copies the log to a document the user has chosen, given the URI their picker returned.
     *
     * A string rather than a typed Uri so this interface stays free of Android — the caller
     * has the platform type and the implementation parses it back.
     */
    suspend fun export(destinationUri: String): Boolean

    /**
     * Switches recording on or off and remembers nothing else.
     *
     * Whether it is on is stored as an ordinary preference; this is what makes the in-memory
     * gate agree with it, and what starts the file's seven-day clock the first time.
     */
    suspend fun setEnabled(enabled: Boolean)
}
