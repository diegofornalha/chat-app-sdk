#!/usr/bin/env python3
"""
Script para testar e debugar o erro 'asdict() should be called on dataclass instances'
"""
import sys
sys.path.insert(0, 'backend')

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid

# Importar as classes do app
from app import ChatSession, Message

def test_dataclass_conversion():
    """Testa se ChatSession está sendo convertido incorretamente para dict"""
    print("=== Teste 1: Criação de ChatSession ===")
    
    # Criar uma sessão corretamente
    session = ChatSession()
    print(f"Tipo da sessão criada: {type(session)}")
    print(f"É uma instância de ChatSession? {isinstance(session, ChatSession)}")
    
    # Testar conversão para dict
    try:
        session_dict = asdict(session)
        print("✓ asdict() funcionou corretamente")
    except Exception as e:
        print(f"✗ Erro ao converter para dict: {e}")
    
    print("\n=== Teste 2: Salvamento em Dict ===")
    
    # Simular o que acontece no código
    sessions = {}
    sessions[session.id] = session
    
    # Verificar o tipo armazenado
    stored_session = sessions[session.id]
    print(f"Tipo armazenado em sessions: {type(stored_session)}")
    print(f"É uma instância de ChatSession? {isinstance(stored_session, ChatSession)}")
    
    # Tentar converter o que está armazenado
    try:
        stored_dict = asdict(stored_session)
        print("✓ asdict() funcionou no objeto armazenado")
    except Exception as e:
        print(f"✗ Erro ao converter objeto armazenado: {e}")
    
    print("\n=== Teste 3: Conversão incorreta para dict puro ===")
    
    # Simular conversão incorreta (possível bug)
    wrong_session = {
        'id': str(uuid.uuid4()),
        'messages': [],
        'created_at': datetime.now(),
        'last_activity': datetime.now(),
        'title': 'Nova Conversa',
        'context': '',
        'claude_session_id': None
    }
    
    sessions['wrong'] = wrong_session
    print(f"Tipo do dict puro: {type(wrong_session)}")
    
    # Tentar asdict em um dict puro
    try:
        wrong_dict = asdict(wrong_session)
        print("✓ asdict() funcionou (não deveria!)")
    except TypeError as e:
        print(f"✗ Erro esperado ao tentar asdict em dict puro: {e}")
    
    print("\n=== Teste 4: Verificação de mensagens ===")
    
    # Criar mensagem
    msg = Message(role="user", content="teste")
    session.messages.append(msg)
    
    print(f"Tipo da mensagem: {type(msg)}")
    print(f"É uma instância de Message? {isinstance(msg, Message)}")
    
    # Testar conversão de mensagem
    try:
        msg_dict = asdict(msg)
        print("✓ asdict() funcionou na mensagem")
    except Exception as e:
        print(f"✗ Erro ao converter mensagem: {e}")
    
    return sessions

def test_mesop_state():
    """Testa como o Mesop gerencia o estado"""
    print("\n=== Teste 5: Estado do Mesop ===")
    
    import mesop as me
    
    @me.stateclass
    class TestState:
        current_session: ChatSession = field(default_factory=ChatSession)
        sessions: Dict[str, ChatSession] = field(default_factory=dict)
    
    # Simular criação de estado
    state = TestState()
    print(f"Tipo de current_session no estado: {type(state.current_session)}")
    print(f"É ChatSession? {isinstance(state.current_session, ChatSession)}")
    
    # Simular adição de sessão
    new_session = ChatSession()
    state.sessions[new_session.id] = new_session
    state.current_session = new_session
    
    print(f"Tipo após atribuição: {type(state.current_session)}")
    
    # Testar se dict contamina o estado
    dict_session = {
        'id': 'test',
        'messages': [],
        'title': 'Test'
    }
    
    # Simular problema: atribuir dict em vez de ChatSession
    state.sessions['bad'] = dict_session  # Isto é o problema!
    
    print(f"Tipo do item 'bad' em sessions: {type(state.sessions.get('bad'))}")
    
    # Verificar todos os itens em sessions
    print("\n=== Verificação de todos os items em sessions ===")
    for key, value in state.sessions.items():
        print(f"  {key}: {type(value)} - É ChatSession? {isinstance(value, ChatSession)}")

if __name__ == "__main__":
    print("Teste de Debug do Erro de Dataclass\n")
    print("=" * 50)
    
    sessions = test_dataclass_conversion()
    test_mesop_state()
    
    print("\n" + "=" * 50)
    print("Conclusão:")
    print("O erro ocorre quando dicts puros são salvos em state.sessions")
    print("em vez de objetos ChatSession. Isso pode acontecer quando:")
    print("1. A sessão é convertida para dict inadvertidamente")
    print("2. Dados são restaurados de algum armazenamento como dict")
    print("3. Mesop serializa/deserializa o estado incorretamente")