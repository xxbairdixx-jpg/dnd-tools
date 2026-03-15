package com.veiledge.vtt

import android.util.Log
import kotlinx.coroutines.*
import okhttp3.*
import java.io.IOException

class CommandServer(private val context: Context) {
    private var client: OkHttpClient = OkHttpClient()
    
    // Polling job for commands
    private var pollingJob: Job? = null
    
    fun startPolling(interval: Long = 500) {
        pollingJob?.cancel()
        
        pollingJob = CoroutineScope(Dispatchers.IO).launch {
            while (true) {
                try {
                    val response = client.newCall(Request.Builder().url("http://localhost:9000/commands").build()).execute()
                    
                    if (!response.isSuccessful) {
                        Log.e("CommandServer", "Error fetching commands: ${response.code}")
                        continue
                    }
                    
                    val body = response.body?.string()
                    if (body != null && body.trim().isNotEmpty()) {
                        try {
                            parseCommands(body)
                        } catch (e: Exception) {
                            Log.e("CommandServer", "Failed to parse commands: $e")
                        }
                    }
                } catch (e: IOException) {
                    Log.e("CommandServer", "Network error: ${e.message}")
                }
                
                delay(interval)
            }
        }
    }
    
    private suspend fun parseCommands(commandsString: String) {
        val commands = commandsString.split(";").map { it.trim() }.filter { it.isNotEmpty() }
        
        for (command in commands) {
            try {
                when {
                    command.startsWith("add_token") -> handleAddToken(command)
                    command.startsWith("move_token") -> handleMoveToken(command)
                    command.startsWith("damage_token") -> handleDamageToken(command)
                    command.startsWith("heal_token") -> handleHealToken(command)
                    command.startsWith("remove_token") -> handleRemoveToken(command)
                    command.startsWith("roll_initiative") -> handleRollInitiative()
                    command.startsWith("next_turn") -> handleNextTurn()
                    command.startsWith("set_condition") -> handleSetCondition(command)
                    command.startsWith("remove_condition") -> handleRemoveCondition(command)
                    command.startsWith("load_map") -> handleLoadMap(command)
                    command.startsWith("clear_all") -> handleClearAll()
                    else -> Log.w("CommandServer", "Unknown command: $command")
                }
            } catch (e: Exception) {
                Log.e("CommandServer", "Error processing command '$command': ${e.message}")
            }
        }
    }
    
    private suspend fun handleAddToken(command: String) {
        val parts = command.split(",").map { it.trim() }
        
        if (parts.size < 6) return
        
        val id = parts[1]
        val name = parts[2]
        val type = parts[3]
        val hp = parts[4].toIntOrNull() ?: 0
        val maxHp = parts[5].toIntOrNull() ?: 20
        val ac = parts[6].toIntOrNull() ?: 10
        
        // Find the view to update
        val vttView = context.applicationContext?.findViewById(com.veiledge.vtt.VTTView::class.java)
        
        if (vttView != null) {
            vttView.addTokenAt(vttView.width / 2f, vttView.height / 2f)
            
            // Update state
            val token = Token(
                id = id,
                name = name,
                type = type,
                hp = hp,
                maxHp = maxHp,
                ac = ac,
                x = 0f,
                y = 0f
            )
            
            vttView.tokens.add(token)
        }
    }
    
    private suspend fun handleMoveToken(command: String) {
        val parts = command.split(",").map { it.trim() }
        
        if (parts.size < 5) return
        
        val id = parts[1]
        val x = parts[2].toFloat()
        val y = parts[3].toFloat()
        
        // Find the view and token
        val vttView = context.applicationContext?.findViewById(com.veiledge.vtt.VTTView::class.java)
        
        if (vttView != null) {
            for (token in vttView.tokens) {
                if (token.id == id) {
                    token.x = x / 50f
                    token.y = y / 50f
                    
                    // Update UI
                    vttView.invalidate()
                    break
                }
            }
        }
    }
    
    private suspend fun handleDamageToken(command: String) {
        val parts = command.split(",").map { it.trim() }
        
        if (parts.size < 3) return
        
        val id = parts[1]
        val amount = parts[2].toIntOrNull() ?: 0
        
        // Find the view and token
        val vttView = context.applicationContext?.findViewById(com.veiledge.vtt.VTTView::class.java)
        
        if (vttView != null) {
            for (token in vttView.tokens) {
                if (token.id == id) {
                    token.hp -= amount
                    if (token.hp < 0) token.hp = 0
                    
                    // Update UI
                    vttView.invalidate()
                    break
                }
            }
        }
    }
    
