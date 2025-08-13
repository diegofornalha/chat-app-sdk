#!/bin/bash

# Mesop-Chat Starter Script
# =========================

echo "🚀 Mesop-Chat com Claude Code SDK"
echo "=================================="
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Por favor, instale Python 3.12+"
    exit 1
fi

# Verificar versão do Python
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
REQUIRED_VERSION="3.12"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $REQUIRED_VERSION+ é necessário (encontrado: $PYTHON_VERSION)"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION detectado"

# Verificar uv
if command -v uv &> /dev/null; then
    echo "✅ UV detectado - usando UV para gerenciar dependências"
    USE_UV=true
else
    echo "ℹ️  UV não encontrado - usando pip"
    USE_UV=false
fi

# Instalar dependências
echo ""
echo "📦 Instalando dependências..."
if [ "$USE_UV" = true ]; then
    uv sync
else
    pip install -r requirements.txt 2>/dev/null || pip install mesop claude-code-sdk fastapi uvicorn httpx python-dotenv anthropic
fi

# Verificar Claude auth
echo ""
echo "🔐 Verificando autenticação Claude..."
if command -v claude &> /dev/null; then
    if claude auth status &> /dev/null; then
        echo "✅ Claude autenticado"
    else
        echo "⚠️  Claude não autenticado. Execute: claude auth login"
    fi
else
    echo "ℹ️  Claude CLI não encontrado - usando fallback para API key"
fi

# Carregar variáveis de ambiente
if [ -f .env ]; then
    echo "✅ Arquivo .env encontrado"
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "⚠️  Arquivo .env não encontrado - usando configurações padrão"
    export A2A_UI_PORT=32123
    export A2A_UI_HOST=0.0.0.0
fi

# Verificar porta
PORT=${A2A_UI_PORT:-32123}
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "❌ Porta $PORT já está em uso"
    echo "   Execute: lsof -i :$PORT para ver o processo"
    echo "   Ou defina outra porta em .env (A2A_UI_PORT=XXXX)"
    exit 1
fi

echo "✅ Porta $PORT disponível"

# Iniciar servidor
echo ""
echo "=============================================="
echo "🎯 Iniciando servidor em http://localhost:$PORT"
echo "=============================================="
echo ""
echo "Pressione Ctrl+C para parar o servidor"
echo ""

# Executar com UV ou Python
if [ "$USE_UV" = true ]; then
    uv run python main.py
else
    python3 main.py
fi