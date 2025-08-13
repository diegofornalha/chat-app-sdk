#!/bin/bash

echo "🚀 Instalação Completa do Mesop-Chat"
echo "====================================="
echo ""

# Instalar TODAS as dependências
echo "📦 Instalando todas as dependências..."
echo ""

pip3 install --break-system-packages \
  mesop \
  fastapi \
  uvicorn \
  anthropic \
  claude-code-sdk \
  httpx \
  python-dotenv \
  aiofiles \
  python-socketio

echo ""
echo "✅ Dependências instaladas!"
echo ""

# Navegar para o diretório
cd /Users/agents/Desktop/chat-app-sdk/mesop-chat

# Fazer backup e usar o novo main.py
if [ -f "main.py" ] && [ -f "main_new.py" ]; then
    echo "📂 Configurando arquivos..."
    mv main.py main_backup_$(date +%Y%m%d_%H%M%S).py
    mv main_new.py main.py
    echo "✅ Novo main.py configurado!"
fi

echo ""
echo "====================================="
echo "🎯 Iniciando servidor completo..."
echo "====================================="
echo ""
echo "📍 URL: http://localhost:32123"
echo "🔧 Modo: COMPLETO (FastAPI + Mesop + Claude SDK + A2A)"
echo ""
echo "Pressione Ctrl+C para parar"
echo ""

# Executar o servidor
python3 main.py