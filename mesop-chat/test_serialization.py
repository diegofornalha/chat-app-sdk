#!/usr/bin/env python3
"""
Script de teste para verificar serialização do estado do Mesop
"""
import sys
import json
from dataclasses import asdict, is_dataclass
from datetime import datetime

# Adicionar o diretório ao path para importar o app
sys.path.insert(0, '/Users/agents/Desktop/chat-app-sdk/backend')

# Importar as classes do app
from app import Message, ChatSession, State, ProcessingStep

def test_serialization():
    """Testa se as classes são serializáveis para JSON"""
    
    print("🧪 Testando serialização das classes...")
    
    # Teste 1: Message
    print("\n1. Testando Message...")
    msg = Message(
        id="test-123",
        role="user",
        content="Teste de mensagem"
    )
    print(f"   Message criada: {msg}")
    print(f"   É dataclass? {is_dataclass(msg)}")
    print(f"   Timestamp type: {type(msg.timestamp)}")
    print(f"   Timestamp value: {msg.timestamp}")
    
    try:
        msg_dict = asdict(msg)
        json_str = json.dumps(msg_dict)
        print(f"   ✅ Message é serializável! JSON length: {len(json_str)}")
    except Exception as e:
        print(f"   ❌ Erro ao serializar Message: {e}")
        return False
    
    # Teste 2: ChatSession
    print("\n2. Testando ChatSession...")
    session = ChatSession()
    session.messages.append(msg)
    print(f"   ChatSession criada com ID: {session.id}")
    print(f"   É dataclass? {is_dataclass(session)}")
    print(f"   created_at type: {type(session.created_at)}")
    print(f"   last_activity type: {type(session.last_activity)}")
    
    try:
        session_dict = asdict(session)
        json_str = json.dumps(session_dict)
        print(f"   ✅ ChatSession é serializável! JSON length: {len(json_str)}")
    except Exception as e:
        print(f"   ❌ Erro ao serializar ChatSession: {e}")
        return False
    
    # Teste 3: ProcessingStep
    print("\n3. Testando ProcessingStep...")
    step = ProcessingStep(
        type="test",
        message="Processando teste"
    )
    print(f"   ProcessingStep criado")
    print(f"   É dataclass? {is_dataclass(step)}")
    print(f"   timestamp type: {type(step.timestamp)}")
    
    try:
        step_dict = asdict(step)
        json_str = json.dumps(step_dict)
        print(f"   ✅ ProcessingStep é serializável! JSON length: {len(json_str)}")
    except Exception as e:
        print(f"   ❌ Erro ao serializar ProcessingStep: {e}")
        return False
    
    # Teste 4: State completo
    print("\n4. Testando State completo...")
    state = State()
    state.sessions[session.id] = session
    state.current_session = session
    state.processing_steps.append(step)
    
    print(f"   State criado com {len(state.sessions)} sessão(ões)")
    print(f"   É dataclass? {is_dataclass(state)}")
    
    # Verificar tipos no estado
    print("\n   Verificando tipos dos campos:")
    print(f"   - current_session: {type(state.current_session)}, is_dataclass: {is_dataclass(state.current_session)}")
    print(f"   - sessions: {type(state.sessions)}")
    for sid, sess in state.sessions.items():
        print(f"     - session {sid[:8]}...: {type(sess)}, is_dataclass: {is_dataclass(sess)}")
    print(f"   - processing_steps: {type(state.processing_steps)}")
    if state.processing_steps:
        print(f"     - first step: {type(state.processing_steps[0])}, is_dataclass: {is_dataclass(state.processing_steps[0])}")
    
    try:
        state_dict = asdict(state)
        json_str = json.dumps(state_dict)
        print(f"\n   ✅ State completo é serializável! JSON length: {len(json_str)}")
    except Exception as e:
        print(f"\n   ❌ Erro ao serializar State: {e}")
        print(f"   Tipo do erro: {type(e).__name__}")
        return False
    
    # Teste 5: Simular clique em "Novo Chat"
    print("\n5. Simulando criação de novo chat...")
    new_session = ChatSession()
    new_session.messages = []
    state.sessions[new_session.id] = new_session
    state.current_session = new_session
    
    print(f"   Nova sessão criada: {new_session.id[:8]}...")
    print(f"   Nova sessão é dataclass? {is_dataclass(new_session)}")
    
    try:
        state_dict = asdict(state)
        json_str = json.dumps(state_dict)
        print(f"   ✅ State após novo chat é serializável! JSON length: {len(json_str)}")
    except Exception as e:
        print(f"   ❌ Erro ao serializar State após novo chat: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("="*60)
    print("TESTE DE SERIALIZAÇÃO DO MESOP")
    print("="*60)
    
    success = test_serialization()
    
    print("\n" + "="*60)
    if success:
        print("✅ TODOS OS TESTES PASSARAM!")
        print("O estado do Mesop está serializável.")
    else:
        print("❌ ALGUM TESTE FALHOU!")
        print("Verifique os erros acima.")
    print("="*60)
    
    sys.exit(0 if success else 1)