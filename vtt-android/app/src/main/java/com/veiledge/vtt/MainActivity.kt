package com.veiledge.vtt

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.util.*

class MainActivity : AppCompatActivity() {
    
    private lateinit var vttView: VTTView
    private lateinit var commandServer: CommandServer
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Set dark theme
        setTheme(R.style.AppTheme)
        
        setContentView(R.layout.activity_main)
        
        vttView = findViewById(R.id.vtt_view)
        commandServer = CommandServer(this)
        
        // Start polling for commands
        commandServer.startPolling()
    }
    
    override fun onDestroy() {
        super.onDestroy()
        
        // Stop polling and close connections
        commandServer.pollingJob?.cancel()
        commandServer.close()
    }
}