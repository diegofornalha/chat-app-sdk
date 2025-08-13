#!/bin/bash
# Script simples para executar o chat

echo "🚀 Iniciando Chat com Claude..."
echo "================================"

# Verifica se tem API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  Configure sua API key:"
    echo "export ANTHROPIC_API_KEY='sua-chave'"
    exit 1
fi

# Verifica se tem anthropic instalado
if ! python -c "import anthropic" 2>/dev/null; then
    echo "📦 Instalando dependências..."
    pip install anthropic
fi

# Executa o chat
python chat_app.py