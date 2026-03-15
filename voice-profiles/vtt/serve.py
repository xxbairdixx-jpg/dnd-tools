#!/usr/bin/env python3
"""VTT Server - binds to 0.0.0.0 so PCs on the network can reach it"""
import http.server, socketserver, os, sys

PORT = 8080
DIR = os.path.expanduser("~/voice-profiles/vtt")
os.chdir(DIR)

class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
    print(f"VTT serving on port {PORT} (0.0.0.0) - all interfaces", flush=True)
    httpd.serve_forever()
