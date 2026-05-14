package com.whisperkeyboard

import android.os.Bundle
import android.widget.Button
import android.widget.RadioGroup
import android.widget.Spinner
import android.widget.Switch
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import java.io.File

class SettingsActivity : AppCompatActivity() {

    private lateinit var modelSpinner: Spinner
    private lateinit var languageGroup: RadioGroup
    private lateinit var tapToTalkSwitch: Switch
    private lateinit var hapticsSwitch: Switch
    private lateinit var downloadModelButton: Button
    private lateinit var clearCacheButton: Button

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_settings)

        AppPreferences.init(this)

        modelSpinner = findViewById(R.id.modelSpinner)
        languageGroup = findViewById(R.id.languageGroup)
        tapToTalkSwitch = findViewById(R.id.tapToTalkSwitch)
        hapticsSwitch = findViewById(R.id.hapticsSwitch)
        downloadModelButton = findViewById(R.id.downloadModelButton)
        clearCacheButton = findViewById(R.id.clearCacheButton)

        loadCurrentSettings()
        setupListeners()
    }

    private fun loadCurrentSettings() {
        val models = resources.getStringArray(R.array.model_values)
        val modelIndex = models.indexOf(AppPreferences.modelSize)
        val adapter = android.widget.ArrayAdapter.createFromResource(
            this, R.array.model_values, android.R.layout.simple_spinner_item
        )
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
        modelSpinner.adapter = adapter
        if (modelIndex >= 0) modelSpinner.setSelection(modelIndex)

        when (AppPreferences.language) {
            "en" -> languageGroup.check(R.id.langEnglish)
            "hi" -> languageGroup.check(R.id.langHinglish)
            else -> languageGroup.check(R.id.langAuto)
        }

        tapToTalkSwitch.isChecked = AppPreferences.tapToTalk
        hapticsSwitch.isChecked = AppPreferences.hapticsEnabled

        val engine = WhisperEngine(this)
        if (engine.isModelAvailable()) {
            downloadModelButton.text = "Model downloaded (${formatSize(engine.getModelFile())})"
            downloadModelButton.isEnabled = false
        } else {
            downloadModelButton.text = "Download Model (~484 MB)"
        }
    }

    private fun setupListeners() {
        modelSpinner.onItemSelectedListener = object : android.widget.AdapterView.OnItemSelectedListener {
            override fun onItemSelected(parent: android.widget.AdapterView<*>?, view: android.view.View?, position: Int, id: Long) {
                AppPreferences.modelSize = parent?.getItemAtPosition(position).toString()
            }
            override fun onNothingSelected(parent: android.widget.AdapterView<*>?) {}
        }

        languageGroup.setOnCheckedChangeListener { _, checkedId ->
            AppPreferences.language = when (checkedId) {
                R.id.langEnglish -> "en"
                R.id.langHinglish -> "hi"
                else -> "auto"
            }
        }

        tapToTalkSwitch.setOnCheckedChangeListener { _, isChecked ->
            AppPreferences.tapToTalk = isChecked
        }

        hapticsSwitch.setOnCheckedChangeListener { _, isChecked ->
            AppPreferences.hapticsEnabled = isChecked
        }

        downloadModelButton.setOnClickListener {
            downloadModelButton.text = "Downloading..."
            downloadModelButton.isEnabled = false
            Thread {
                val engine = WhisperEngine(this)
                val result = engine.ensureModel()
                runOnUiThread {
                    if (result != null) {
                        downloadModelButton.text = "Model downloaded (${formatSize(result)})"
                        Toast.makeText(this, "Model downloaded successfully", Toast.LENGTH_SHORT).show()
                    } else {
                        downloadModelButton.text = "Download failed — tap to retry"
                        downloadModelButton.isEnabled = true
                        Toast.makeText(this, "Download failed. Check internet connection.", Toast.LENGTH_LONG).show()
                    }
                }
            }.start()
        }

        clearCacheButton.setOnClickListener {
            val engine = WhisperEngine(this)
            engine.destroy()
            val modelFile = engine.getModelFile()
            if (modelFile.exists()) {
                modelFile.delete()
                downloadModelButton.text = "Download Model (~484 MB)"
                downloadModelButton.isEnabled = true
                Toast.makeText(this, "Model cache cleared", Toast.LENGTH_SHORT).show()
            } else {
                Toast.makeText(this, "No model to clear", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun formatSize(file: File): String {
        val sizeMb = file.length() / (1024 * 1024)
        return "$sizeMb MB"
    }
}
