#!/bin/bash
# Voice Profile Generator for "The Veil's Edge" Campaign
# Usage: bash generate.sh "text" "character"
# Or: bash generate.sh "text" "voice-id"

TEXT="$1"
CHAR="$2"
OUTDIR="$HOME/voice-profiles/output"
mkdir -p "$OUTDIR"

# Character voice mappings
case "$CHAR" in
  # NARRATOR
  narrator|narrator)
    VOICE="en-US-AndrewMultilingualNeural"
    RATE="+5%"
    PITCH="-5Hz"
    ;;
  
  # VILLAINS
  iron-hand|ironhand)
    VOICE="en-US-GuyNeural"
    RATE="-10%"
    PITCH="-10Hz"
    ;;
  whispering-queen|queen)
    VOICE="en-US-AriaNeural"
    RATE="-5%"
    PITCH="+5Hz"
    ;;
  emperor)
    VOICE="en-US-ChristopherNeural"
    RATE="-10%"
    PITCH="-15Hz"
    ;;
  archon)
    VOICE="en-US-RogerNeural"
    RATE="-15%"
    PITCH="-10Hz"
    ;;
  weaving-mind|weavingmind)
    VOICE="en-US-EricNeural"
    RATE="-20%"
    PITCH="-15Hz"
    ;;
  
  # NPC TYPES
  merchant)
    VOICE="en-US-BrianMultilingualNeural"
    RATE="+10%"
    PITCH="+0Hz"
    ;;
  guard)
    VOICE="en-US-AndrewNeural"
    RATE="+0%"
    PITCH="-5Hz"
    ;;
  innkeeper)
    VOICE="en-US-EmmaMultilingualNeural"
    RATE="+5%"
    PITCH="+5Hz"
    ;;
  priest)
    VOICE="en-US-SteffanNeural"
    RATE="-5%"
    PITCH="+0Hz"
    ;;
  child)
    VOICE="en-US-AnaNeural"
    RATE="+15%"
    PITCH="+10Hz"
    ;;
  mysterious)
    VOICE="en-US-MichelleNeural"
    RATE="-10%"
    PITCH="+0Hz"
    ;;
  
  # DIRECT VOICE ID (pass any edge-tts voice name)
  *)
    VOICE="$CHAR"
    RATE="+0%"
    PITCH="+0Hz"
    ;;
esac

OUTFILE="$OUTDIR/${CHAR}_$(date +%s).mp3"
edge-tts --voice "$VOICE" --text "$TEXT" --write-media "$OUTFILE" 2>&1
echo "Saved: $OUTFILE"
