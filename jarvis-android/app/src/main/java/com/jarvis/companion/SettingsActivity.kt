package com.jarvis.companion

import android.content.SharedPreferences
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.Switch
import androidx.appcompat.app.AppCompatActivity
import androidx.preference.PreferenceManager

class SettingsActivity : AppCompatActivity() {

    private lateinit var serverUrlEditText: EditText
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        setContentView(R.layout.activity_settings)

        serverUrlEditText = findViewById(R.id.serverUrlEditText)
        
        // Load current settings
        val sharedPreferences = PreferenceManager.getDefaultSharedPreferences(this)
        serverUrlEditText.setText(sharedPreferences.getString("server_url", "http://192.168.0.222:1234"))
    }
}