#!/usr/bin/env python3
"""
Simula o comportamento do Mesop para encontrar onde o erro ocorre
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import mesop as me
from dataclasses import dataclass, field, is_dataclass, asdict
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
import uuid

print("\n🎭 SIMULAÇÃO DO COMPORTAMENTO DO MESOP")
print("=" * 70)

# Importar as classes
from app import (
    Message,
    ChatSession, 
    ProcessingStep,
    State,
    create_new_session,
    ensure_chatsession,
    handle_new_chat
)

# Simular o que o Mesop faz
print("\n1️⃣ Simulando criação inicial do State pelo Mesop...")

# O Mesop cria o State assim
state = me.state(State)
print(f"   State criado: {type(state)}")
print(f"   current_session: {type(state.current_session)}")
print(f"   É dataclass? {is_dataclass(state.current_session)}")

# Verificar se há algum campo extra adicionado pelo Mesop
print("\n2️⃣ Verificando campos do State...")
for attr_name in dir(state):
    if not attr_name.startswith('_'):
        value = getattr(state, attr_name, None)
        if value is not None and not callable(value):
            print(f"   {attr_name}: {type(value)}")

# Simular o clique no botão
print("\n3️⃣ Simulando clique no botão 'Novo Chat'...")

# Criar um mock do evento
class MockClickEvent:
    pass

event = MockClickEvent()

# Chamar o handler
try:
    handle_new_chat(event)
    print("   ✅ handle_new_chat executado sem erro")
except Exception as e:
    print(f"   ❌ ERRO em handle_new_chat: {e}")
    import traceback
    traceback.print_exc()

# Verificar o estado após o handler
print("\n4️⃣ Verificando estado após handle_new_chat...")
print(f"   Sessões no state: {len(state.sessions)}")
for session_id, session in state.sessions.items():
    print(f"   - {session_id}: type={type(session)}, is_dataclass={is_dataclass(session)}")
    if hasattr(session, 'created_at'):
        print(f"     created_at: type={type(session.created_at)}")

# Tentar serializar como o Mesop faria
print("\n5️⃣ Tentando serializar como o Mesop...")

# Importar o encoder do Mesop
from mesop.dataclass_utils.dataclass_utils import MesopJSONEncoder

# Verificar cada campo individualmente
print("\n   Testando campos individuais:")

# current_session
try:
    cs_dict = asdict(state.current_session)
    json.dumps(cs_dict)
    print("   ✅ current_session é serializável")
except Exception as e:
    print(f"   ❌ current_session NÃO é serializável: {e}")

# sessions
for sid, sess in state.sessions.items():
    try:
        sess_dict = asdict(sess)
        json.dumps(sess_dict)
        print(f"   ✅ session {sid} é serializável")
    except Exception as e:
        print(f"   ❌ session {sid} NÃO é serializável: {e}")

# processing_steps
if state.processing_steps:
    for i, step in enumerate(state.processing_steps):
        try:
            step_dict = asdict(step)
            json.dumps(step_dict)
            print(f"   ✅ processing_step {i} é serializável")
        except Exception as e:
            print(f"   ❌ processing_step {i} NÃO é serializável: {e}")

# Estado completo
print("\n6️⃣ Tentando serializar estado completo...")
try:
    # Método 1: asdict direto
    state_dict = asdict(state)
    json_str = json.dumps(state_dict)
    print(f"   ✅ asdict + json.dumps OK ({len(json_str)} bytes)")
except Exception as e:
    print(f"   ❌ asdict + json.dumps FALHOU: {e}")

try:
    # Método 2: MesopJSONEncoder
    json_str = json.dumps(state, cls=MesopJSONEncoder)
    print(f"   ✅ MesopJSONEncoder OK ({len(json_str)} bytes)")
except Exception as e:
    print(f"   ❌ MesopJSONEncoder FALHOU: {e}")
    
    # Tentar encontrar o objeto problemático
    print("\n   🔍 Procurando objeto problemático...")
    
    # Verificar se há algum objeto não-dataclass
    for field_name in ['current_session', 'sessions', 'processing_steps']:
        field_value = getattr(state, field_name)
        if field_value:
            if isinstance(field_value, dict):
                for k, v in field_value.items():
                    if not is_dataclass(v) and not isinstance(v, (str, int, float, bool, list, dict, type(None))):
                        print(f"   ⚠️  {field_name}[{k}] não é dataclass nem tipo primitivo: {type(v)}")
            elif isinstance(field_value, list):
                for i, item in enumerate(field_value):
                    if not is_dataclass(item) and not isinstance(item, (str, int, float, bool, dict, type(None))):
                        print(f"   ⚠️  {field_name}[{i}] não é dataclass nem tipo primitivo: {type(item)}")

print("\n" + "=" * 70)
print("🔎 Simulação Completa")
print("=" * 70)