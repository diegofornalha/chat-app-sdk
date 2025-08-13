#!/usr/bin/env python3
"""
Script para executar o servidor Mesop
"""
import subprocess
import sys

def main():
    """Executa o servidor Mesop"""
    print("🚀 Iniciando servidor Mesop...")
    print("=" * 60)
    print("📍 URL: http://localhost:32123")
    print("=" * 60)
    
    try:
        # Executar o servidor Mesop
        subprocess.run([
            sys.executable, "-m", "mesop",
            "backend.app",
            "--port", "32123"
        ])
    except KeyboardInterrupt:
        print("\n👋 Servidor interrompido")
    except Exception as e:
        print(f"❌ Erro ao executar servidor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()