package com.veiledge.vtt

import android.util.Log
import okhttp3.*
import java.io.IOException
import java.net.InetSocketAddress
import java.nio.channels.SocketChannel
import java.util.concurrent.ConcurrentHashMap

class WebSocketClient(private val context: Context) {
    private var socket: SocketChannel? = null
    
    // Map to store connected clients by token ID
    private val clients = ConcurrentHashMap<String, ClientConnection>()
    
    init {
        start()
    }
    
    fun connect(tokenId: String): Boolean {
        if (clients.containsKey(tokenId)) return true
        
        try {
            socket = SocketChannel.open(InetSocketAddress("localhost", 9001))
            
            // Create client connection
            val connection = ClientConnection(socket!!, tokenId)
            clients[tokenId] = connection
            
            Log.d("WebSocketClient", "Connected to server for token $tokenId")
            return true
        } catch (e: IOException) {
            Log.e("WebSocketClient", "Failed to connect: ${e.message}", e)
            return false
        }
    }
    
    fun disconnect(tokenId: String): Boolean {
        clients.remove(tokenId)?.close()
        return true
    }
    
    private inner class ClientConnection(private val socket: SocketChannel, 
                                        private val tokenId: String) : Runnable {
        
        override fun run() {
            try {
                // Create request
                val request = Request.Builder().url("ws://localhost:9001").build()
                
                // Connect and start reading/writing
                socket.connect(InetSocketAddress("localhost", 9001))
                socket.configureBlocking(false)
                
                // Read from server
                while (socket.isConnected) {
                    try {
                        if (socket.read(null) < 0) break
                        
                        // In a real implementation, we would read messages here
                        Log.d("WebSocketClient", "Received message for token $tokenId")
                        
                        // Send state updates back to server
                        sendStateUpdate()
                        
                    } catch (e: IOException) {
                        if (!socket.isConnected) {
                            Log.e("WebSocketClient", "Connection lost for token $tokenId")
                            break
                        }
                    }
                }
            } catch (e: Exception) {
                Log.e("WebSocketClient", "Error in client connection: ${e.message}", e)
            } finally {
                try {
                    socket.close()
                } catch (e: IOException) {
                    // Ignore
                }
            }
        }
        
        fun sendStateUpdate() {
            val state = buildStateMessage()
            
            if (!state.isNullOrEmpty()) {
                try {
                    val body = state.toByteArray(Charsets.UTF_8)
                    val request = Request.Builder().url("http://localhost:9000/state").post(
                        RequestBody.create(MediaType.parse("application/json"), body)
                    ).build()
                    
                    client.newCall(request).execute()
                } catch (e: IOException) {
                    Log.e("WebSocketClient", "Failed to send state update: ${e.message}")
                }
            }
        }
        
        private fun buildStateMessage(): String {
            // In a real implementation, we would construct the state message
            return "{ \"token\": \"$tokenId\", \"state\": { \"round\": 1 } }"
        }
    }
    
    fun close() {
        clients.values.forEach { it.close() }
        socket?.close()
    }
}