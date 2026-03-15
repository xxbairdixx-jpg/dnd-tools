#!/bin/bash
# Clean startup for VTT + Voice DM system
echo "🧹 Cleaning up old processes..."
pkill -9 -f "serve.py\|command-server\|voice-dm\|http.server" 2>/dev/null
sleep 3

echo "🚀 Starting services..."

# 1. VTT Web Server (port 8080, bound to all interfaces)
cd ~/voice-profiles/vtt && python3 -u -c "
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os; os.chdir(os.path.expanduser('~/voice-profiles/vtt'))
HTTPServer(('0.0.0.0', 8080), SimpleHTTPRequestHandler).serve_forever()
" &
echo "  VTT web: port 8080"
sleep 1

# 2. Command Server (port 9000)
python3 ~/voice-profiles/vtt/command-server.py &
echo "  Command server: port 9000"
sleep 1

# 3. Voice DM (PTT on 9001)
python3 -u ~/voice-profiles/voice-dm.py &
echo "  Voice DM: PTT port 9001"
sleep 3

echo ""
echo "✅ All services started!"
echo "VTT: http://192.168.0.164:8080"
echo "PTT: Hold mic button or spacebar"
echo ""
