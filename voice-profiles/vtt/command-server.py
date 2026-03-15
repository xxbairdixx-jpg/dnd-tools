#!/usr/bin/env python3
"""
Simple HTTP command server for VTT
DM writes commands → VTT polls and executes
No WebSocket complexity!
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import threading

# Command queue
commands = []
commands_lock = threading.Lock()
# VTT state cache
vtt_state = {}
state_lock = threading.Lock()

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass  # Quiet logs
    
    def do_GET(self):
        global commands, vtt_state
        
        if self.path == '/commands':
            # VTT polls for pending commands
            with commands_lock:
                cmds = commands.copy()
                commands.clear()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(cmds).encode())
            
        elif self.path == '/state':
            # DM queries VTT state
            with state_lock:
                state = vtt_state.copy()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(state).encode())
            
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        global commands, vtt_state
        
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        
        if self.path == '/command':
            # DM sends a command
            with commands_lock:
                commands.append(body)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
            
        elif self.path == '/state':
            # VTT reports its state
            with state_lock:
                vtt_state = body
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

if __name__ == '__main__':
    print("VTT Command Server on http://localhost:9000")
    print("DM sends: POST /command {action, ...}")
    print("VTT polls: GET /commands")
    print("DM queries: GET /state")
    HTTPServer(('localhost', 9000), Handler).serve_forever()
