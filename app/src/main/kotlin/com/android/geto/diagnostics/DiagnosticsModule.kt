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

import com.android.geto.domain.framework.DiagnosticLogStore
import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

/**
 * The log's reading half, bound in the app module because that is where the file lives.
 *
 * Installed into the singleton component, so the settings screen can inject the interface
 * without depending on this module — the same arrangement every framework wrapper uses, only
 * from here rather than from a `framework/` module, because nothing in `framework/` is about
 * this app's own private storage.
 */
@Module
@InstallIn(SingletonComponent::class)
internal interface DiagnosticsModule {

    @Binds
    @Singleton
    fun diagnosticLogStore(impl: DefaultDiagnosticLogStore): DiagnosticLogStore
}
