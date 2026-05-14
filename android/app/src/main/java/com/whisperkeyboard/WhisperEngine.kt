package com.whisperkeyboard

import android.content.Context
import android.util.Log
import java.io.File
import java.io.FileOutputStream
import java.net.HttpURLConnection
import java.net.URL

class WhisperEngine(private val context: Context) {

    companion object {
        private const val TAG = "WhisperEngine"
        private const val MODEL_URL = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin"
        private const val MODEL_NAME = "ggml-small.bin"

        init {
            System.loadLibrary("whisper_jni")
        }
    }

    private var contextPtr: Long = 0
    private var isLoaded: Boolean = false
    var onStatus: ((String) -> Unit)? = null

    private external fun nativeInit(modelPath: String, useGpu: Boolean): Long
    private external fun nativeTranscribe(contextPtr: Long, audioPath: String, language: String?, nThreads: Int): String
    private external fun nativeDestroy(contextPtr: Long)

    fun getModelFile(): File {
        val modelsDir = File(context.filesDir, "models")
        if (!modelsDir.exists()) modelsDir.mkdirs()
        return File(modelsDir, MODEL_NAME)
    }

    fun isModelAvailable(): Boolean = getModelFile().exists()

    fun ensureModel(): File? {
        val modelFile = getModelFile()
        if (modelFile.exists()) {
            Log.i(TAG, "Model already downloaded: ${modelFile.absolutePath}")
            return modelFile
        }

        Log.i(TAG, "Downloading model from $MODEL_URL...")
        onStatus?.invoke("Downloading model...")

        return try {
            val url = URL(MODEL_URL)
            val connection = url.openConnection() as HttpURLConnection
            connection.connectTimeout = 10000
            connection.readTimeout = 300000

            val inputStream = connection.inputStream
            val outputStream = FileOutputStream(modelFile)

            val buffer = ByteArray(8192)
            var totalBytes = 0L
            var bytesRead: Int

            while (inputStream.read(buffer).also { bytesRead = it } != -1) {
                outputStream.write(buffer, 0, bytesRead)
                totalBytes += bytesRead
                if (totalBytes % (10 * 1024 * 1024) == 0L) {
                    onStatus?.invoke("Downloading model... ${totalBytes / (1024 * 1024)} MB")
                }
            }

            outputStream.close()
            inputStream.close()
            connection.disconnect()

            Log.i(TAG, "Model downloaded: ${totalBytes / (1024 * 1024)} MB")
            modelFile
        } catch (e: Exception) {
            Log.e(TAG, "Failed to download model: ${e.message}")
            modelFile.delete()
            null
        }
    }

    fun load(): Boolean {
        if (isLoaded) return true

        onStatus?.invoke("Loading model...")
        val modelFile = ensureModel() ?: return false

        contextPtr = nativeInit(modelFile.absolutePath, false)
        isLoaded = contextPtr != 0L
        if (isLoaded) {
            onStatus?.invoke("Ready")
        } else {
            onStatus?.invoke("Failed to load model")
        }
        return isLoaded
    }

    fun transcribe(audioFile: File, language: String? = null, nThreads: Int = 4): String {
        if (!isLoaded) {
            Log.w(TAG, "Model not loaded, attempting load...")
            if (!load()) return ""
        }

        onStatus?.invoke("Transcribing...")
        val result = nativeTranscribe(contextPtr, audioFile.absolutePath, language, nThreads)
        onStatus?.invoke("Ready")
        return result
    }

    fun destroy() {
        if (contextPtr != 0L) {
            nativeDestroy(contextPtr)
            contextPtr = 0
        }
        isLoaded = false
    }

    protected fun finalize() {
        destroy()
    }
}
