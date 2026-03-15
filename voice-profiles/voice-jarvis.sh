#!/bin/bash
# Voice Chat with Jarvis - Full OpenClaw Session
# Routes through OpenClaw so Jarvis has access to all tools and files
# Ctrl+C to stop

VOICE="en-US-AndrewMultilingualNeural"
OUTDIR="$HOME/voice-profiles/chat"
GATEWAY="http://localhost:18789"
TOKEN="9104d4c62d36e2e27eaa8dc7f9173d8c8df3016de16fac86"
mkdir -p "$OUTDIR"

# Create or reuse a dedicated voice chat session
SESSION_FILE="$OUTDIR/.session_key"

cleanup() {
    echo ""
    echo "🔇 Voice chat ended."
    exit 0
}
trap cleanup SIGINT SIGTERM

echo "🎙️ JARVIS - Full Voice Chat"
echo "============================"
echo "Connected to OpenClaw session with full tool access."
echo "Ctrl+C to stop."
echo ""

# Startup
edge-tts --voice "$VOICE" --text "Voice chat online. I have full access to your campaign files. What do you need?" --write-media "$OUTDIR/startup.mp3" 2>/dev/null
termux-media-player play "$OUTDIR/startup.mp3" 2>/dev/null
sleep 4

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
    echo "🤔 Sending to Jarvis..."
    
    # Escape for JSON
    ESCAPED=$(python3 -c "import sys,json; print(json.dumps(sys.argv[1]))" "$TEXT")
    
    # Use wake event to inject into main session
    WAKE_RESP=$(curl -s -X POST "$GATEWAY/api/wake" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d "{\"text\": \"[VOICE CHAT] $ESCAPED\", \"mode\": \"now\"}" 2>/dev/null)
    
    WAKE_STATUS=$(echo "$WAKE_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))" 2>/dev/null)
    
    if [ "$WAKE_STATUS" != "ok" ] && [ "$WAKE_STATUS" != "accepted" ]; then
        echo "❌ Wake failed: $WAKE_RESP"
        continue
    fi
    
    echo "⏳ Waiting for response..."
    
    # Wait for the agent to process and respond
    # Poll session history for new response
    MAX_WAIT=60
    WAITED=0
    LAST_MSG=""
    
    while [ $WAITED -lt $MAX_WAIT ]; do
        sleep 3
        WAITED=$((WAITED + 3))
        
        # Get latest assistant message
        SESSIONS=$(curl -s "$GATEWAY/api/sessions?limit=1&messageLimit=2" \
            -H "Authorization: Bearer $TOKEN" 2>/dev/null)
        
        REPLY_TEXT=$(echo "$SESSIONS" | python3 -c "
import sys,json
try:
    data = json.load(sys.stdin)
    sessions = data.get('sessions', [])
    if sessions:
        msgs = sessions[0].get('messages', [])
        for m in reversed(msgs):
            if m.get('role') == 'assistant':
                content = m.get('content', '')
                if isinstance(content, list):
                    for c in content:
                        if isinstance(c, dict) and c.get('type') == 'text':
                            t = c['text']
                            # Skip internal/system messages
                            if t and not t.startswith('NO_REPLY') and not t.startswith('HEARTBEAT'):
                                print(t[:800])
                                sys.exit()
                elif isinstance(content, str) and content and not content.startswith('NO_REPLY'):
                    print(content[:800])
                    sys.exit()
except Exception as e:
    pass
" 2>/dev/null)
        
        # Check if we got a new response (different from last)
        if [ -n "$REPLY_TEXT" ] && [ "$REPLY_TEXT" != "$LAST_MSG" ]; then
            LAST_MSG="$REPLY_TEXT"
            break
        fi
    done
    
    if [ -z "$REPLY_TEXT" ]; then
        echo "❌ No response after ${MAX_WAIT}s"
        continue
    fi
    
    echo "💬 Jarvis: $REPLY_TEXT"
    
    # Generate and play speech
    OUTFILE="$OUTDIR/reply_${LOOP}.mp3"
    edge-tts --voice "$VOICE" --text "$REPLY_TEXT" --write-media "$OUTFILE" 2>/dev/null
    termux-media-player play "$OUTFILE" 2>/dev/null
    
    # Wait for playback
    DURATION=$(( ${#REPLY_TEXT} / 12 + 2 ))
    sleep $DURATION
    
    echo "✅ Done"
    echo ""
done
