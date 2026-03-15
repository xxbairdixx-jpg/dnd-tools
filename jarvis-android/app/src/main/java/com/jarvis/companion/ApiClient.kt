package com.jarvis.companion

import android.content.Context
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody.Part
import okhttp3.RequestBody.Companion.asRequestBody
import java.io.File
import java.util.concurrent.TimeUnit

class ApiClient(private val context: Context) {
    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .build()

    fun sendMessage(message: String): Call {
        // Create request body
        val requestBody = MultipartBody.Builder().setType(MultipartBody.FORM)
            .addFormDataPart("messages", message)
            .build()
        
        return client.newCall(Request.Builder()
            .url("http://192.168.0.222:1234/v1/chat/completions")
            .post(requestBody)
            .build())
    }

    fun sendImage(imagePath: String): Call {
        val file = File(imagePath)
        val requestBody = MultipartBody.Builder().setType(MultipartBody.FORM)
            .addFormDataPart("messages", "Image message")
            .addFormDataPart("image", file.name, file.asRequestBody("image/jpeg".toMediaType()))
            .build()
        
        return client.newCall(Request.Builder()
            .url("http://192.168.0.222:1234/v1/chat/completions")
            .post(requestBody)
            .build())
    }
}