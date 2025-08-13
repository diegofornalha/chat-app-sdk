#!/usr/bin/env python3
"""
Script para testar e executar o main.py
"""
import sys
import os
import subprocess

print("🔍 Verificando dependências para main.py...")
print("=" * 50)

# Lista de dependências necessárias
deps = {
    'mesop': 'mesop',
    'fastapi': 'fastapi', 
    'uvicorn': 'uvicorn',
    'httpx': 'httpx',
    'dotenv': 'python-dotenv'
}

missing = []
for module, package in deps.items():
    try:
        __import__(module)
        print(f"✅ {module}")
    except ImportError:
        print(f"❌ {module}")
        missing.append(package)

if missing:
    print("\n❌ Dependências faltando!")
    print("\n📦 Para instalar, execute:")
    print(f"pip3 install {' '.join(missing)} --break-system-packages")
    print("\n🔧 Ou execute este comando completo:")
    print("pip3 install mesop fastapi uvicorn httpx python-dotenv --break-system-packages")
else:
    print("\n✅ Todas as dependências estão instaladas!")
    print("\n🚀 Iniciando servidor...")
    print("📍 URL: http://localhost:32123")
    print("=" * 50)
    
    # Executar main.py
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    subprocess.run([sys.executable, "main.py"])