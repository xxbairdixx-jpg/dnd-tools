#!/bin/bash
# VTT Control - Send commands from Voice DM to VTT
# Usage: bash vtt.sh <action> [params]

ACTION="$1"
shift

case "$ACTION" in
  add)
    # vtt.sh add "Goblin 1" enemy 7 13 400 200
    NAME="$1"; TYPE="$2"; HP="$3"; AC="$4"; X="$5"; Y="$6"
    CMD="{\"action\":\"add_token\",\"name\":\"$NAME\",\"type\":\"$TYPE\",\"hp\":$HP,\"ac\":$AC,\"x\":$X,\"y\":$Y}"
    ;;
  move)
    # vtt.sh move "Goblin 1" 500 300
    NAME="$1"; X="$2"; Y="$3"
    CMD="{\"action\":\"move_token\",\"name\":\"$NAME\",\"x\":$X,\"y\":$Y}"
    ;;
  damage)
    # vtt.sh damage "Goblin 1" 5
    NAME="$1"; AMOUNT="$2"
    CMD="{\"action\":\"damage_token\",\"name\":\"$NAME\",\"amount\":$AMOUNT}"
    ;;
  heal)
    # vtt.sh heal "Bairdi" 8
    NAME="$1"; AMOUNT="$2"
    CMD="{\"action\":\"heal_token\",\"name\":\"$NAME\",\"amount\":$AMOUNT}"
    ;;
  remove)
    NAME="$1"
    CMD="{\"action\":\"remove_token\",\"name\":\"$NAME\"}"
    ;;
  next)
    CMD="{\"action\":\"next_turn\"}"
    ;;
  initiative)
    CMD="{\"action\":\"roll_initiative\"}"
    ;;
  condition)
    # vtt.sh condition "Goblin 1" poisoned
    NAME="$1"; COND="$2"
    CMD="{\"action\":\"set_condition\",\"name\":\"$NAME\",\"condition\":\"$COND\"}"
    ;;
  uncondition)
    NAME="$1"; COND="$2"
    CMD="{\"action\":\"remove_condition\",\"name\":\"$NAME\",\"condition\":\"$COND\"}"
    ;;
  map)
    URL="$1"
    CMD="{\"action\":\"load_map\",\"url\":\"$URL\"}"
    ;;
  clear)
    CMD="{\"action\":\"clear_all\"}"
    ;;
  *)
    echo "Usage: vtt.sh <action> [params]"
    echo "Actions: add, move, damage, heal, remove, next, initiative, condition, uncondition, map, clear"
    exit 1
    ;;
esac

# Send via Python WebSocket client
python3 -c "
import asyncio, websockets, json
async def send():
    try:
        async with websockets.connect('ws://localhost:8765') as ws:
            await ws.send('$CMD')
            resp = await asyncio.wait_for(ws.recv(), timeout=2)
            print(resp)
    except Exception as e:
        print(f'Error: {e}')
asyncio.run(send())
"
