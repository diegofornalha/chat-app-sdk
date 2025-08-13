#!/usr/bin/env python3
"""Chat Simples com Claude"""
import os
from anthropic import Anthropic

# Configuração
API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not API_KEY:
    print("Configure: export ANTHROPIC_API_KEY='sua-chave'")
    exit(1)

# Cliente
client = Anthropic(api_key=API_KEY)

# Chat
print("Chat com Claude - Digite 'sair' para encerrar")
print("-" * 40)

messages = []
while True:
    user_input = input("\nVocê: ").strip()
    
    if user_input.lower() == 'sair':
        print("Até logo!")
        break
    
    if not user_input:
        continue
    
    messages.append({"role": "user", "content": user_input})
    
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            messages=messages
        )
        
        assistant_msg = response.content[0].text
        messages.append({"role": "assistant", "content": assistant_msg})
        
        print(f"\nClaude: {assistant_msg}")
        
    except Exception as e:
        print(f"Erro: {e}")
        messages.pop()