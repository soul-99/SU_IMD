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
package com.android.geto.diagnostics

import android.content.Context
import android.net.Uri
import com.android.geto.common.ApplicationScope
import com.android.geto.domain.common.DiagnosticSink
import com.android.geto.domain.common.Diagnostics
import com.android.geto.domain.common.dispatcher.Dispatcher
import com.android.geto.domain.common.dispatcher.GetoDispatchers
import com.android.geto.domain.framework.DiagnosticLogStore
import com.android.geto.domain.repository.UserDataRepository
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import javax.inject.Inject
import javax.inject.Singleton

/**
 * The diagnostic log, on disk, in IMD's own private storage.
 *
 * ### Why this does nothing when nothing is happening
 *
 * There is no thread, no timer and no service here. Lines arrive because something else was
 * already running — a hide, a revert, a watcher tick — and with nothing hidden and IMD+ off,
 * nothing calls [write] at all. Recording being *switched on* costs one volatile boolean; it
 * is only writing that costs anything, and only when there is something to write.
 *
 * The flush is a coroutine that exists **only while the buffer is not empty**. It is launched
 * by the first line after a flush, waits [FLUSH_DEBOUNCE_MILLIS] so a burst of twenty lines
 * becomes one file write, and then ends. When the app is idle there is no job, no wake-up and
 * no handle held open — the file is opened, appended to and closed each time.
 *
 * ### What bounds it
 *
 * Two limits, both applied on flush rather than on a schedule, because a schedule would be
 * exactly the background work this is trying not to do:
 *
 * - **Age.** Seven days from the moment the file was first created, tracked in a sidecar file
 *   rather than the log's own timestamp — `lastModified` moves on every append and would
 *   restart the week on every write.
 * - **Size.** Capped at [MAX_BYTES], and when it is reached the **oldest** lines go rather
 *   than the file being wiped. What a diagnostic needs is the run-up to the problem, and the
 *   problem is nearly always recent.
 */
