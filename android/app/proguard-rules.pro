# Whisper Keyboard ProGuard Rules

# Keep native method signatures
-keepclasseswithmembernames,includedescriptorclasses class * {
    native <methods>;
}

# Keep WhisperEngine class (JNI bridge)
-keep class com.whisperkeyboard.WhisperEngine { *; }

# Keep VoiceCommands data classes
-keep class com.whisperkeyboard.VoiceCommand { *; }
-keep class com.whisperkeyboard.VoiceCommands { *; }
-keep class com.whisperkeyboard.CommandProcessor { *; }
-keep class com.whisperkeyboard.TextPostProcessor { *; }
-keep class com.whisperkeyboard.AppPreferences { *; }

# Keep model file paths
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}
