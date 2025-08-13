#!/bin/bash

echo "🔧 Corrigindo dependências do Mesop-Chat..."
echo ""

# Usar pip3 com --break-system-packages para forçar instalação
echo "📦 Instalando anthropic..."
pip3 install anthropic --break-system-packages --quiet

echo "📦 Instalando claude-code-sdk..."
pip3 install claude-code-sdk --break-system-packages --quiet

echo "📦 Instalando python-dotenv..."
pip3 install python-dotenv --break-system-packages --quiet

echo ""
echo "✅ Dependências instaladas!"
echo ""
echo "🚀 Agora execute:"
echo "   mesop app.py --port 32123"