@Singleton
class DefaultDiagnosticLogStore @Inject constructor(
    @param:ApplicationContext private val context: Context,
    private val userDataRepository: UserDataRepository,
    @param:ApplicationScope private val appScope: CoroutineScope,
    @param:Dispatcher(GetoDispatchers.IO) private val ioDispatcher: CoroutineDispatcher,
) : DiagnosticSink, DiagnosticLogStore {

    private val buffer = ArrayDeque<Line>()

    private val lock = Any()

    private var flushJob: Job? = null

    private val directory: File get() = File(context.filesDir, DIRECTORY)

    private val logFile: File get() = File(directory, FILE_NAME)

    private val createdFile: File get() = File(directory, CREATED_NAME)

    /**
     * Called from every module, on whatever thread happened to be running.
     *
     * Deliberately trivial: take the clock, put a line in a list, and make sure a flush is
     * pending. No formatting, no file, no I/O — all of that waits for the flush, so a caller
     * on a hot path pays almost nothing.
     */
    override fun write(tag: String, message: String) {
        val start: Boolean

        synchronized(lock) {
            buffer.addLast(Line(at = System.currentTimeMillis(), tag = tag, message = message))

            // Bound the memory a burst can take even if a flush is somehow not running.
            while (buffer.size > MAX_BUFFERED_LINES) buffer.removeFirst()

            start = flushJob == null
        }

        if (!start) return

        synchronized(lock) {
            if (flushJob != null) return

            flushJob = appScope.launch {
                delay(FLUSH_DEBOUNCE_MILLIS)

                flush()
            }
        }
    }

    override suspend fun read(): String = withContext(ioDispatcher) {
        flush()

        runCatching { logFile.readText() }.getOrDefault("")
    }

    override suspend fun clear(): Unit = withContext(ioDispatcher) {
        synchronized(lock) { buffer.clear() }

        runCatching {
            logFile.delete()

            createdFile.delete()
        }
    }

    override suspend fun export(destinationUri: String): Boolean = withContext(ioDispatcher) {
        flush()

        runCatching {
            val uri = Uri.parse(destinationUri)

            context.contentResolver.openOutputStream(uri)?.use { output ->
                if (logFile.exists()) {
                    logFile.inputStream().use { input -> input.copyTo(output) }
                } else {
                    output.write(ByteArray(0))
                }
            } != null
        }.getOrDefault(false)
    }

    /**
     * Switches recording on or off.
     *
     * The in-memory gate is moved **first** and the preference written after, so a caller who
     * has just switched recording off cannot have one more line slip in behind them while the
     * datastore write is in flight.
     */
    override suspend fun setEnabled(enabled: Boolean) {
        Diagnostics.enabled = enabled

        if (enabled) {
            withContext(ioDispatcher) { ensureFile() }

            Diagnostics.log(tag = TAG_SESSION, message = "recording started")
        } else {
            flush()
        }

        userDataRepository.updateDiagnosticsEnabled(enabled = enabled)
    }

    /**
     * Everything buffered, in one file write, plus the two limits.
     *
     * Never throws. A failure here means a lost diagnostic, which is a nuisance; a failure
     * that propagated would mean a broken hide, which is not.
     */
    private suspend fun flush() = withContext(ioDispatcher) {
        val lines: List<Line>

        synchronized(lock) {
            flushJob = null

            if (buffer.isEmpty()) return@withContext

            lines = buffer.toList()

            buffer.clear()
        }

        runCatching {
            ensureFile()

            val format = SimpleDateFormat(TIMESTAMP_FORMAT, Locale.US)

            val text = buildString {
                lines.forEach { line ->
                    append(format.format(Date(line.at)))
                    append(' ')
                    append(line.tag.padEnd(TAG_WIDTH))
                    append(' ')
                    append(line.message)
                    append('\n')
                }
            }

            logFile.appendText(text)

            trimIfOversized()
        }

        Unit
    }

    /** Creates the file and starts its seven-day clock, or restarts both once that runs out. */
    private fun ensureFile() {
        directory.mkdirs()

        val createdAt = runCatching { createdFile.readText().trim().toLong() }.getOrNull()

        val expired = createdAt != null &&
            System.currentTimeMillis() - createdAt > RETENTION_MILLIS

        if (createdAt == null || expired) {
            logFile.delete()

            createdFile.writeText(System.currentTimeMillis().toString())
        }

        if (!logFile.exists()) logFile.createNewFile()
    }

    /**
     * Drops the oldest lines once the file passes its cap.
     *
     * Rewritten down to [TRIM_TO_BYTES] rather than exactly to the cap, so a file sitting at
     * the limit is not rewritten on every single flush — trimming to the same size it already
     * is would turn every append into a full copy.
     */
    private fun trimIfOversized() {
        if (logFile.length() <= MAX_BYTES) return

        val text = logFile.readText()

        val keep = text.takeLast(TRIM_TO_BYTES.toInt())

        // From the first whole line, so the file never opens mid-sentence.
        val fromLineStart = keep.indexOf('\n').let { if (it == -1) 0 else it + 1 }

        logFile.writeText(TRIM_NOTE + keep.substring(fromLineStart))
    }

    private data class Line(val at: Long, val tag: String, val message: String)

    private companion object {
        const val DIRECTORY = "diagnostics"

        const val FILE_NAME = "imd-diagnostics.log"

        const val CREATED_NAME = "imd-diagnostics.created"

        /** Logcat's own shape, which anyone reading this will already know how to scan. */
        const val TIMESTAMP_FORMAT = "MM-dd HH:mm:ss.SSS"

        /** Wide enough for the longest tag, so the messages line up into a column. */
        const val TAG_WIDTH = 7

        /**
         * Long enough that a burst of lines from one hide becomes a single write, short enough
         * that the log is current by the time anyone opens the viewer.
         */
        const val FLUSH_DEBOUNCE_MILLIS = 2_000L

        const val MAX_BUFFERED_LINES = 2_000

        /** Five megabytes, at the author's choice — roughly 60,000 lines. */
        const val MAX_BYTES = 5L * 1024 * 1024

        const val TRIM_TO_BYTES = 4L * 1024 * 1024

        const val RETENTION_MILLIS = 7L * 24 * 60 * 60 * 1000

        const val TRIM_NOTE = "--- older lines dropped, log reached its size limit ---\n"

        const val TAG_SESSION = "session"
    }
}
