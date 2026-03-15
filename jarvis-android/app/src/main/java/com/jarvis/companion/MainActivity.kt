package com.jarvis.companion

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.text.Editable
import android.text.TextWatcher
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.ImageView
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.jarvis.companion.Message.toChatMessage
import java.util.*

class MainActivity : AppCompatActivity() {

    private lateinit var recyclerView: RecyclerView
    private lateinit var chatAdapter: ChatAdapter
    private lateinit var editTextMessage: EditText
    
    // Push-to-Talk components
    private lateinit var pttButton: Button
    private lateinit var speechRecognizer: SpeechRecognizer
    private var isRecording = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        setContentView(R.layout.activity_chat)

        recyclerView = findViewById(R.id.recyclerViewMessages)
        editTextMessage = findViewById(R.id.editTextMessage)
        pttButton = findViewById(R.id.pttButton)
        
        // Initialize speech recognizer
        speechRecognizer = SpeechRecognizer.createSpeechRecognizer(this)
        speechRecognizer.setRecognitionListener(object : RecognitionListener {
            override fun onResults(results: Bundle?) {
                if (results != null) {
                    val speechText = results.getString(SpeechRecognizer.RESULTS_RECOGNITION)
                    editTextMessage.setText(speechText)
                    stopRecording()
                }
            }

            override fun onError(errorCode: Int) {}
            override fun onReady() {}
            override fun onPartialResults(p0: Bundle?) {}
            override fun onEvent(eventType: Int, params: Bundle?) {}
        })

        // Set up RecyclerView
        recyclerView.layoutManager = LinearLayoutManager(this)
        chatAdapter = ChatAdapter(this, emptyList())
        recyclerView.adapter = chatAdapter

        // Setup text watcher for auto-send
        editTextMessage.addTextChangedListener(object : TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {
                // Auto send when user presses enter
                if (s != null && s.isNotEmpty() && s.last().toString() == "\n") {
                    sendMessage(s.toString().dropLast(1))
                }
            }

            override fun afterTextChanged(s: Editable?) {}
        })

        // Setup buttons
        val sendButton = findViewById<Button>(R.id.sendButton)
        sendButton.setOnClickListener { sendMessage(editTextMessage.text.toString()) }
        
        pttButton.setOnClickListener {
            if (!isRecording) {
                startRecording()
            } else {
                stopRecording()
            }
        }

        val cameraButton = findViewById<Button>(R.id.cameraButton)
        cameraButton.setOnClickListener { openCamera() }
    }

    private fun sendMessage(text: String) {
        // Create message
        val newMessage = Message(
            id = UUID.randomUUID().toString(),
            text = text,
            timestamp = System.currentTimeMillis()
        )
        
        // Add to adapter
        chatAdapter.addMessage(newMessage)
        chatAdapter.notifyDataSetChanged()
        
        // Scroll to bottom
        recyclerView.scrollToPosition(chatAdapter.itemCount - 1)

        // Clear input field
        editTextMessage.setText("")
    }

    private fun startRecording() {
        isRecording = true
        
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
        
        speechRecognizer.startListening(intent)
        pttButton.setBackgroundResource(R.color.ptt_button_recording) // Red color while recording
    }

    private fun stopRecording() {
        isRecording = false
        
        if (speechRecognizer.isListening) {
            speechRecognizer.stopListening()
        }
        
        pttButton.setBackgroundResource(R.color.ptt_button_normal)
    }

    private fun openCamera() {
        val intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
        startActivityForResult(intent, REQUEST_CODE_CAMERA)
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Bundle?) {
        super.onActivityResult(requestCode, resultCode, data)

        if (requestCode == REQUEST_CODE_CAMERA && resultCode == RESULT_OK) {
            // Handle captured image
            val imageBitmap = data?.get("data") as Bitmap
            
            // Convert to base64
            val imageBytes = ByteArrayOutputStream()
            imageBitmap.compress(Bitmap.CompressFormat.JPEG, 100, imageBytes)
            val imageData = Base64.encodeToString(imageBytes.toByteArray(), Base64.DEFAULT)

            // Create message with image
            val newMessage = Message(
                id = UUID.randomUUID().toString(),
                text = "Photo captured",
                image = imageData,
                timestamp = System.currentTimeMillis()
            )
            
            chatAdapter.addMessage(newMessage)
            chatAdapter.notifyDataSetChanged()
        }
    }

    companion object {
        private const val REQUEST_CODE_CAMERA = 1001
    }
}