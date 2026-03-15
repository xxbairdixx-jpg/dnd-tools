#!/usr/bin/env python3
import flask
from flask_cors import CORS
import requests
import json
import logging
import base64

# Initialize Flask app and enable CORS
app = flask.Flask(__name__)
CORS(app)

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return "OK"

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    """
    Chat endpoint that handles both text-only and text+image messages.
    Maintains conversation history (last 20 messages) and forwards to LM Studio.
    """
    data = flask.request.get_json()
    
    if not data:
        return flask.jsonify({"error": "No JSON data provided"}), 400
    
    message_text = data.get('message')
    image_base64 = data.get('image')
    
    # Validate required fields
    if not message_text:
        return flask.jsonify({"error": "'message' field is required"}), 400

    # Initialize conversation history with system prompt and user's initial message
    messages = [
        {"role": "system", "content": 
         "You are Jarvis, a helpful AI assistant. Keep responses concise and conversational (2-4 sentences). You can see images when provided."
        }
    ]
    
    # Add user message(s)
    if image_base64:
        # Include base64 image in OpenAI-compatible format
        messages.append({
            "role": "user",
            "content": "",
            "image_url": {
                "url": f"data:image/jpeg;base64,{image_base64}"
            }
        })
    else:
        messages.append({"role": "user", "content": message_text})
    
    # Call LM Studio API
    try:
        lm_studio_url = "http://192.168.0.222:1234/v1/chat/completions"
        
        response_data = {
            "model": "zai-org/glm-4.6v-flash",
            "messages": messages,
        }
        
        lm_response = requests.post(lm_studio_url, json=response_data)
        lm_response.raise_for_status()
        
        lm_result = lm_response.json()
        
        # Extract assistant's response
        assistant_message = lm_result.get('choices', [{}])[0].get('message', {}).get('content', '')
        
        # Strip thinking tags and special tokens from GLM
        import re
        assistant_message = re.sub(r'<think>.*？>', '', assistant_message, flags=re.DOTALL)
        if '</think>' in assistant_message:
            assistant_message = assistant_message.split('</think>')[-1]
        assistant_message = re.sub(r'<\|begin_of_box\|>', '', assistant_message)
        assistant_message = re.sub(r'<\|end_of_box\|>', '', assistant_message)
        assistant_message = assistant_message.strip()
        
        # Update conversation history with new messages (keep last 20)
        if assistant_message:
            messages.append({"role": "assistant", "content": assistant_message})
            
        # Keep only last 20 messages
        if len(messages) > 20:
            messages = messages[-20:]
            
        return flask.jsonify({
            "reply": assistant_message,
            "history": messages
        })
        
    except requests.exceptions.RequestException as e:
        logging.error(f"LM Studio API error: {str(e)}")
        return flask.jsonify({"error": f"Failed to connect to LM Studio: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8090, debug=False)