package com.jarvis.companion

import android.content.Context
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import java.text.SimpleDateFormat
import java.util.*

class ChatAdapter(private val context: Context, private var messages: List<ChatMessage>) :
    RecyclerView.Adapter<RecyclerView.ViewHolder>() {

    companion object {
        const val VIEW_TYPE_USER = 0
        const val VIEW_TYPE_ASSISTANT = 1
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): RecyclerView.ViewHolder {
        return when (viewType) {
            VIEW_TYPE_USER -> UserViewHolder(
                LayoutInflater.from(context).inflate(R.layout.item_message_user, parent, false)
            )
            VIEW_TYPE_ASSISTANT -> AssistantViewHolder(
                LayoutInflater.from(context).inflate(R.layout.item_message_assistant, parent, false)
            )
            else -> throw IllegalArgumentException("Invalid view type")
        }
    }

    override fun onBindViewHolder(holder: RecyclerView.ViewHolder, position: Int) {
        when (holder.itemViewType) {
            VIEW_TYPE_USER -> {
                val userViewHolder = holder as UserViewHolder
                val message = messages[position]
                
                userViewHolder.messageText.text = message.text
                // Add timestamp if needed
            }
            VIEW_TYPE_ASSISTANT -> {
                val assistantViewHolder = holder as AssistantViewHolder
                val message = messages[position]
                
                assistantViewHolder.messageText.text = message.text
            }
        }
    }

    override fun getItemCount(): Int {
        return messages.size
    }

    override fun getItemViewType(position: Int): Int {
        return if (messages[position].senderType == SenderType.USER) {
            VIEW_TYPE_USER
        } else {
            VIEW_TYPE_ASSISTANT
        }
    }

    class UserViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        val messageText: TextView = itemView.findViewById(R.id.messageText)
    }

    class AssistantViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        val messageText: TextView = itemView.findViewById(R.id.messageText)
    }
}