    private suspend fun handleHealToken(command: String) {
        val parts = command.split(",").map { it.trim() }
        
        if (parts.size < 3) return
        
        val id = parts[1]
        val amount = parts[2].toIntOrNull() ?: 0
        
        // Find the view and token
        val vttView = context.applicationContext?.findViewById(com.veiledge.vtt.VTTView::class.java)
        
        if (vttView != null) {
            for (token in vttView.tokens) {
                if (token.id == id) {
                    token.hp += amount
                    if (token.hp > token.maxHp) token.hp = token.maxHp
                    
                    // Update UI
                    vttView.invalidate()
                    break
                }
            }
        }
    }
    
    private suspend fun handleRemoveToken(command: String) {
        val parts = command.split(",").map { it.trim() }
        
        if (parts.size < 2) return
        
        val id = parts[1]
        
        // Find the view and token
        val vttView = context.applicationContext?.findViewById(com.veiledge.vtt.VTTView::class.java)
        
        if (vttView != null) {
            vttView.tokens.removeAll { it.id == id }
            
            // Update UI
            vttView.invalidate()
        }
    }
    
    private suspend fun handleRollInitiative() {
        val vttView = context.applicationContext?.findViewById(com.veiledge.vtt.VTTView::class.java)
        
        if (vttView != null) {
            for (token in vttView.tokens) {
                token.initiativeRoll = (1..20).random() + 20 - token.ac
            }
            
            // Sort tokens by initiative roll
            val sortedTokens = vttView.tokens.sortedBy { it.initiativeRoll }.also {
                if (it.isNotEmpty()) {
                    for ((index, token) in it.withIndex()) {
                        token.isCurrentTurn = index == 0
                    }
                }
            }
            
            // Update UI
            vttView.invalidate()
        }
    }
    
    private suspend fun handleNextTurn() {
        val vttView = context.applicationContext?.findViewById(com.veiledge.vtt.VTTView::class.java)
        
        if (vttView != null) {
            for ((index, token) in vttView.tokens.withIndex()) {
                token.isCurrentTurn = index == 0
            }
            
            // Update UI
            vttView.invalidate()
        }
    }
    
    private suspend fun handleSetCondition(command: String) {
        val parts = command.split(",").map { it.trim() }
        
        if (parts.size < 3) return
        
        val id = parts[1]
        val condition = parts[2]
        
        // Find the view and token
        val vttView = context.applicationContext?.findViewById(com.veiledge.vtt.VTTView::class.java)
        
        if (vttView != null) {
            for (token in vttView.tokens) {
                if (token.id == id) {
                    if (!token.conditions.contains(condition)) {
                        token.conditions.add(condition)
                        
                        // Update UI
                        vttView.invalidate()
                    }
                    break
                }
            }
        }
    }
    
    private suspend fun handleRemoveCondition(command: String) {
        val parts = command.split(",").map { it.trim() }
        
        if (parts.size < 3) return
        
        val id = parts[1]
        val condition = parts[2]
        
        // Find the view and token
        val vttView = context.applicationContext?.findViewById(com.veiledge.vtt.VTTView::class.java)
        
        if (vttView != null) {
            for (token in vttView.tokens) {
                if (token.id == id && token.conditions.contains(condition)) {
                    token.conditions.remove(condition)
                    
                    // Update UI
                    vttView.invalidate()
                    break
                }
            }
        }
    }
    
    private suspend fun handleLoadMap(command: String) {
        val parts = command.split(",").map { it.trim() }
        
        if (parts.size < 2) return
        
        val imageUrl = parts[1]
        
        // Find the view
        val vttView = context.applicationContext?.findViewById(com.veiledge.vtt.VTTView::class.java)
        
        if (vttView != null) {
            // In a real implementation, we would load the image here
            Log.d("CommandServer", "Loading map from URL: $imageUrl")
            
            // Update UI - in a real app you'd update background
            vttView.invalidate()
        }
    }
    
    private suspend fun handleClearAll() {
        val vttView = context.applicationContext?.findViewById(com.veiledge.vtt.VTTView::class.java)
        
        if (vttView != null) {
            vttView.clearAll()
        }
    }
}