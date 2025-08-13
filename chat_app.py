#!/usr/bin/env python3
"""
Chat App Minimalista - 100% Funcional
Apenas o essencial para chat com Claude
"""
import os
import json
from anthropic import Anthropic

# Configuração simples
API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not API_KEY:
    print("⚠️  Configure ANTHROPIC_API_KEY no ambiente")
    print("   export ANTHROPIC_API_KEY='sua-chave'")
    exit(1)

# Cliente Claude
client = Anthropic(api_key=API_KEY)

# Arquivo para salvar histórico
HISTORY_FILE = "chat_history.json"

def load_history():
    """Carrega histórico salvo"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_history(messages):
    """Salva histórico"""
    with open(HISTORY_FILE, 'w') as f:
        json.dump(messages, f, indent=2, ensure_ascii=False)

def chat():
    """Loop principal do chat"""
    print("🤖 Chat com Claude - Digite 'sair' para encerrar")
    print("   Digite 'limpar' para limpar histórico")
    print("-" * 50)
    
    messages = load_history()
    if messages:
        print(f"📚 {len(messages)//2} mensagens no histórico")
    
    while True:
        # Input do usuário
        user_input = input("\n👤 Você: ").strip()
        
        if user_input.lower() == 'sair':
            save_history(messages)
            print("💾 Histórico salvo!")
            print("👋 Até logo!")
            break
        
        if user_input.lower() == 'limpar':
            messages = []
            if os.path.exists(HISTORY_FILE):
                os.remove(HISTORY_FILE)
            print("🧹 Histórico limpo!")
            continue
        
        if not user_input:
            continue
        
        # Adiciona mensagem do usuário
        messages.append({"role": "user", "content": user_input})
        
        try:
            # Chama Claude
            print("⏳ Pensando...")
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                messages=messages
            )
            
            # Extrai resposta
            assistant_msg = response.content[0].text
            
            # Adiciona resposta ao histórico
            messages.append({"role": "assistant", "content": assistant_msg})
            
            # Mostra resposta
            print(f"\n🤖 Claude: {assistant_msg}")
            
        except Exception as e:
            print(f"\n❌ Erro: {e}")
            # Remove última mensagem se houver erro
            if messages and messages[-1]["role"] == "user":
                messages.pop()

if __name__ == "__main__":
    chat()