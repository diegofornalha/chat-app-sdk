#!/bin/bash

echo "📦 Instalando dependências do Mesop-Chat..."
echo "=========================================="

# Detectar Python
if command -v python3.13 &> /dev/null; then
    PYTHON=python3.13
elif command -v python3.12 &> /dev/null; then
    PYTHON=python3.12
elif command -v python3 &> /dev/null; then
    PYTHON=python3
else
    echo "❌ Python 3 não encontrado"
    exit 1
fi

echo "✅ Usando $PYTHON"

# Instalar dependências
echo ""
echo "📥 Instalando pacotes necessários..."

$PYTHON -m pip install --upgrade pip
$PYTHON -m pip install anthropic>=0.62.0
$PYTHON -m pip install claude-code-sdk>=0.0.20
$PYTHON -m pip install mesop>=1.1.0
$PYTHON -m pip install python-dotenv>=1.0.0
$PYTHON -m pip install fastapi>=0.115.0
$PYTHON -m pip install uvicorn>=0.32.0
$PYTHON -m pip install httpx>=0.28.0
$PYTHON -m pip install aiofiles>=24.1.0
$PYTHON -m pip install python-socketio>=5.13.0

echo ""
echo "✅ Dependências instaladas com sucesso!"
echo ""
echo "🚀 Para executar o servidor, use:"
echo "   mesop app.py --port 32123"
echo "   ou"
echo "   python3 -m mesop app.py --port 32123"