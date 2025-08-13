#!/usr/bin/env python3
"""
Execução direta do Mesop sem dependências externas
"""
import sys
import os

# Adicionar caminho
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Tentar importar e executar
try:
    import mesop as me
    
    # Importar o app
    from app import main_page
    
    print("🚀 Servidor Mesop iniciando...")
    print("📍 URL: http://localhost:32123")
    print("=" * 50)
    
    # Executar servidor
    me.run(port=32123, host="0.0.0.0")
    
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    print("\n📦 Instale as dependências:")
    print("pip3 install mesop anthropic claude-code-sdk --break-system-packages")
except Exception as e:
    print(f"❌ Erro: {e}")