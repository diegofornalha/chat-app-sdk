#!/usr/bin/env python3
"""
Script para corrigir todas as verificações de dict no app.py
Remove tratamento de current_session como dict e força sempre dataclass
"""

import re

# Ler o arquivo
with open('app.py', 'r') as f:
    content = f.read()

# Contador de correções
fixes = 0

# Padrões a corrigir
patterns_to_fix = [
    # Remove verificações de isinstance dict para current_session
    (r'elif isinstance\(state\.current_session, dict\):[^\n]*\n[^\n]*', '# Removido: verificação de dict - sempre usar dataclass'),
    (r'if isinstance\(state\.current_session, dict\):[^\n]*\n[^\n]*', '# Removido: verificação de dict - sempre usar dataclass'),
    
    # Remove gets de dict em current_session
    (r'state\.current_session\.get\([\'"]messages[\'"]\s*,\s*\[\]\)', 'state.current_session.messages'),
    (r'state\.current_session\.get\([\'"]id[\'"]\)', 'state.current_session.id'),
    (r'state\.current_session\.get\([\'"]title[\'"]\)', 'state.current_session.title'),
]

# Aplicar correções
for pattern, replacement in patterns_to_fix:
    new_content, n = re.subn(pattern, replacement, content)
    if n > 0:
        content = new_content
        fixes += n
        print(f"✅ Corrigido {n} ocorrência(s) de: {pattern[:50]}...")

print(f"\n📊 Total de correções: {fixes}")

# Salvar arquivo corrigido
if fixes > 0:
    with open('app_fixed.py', 'w') as f:
        f.write(content)
    print("✅ Arquivo salvo como app_fixed.py")
    print("\n⚠️  IMPORTANTE: Revise as mudanças antes de aplicar!")
else:
    print("ℹ️  Nenhuma correção necessária")

# Mostrar linhas problemáticas restantes
print("\n🔍 Verificando linhas problemáticas restantes...")
lines = content.split('\n')
for i, line in enumerate(lines, 1):
    if 'isinstance' in line and 'dict' in line and 'current_session' in line:
        print(f"   Linha {i}: {line.strip()}")
    elif 'current_session.get(' in line:
        print(f"   Linha {i}: {line.strip()}")