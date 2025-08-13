#!/usr/bin/env python3
"""
Chat App Minimalista - 100% Funcional
Apenas o essencial para chat com Claude
"""
import os
from anthropic import Anthropic

# Configuração simples
API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not API_KEY:
    print("⚠️  Configure ANTHROPIC_API_KEY no ambiente")
    exit(1)

# Cliente Claude
client = Anthropic(api_key=API_KEY)

def chat():
    """Loop principal do chat"""
    print("🤖 Chat com Claude - Digite 'sair' para encerrar")
    print("-" * 50)
    
    messages = []
    
    while True:
        # Input do usuário
        user_input = input("\n👤 Você: ").strip()
        
        if user_input.lower() == 'sair':
            print("👋 Até logo!")
            break
        
        if not user_input:
            continue
        
        # Adiciona mensagem do usuário
        messages.append({"role": "user", "content": user_input})
        
        try:
            # Chama Claude
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