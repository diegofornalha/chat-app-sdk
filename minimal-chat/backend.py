#!/usr/bin/env python3
"""
Chat Minimalista com Claude - Backend
Apenas o essencial para funcionar
"""
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from anthropic import Anthropic

app = Flask(__name__)
CORS(app)

# Cliente Claude
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

@app.route('/chat', methods=['POST'])
def chat():
    """Endpoint único do chat"""
    try:
        data = request.json
        message = data.get('message', '')
        
        if not message:
            return jsonify({'error': 'Mensagem vazia'}), 400
        
        # Chamar Claude
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            messages=[{"role": "user", "content": message}]
        )
        
        return jsonify({'response': response.content[0].text})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)