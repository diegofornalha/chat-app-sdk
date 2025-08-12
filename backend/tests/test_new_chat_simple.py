#!/usr/bin/env python3
"""
Teste simples para o botão "Novo Chat" do Mesop sem dependências externas
Verifica que a funcionalidade funciona corretamente e não quebra a serialização
"""

import unittest
import uuid
import json
from unittest.mock import Mock, patch
from datetime import datetime
from dataclasses import asdict, is_dataclass

# Import das classes do app.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import (
    ChatSession, 
    Message, 
    State, 
    handle_new_chat,
    create_new_session
)


class TestNewChatButton(unittest.TestCase):
    """Testes para a funcionalidade do botão Novo Chat"""
    
    def setUp(self):
        """Configuração inicial para cada teste"""
        self.mock_state = Mock()
        self.mock_state.sessions = {}
        self.mock_state.current_session = None
        self.mock_state.processing_steps = []
        self.mock_state.error_message = ""
        self.mock_state.input_text = ""
        self.mock_state.validate_sessions = Mock()

    def test_create_new_session_is_dataclass(self):
        """Verifica que create_new_session retorna uma dataclass válida"""
        session = create_new_session()
        
        # Verificar que é dataclass
        self.assertTrue(is_dataclass(session))
        self.assertIsInstance(session, ChatSession)
        
        # Verificar campos obrigatórios
        self.assertTrue(hasattr(session, 'id'))
        self.assertTrue(hasattr(session, 'title'))
        self.assertTrue(hasattr(session, 'messages'))
        self.assertTrue(hasattr(session, 'created_at'))
        self.assertTrue(hasattr(session, 'last_activity'))

    def test_timestamps_are_iso_strings(self):
        """Verifica que timestamps são strings ISO, não datetime"""
        session = create_new_session()
        
        # Verificar tipos
        self.assertIsInstance(session.created_at, str)
        self.assertIsInstance(session.last_activity, str)
        
        # Verificar formato ISO (deve não falhar)
        datetime.fromisoformat(session.created_at)
        datetime.fromisoformat(session.last_activity)
        
        # Verificar que contém 'T' (formato ISO)
        self.assertIn('T', session.created_at)
        self.assertIn('T', session.last_activity)

    def test_session_is_json_serializable(self):
        """Verifica que a sessão pode ser serializada para JSON"""
        session = create_new_session()
        
        try:
            # Converter para dict
            session_dict = asdict(session)
            self.assertIsInstance(session_dict, dict)
            
            # Converter para JSON
            json_str = json.dumps(session_dict)
            self.assertIsInstance(json_str, str)
            self.assertTrue(len(json_str) > 0)
            
        except Exception as e:
            self.fail(f"Sessão não é serializável: {e}")

    def test_uuid_validity(self):
        """Verifica que o ID da sessão é um UUID válido"""
        session = create_new_session()
        
        # Verificar que é string
        self.assertIsInstance(session.id, str)
        
        # Verificar que é UUID válido (não deve falhar)
        parsed_uuid = uuid.UUID(session.id)
        self.assertEqual(str(parsed_uuid), session.id)

    @patch('app.me.state')
    def test_handle_new_chat_execution(self, mock_me_state):
        """Testa execução da função handle_new_chat"""
        mock_me_state.return_value = self.mock_state
        mock_click_event = Mock()
        
        # Executar função
        handle_new_chat(mock_click_event)
        
        # Verificar que validate_sessions foi chamado
        self.mock_state.validate_sessions.assert_called_once()

    @patch('app.me.state')
    def test_new_chat_creates_session(self, mock_me_state):
        """Verifica que handle_new_chat cria uma nova sessão"""
        state = State()
        state.sessions = {}
        mock_me_state.return_value = state
        
        mock_click_event = Mock()
        handle_new_chat(mock_click_event)
        
        # Verificar que uma sessão foi criada
        self.assertEqual(len(state.sessions), 1)
        self.assertIsNotNone(state.current_session)
        
        # Verificar que a sessão é uma dataclass
        session_id = list(state.sessions.keys())[0]
        created_session = state.sessions[session_id]
        self.assertTrue(is_dataclass(created_session))

    def test_message_dataclass_serializable(self):
        """Verifica que Message é serializável"""
        message = Message(role="user", content="Teste")
        
        self.assertTrue(is_dataclass(message))
        
        try:
            message_dict = asdict(message)
            json_str = json.dumps(message_dict)
            self.assertTrue(len(json_str) > 0)
        except Exception as e:
            self.fail(f"Message não é serializável: {e}")

    def test_complete_state_serializable(self):
        """Verifica que o estado completo é serializável"""
        state = State()
        session = create_new_session("Teste")
        session.messages.append(Message(role="user", content="Teste"))
        
        state.sessions[session.id] = session
        state.current_session = session
        
        try:
            state_dict = asdict(state)
            json_str = json.dumps(state_dict)
            self.assertTrue(len(json_str) > 0)
        except Exception as e:
            self.fail(f"Estado completo não é serializável: {e}")

    def test_no_datetime_objects_in_session(self):
        """Verifica que não há objetos datetime na sessão"""
        session = create_new_session()
        
        # Converter para dict e verificar tipos
        session_dict = asdict(session)
        
        def check_no_datetime(obj, path=""):
            if isinstance(obj, datetime):
                self.fail(f"Objeto datetime encontrado em: {path}")
            elif isinstance(obj, dict):
                for key, value in obj.items():
                    check_no_datetime(value, f"{path}.{key}")
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_no_datetime(item, f"{path}[{i}]")
        
        check_no_datetime(session_dict, "session")

    def test_session_initial_values(self):
        """Verifica valores iniciais da sessão"""
        session = create_new_session()
        
        self.assertEqual(session.title, "Nova Conversa")
        self.assertEqual(session.messages, [])
        self.assertEqual(session.context, "")
        self.assertIsNone(session.claude_session_id)

    def test_multiple_sessions_unique_ids(self):
        """Verifica que múltiplas sessões têm IDs únicos"""
        sessions = [create_new_session() for _ in range(5)]
        
        # Coletar IDs
        ids = [session.id for session in sessions]
        
        # Verificar que são únicos
        self.assertEqual(len(ids), len(set(ids)))
        
        # Verificar que todos são UUIDs válidos
        for session_id in ids:
            uuid.UUID(session_id)  # Não deve falhar


def run_tests():
    """Executa todos os testes e imprime resultados"""
    print("🧪 Executando testes do botão 'Novo Chat'...")
    print("=" * 60)
    
    # Configurar test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestNewChatButton)
    runner = unittest.TextTestRunner(verbosity=2)
    
    # Executar testes
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✅ Todos os testes passaram!")
        print(f"   Executados: {result.testsRun} testes")
        print("   O botão 'Novo Chat' está funcionando corretamente!")
    else:
        print("❌ Alguns testes falharam!")
        print(f"   Executados: {result.testsRun} testes")
        print(f"   Falhas: {len(result.failures)}")
        print(f"   Erros: {len(result.errors)}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)