#!/usr/bin/env python3
"""
VTT WebSocket Server - Relays between browsers and voice DM
Port 8765
"""
import asyncio
import json
import websockets

browsers = set()
dm_clients = set()
pending_query = None

async def handler(websocket):
    global pending_query
    is_dm = False
    
    # First message determines client type
    try:
        first_msg = await asyncio.wait_for(websocket.recv(), timeout=5)
        data = json.loads(first_msg)
        
        if data.get('action') == 'dm_connect':
            # Voice DM client
            dm_clients.add(websocket)
            is_dm = True
            print(f"DM connected. Browsers: {len(browsers)}, DMs: {len(dm_clients)}")
        else:
            # Browser client
            browsers.add(websocket)
            print(f"Browser connected. Browsers: {len(browsers)}, DMs: {len(dm_clients)}")
            
            # Handle first message as normal - ensure sync_request is sent on connect
            if data.get('action') == 'sync_request':
                await process_message(websocket, data)
    except:
        browsers.add(websocket)
    
    try:
        async for message in websocket:
            data = json.loads(message)
            await process_message(websocket, data)
    except websockets.ConnectionClosed:
        pass
    finally:
        if is_dm:
            dm_clients.discard(websocket)
        else:
            browsers.discard(websocket)

async def process_message(sender, data):
    action = data.get('action')
    
    # Messages from DM → broadcast to browsers
    if sender in dm_clients:
        if action == 'query_state':
            # Send query to first browser, wait for response
            if browsers and len(browsers) > 0:
                target = next(iter(browsers))
                await target.send(json.dumps(data))
        else:
            # Broadcast to all browsers
            if browsers:
                await asyncio.gather(*[ws.send(json.dumps(data)) for ws in browsers])
    
    # Messages from browsers
    elif sender in browsers:
        if action == 'state_response':
            # Send back to DM clients
            if dm_clients and len(dm_clients) > 0:
                await asyncio.gather(*[ws.send(json.dumps(data)) for ws in dm_clients])
        elif action == 'sync_request':
            # New browser - tell it we're ready
            await sender.send(json.dumps({'action': 'sync_ready'}))
        elif action == 'player_speech':
            # PTT from browser → forward to DM
            if dm_clients and len(dm_clients) > 0:
                await asyncio.gather(*[ws.send(json.dumps(data)) for ws in dm_clients])
        else:
            # Regular sync - broadcast to all other browsers AND DMs
            recipients = (browsers - {sender}) | dm_clients
            if recipients and len(recipients) > 0:
                await asyncio.gather(*[ws.send(json.dumps(data)) for ws in recipients])

async def main():
    print("VTT WebSocket Server on ws://localhost:8765")
    print("Handles: browser sync, DM commands, state queries")
    async with websockets.serve(handler, "localhost", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
