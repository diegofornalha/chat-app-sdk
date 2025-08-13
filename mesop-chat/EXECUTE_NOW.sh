#!/bin/bash

# Script de execução rápida do Mesop-Chat
# =========================================

echo "🚀 Mesop-Chat - Execução Rápida"
echo "================================"
echo ""

# Instalar dependências mínimas necessárias
echo "📦 Instalando dependências essenciais..."
/opt/homebrew/bin/pip3 install anthropic claude-code-sdk python-dotenv mesop --break-system-packages --quiet

echo ""
echo "✅ Dependências instaladas!"
echo ""
echo "🌐 Iniciando servidor em http://localhost:32123"
echo "================================================"
echo ""

# Executar o servidor
cd /Users/agents/Desktop/chat-app-sdk/mesop-chat
/opt/homebrew/bin/mesop app.py --port 32123