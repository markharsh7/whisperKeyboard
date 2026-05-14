package com.whisperkeyboard

class TextPostProcessor {

    private val hinglishCorrections = mapOf(
        "mein" to "main",
        "hein" to "hain",
        "he" to "hai",
        "theek" to "theek",
        "acha" to "accha",
        "aacha" to "accha",
        "bahut" to "bahut",
        "bohot" to "bahut",
        "kyun" to "kyun",
        "kyu" to "kyun",
        "sch" to "sh",
    )

    private val alwaysCapitalize = setOf("i", "i'm", "i'll", "i've", "i'd")

    private val devanagariStart = 0x0900
    private val devanagariEnd = 0x097F

    private val independentVowels = mapOf(
        'अ' to "a", 'आ' to "aa", 'इ' to "i", 'ई' to "ee", 'उ' to "u", 'ऊ' to "oo",
        'ए' to "e", 'ऐ' to "ai", 'ओ' to "o", 'औ' to "au", 'ऋ' to "ri",
    )

    private val vowelSigns = mapOf(
        'ा' to "aa", 'ि' to "i", 'ी' to "ee", 'ु' to "u", 'ू' to "oo",
        'े' to "e", 'ै' to "ai", 'ो' to "o", 'ौ' to "au", 'ृ' to "ri",
    )

    private val consonants = mapOf(
        "क" to "ka", "ख" to "kha", "ग" to "ga", "घ" to "gha", "ङ" to "nga",
        "च" to "cha", "छ" to "chha", "ज" to "ja", "झ" to "jha", "ञ" to "nya",
        "ट" to "ta", "ठ" to "tha", "ड" to "da", "ढ" to "dha", "ण" to "na",
        "त" to "ta", "थ" to "tha", "द" to "da", "ध" to "dha", "न" to "na",
        "प" to "pa", "फ" to "pha", "ब" to "ba", "भ" to "bha", "म" to "ma",
        "य" to "ya", "र" to "ra", "ल" to "la", "व" to "va",
        "श" to "sha", "ष" to "sha", "स" to "sa", "ह" to "ha",
        "क्ष" to "ksha", "त्र" to "tra", "ज्ञ" to "gya", "श्र" to "shra",
        "क़" to "qa", "ख़" to "kha", "ग़" to "gha", "ज़" to "za", "ड़" to "da", "ढ़" to "dha",
        "फ़" to "fa", "य़" to "ya",
    )

    private val consonantLengths = consonants.keys.map { it.length }.maxOrNull() ?: 1

    private val nasal = mapOf("ं" to "n", "ँ" to "n")
    private val halant = "्"
    private val visarga = "ः"

    private val digits = mapOf(
        "०" to "0", "१" to "1", "२" to "2", "३" to "3", "४" to "4",
        "५" to "5", "६" to "6", "७" to "7", "८" to "8", "९" to "9",
    )

    fun process(text: String, language: String = "auto", detectedLanguage: String? = null): String {
        var result = text.trim()
        if (result.isEmpty()) return ""

        if (detectedLanguage == "hi" || language == "hi" && hasDevanagari(result)) {
            result = transliterateDevanagari(result)
        } else if (hasDevanagari(result)) {
            result = transliterateDevanagari(result)
        }

        if (language == "hi" || language == "auto") {
            result = applyHinglishCorrections(result)
        }

        result = removeLeadingTrailingSpace(result)
        if (result.isNotEmpty() && result[0].isLetter()) {
            result = result[0].uppercaseChar() + result.substring(1)
        }

        result = capitalizeI(result)
        result = fixSpacingAfterPunctuation(result)
        result = capitalizeSentences(result)

        return result
    }

    private fun hasDevanagari(text: String): Boolean =
        text.any { it.code in devanagariStart..devanagariEnd }

