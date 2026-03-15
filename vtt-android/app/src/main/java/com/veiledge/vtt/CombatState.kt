package com.veiledge.vtt

import java.util.*

data class CombatState(
    var round: Int = 1,
    var currentTurnIndex: Int = 0,
    val tokens: MutableList<Token> = mutableListOf(),
    var initiativeOrder: List<String> = emptyList() // token IDs in order
) {
    
    fun rollInitiative(): List<Token> {
        val newTokens = tokens.map { token ->
            val roll = (1..20).random() + 20 - token.ac
            token.copy(initiativeRoll = roll)
        }
        
        return newTokens.sortedBy { it.initiativeRoll }.also {
            // Update current turn index based on sorted order
            if (it.isNotEmpty()) {
                currentTurnIndex = it.indexOfFirst { it.id == tokens[currentTurnIndex].id } + 1
            }
        }
    }
    
    fun nextTurn(): Token? {
        val currentIndex = currentTurnIndex % tokens.size
        
        // Find the token with highest initiative roll that hasn't acted yet
        var nextToken: Token? = null
        for (i in currentIndex until tokens.size) {
            if (!tokens[i].isCurrentTurn && tokens[i].initiativeRoll != null) {
                nextToken = tokens[i]
                currentTurnIndex = i + 1
                break
            }
        }
        
        // If we're at the end of the list, go back to beginning
        if (nextToken == null) {
            for (i in 0 until currentIndex) {
                if (!tokens[i].isCurrentTurn && tokens[i].initiativeRoll != null) {
                    nextToken = tokens[i]
                    currentTurnIndex = i + 1
                    break
                }
            }
        }
        
        return nextToken
    }
    
    fun clearAll() {
        round = 1
        currentTurnIndex = 0
        tokens.clear()
        initiativeOrder.clear()
    }
}