package com.whisperkeyboard

import android.content.Context
import android.content.SharedPreferences

object AppPreferences {
    private const val PREFS_NAME = "whisper_keyboard_prefs"
    private const val KEY_MODEL_SIZE = "model_size"
    private const val KEY_LANGUAGE = "language"
    private const val KEY_TAP_TO_TALK = "tap_to_talk"
    private const val KEY_HAPTICS = "haptics"

    private lateinit var prefs: SharedPreferences

    fun init(context: Context) {
        prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    }

    var modelSize: String
        get() = prefs.getString(KEY_MODEL_SIZE, "small") ?: "small"
        set(value) = prefs.edit().putString(KEY_MODEL_SIZE, value).apply()

    var language: String
        get() = prefs.getString(KEY_LANGUAGE, "auto") ?: "auto"
        set(value) = prefs.edit().putString(KEY_LANGUAGE, value).apply()

    var tapToTalk: Boolean
        get() = prefs.getBoolean(KEY_TAP_TO_TALK, false)
        set(value) = prefs.edit().putBoolean(KEY_TAP_TO_TALK, value).apply()

    var hapticsEnabled: Boolean
        get() = prefs.getBoolean(KEY_HAPTICS, true)
        set(value) = prefs.edit().putBoolean(KEY_HAPTICS, value).apply()
}
