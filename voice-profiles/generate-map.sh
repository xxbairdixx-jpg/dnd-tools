#!/bin/bash
# Generate battlemap images - free via Pollinations.ai
# Usage: bash generate-map.sh "description" [filename]
# Example: bash generate-map.sh "medieval tavern interior with wooden tables and fireplace" tavern

PROMPT="$1"
FILENAME="${2:-battlemap}"
OUTDIR="$HOME/voice-profiles/maps"
mkdir -p "$OUTDIR"

# Enhance prompt for battlemap style
FULL_PROMPT="top-down battlemap view, ${PROMPT}, fantasy RPG style, detailed, grid-friendly, clear terrain features, birds eye view, ${FILENAME}"

# URL encode the prompt
ENCODED=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$FULL_PROMPT'))")

URL="https://image.pollinations.ai/prompt/${ENCODED}?width=1024&height=1024&seed=${RANDOM}&nologo=true"

echo "🎨 Generating: $FILENAME"
echo "📝 Prompt: $PROMPT"
echo "⏳ Downloading..."

curl -s -L "$URL" -o "$OUTDIR/${FILENAME}.jpg"

if [ -f "$OUTDIR/${FILENAME}.jpg" ] && [ -s "$OUTDIR/${FILENAME}.jpg" ]; then
    SIZE=$(ls -lh "$OUTDIR/${FILENAME}.jpg" | awk '{print $5}')
    echo "✅ Saved: $OUTDIR/${FILENAME}.jpg ($SIZE)"
else
    echo "❌ Failed to generate"
fi
