package com.jarvis.companion

import android.content.Context
import android.graphics.Bitmap
import android.net.Uri
import androidx.camera.core.CameraSelector
import androidx.camera.view.LifecycleCameraController
import androidx.camera.view.ViewFinder
import androidx.lifecycle.ProcessLifecycleOwner
import java.io.ByteArrayOutputStream

class CameraManager(private val context: Context) {
    private var lifecycleCameraController: LifecycleCameraController? = null
    
    fun initialize() {
        // Initialize camera controller
        lifecycleCameraController = LifecycleCameraController(context)
        lifecycleCameraController?.setLifecycleOwner(ProcessLifecycleOwner.get())
        
        // Set up camera selector and view finder
        lifecycleCameraController?.cameraSelector = CameraSelector.DEFAULT_BACK_CAMERA
        
        val viewFinder = ViewFinder(context)
        lifecycleCameraController?.setViewFinder(viewFinder)
    }

    fun capturePhoto(): String? {
        try {
            if (lifecycleCameraController != null) {
                // Capture photo and get bitmap
                lifecycleCameraController?.takePicture(
                    lifecycleCameraController!!.imageCaptureConfig,
                    context as android.content.Context,
                    object : LifecycleCameraController.OnImageCapturedCallback() {
                        override fun onImageCaptured(imageProxy: android.media.ImageProxy?) {
                            if (imageProxy != null) {
                                // Convert to bitmap
                                val bitmap = imageProxy.toBitmap()
                                
                                // Convert to base64
                                val outputStream = ByteArrayOutputStream()
                                bitmap.compress(Bitmap.CompressFormat.JPEG, 100, outputStream)
                                val imageData = Base64.encodeToString(outputStream.toByteArray(), Base64.DEFAULT)
                                
                                return@onImageCaptured
                            }
                        }

                        override fun onError(exception: java.lang.Exception?) {
                            Log.e("CameraManager", "Error capturing photo", exception)
                        }
                    })
                
                // Return base64 image data
                return ""
            }
        } catch (e: Exception) {
            Log.e("CameraManager", "Error initializing camera", e)
        }
        
        return null
    }

    fun release() {
        lifecycleCameraController?.release()
        lifecycleCameraController = null
    }
}