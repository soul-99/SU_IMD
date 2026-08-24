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
package com.android.geto.common

import android.app.LocaleManager
import android.content.Context
import android.content.res.Configuration
import android.os.Build
import android.os.LocaleList
import java.util.Locale

/**
 * Which language the app draws itself in.
 *
 * Not in the proto DataStore with every other preference, and the reason is timing rather
 * than taste: this value is needed in `attachBaseContext`, before anything else in the
 * process exists, and a DataStore read is suspending. Blocking the main thread on it at
 * every cold start to save a file is the wrong trade. A one-key SharedPreferences file is
 * readable synchronously, which is exactly what this moment needs.
 *
 * On Android 13 and up the platform owns this instead. `LocaleManager` persists the choice,
 * shows it in Android's own per-app language screen, and applies it before the process
 * starts, so there is nothing to wrap and the two settings can never disagree. Below 13
 * there is no such API and every context has to be wrapped by hand.
 */
object AppLocale {

    /** Follow the system, and fall back to English when the system language is not one of ours. */
    const val SYSTEM = ""

    /**
     * BCP-47 tags in the order the picker lists them, each with the name of the language
     * written in that language.
     *
     * The names are spelled out here rather than read from `Locale.getDisplayName`, which
     * depends on the ICU data of the device it runs on: on a stripped-down build it can
     * return a bare code, and it capitalises inconsistently between languages.
     */
    val LANGUAGES: List<Pair<String, String>> = listOf(
        "en" to "English",
        "pt-BR" to "Português (Brasil)",
        "es" to "Español",
        "zh-Hans" to "简体中文",
        "fr" to "Français",
        "de" to "Deutsch",
        "ru" to "Русский",
        "hi" to "हिन्दी",
        "ar" to "العربية",
        "ko" to "한국어",
        "ja" to "日本語",
    )

    private const val PREFS = "app_locale"
    private const val KEY_TAG = "tag"
    private const val KEY_PROMPTED = "prompted"

    /**
     * The chosen tag, or [SYSTEM].
     *
     * Read from the platform on 13 and up so that a change made in Android's settings rather
     * than in ours is picked up rather than overwritten.
     */
    fun stored(context: Context): String {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            val locales = context.getSystemService(LocaleManager::class.java)
                ?.applicationLocales

            // toLanguageTags rather than locales[0]: the list is a Java type whose get()
            // is not declared an operator, and this needs no unwrapping to read.
            return if (locales == null || locales.isEmpty) {
                SYSTEM
            } else {
                locales.toLanguageTags().substringBefore(',')
            }
        }

        return prefs(context).getString(KEY_TAG, SYSTEM) ?: SYSTEM
    }

    /**
     * Store the choice and, where the platform supports it, hand it over.
     *
     * Returns true when the caller has to recreate the activity itself. On 13 and up the
     * system does that as part of applying the locale, and doing it again would restart the
     * screen twice in a row.
     */
    fun set(context: Context, tag: String): Boolean {
        prefs(context).edit().putString(KEY_TAG, tag).apply()

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            context.getSystemService(LocaleManager::class.java)?.applicationLocales =
                if (tag == SYSTEM) LocaleList.getEmptyLocaleList() else LocaleList.forLanguageTags(tag)

            return false
        }

        applyToDefault(tag)

        return true
    }

    /**
     * Wrap a context so its resources resolve in the chosen language.
     *
     * Called from `attachBaseContext` in the Application and in every activity. A no-op on
     * 13 and up, where the platform has already done it.
     */
    fun wrap(base: Context): Context {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) return base

        val tag = prefs(base).getString(KEY_TAG, SYSTEM) ?: SYSTEM

        if (tag == SYSTEM) return base

        applyToDefault(tag)

        val config = Configuration(base.resources.configuration)
        val locale = Locale.forLanguageTag(tag)

        config.setLocale(locale)
        config.setLocales(LocaleList(locale))

        return base.createConfigurationContext(config)
    }

    /** Has the first-run picker been shown yet? */
    fun prompted(context: Context): Boolean = prefs(context).getBoolean(KEY_PROMPTED, false)

    fun markPrompted(context: Context) {
        prefs(context).edit().putBoolean(KEY_PROMPTED, true).apply()
    }

    /**
     * Anything that formats without a context - a date, a number, `String.format` - reads
     * `Locale.getDefault()`, which the configuration wrapping above does not touch.
     */
    private fun applyToDefault(tag: String) {
        val locale = Locale.forLanguageTag(tag)

        Locale.setDefault(locale)
        LocaleList.setDefault(LocaleList(locale))
    }

    private fun prefs(context: Context) =
        context.applicationContext.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
}
