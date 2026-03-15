#!/bin/bash
# Hands-free Voice Chat with Jarvis (Hunter Alpha)
# Continuous listening - just talk!
# Ctrl+C to stop

VOICE="en-US-AndrewMultilingualNeural"
OUTDIR="$HOME/voice-profiles/chat"
API_KEY="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"
MODEL="openrouter/hunter-alpha"
mkdir -p "$OUTDIR"

# Conversation history
HISTORY='[{"role": "system", "content": "You are Jarvis, a sharp, competent AI assistant. Keep responses concise (2-4 sentences) since they will be spoken aloud. Be natural and conversational. You are helping Kevin (xXBairdiXx) with D&D campaigns, coding, and general tasks."}]'

cleanup() {
    echo ""
    echo "🔇 Voice chat ended."
    exit 0
}
trap cleanup SIGINT SIGTERM

echo "🎙️ JARVIS - Hands-Free Voice Chat"
echo "=================================="
echo "Model: Hunter Alpha | Voice: Andrew"
echo "Just start talking! Ctrl+C to stop."
echo ""

# Startup greeting
edge-tts --voice "$VOICE" --text "Voice chat activated. I'm all ears, Kevin." --write-media "$OUTDIR/startup.mp3" 2>/dev/null
termux-media-player play "$OUTDIR/startup.mp3" 2>/dev/null
sleep 3

LOOP=0
while true; do
    LOOP=$((LOOP + 1))
    echo "🔴 Listening... (turn $LOOP)"
    
    TEXT=$(termux-speech-to-text 2>/dev/null)
    
    if [ -z "$TEXT" ] || [ ${#TEXT} -lt 3 ]; then
        echo "   ⏭️  No speech, retrying..."
        continue
    fi
    
    echo "📝 You: $TEXT"
    echo "🤔 Thinking..."
    
    # Escape for JSON
    ESCAPED=$(python3 -c "import sys,json; print(json.dumps(sys.argv[1]))" "$TEXT")
    
    # Add user message to history
    HISTORY=$(python3 -c "
import sys, json
hist = json.loads(sys.argv[1])
hist.append({'role': 'user', 'content': sys.argv[2]})
print(json.dumps(hist))
" "$HISTORY" "$TEXT")
    
    # Call OpenRouter API
    RESPONSE=$(curl -s -X POST "https://openrouter.ai/api/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $API_KEY" \
        -d "{\"model\": \"$MODEL\", \"messages\": $HISTORY, \"max_tokens\": 300}" 2>/dev/null)
    
    REPLY_TEXT=$(echo "$RESPONSE" | python3 -c "
import sys,json
try:
    d = json.load(sys.stdin)
    print(d['choices'][0]['message']['content'])
except:
    print('')
" 2>/dev/null)
    
    if [ -z "$REPLY_TEXT" ]; then
        echo "❌ API error, retrying..."
        # Remove failed user message from history
        HISTORY=$(python3 -c "
import sys,json
hist = json.loads(sys.argv[1])
if hist and hist[-1]['role'] == 'user':
    hist = hist[:-1]
print(json.dumps(hist))
" "$HISTORY")
        continue
    fi
    
    echo "💬 Jarvis: $REPLY_TEXT"
    
    # Add assistant response to history
    HISTORY=$(python3 -c "
import sys,json
hist = json.loads(sys.argv[1])
hist.append({'role': 'assistant', 'content': sys.argv[2]})
print(json.dumps(hist))
" "$HISTORY" "$REPLY_TEXT")
    
    # Keep history manageable (last 20 messages)
    HISTORY=$(python3 -c "
import sys,json
hist = json.loads(sys.argv[1])
if len(hist) > 21:  # system + 20 messages
    hist = [hist[0]] + hist[-20:]
print(json.dumps(hist))
" "$HISTORY")
    
    # Generate speech
    OUTFILE="$OUTDIR/reply_${LOOP}.mp3"
    edge-tts --voice "$VOICE" --text "$REPLY_TEXT" --write-media "$OUTFILE" 2>/dev/null
    
    # Play
    termux-media-player play "$OUTFILE" 2>/dev/null
    
    # Wait for playback
    DURATION=$(( ${#REPLY_TEXT} / 12 + 2 ))
    sleep $DURATION
    
    echo "✅ Done"
    echo ""
done
