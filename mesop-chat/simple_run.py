#!/usr/bin/env python3
"""
Script simples para executar o servidor
"""
import os
import subprocess

print("🚀 Iniciando Mesop-Chat...")
print("📍 URL: http://localhost:32123")
print("-" * 40)

# Executar mesop diretamente
subprocess.run(["mesop", "app.py", "--port", "32123"])