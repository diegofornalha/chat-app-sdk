@echo off
REM Mesop-Chat Starter Script for Windows
REM =====================================

echo.
echo 🚀 Mesop-Chat com Claude Code SDK
echo ==================================
echo.

REM Verificar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python não encontrado. Por favor, instale Python 3.12+
    pause
    exit /b 1
)

echo ✅ Python detectado

REM Verificar uv
where uv >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ UV detectado - usando UV para gerenciar dependências
    set USE_UV=1
) else (
    echo ℹ️  UV não encontrado - usando pip
    set USE_UV=0
)

REM Instalar dependências
echo.
echo 📦 Instalando dependências...
if %USE_UV%==1 (
    uv sync
) else (
    pip install mesop claude-code-sdk fastapi uvicorn httpx python-dotenv anthropic
)

REM Verificar Claude auth
echo.
echo 🔐 Verificando autenticação Claude...
where claude >nul 2>&1
if %errorlevel% equ 0 (
    claude auth status >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✅ Claude autenticado
    ) else (
        echo ⚠️  Claude não autenticado. Execute: claude auth login
    )
) else (
    echo ℹ️  Claude CLI não encontrado - usando fallback para API key
)

REM Configurar variáveis de ambiente
if exist .env (
    echo ✅ Arquivo .env encontrado
    for /f "delims=" %%a in (.env) do set %%a
) else (
    echo ⚠️  Arquivo .env não encontrado - usando configurações padrão
    set A2A_UI_PORT=32123
    set A2A_UI_HOST=0.0.0.0
)

REM Iniciar servidor
echo.
echo ==============================================
echo 🎯 Iniciando servidor em http://localhost:%A2A_UI_PORT%
echo ==============================================
echo.
echo Pressione Ctrl+C para parar o servidor
echo.

REM Executar com UV ou Python
if %USE_UV%==1 (
    uv run python main.py
) else (
    python main.py
)

pause