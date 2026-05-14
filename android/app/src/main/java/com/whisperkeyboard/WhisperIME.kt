package com.whisperkeyboard

import android.content.Context
import android.os.Build
import android.os.Handler
import android.os.HandlerThread
import android.os.Looper
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.view.KeyEvent
import android.view.View
import android.view.animation.AnimationUtils
import android.view.inputmethod.EditorInfo
import android.view.inputmethod.InputConnection
import android.widget.ImageButton
import android.widget.TextView
import android.widget.Toast
import android.inputmethodservice.InputMethodService
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import java.io.ByteArrayOutputStream
import java.io.File
import java.io.FileOutputStream

class WhisperIME : InputMethodService() {

    private var micButton: ImageButton? = null
    private var statusText: TextView? = null
    private var isRecording = false
    private var audioRecord: AudioRecord? = null
    private var audioFile: File? = null
    private var recordingThread: Thread? = null
    private var audioSamples = ByteArrayOutputStream()

    private val mainHandler = Handler(Looper.getMainLooper())
    private val backgroundThread = HandlerThread("WhisperEngine")
    private var backgroundHandler: Handler? = null

    private lateinit var whisperEngine: WhisperEngine
    private lateinit var commandProcessor: CommandProcessor
    private lateinit var textPostProcessor: TextPostProcessor
    private var vibrator: Vibrator? = null
    private var pulseAnimation: android.animation.AnimatorSet? = null

    override fun onCreate() {
        super.onCreate()

        AppPreferences.init(this)
        backgroundThread.start()
        backgroundHandler = Handler(backgroundThread.looper)

        whisperEngine = WhisperEngine(this)
        commandProcessor = CommandProcessor()
        textPostProcessor = TextPostProcessor()
        vibrator = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            val manager = getSystemService(VibratorManager::class.java)
            manager?.defaultVibrator
        } else {
            @Suppress("DEPRECATION")
            getSystemService(Context.VIBRATOR_SERVICE) as Vibrator
        }

        whisperEngine.onStatus = { status ->
            mainHandler.post { statusText?.text = status }
        }

