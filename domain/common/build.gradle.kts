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

plugins {
    alias(libs.plugins.com.android.geto.jvmLibrary)
}

dependencies {
    api(libs.javax.inject)

    // ⚠ **api, not implementation.** `IconStyleState.revision` is a StateFlow in this module's
    // public signature and two other modules collect it; under `implementation` the type would
    // not be on their compile classpath and each of them would fail instead. The sibling domain
    // modules use `implementation` because their coroutine types stay behind their own
    // interfaces — this one does not.
    api(libs.kotlinx.coroutines.core)
}