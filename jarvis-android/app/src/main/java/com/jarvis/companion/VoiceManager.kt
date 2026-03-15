package com.jarvis.companion

import android.speech.tts.TextToSpeech
import android.util.Log
import java.util.Locale

class VoiceManager(private val context: Context) {
    private var tts: TextToSpeech? = null
    
    fun initialize() {
        tts = TextToSpeech(context, TextToSpeech.OnInitListener { status ->
            if (status == TextToSpeech.SUCCESS) {
                // Set default language
                val result = tts?.setLanguage(Locale.US)
                
                if (result == TextToSpeech.LANG_MISSING_DATA || 
                    result == TextToSpeech.LANG_NOT_SUPPORTED) {
                    Log.e("VoiceManager", "Language not supported")
                } else {
                    Log.d("VoiceManager", "TTS initialized successfully")
                }
            } else {
                Log.e("VoiceManager", "TTS initialization failed")
            }
        })
    }

    fun speak(text: String) {
        tts?.speak(text, TextToSpeech.QUEUE_FLUSH, null)
    }

    fun stop() {
        tts?.stop()
    }

    fun shutdown() {
        if (tts != null) {
            tts?.shutdown()
            tts = null
        }
    }
}