package com.veiledge.vtt

import android.content.Context
import android.graphics.*
import android.util.AttributeSet
import android.view.MotionEvent
import android.view.View
import androidx.core.content.ContextCompat
import java.util.*

class VTTView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
    defStyleAttr: Int = 0
) : View(context, attrs, defStyleAttr) {

    private val paint = Paint(Paint.ANTI_ALIAS_FLAG)
    
    // Grid properties
    var gridSize = 30
    var cellSize = 50f
    
    // Tokens list
    private val tokens = mutableListOf<Token>()
    
    // Touch handlers
    private var isDragging: Boolean = false
    private var draggedToken: Token? = null
    private var dragStartX: Float = 0f
    private var dragStartY: Float = 0f
    
    // Zoom and pan properties
    private var zoomScale = 1.0f
    private var offsetX = 0f
    private var offsetY = 0f
    
    init {
        setWillNotDraw(false)
    }
    
    override fun onSizeChanged(w: Int, h: Int, oldw: Int, oldh: Int) {
        super.onSizeChanged(w, h, oldw, oldh)
    }
    
    override fun onTouchEvent(event: MotionEvent): Boolean {
        when (event.action) {
            MotionEvent.ACTION_DOWN -> {
                val x = event.x
                val y = event.y
                
                // Check if we're clicking on a token
                for (token in tokens.reversed()) {
                    val screenX = offsetX + (token.x * cellSize)
                    val screenY = offsetY + (token.y * cellSize)
                    
                    if (Math.abs(x - screenX) < 40 && Math.abs(y - screenY) < 40) {
                        isDragging = true
                        draggedToken = token
                        dragStartX = x - screenX
                        dragStartY = y - screenY
                        return true
                    }
                }
                
                // Double tap to add new token
                if (event.pointerCount == 1 && event.actionMasked == MotionEvent.ACTION_DOWN) {
                    val downTime = event.getDownTime()
                    
                    for (p in event.pointers()) {
                        val currentTime = System.currentTimeMillis()
                        val timeDiff = currentTime - p.time
                        
                        // Check if it's a double tap
                        if (timeDiff < 300 && timeDiff > 0) {
                            addTokenAt(x, y)
                            return true
                        }
                    }
                }
            }
            
            MotionEvent.ACTION_MOVE -> {
                if (isDragging && draggedToken != null) {
                    val x = event.x - dragStartX
                    val y = event.y - dragStartY
                    
                    // Update token position with grid snapping
                    val snappedX = Math.round((x / cellSize + offsetX) / 50f) * 50f
                    val snappedY = Math.round((y / cellSize + offsetY) / 50f) * 50f
                    
                    draggedToken?.let {
                        it.x = (snappedX - offsetX) / cellSize
                        it.y = (snappedY - offsetY) / cellSize
                        
                        // Update UI
                        invalidate()
                    }
                } else if (event.pointerCount >= 2 && event.actionMasked == MotionEvent.ACTION_MOVE) {
                    // Two finger pinch zoom
                    val distance1 = event.getPointerCount().let { 
                        val p1 = event.getX(0)
                        val p2 = event.getY(0)
                        Math.sqrt((p1 - p2).pow(2))
                    }
                    
                    if (distance1 > 10f) {
                        val distance2 = event.getPointerCount().let {
                            val p3 = event.getX(it-1)
                            val p4 = event.getY(it-1)
                            Math.sqrt((p3 - p4).pow(2))
                        }
                        
                        // Calculate new scale based on pinch distance
                        val newScale = distance2 / distance1
                        
                        zoomScale *= newScale
                        invalidate()
                    } else {
                        // Two finger pan
                        if (event.getPointerCount() == 2) {
                            val dx = event.getX(0) - event.getX(1)
                            val dy = event.getY(0) - event.getY(1)
                            
                            offsetX += dx * zoomScale
                            offsetY += dy * zoomScale
                            invalidate()
                        }
                    }
                }
            }
            
            MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                if (isDragging && draggedToken != null) {
                    isDragging = false
                    draggedToken = null
                    
                    // Update token position with grid snapping
                    val x = event.x - dragStartX
                    val y = event.y - dragStartY
                    
                    val snappedX = Math.round((x / cellSize + offsetX) / 50f) * 50f
                    val snappedY = Math.round((y / cellSize + offsetY) / 50f) * 50f
                    
                    draggedToken?.let {
                        it.x = (snappedX - offsetX) / cellSize
                        it.y = (snappedY - offsetY) / cellSize
                        
                        // Update UI
                        invalidate()
                    }
                }
            }
        }
        
        return true
    }
    
    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        
        // Draw background grid
        drawGrid(canvas)
        
        // Draw tokens
        for (token in tokens.sortedBy { it.initiativeRoll }) {
            drawToken(canvas, token)
        }
    }
    
    private fun drawGrid(canvas: Canvas) {
        paint.color = Color.DKGRAY
        paint.alpha = 30
        
        val width = canvas.width.toFloat()
        val height = canvas.height.toFloat()
        
        // Calculate grid boundaries based on zoom and pan
        val startX = offsetX % cellSize
        val startY = offsetY % cellSize
        
        for (x in startX until width step cellSize) {
            paint.strokeWidth = 1f
            canvas.drawLine(x, startY, x, height, paint)
        }
        
        for (y in startY until height step cellSize) {
            paint.strokeWidth = 1f
            canvas.drawLine(startX, y, width, y, paint)
        }
    }
    
    private fun drawToken(canvas: Canvas, token: Token) {
        // Calculate screen position based on zoom and pan
        val screenX = offsetX + (token.x * cellSize)
        val screenY = offsetY + (token.y * cellSize)
        
        // Determine color based on type
        paint.color = when (token.type) {
            "player" -> Color.GREEN
            "enemy" -> Color.RED
            "npc" -> Color.BLUE
            else -> Color.YELLOW
        }
        
        // Draw token circle with border for current turn
        if (token.isCurrentTurn) {
            paint.style = Paint.Style.STROKE
            paint.strokeWidth = 5f
            canvas.drawCircle(screenX, screenY, 30f, paint)
            
            // Add pulsing animation effect
            val pulseOffset = Math.sin(System.currentTimeMillis() / 200).toFloat()
            paint.style = Paint.Style.FILL
            canvas.drawCircle(screenX + pulseOffset * 2, screenY - pulseOffset * 2, 28f, paint)
        } else {
            paint.style = Paint.Style.FILL
            canvas.drawCircle(screenX, screenY, 30f, paint)
        }
        
        // Draw token initials
        paint.color = Color.BLACK
        paint.textAlign = Paint.Align.CENTER
        paint.textSize = 16f
        canvas.drawText(token.name.substring(0, 2), screenX, screenY + 5, paint)
        
        // Draw HP bar below token
        val hpBarWidth = 60f
        val hpBarHeight = 8f
        
        paint.color = Color.DKGRAY
        canvas.drawRect(screenX - hpBarWidth/2, screenY + 35, 
                       screenX + hpBarWidth/2, screenY + 35 + hpBarHeight,
                       paint)
        
        // HP fill color based on health status
        val hpPercent = token.hp / token.maxHp
        
        if (hpPercent > 0.5) {
            paint.color = Color.GREEN
        } else if (hpPercent > 0.25) {
            paint.color = Color.YELLOW
        } else {
            paint.color = Color.RED
        }
        
        canvas.drawRect(screenX - hpBarWidth/2, screenY + 35,
                       screenX - hpBarWidth/2 + hpBarWidth * hpPercent,
                       screenY + 35 + hpBarHeight,
                       paint)
    }
    
    fun addTokenAt(x: Float, y: Float) {
        val token = Token(
            id = UUID.randomUUID().toString(),
            name = "New Token",
            type = "player",
            hp = 20,
            maxHp = 20,
            ac = 10,
            x = (x - offsetX) / cellSize,
            y = (y - offsetY) / cellSize
        )
        
        tokens.add(token)
        invalidate()
    }
    
    fun clearAll() {
        tokens.clear()
        invalidate()
    }

    data class Token(
        var id: String,
        val name: String,
        val type: String,
        var hp: Int,
        var maxHp: Int,
        var ac: Int,
        var x: Float,
        var y: Float
    )
}