#!/bin/bash
# Live Voice Chat with Jarvis (OpenClaw)
# Uses termux-speech-to-text for input, edge-tts for output
# Press Enter to speak, Ctrl+C to quit

VOICE="en-US-AndrewMultilingualNeural"
OUTDIR="$HOME/voice-profiles/chat"
mkdir -p "$OUTDIR"

echo "🎙️ Voice Chat with Jarvis"
echo "========================="
echo "Press Enter to speak (or 'q' to quit)"
echo ""

while true; do
    read -p "🎤 Speak now (Enter) > " input
    if [ "$input" = "q" ]; then
        echo "Goodbye!"
        exit 0
    fi
    
    echo "Listening..."
    TEXT=$(termux-speech-to-text 2>/dev/null)
    
    if [ -z "$TEXT" ]; then
        echo "❌ Didn't catch that. Try again."
        continue
    fi
    
    echo "📝 You said: $TEXT"
    echo "🤔 Thinking..."
    
    # Send to OpenClaw via gateway API
    RESPONSE=$(curl -s -X POST http://localhost:18789/api/chat \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer 9104d4c62d36e2e27eaa8dc7f9173d8c8df3016de16fac86" \
        -d "{\"message\": \"$TEXT\", \"channel\": \"webchat\"}" 2>/dev/null)
    
    # Extract text response (adjust based on API response format)
    REPLY_TEXT=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('reply',''))" 2>/dev/null)
    
    if [ -z "$REPLY_TEXT" ]; then
        echo "❌ No response. Is OpenClaw running?"
        continue
    fi
    
    echo "💬 Jarvis: $REPLY_TEXT"
    
    # Convert to speech
    OUTFILE="$OUTDIR/reply_$(date +%s).mp3"
    edge-tts --voice "$VOICE" --text "$REPLY_TEXT" --write-media "$OUTFILE" 2>/dev/null
    
    # Play response
    termux-media-player play "$OUTFILE" 2>/dev/null
    
    echo ""
done
