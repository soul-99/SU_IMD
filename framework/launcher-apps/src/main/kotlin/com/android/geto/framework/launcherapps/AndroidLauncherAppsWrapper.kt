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
package com.android.geto.framework.launcherapps

interface AndroidLauncherAppsWrapper {
    fun startMainActivity(componentName: String)

    /**
     * Opens an app by package name, whichever launcher entry it has.
     *
     * What Auto-hide settings (IMD+) needs: it watches packages, because a package name is all
     * an accessibility event carries, and the app it has just force-stopped has to be put back
     * in front of the user. [startMainActivity] cannot serve — a component name is a finer
     * thing than IMD+ ever knows.
     *
     * False when the package has no launcher entry, or the system refused the launch.
     */
    fun startPackage(packageName: String): Boolean
}
