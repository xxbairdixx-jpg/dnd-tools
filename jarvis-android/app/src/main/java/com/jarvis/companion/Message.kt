package com.jarvis.companion

data class Message(
    val id: String,
    val text: String? = null,
    val image: String? = null,
    val timestamp: Long = System.currentTimeMillis(),
    val isUser: Boolean = true
) {

    fun toChatMessage(): ChatMessage {
        return ChatMessage(
            id = this.id,
            text = this.text ?: "",
            image = this.image,
            timestamp = this.timestamp,
            senderType = if (this.isUser) SenderType.USER else SenderType.ASSISTANT
        )
    }
}

data class ChatMessage(
    val id: String,
    val text: String,
    val image: String? = null,
    val timestamp: Long,
    val senderType: SenderType
)

enum class SenderType {
    USER, ASSISTANT
}