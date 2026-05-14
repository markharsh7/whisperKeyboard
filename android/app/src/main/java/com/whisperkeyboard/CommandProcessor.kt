package com.whisperkeyboard

data class ProcessedText(val text: String, val actions: List<String>)

class CommandProcessor {

    private val commandMap: Map<String, VoiceCommand> = buildCommandMap()

    private fun buildCommandMap(): Map<String, VoiceCommand> {
        val map = mutableMapOf<String, VoiceCommand>()
        for (cmd in VoiceCommands.all) {
            for (phrase in cmd.allPhrases()) {
                map[phrase.lowercase()] = cmd
            }
        }
        return map
    }

    fun processText(text: String): ProcessedText {
        if (text.isBlank()) return ProcessedText(text, emptyList())

        val words = text.split("\\s+".toRegex())
        val outputParts = mutableListOf<String>()
        val actions = mutableListOf<String>()
        var i = 0

        while (i < words.size) {
            var matched = false
            for (j in words.size downTo i + 1) {
                val candidate = words.subList(i, j).joinToString(" ").lowercase()
                val cmd = commandMap[candidate]
                if (cmd != null) {
                    actions.add(cmd.phrase)
                    if (cmd.action == "text") {
                        outputParts.add(cmd.value)
                    }
                    i = j
                    matched = true
                    break
                }
            }
            if (!matched) {
                outputParts.add(words[i])
                i++
            }
        }

        val result = outputParts.joinToString(" ")
        return ProcessedText(result, actions)
    }

    fun getCommand(phrase: String): VoiceCommand? = commandMap[phrase.lowercase()]
}
