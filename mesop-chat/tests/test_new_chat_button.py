#!/usr/bin/env python3
"""
Teste automatizado que simula clique no botão 'Novo Chat' do Mesop UI
Verifica criação correta de ChatSession e validação de tipos
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, is_dataclass, asdict
from typing import Dict, List, Any
import json
import uuid

# Adicionar o diretório backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Mock do Mesop antes de importar o app
class MockClickEvent:
    """Mock do me.ClickEvent"""
    def __init__(self):
        self.key = "mock_click"
        self.value = None

class MockState:
    """Mock para me.state()"""
    _instance = None
    
    def __init__(self, state_class):
        if MockState._instance is None:
            MockState._instance = state_class()
        return MockState._instance

# Mock do módulo mesop
class MockMesop:
    @staticmethod
    def state(state_class):
        """Retorna instância do estado"""
        if not hasattr(MockMesop, '_state_instance'):
            MockMesop._state_instance = state_class()
        return MockMesop._state_instance
    
    @staticmethod
    def stateclass(cls):
        """Decorator mock para stateclass"""
        return dataclass(cls)
    
    class ClickEvent:
        def __init__(self):
            self.key = "mock_click"

# Substituir importação do mesop
sys.modules['mesop'] = MockMesop()
sys.modules['mesop.labs'] = MockMesop()
me = MockMesop()

# Agora importar as classes do app
from app import (
    ChatSession, 
    Message, 
    State,
    create_new_session,
    ensure_chatsession,
    normalize_sessions,
    save_session,
    handle_new_chat
)

def test_new_chat_button_click():
    """Testa o comportamento completo do clique no botão Novo Chat"""
    
    print("\n🧪 TESTE: Simulação de clique no botão 'Novo Chat'")
    print("=" * 60)
    
    # 1. Configurar estado inicial
    print("\n1️⃣ Configurando estado inicial...")
    MockMesop._state_instance = State()
    state = MockMesop.state(State)
    
    # Criar sessão inicial
    initial_session = create_new_session("Sessão Inicial")
    state.sessions[initial_session.id] = initial_session
    state.current_session = initial_session
    
    # Adicionar uma mensagem à sessão inicial
    initial_message = Message(
        content="Mensagem de teste",
        role="user"
    )
    state.current_session.messages.append(initial_message)
    
    print(f"   ✅ Estado inicial criado com {len(state.sessions)} sessão")
    print(f"   ✅ Sessão atual: {state.current_session.title}")
    print(f"   ✅ Mensagens na sessão: {len(state.current_session.messages)}")
    
    # 2. Verificar tipos antes do clique
    print("\n2️⃣ Verificando tipos antes do clique...")
    assert isinstance(state.current_session, ChatSession), "current_session deve ser ChatSession"
    assert is_dataclass(state.current_session), "current_session deve ser dataclass"
    
    for session_id, session in state.sessions.items():
        assert isinstance(session, ChatSession), f"Session {session_id} deve ser ChatSession"
        assert is_dataclass(session), f"Session {session_id} deve ser dataclass"
    
    print("   ✅ Todos os tipos estão corretos antes do clique")
    
    # 3. Simular clique no botão
    print("\n3️⃣ Simulando clique no botão 'Novo Chat'...")
    initial_session_count = len(state.sessions)
    initial_session_id = state.current_session.id
    
    # Criar evento mock
    click_event = MockMesop.ClickEvent()
    
    # Executar handler
    handle_new_chat(click_event)
    
    print("   ✅ Handler handle_new_chat executado")
    
    # 4. Verificar nova sessão criada
    print("\n4️⃣ Verificando nova sessão criada...")
    assert len(state.sessions) == initial_session_count + 1, "Deve ter uma nova sessão"
    assert state.current_session.id != initial_session_id, "current_session deve ser diferente"
    assert state.current_session.title == "Nova Conversa", "Título deve ser 'Nova Conversa'"
    assert len(state.current_session.messages) == 0, "Nova sessão deve ter 0 mensagens"
    
    print(f"   ✅ Nova sessão criada com ID: {state.current_session.id}")
    print(f"   ✅ Total de sessões agora: {len(state.sessions)}")
    
    # 5. Verificar que é dataclass, não dict
    print("\n5️⃣ Verificando que nova sessão é dataclass...")
    assert isinstance(state.current_session, ChatSession), "Nova sessão deve ser ChatSession"
    assert is_dataclass(state.current_session), "Nova sessão deve ser dataclass"
    assert not isinstance(state.current_session, dict), "Nova sessão NÃO deve ser dict"
    
    # Verificar no dicionário também
    saved_session = state.sessions[state.current_session.id]
    assert isinstance(saved_session, ChatSession), "Sessão salva deve ser ChatSession"
    assert is_dataclass(saved_session), "Sessão salva deve ser dataclass"
    
    print("   ✅ Nova sessão é dataclass corretamente")
    
    # 6. Verificar timestamps como ISO strings
    print("\n6️⃣ Verificando timestamps como ISO strings...")
    assert isinstance(state.current_session.created_at, str), "created_at deve ser string"
    assert isinstance(state.current_session.last_activity, str), "last_activity deve ser string"
    
    # Verificar formato ISO
    try:
        datetime.fromisoformat(state.current_session.created_at)
        datetime.fromisoformat(state.current_session.last_activity)
        print("   ✅ Timestamps são strings ISO válidas")
    except ValueError as e:
        raise AssertionError(f"Timestamps não estão em formato ISO: {e}")
    
    # 7. Verificar serialização JSON
    print("\n7️⃣ Verificando serialização JSON...")
    try:
        # Tentar serializar como o Mesop faria
        json_str = json.dumps(asdict(state.current_session))
        print(f"   ✅ Sessão é JSON serializável ({len(json_str)} bytes)")
        
        # Verificar todo o estado
        state_dict = asdict(state)
        json_str = json.dumps(state_dict)
        print(f"   ✅ Estado completo é JSON serializável ({len(json_str)} bytes)")
    except TypeError as e:
        raise AssertionError(f"Erro de serialização: {e}")
    
    # 8. Verificar que sessão anterior ainda existe
    print("\n8️⃣ Verificando que sessão anterior ainda existe...")
    assert initial_session_id in state.sessions, "Sessão inicial deve ainda existir"
    old_session = state.sessions[initial_session_id]
    assert len(old_session.messages) == 1, "Sessão antiga deve manter suas mensagens"
    
    print("   ✅ Sessão anterior preservada corretamente")
    
    print("\n" + "=" * 60)
    print("🎉 SUCESSO! Todos os testes passaram!")
    print("✅ O botão 'Novo Chat' está funcionando corretamente")
    print("✅ Não há problemas de dict vs dataclass")
    print("✅ Serialização JSON funciona perfeitamente")
    
    return True

def test_multiple_new_chats():
    """Testa criação de múltiplas novas sessões em sequência"""
    
    print("\n🧪 TESTE: Múltiplos cliques no botão 'Novo Chat'")
    print("=" * 60)
    
    # Resetar estado
    MockMesop._state_instance = State()
    state = MockMesop.state(State)
    
    # Criar várias sessões
    session_ids = []
    for i in range(5):
        click_event = MockMesop.ClickEvent()
        handle_new_chat(click_event)
        session_ids.append(state.current_session.id)
        print(f"   ✅ Sessão {i+1} criada: {state.current_session.id}")
    
    # Verificar que todas são diferentes
    assert len(set(session_ids)) == 5, "Todas as sessões devem ter IDs únicos"
    assert len(state.sessions) >= 5, "Deve ter pelo menos 5 sessões"
    
    # Verificar que todas são dataclasses
    for session_id, session in state.sessions.items():
        assert is_dataclass(session), f"Session {session_id} deve ser dataclass"
        assert isinstance(session.created_at, str), f"Session {session_id} created_at deve ser string"
    
    print("\n✅ Múltiplas sessões criadas com sucesso!")
    return True

def test_error_prevention():
    """Testa que o erro 'asdict() should be called on dataclass instances' não ocorre"""
    
    print("\n🧪 TESTE: Prevenção do erro de serialização")
    print("=" * 60)
    
    # Resetar estado
    MockMesop._state_instance = State()
    state = MockMesop.state(State)
    
    # Simular cenário que causava erro
    print("\n1️⃣ Criando sessão com potencial para erro...")
    
    # Tentar forçar o problema antigo
    bad_session = {
        'id': 'test-id',
        'title': 'Test Session',
        'messages': [],
        'created_at': datetime.now(),  # datetime object - causaria erro!
        'last_activity': datetime.now()
    }
    
    # Nossa função deve corrigir isso
    fixed_session = ensure_chatsession(bad_session)
    
    print("   ✅ ensure_chatsession corrigiu o problema")
    
    # Verificar que foi corrigido
    assert isinstance(fixed_session.created_at, str), "created_at deve ser string após correção"
    assert isinstance(fixed_session.last_activity, str), "last_activity deve ser string após correção"
    
    # Tentar serializar
    try:
        json_str = json.dumps(asdict(fixed_session))
        print(f"   ✅ Sessão corrigida é serializável ({len(json_str)} bytes)")
    except TypeError as e:
        raise AssertionError(f"Correção falhou: {e}")
    
    print("\n✅ Proteção contra erro de serialização funcionando!")
    return True

if __name__ == "__main__":
    """Executar todos os testes"""
    
    print("\n" + "🚀" * 30)
    print("INICIANDO SUITE DE TESTES - BOTÃO 'NOVO CHAT' MESOP")
    print("🚀" * 30)
    
    tests_passed = 0
    tests_failed = 0
    
    tests = [
        test_new_chat_button_click,
        test_multiple_new_chats,
        test_error_prevention
    ]
    
    for test_func in tests:
        try:
            if test_func():
                tests_passed += 1
        except Exception as e:
            tests_failed += 1
            print(f"\n❌ FALHA em {test_func.__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"📊 RESULTADO FINAL:")
    print(f"   ✅ Testes passados: {tests_passed}")
    print(f"   ❌ Testes falhados: {tests_failed}")
    
    if tests_failed == 0:
        print("\n🎊 TODOS OS TESTES PASSARAM COM SUCESSO! 🎊")
        print("O botão 'Novo Chat' está funcionando perfeitamente!")
    else:
        print(f"\n⚠️ {tests_failed} teste(s) falharam. Verifique os erros acima.")
    
    sys.exit(0 if tests_failed == 0 else 1)