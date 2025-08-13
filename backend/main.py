#!/usr/bin/env python3
"""
Backend Minimalista - Chat com Claude
Versão super simplificada e 100% funcional
"""
import os
import json
from datetime import datetime
from anthropic import Anthropic

# Configuração
API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not API_KEY:
    print("⚠️  Configure ANTHROPIC_API_KEY")
    exit(1)

client = Anthropic(api_key=API_KEY)

# Armazenamento simples em arquivo
HISTORY_FILE = "chat_history.json"

def load_history():
    """Carrega histórico de conversas"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return []

def save_history(messages):
    """Salva histórico de conversas"""
    with open(HISTORY_FILE, 'w') as f:
        json.dump(messages, f, indent=2)

def chat_with_claude(message, history=[]):
    """Envia mensagem para Claude e retorna resposta"""
    try:
        # Prepara mensagens
        messages = history + [{"role": "user", "content": message}]
        
        # Chama API
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            messages=messages
        )
        
        # Retorna texto da resposta
        return response.content[0].text
    except Exception as e:
        return f"Erro: {str(e)}"

def main():
    """Loop principal"""
    print("🤖 Chat Backend - Claude")
    print("Digite 'sair' para encerrar")
    print("-" * 40)
    
    history = load_history()
    
    while True:
        # Input
        user_input = input("\n👤 Você: ").strip()
        
        if user_input.lower() == 'sair':
            save_history(history)
            print("👋 Conversa salva. Até logo!")
            break
        
        if not user_input:
            continue
        
        # Processa com Claude
        print("⏳ Processando...")
        response = chat_with_claude(user_input, history)
        
        # Atualiza histórico
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": response})
        
        # Mostra resposta
        print(f"\n🤖 Claude: {response}")
    
if __name__ == "__main__":
    main()