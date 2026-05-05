package com.whisperkeyboard

import android.inputmethodservice.InputMethodService
import android.media.MediaRecorder
import android.os.Handler
import android.os.Looper
import android.view.KeyEvent
import android.view.View
import android.view.inputmethod.EditorInfo
import android.view.inputmethod.InputConnection
import android.widget.ImageButton
import android.widget.Toast
import java.io.File

class WhisperIME : InputMethodService() {

    private var micButton: ImageButton? = null
    private var isRecording = false
    private var mediaRecorder: MediaRecorder? = null
    private var audioFile: File? = null
    private val mainHandler = Handler(Looper.getMainLooper())

    // TODO: Phase 5 - WhisperEngine integration
    // private lateinit var whisperEngine: WhisperEngine
    // TODO: Phase 6 - CommandProcessor integration
    // private lateinit var commandProcessor: CommandProcessor

    override fun onCreate() {
        super.onCreate()
        // TODO: Phase 5 - Initialize WhisperEngine with model from assets
    }

    override fun onCreateInputView(): View {
        val view = layoutInflater.inflate(R.layout.keyboard, null)
        micButton = view.findViewById(R.id.micButton)

        micButton?.setOnClickListener {
            if (isRecording) {
                stopRecordingAndTranscribe()
            } else {
                startRecording()
            }
        }

        return view
    }

    override fun onStartInputView(info: EditorInfo?, restarting: Boolean) {
        super.onStartInputView(info, restarting)
        // Reset state when input view appears
        isRecording = false
        micButton?.isSelected = false
    }

    private fun startRecording() {
        try {
            audioFile = File.createTempFile("whisper_record", ".wav", cacheDir)
            mediaRecorder = if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.S) {
                MediaRecorder(this)
            } else {
                @Suppress("DEPRECATION")
                MediaRecorder()
            }

            mediaRecorder?.apply {
                setAudioSource(MediaRecorder.AudioSource.MIC)
                setOutputFormat(MediaRecorder.OutputFormat.DEFAULT)
                setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
                setAudioSamplingRate(16000)
                setOutputFile(audioFile?.absolutePath)
                prepare()
                start()
            }

            isRecording = true
            micButton?.isSelected = true
            vibrate()
        } catch (e: Exception) {
            Toast.makeText(this, "Failed to start recording: ${e.message}", Toast.LENGTH_SHORT).show()
            isRecording = false
            micButton?.isSelected = false
        }
    }

    private fun stopRecordingAndTranscribe() {
        try {
            mediaRecorder?.apply {
                stop()
                release()
            }
            mediaRecorder = null
            isRecording = false
            micButton?.isSelected = false
            vibrate()

            // TODO: Phase 5 - Send audio to WhisperEngine for transcription
            // TODO: Phase 6 - Pass transcription through CommandProcessor
            // For now, insert a placeholder to verify IME flow
            val testText = "[Transcription placeholder]"
            commitText(testText)

        } catch (e: Exception) {
            Toast.makeText(this, "Transcription failed: ${e.message}", Toast.LENGTH_SHORT).show()
        }
    }

    private fun commitText(text: String) {
        val ic: InputConnection = currentInputConnection ?: return
        ic.commitText(text, 1)
    }

    private fun deleteLastWord() {
        val ic: InputConnection = currentInputConnection ?: return
        val before = ic.getTextBeforeCursor(256, 0) ?: return
        // Find last word boundary
        val lastSpace = before.toString().trimEnd().lastIndexOf(' ')
        val charsToDelete = if (lastSpace >= 0) {
            before.length - lastSpace
        } else {
            before.length
        }
        ic.deleteSurroundingText(charsToDelete, 0)
    }

    private fun deleteSurroundingText(before: Int, after: Int) {
        val ic: InputConnection = currentInputConnection ?: return
        ic.deleteSurroundingText(before, after)
    }

    private fun sendKeyEvent(keyCode: Int) {
        val ic: InputConnection = currentInputConnection ?: return
        ic.sendKeyEvent(KeyEvent(KeyEvent.ACTION_DOWN, keyCode))
        ic.sendKeyEvent(KeyEvent(KeyEvent.ACTION_UP, keyCode))
    }

    private fun vibrate() {
        // TODO: Add haptic feedback via Vibrator service
    }

    override fun onDestroy() {
        super.onDestroy()
        try {
            mediaRecorder?.apply {
                stop()
                release()
            }
        } catch (_: Exception) {}
        mediaRecorder = null
    }
}
