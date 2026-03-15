package com.veiledge.vtt

import java.util.*

data class Token(
    var id: String,
    val name: String,
    val type: String, // player/enemy/npc/neutral
    var hp: Int,
    var maxHp: Int,
    var ac: Int,
    var x: Float,
    var y: Float,
    var conditions: List<String> = emptyList(),
    var initiativeRoll: Int? = null,
    var isCurrentTurn: Boolean = false
) {
    
    fun damage(amount: Int): Int {
        hp -= amount
        if (hp < 0) hp = 0
        return hp
    }
    
    fun heal(amount: Int): Int {
        hp += amount
        if (hp > maxHp) hp = maxHp
        return hp
    }
}