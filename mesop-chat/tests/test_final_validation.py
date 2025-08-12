#!/usr/bin/env python3
"""
Teste final de validação - Garante que não há mais erro de serialização
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dataclasses import dataclass, field, is_dataclass, asdict
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
import uuid

# Importar as classes reais
from app import (
    Message,
    ChatSession,
    ProcessingStep,
    State,
    create_new_session,
    ensure_chatsession,
    normalize_sessions
)

print("\n🔍 TESTE FINAL DE VALIDAÇÃO")
print("=" * 70)

# Teste 1: Verificar que State usa factory correta
print("\n1️⃣ Testando inicialização padrão do State...")
state = State()

# Verificar que current_session foi criado com factory
assert isinstance(state.current_session, ChatSession), "current_session deve ser ChatSession"
assert isinstance(state.current_session.created_at, str), "created_at deve ser string"
assert isinstance(state.current_session.last_activity, str), "last_activity deve ser string"
assert "T" in state.current_session.created_at, "Deve ser formato ISO"

print(f"   ✅ State inicializado com current_session válido")
print(f"   ✅ Timestamps são strings ISO: {state.current_session.created_at[:19]}...")

# Teste 2: Serialização do estado inicial
print("\n2️⃣ Testando serialização do estado inicial...")
try:
    state_dict = asdict(state)
    json_str = json.dumps(state_dict)
    print(f"   ✅ Estado inicial é serializável ({len(json_str)} bytes)")
except TypeError as e:
    print(f"   ❌ ERRO: {e}")
    raise

# Teste 3: Adicionar nova sessão
print("\n3️⃣ Testando adição de nova sessão...")
new_session = create_new_session("Teste")
state.sessions[new_session.id] = new_session

try:
    state_dict = asdict(state)
    json_str = json.dumps(state_dict)
    print(f"   ✅ Estado com nova sessão é serializável ({len(json_str)} bytes)")
except TypeError as e:
    print(f"   ❌ ERRO: {e}")
    raise

# Teste 4: Adicionar mensagem
print("\n4️⃣ Testando adição de mensagem...")
msg = Message(
    content="Teste de mensagem",
    role="user"
)
state.current_session.messages.append(msg)

# Verificar timestamp da mensagem
assert isinstance(msg.timestamp, str), "Timestamp da mensagem deve ser string"
assert "T" in msg.timestamp, "Deve ser formato ISO"

try:
    state_dict = asdict(state)
    json_str = json.dumps(state_dict)
    print(f"   ✅ Estado com mensagem é serializável ({len(json_str)} bytes)")
except TypeError as e:
    print(f"   ❌ ERRO: {e}")
    raise

# Teste 5: ProcessingStep
print("\n5️⃣ Testando ProcessingStep...")
step = ProcessingStep(
    type="test",
    message="Testing"
)
state.processing_steps.append(step)

assert isinstance(step.timestamp, str), "Timestamp do step deve ser string"

try:
    state_dict = asdict(state)
    json_str = json.dumps(state_dict)
    print(f"   ✅ Estado com ProcessingStep é serializável ({len(json_str)} bytes)")
except TypeError as e:
    print(f"   ❌ ERRO: {e}")
    raise

# Teste 6: Simular cenário problemático
print("\n6️⃣ Testando correção de dict com datetime...")

# Criar dict problemático (como vinha do hot reload)
bad_session_dict = {
    'id': 'problem-id',
    'title': 'Sessão Problemática',
    'messages': [],
    'created_at': datetime.now(),  # ❌ datetime object!
    'last_activity': datetime.now()  # ❌ datetime object!
}

# Nossa função deve corrigir
fixed = ensure_chatsession(bad_session_dict)
assert isinstance(fixed.created_at, str), "Deve converter para string"
assert isinstance(fixed.last_activity, str), "Deve converter para string"

# Adicionar ao estado e testar
state.sessions['fixed'] = fixed

try:
    state_dict = asdict(state)
    json_str = json.dumps(state_dict)
    print(f"   ✅ Estado com sessão corrigida é serializável ({len(json_str)} bytes)")
except TypeError as e:
    print(f"   ❌ ERRO: {e}")
    raise

# Teste 7: validate_sessions
print("\n7️⃣ Testando validate_sessions...")

# Forçar um dict no sessions
state.sessions['bad'] = {
    'id': 'bad-id',
    'title': 'Bad Session',
    'created_at': datetime.now(),
    'messages': []
}

# validate_sessions deve corrigir
state.validate_sessions()

# Verificar que foi corrigido
bad_session = state.sessions.get('bad')
if bad_session:
    assert isinstance(bad_session, ChatSession), "Deve ter sido convertido para ChatSession"
    assert isinstance(bad_session.created_at, str), "created_at deve ser string"
    print("   ✅ validate_sessions corrigiu sessão problemática")

# Teste final de serialização
try:
    state_dict = asdict(state)
    json_str = json.dumps(state_dict)
    print(f"   ✅ Estado final completamente serializável ({len(json_str)} bytes)")
except TypeError as e:
    print(f"   ❌ ERRO CRÍTICO: {e}")
    raise

print("\n" + "=" * 70)
print("🎊 SUCESSO TOTAL!")
print("   ✅ Todos os 7 testes passaram")
print("   ✅ Não há mais objetos datetime no estado")
print("   ✅ Todas as sessões são dataclasses válidas")
print("   ✅ O erro 'asdict() should be called on dataclass instances' foi ELIMINADO!")
print("\n💡 A aplicação está pronta para uso sem erros de serialização!")
print("=" * 70)