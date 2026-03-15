#!/usr/bin/env python3
"""Serve all web apps from ~/voice-profiles on port 8080"""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
os.chdir(os.path.expanduser('~/voice-profiles'))
print("Serving ~/voice-profiles on port 8080")
print("VTT: http://localhost:8080/vtt/")
print("Jarvis: http://localhost:8080/jarvis/")
HTTPServer(('0.0.0.0', 8080), SimpleHTTPRequestHandler).serve_forever()