        backgroundHandler?.post {
            whisperEngine.load()
        }
    }

    override fun onCreateInputView(): View {
        val view = layoutInflater.inflate(R.layout.keyboard, null)
        micButton = view.findViewById(R.id.micButton)
        statusText = view.findViewById(R.id.statusText)

        updateStatusText("Tap to speak")

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
        isRecording = false
        micButton?.isSelected = false
        updateStatusText("Tap to speak")
    }

    private fun startRecording() {
        if (isRecording) return

        try {
            val sampleRate = 16000
            val channelConfig = AudioFormat.CHANNEL_IN_MONO
            val audioFormat = AudioFormat.ENCODING_PCM_16BIT
            val minBufferSize = AudioRecord.getMinBufferSize(sampleRate, channelConfig, audioFormat)
            val bufferSize = kotlin.math.max(minBufferSize, sampleRate)

            audioRecord = AudioRecord(
                MediaRecorder.AudioSource.MIC,
                sampleRate,
                channelConfig,
                audioFormat,
                bufferSize
            )

            audioSamples.reset()
            audioRecord?.startRecording()
            isRecording = true
            micButton?.isSelected = true
            startPulseAnimation()
            updateStatusText("Listening...")
            vibrate()

            recordingThread = Thread {
                val buffer = ByteArray(bufferSize)
                while (isRecording && !Thread.currentThread().isInterrupted) {
                    val bytesRead = audioRecord?.read(buffer, 0, buffer.size) ?: -1
                    if (bytesRead > 0) {
                        audioSamples.write(buffer, 0, bytesRead)
                    }
                }
            }
            recordingThread?.start()

        } catch (e: Exception) {
            Toast.makeText(this, "Failed to start recording: ${e.message}", Toast.LENGTH_SHORT).show()
            isRecording = false
            micButton?.isSelected = false
            updateStatusText("Tap to speak")
        }
    }

    private fun stopRecordingAndTranscribe() {
        if (!isRecording) return

        isRecording = false
        micButton?.isSelected = false
        stopPulseAnimation()
        updateStatusText("Processing...")

        try {
            audioRecord?.stop()
            audioRecord?.release()
        } catch (_: Exception) {}

        audioRecord = null

        try {
            recordingThread?.join(1000)
        } catch (_: Exception) {}
        recordingThread = null

        vibrate()

        val pcmData = audioSamples.toByteArray()
        audioSamples.reset()

        if (pcmData.size < 1600) {
            Toast.makeText(this, "Recording too short", Toast.LENGTH_SHORT).show()
            updateStatusText("Tap to speak")
            return
        }

        try {
            audioFile = File.createTempFile("whisper_record", ".wav", cacheDir)
            writeWavFile(audioFile!!, pcmData, 16000, 1, 16)
        } catch (e: Exception) {
            Toast.makeText(this, "Failed to save audio: ${e.message}", Toast.LENGTH_SHORT).show()
            updateStatusText("Tap to speak")
            return
        }

        backgroundHandler?.post {
            try {
                mainHandler.post { micButton?.isEnabled = false }

                val rawText = whisperEngine.transcribe(audioFile!!)

                mainHandler.post {
                    micButton?.isEnabled = true
                    if (rawText.isNotEmpty()) {
                        updateStatusText("Done")
                        processAndType(rawText)
                        mainHandler.postDelayed({ updateStatusText("Tap to speak") }, 2000)
                    } else {
                        Toast.makeText(this@WhisperIME, "No speech detected", Toast.LENGTH_SHORT).show()
                        updateStatusText("Tap to speak")
                    }
                }
            } catch (e: Exception) {
                mainHandler.post {
                    micButton?.isEnabled = true
                    Toast.makeText(this@WhisperIME, "Transcription failed: ${e.message}", Toast.LENGTH_SHORT).show()
                    updateStatusText("Tap to speak")
                }
            } finally {
                try { audioFile?.delete() } catch (_: Exception) {}
            }
        }
    }

    private fun processAndType(rawText: String) {
        val processed = commandProcessor.processText(rawText)
        var finalText = processed.text
        val actions = processed.actions

        finalText = applyCapsCommands(finalText, actions)
        finalText = textPostProcessor.process(finalText)

        val ic: InputConnection = currentInputConnection ?: return

        for (actionName in actions) {
            val cmd = commandProcessor.getCommand(actionName) ?: continue
            when (cmd.action) {
                "key" -> executeKeyAction(ic, cmd)
                "caps" -> {}
            }
        }

        if (finalText.isNotEmpty()) {
            ic.commitText(finalText, 1)
        }
    }

    private fun applyCapsCommands(text: String, actions: List<String>): String {
        val words = text.split(" ")
        val result = mutableListOf<String>()
        var capsMode: String? = null
        var actionIndex = 0

        for (word in words) {
            while (actionIndex < actions.size) {
                val cmd = commandProcessor.getCommand(actions[actionIndex])
                if (cmd?.action == "caps") {
                    capsMode = cmd.value
                    actionIndex++
                } else {
                    break
                }
            }

            val modified = when (capsMode) {
                "upper" -> word.uppercase()
                "lower" -> word.lowercase()
                "title" -> word.replaceFirstChar { it.uppercaseChar() }
                else -> word
            }
            result.add(modified)
            capsMode = null
        }

        return result.joinToString(" ")
    }

    private fun executeKeyAction(ic: InputConnection, cmd: VoiceCommand) {
        when (cmd.value) {
            "backspace" -> repeat(cmd.count) { ic.deleteSurroundingText(1, 0) }
            "ctrl_backspace" -> repeat(cmd.count) { deleteLastWord(ic) }
            "enter" -> repeat(cmd.count) {
                ic.sendKeyEvent(KeyEvent(KeyEvent.ACTION_DOWN, KeyEvent.KEYCODE_ENTER))
                ic.sendKeyEvent(KeyEvent(KeyEvent.ACTION_UP, KeyEvent.KEYCODE_ENTER))
            }
            "tab" -> {
                ic.sendKeyEvent(KeyEvent(KeyEvent.ACTION_DOWN, KeyEvent.KEYCODE_TAB))
                ic.sendKeyEvent(KeyEvent(KeyEvent.ACTION_UP, KeyEvent.KEYCODE_TAB))
            }
            "ctrl_z" -> {
                ic.sendKeyEvent(KeyEvent(KeyEvent.ACTION_DOWN, KeyEvent.KEYCODE_Z))
                ic.sendKeyEvent(KeyEvent(KeyEvent.ACTION_UP, KeyEvent.KEYCODE_Z))
            }
            "ctrl_y" -> {
                ic.sendKeyEvent(KeyEvent(KeyEvent.ACTION_DOWN, KeyEvent.KEYCODE_Y))
                ic.sendKeyEvent(KeyEvent(KeyEvent.ACTION_UP, KeyEvent.KEYCODE_Y))
            }
            "ctrl_a" -> {
                ic.sendKeyEvent(KeyEvent(KeyEvent.ACTION_DOWN, KeyEvent.KEYCODE_A))
                ic.sendKeyEvent(KeyEvent(KeyEvent.ACTION_UP, KeyEvent.KEYCODE_A))
            }
        }
    }

    private fun deleteLastWord(ic: InputConnection) {
        val before = ic.getTextBeforeCursor(256, 0) ?: return
        val trimmed = before.toString().trimEnd()
        val lastSpace = trimmed.lastIndexOf(' ')
        val charsToDelete = if (lastSpace >= 0) before.length - lastSpace else before.length
        ic.deleteSurroundingText(charsToDelete, 0)
    }

    private fun vibrate() {
        if (!AppPreferences.hapticsEnabled) return
        val v = vibrator ?: return
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            v.vibrate(VibrationEffect.createOneShot(30, VibrationEffect.DEFAULT_AMPLITUDE))
        } else {
            @Suppress("DEPRECATION")
            v.vibrate(30)
        }
    }

    private fun startPulseAnimation() {
        val button = micButton ?: return
        val scaleX = android.animation.ObjectAnimator.ofFloat(button, "scaleX", 1f, 1.12f, 1f).apply {
            duration = 800
            repeatCount = android.animation.ValueAnimator.INFINITE
            repeatMode = android.animation.ValueAnimator.RESTART
        }
        val scaleY = android.animation.ObjectAnimator.ofFloat(button, "scaleY", 1f, 1.12f, 1f).apply {
            duration = 800
            repeatCount = android.animation.ValueAnimator.INFINITE
            repeatMode = android.animation.ValueAnimator.RESTART
        }
        pulseAnimation = android.animation.AnimatorSet().apply {
            playTogether(scaleX, scaleY)
            start()
        }
    }

    private fun stopPulseAnimation() {
        pulseAnimation?.cancel()
        pulseAnimation = null
        micButton?.scaleX = 1f
        micButton?.scaleY = 1f
    }

    private fun updateStatusText(text: String) {
        statusText?.text = text
    }

    private fun writeWavFile(file: File, pcmData: ByteArray, sampleRate: Int, channels: Int, bitsPerSample: Int) {
        val totalDataLen = pcmData.size + 36
        val byteRate = sampleRate * channels * bitsPerSample / 8
        val blockAlign = channels * bitsPerSample / 8

        FileOutputStream(file).use {
            it.write(generateWavHeader(totalDataLen, sampleRate, byteRate, blockAlign, bitsPerSample, pcmData.size))
            it.write(pcmData)
        }
    }

    private fun generateWavHeader(
        totalDataLen: Int, sampleRate: Int, byteRate: Int,
        blockAlign: Int, bitsPerSample: Int, dataSize: Int
    ): ByteArray {
        val header = ByteArrayOutputStream(44)

        fun writeInt(value: Int, size: Int) {
            for (i in 0 until size) header.write((value shr (8 * i)) and 0xFF)
        }

        fun writeString(value: String) {
            for (c in value) header.write(c.code)
        }

        writeString("RIFF")
        writeInt(totalDataLen, 4)
        writeString("WAVE")
        writeString("fmt ")
        writeInt(16, 4)
        writeInt(1, 2)
        writeInt(1, 2)
        writeInt(sampleRate, 4)
        writeInt(byteRate, 4)
        writeInt(blockAlign, 2)
        writeInt(bitsPerSample, 2)
        writeString("data")
        writeInt(dataSize, 4)

        return header.toByteArray()
    }

    override fun onDestroy() {
        super.onDestroy()
        try {
            isRecording = false
            audioRecord?.apply { stop(); release() }
        } catch (_: Exception) {}
        audioRecord = null
        stopPulseAnimation()

        whisperEngine.destroy()
        backgroundThread.quitSafely()
    }
}