    private fun transliterateDevanagari(text: String): String {
        if (!hasDevanagari(text)) return text

        val result = mutableListOf<String>()
        var i = 0
        while (i < text.length) {
            val c = text[i]
            val codepoint = c.code

            if (codepoint !in devanagariStart..devanagariEnd) {
                result.add(c.toString())
                i++
                continue
            }

            if (c in independentVowels) {
                result.add(independentVowels[c]!!)
                i++
                continue
            }

            // Try to match consonants longest-first (for conjuncts like क्ष)
            var matchedConsonant = false
            for (len in consonantLengths downTo 1) {
                if (i + len <= text.length) {
                    val sub = text.substring(i, i + len)
                    if (sub in consonants) {
                        var base = consonants[sub]!!
                        i += len

                        if (i < text.length) {
                            val nextC = text[i]

                            if (nextC in vowelSigns) {
                                val vowel = vowelSigns[nextC]!!
                                base = if (base.endsWith('a')) {
                                    base.dropLast(1) + vowel
                                } else {
                                    base + vowel
                                }
                                i++
                            } else if (nextC.toString() == halant) {
                                base = base.dropLast(1)
                                i++
                            }

                            if (i < text.length && text[i].toString() in nasal) {
                                base += nasal[text[i].toString()]!!
                                i++
                            }

                            if (i < text.length && text[i].toString() == visarga) {
                                base += 'h'
                                i++
                            }
                        }

                        result.add(base)
                        matchedConsonant = true
                        break
                    }
                }
            }
            if (matchedConsonant) continue

            if (c in vowelSigns) {
                result.add(vowelSigns[c]!!)
                i++
                continue
            }

            if (c.toString() in nasal) {
                result.add(nasal[c.toString()]!!)
                i++
                continue
            }

            if (c.toString() == visarga) {
                result.add("h")
                i++
                continue
            }

            if (c.toString() == halant) {
                i++
                continue
            }

            if (c.toString() in digits) {
                result.add(digits[c.toString()]!!)
                i++
                continue
            }

            i++
        }

        return applySchwaDeletion(result.joinToString(""))
    }

    private fun applySchwaDeletion(text: String): String {
        val words = text.split(" ")
        val result = words.map { word ->
            var w = word
            val consonantsCount = w.count { it in 'b'..'z' && it !in "aeiou" }
            val vowelsCount = w.count { it in "aeiou" }
            if (w.endsWith("aa") && consonantsCount >= vowelsCount) {
                w = w.dropLast(2) + "a"
            } else if (w.length > 1 && w.endsWith('a') && w[w.length - 2] !in "aeiou") {
                w = w.dropLast(1)
            }
            w
        }
        return result.joinToString(" ")
    }

    private fun applyHinglishCorrections(text: String): String {
        val words = text.split(" ")
        val corrected = words.map { word ->
            val lower = word.lowercase()
            hinglishCorrections[lower] ?: word
        }
        return corrected.joinToString(" ")
    }

    private fun capitalizeI(text: String): String {
        val words = text.split(" ")
        val result = words.map { word ->
            val stripped = word.trim { it in ".,!?;:'\"" }
            val lower = stripped.lowercase()
            if (lower in alwaysCapitalize) {
                word.replace(stripped, stripped.replaceFirstChar { it.uppercaseChar() })
            } else {
                word
            }
        }
        return result.joinToString(" ")
    }

    private fun capitalizeSentences(text: String): String {
        val parts = text.split("(?<=[.!?])\\s+".toRegex())
        return parts.mapIndexed { i, part ->
            if (i == 0 || part.isNotEmpty() && part[0].isLetter()) {
                part.replaceFirstChar { it.uppercaseChar() }
            } else {
                part
            }
        }.joinToString(" ")
    }

    private fun fixSpacingAfterPunctuation(text: String): String {
        var result = text.replace("\\s+([.,!?;:])".toRegex(), "$1")
        result = result.replace("([.,!?;:])([^\\s\\d])".toRegex(), "$1 $2")
        return result
    }

    private fun removeLeadingTrailingSpace(text: String): String = text.trim()
}
