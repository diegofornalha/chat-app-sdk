#!/usr/bin/env python3
"""
Debug para encontrar o problema exato
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

print("\n🔍 DEBUG: Encontrando o problema exato")
print("=" * 70)

# Importar as classes
from app import (
    Message,
    ChatSession, 
    ProcessingStep,
    State,
    create_new_session
)

# Teste 1: Criar State fresco
print("\n1️⃣ Criando State novo...")
state = State()

print(f"   Type de current_session: {type(state.current_session)}")
print(f"   É dataclass? {is_dataclass(state.current_session)}")
print(f"   current_session.created_at type: {type(state.current_session.created_at)}")
print(f"   current_session.created_at value: {state.current_session.created_at}")

# Teste 2: Tentar serializar
print("\n2️⃣ Tentando serializar State...")
try:
    state_dict = asdict(state)
    print("   ✅ asdict() funcionou")
    
    # Analisar o dict resultante
    if 'current_session' in state_dict:
        cs = state_dict['current_session']
        print(f"   current_session no dict: {type(cs)}")
        if isinstance(cs, dict) and 'created_at' in cs:
            print(f"   created_at no dict: type={type(cs['created_at'])}, value={cs['created_at']}")
    
    # Tentar JSON
    json_str = json.dumps(state_dict)
    print(f"   ✅ JSON serialization OK ({len(json_str)} bytes)")
    
except TypeError as e:
    print(f"   ❌ ERRO: {e}")
    import traceback
    traceback.print_exc()

# Teste 3: Verificar se o problema é no MesopJSONEncoder
print("\n3️⃣ Testando com MesopJSONEncoder...")
from mesop.dataclass_utils.dataclass_utils import MesopJSONEncoder

try:
    json_str = json.dumps(state, cls=MesopJSONEncoder)
    print(f"   ✅ MesopJSONEncoder OK ({len(json_str)} bytes)")
except Exception as e:
    print(f"   ❌ ERRO com MesopJSONEncoder: {e}")
    
    # Tentar encontrar o objeto problemático
    print("\n   Analisando campos do State:")
    for field_name in dir(state):
        if not field_name.startswith('_'):
            value = getattr(state, field_name)
            print(f"   - {field_name}: type={type(value)}, is_dataclass={is_dataclass(value)}")
            
            # Se for lista, verificar itens
            if isinstance(value, list) and value:
                print(f"     First item: type={type(value[0])}, is_dataclass={is_dataclass(value[0])}")
            
            # Se for dict, verificar valores
            if isinstance(value, dict) and value:
                for k, v in list(value.items())[:1]:
                    print(f"     First value: type={type(v)}, is_dataclass={is_dataclass(v)}")

# Teste 4: Verificar se há algum campo com problema
print("\n4️⃣ Verificando campos específicos...")

# Verificar ChatSession
session = create_new_session()
print(f"\nChatSession criada com factory:")
print(f"   type: {type(session)}")
print(f"   is_dataclass: {is_dataclass(session)}")
print(f"   created_at type: {type(session.created_at)}")
print(f"   created_at value: {session.created_at}")

try:
    session_dict = asdict(session)
    json.dumps(session_dict)
    print("   ✅ ChatSession é serializável")
except Exception as e:
    print(f"   ❌ ChatSession NÃO é serializável: {e}")

# Verificar Message
msg = Message()
print(f"\nMessage criada:")
print(f"   type: {type(msg)}")
print(f"   is_dataclass: {is_dataclass(msg)}")
print(f"   timestamp type: {type(msg.timestamp)}")
print(f"   timestamp value: {msg.timestamp}")

try:
    msg_dict = asdict(msg)
    json.dumps(msg_dict)
    print("   ✅ Message é serializável")
except Exception as e:
    print(f"   ❌ Message NÃO é serializável: {e}")

# Verificar ProcessingStep
step = ProcessingStep(type="test", message="test")
print(f"\nProcessingStep criado:")
print(f"   type: {type(step)}")
print(f"   is_dataclass: {is_dataclass(step)}")
print(f"   timestamp type: {type(step.timestamp)}")
print(f"   timestamp value: {step.timestamp}")

try:
    step_dict = asdict(step)
    json.dumps(step_dict)
    print("   ✅ ProcessingStep é serializável")
except Exception as e:
    print(f"   ❌ ProcessingStep NÃO é serializável: {e}")

print("\n" + "=" * 70)
print("🔎 Análise Completa Finalizada")
print("=" * 70)