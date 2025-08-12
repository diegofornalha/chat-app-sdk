#!/usr/bin/env python3
"""
Script de teste para debugar o erro 'asdict() should be called on dataclass instances'
"""
import sys
sys.path.insert(0, 'backend')

from dataclasses import asdict, is_dataclass
from app import ChatSession, Message, State, dict_to_chat_session
import traceback

def test_serialization():
    """Testa se as classes podem ser serializadas com asdict()"""
    print("=" * 60)
    print("TESTE DE SERIALIZAÇÃO")
    print("=" * 60)
    
    # Teste 1: Message
    print("\n1. Testando Message...")
    msg = Message(role="user", content="Olá")
    print(f"   Message criada: {type(msg)}")
    print(f"   É dataclass? {is_dataclass(msg)}")
    try:
        msg_dict = asdict(msg)
        print(f"   ✅ Serialização OK: {len(msg_dict)} campos")
    except Exception as e:
        print(f"   ❌ Erro na serialização: {e}")
    
    # Teste 2: ChatSession
    print("\n2. Testando ChatSession...")
    session = ChatSession()
    session.messages.append(msg)
    print(f"   ChatSession criada: {type(session)}")
    print(f"   É dataclass? {is_dataclass(session)}")
    try:
        session_dict = asdict(session)
        print(f"   ✅ Serialização OK: {len(session_dict)} campos")
    except Exception as e:
        print(f"   ❌ Erro na serialização: {e}")
        traceback.print_exc()
    
    # Teste 3: State
    print("\n3. Testando State...")
    state = State()
    print(f"   State criado: {type(state)}")
    print(f"   É dataclass? {is_dataclass(state)}")
    print(f"   current_session type: {type(state.current_session)}")
    print(f"   current_session é dataclass? {is_dataclass(state.current_session)}")
    try:
        state_dict = asdict(state)
        print(f"   ✅ Serialização OK: {len(state_dict)} campos")
    except Exception as e:
        print(f"   ❌ Erro na serialização: {e}")
        traceback.print_exc()
    
    # Teste 4: Conversão dict -> ChatSession
    print("\n4. Testando conversão dict -> ChatSession...")
    dict_session = {
        'id': 'test-123',
        'title': 'Teste',
        'messages': [
            {'role': 'user', 'content': 'Oi'}
        ]
    }
    converted = dict_to_chat_session(dict_session)
    print(f"   Convertido: {type(converted)}")
    print(f"   É dataclass? {is_dataclass(converted)}")
    try:
        converted_dict = asdict(converted)
        print(f"   ✅ Serialização OK: {len(converted_dict)} campos")
    except Exception as e:
        print(f"   ❌ Erro na serialização: {e}")

def test_new_chat_flow():
    """Simula o fluxo do botão Novo Chat"""
    print("\n" + "=" * 60)
    print("SIMULAÇÃO DO FLUXO 'NOVO CHAT'")
    print("=" * 60)
    
    # Criar estado inicial
    state = State()
    print(f"\n1. Estado inicial criado")
    print(f"   current_session: {type(state.current_session)}")
    print(f"   sessions: {len(state.sessions)} sessões")
    
    # Validar sessões (como no validate_state_before_render)
    print(f"\n2. Validando sessões...")
    state.validate_sessions()
    print(f"   current_session após validação: {type(state.current_session)}")
    
    # Criar nova sessão (como no handle_new_chat)
    print(f"\n3. Criando nova sessão...")
    new_session = ChatSession()
    new_session.messages = []
    print(f"   Nova sessão: {type(new_session)}")
    print(f"   É dataclass? {is_dataclass(new_session)}")
    
    # Adicionar ao estado
    state.sessions[new_session.id] = new_session
    state.current_session = new_session
    print(f"   Sessão adicionada ao estado")
    print(f"   current_session: {type(state.current_session)}")
    
    # Tentar serializar o estado completo
    print(f"\n4. Tentando serializar estado completo...")
    try:
        state_dict = asdict(state)
        print(f"   ✅ SUCESSO! Estado serializado com {len(state_dict)} campos")
    except Exception as e:
        print(f"   ❌ ERRO: {e}")
        print(f"\n   Detalhes do erro:")
        traceback.print_exc()
        
        # Diagnóstico adicional
        print(f"\n   Diagnóstico:")
        print(f"   - state é dataclass? {is_dataclass(state)}")
        print(f"   - current_session é dataclass? {is_dataclass(state.current_session)}")
        for sid, sess in state.sessions.items():
            print(f"   - session {sid} é dataclass? {is_dataclass(sess)}")

if __name__ == "__main__":
    print("🔍 INICIANDO TESTES DE DEBUG")
    print("=" * 60)
    
    test_serialization()
    test_new_chat_flow()
    
    print("\n" + "=" * 60)
    print("✅ TESTES CONCLUÍDOS")
    print("=" * 60)