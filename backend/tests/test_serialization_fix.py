#!/usr/bin/env python3
"""
Teste para verificar que a correção do erro 'asdict() should be called on dataclass instances' está funcionando
Este teste valida especificamente que o botão Novo Chat não quebra a serialização do Mesop

Verifica:
1. Que ChatSession é uma dataclass válida
2. Que timestamps são strings ISO, não datetime objects
3. Que o estado completo é serializável pelo Mesop
4. Que o erro proto.mesop.ServerError não ocorre mais
"""

import pytest
import json
import uuid
from datetime import datetime
from dataclasses import asdict, is_dataclass
from unittest.mock import Mock, patch

# Import das classes do app.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import (
    ChatSession, 
    Message, 
    State, 
    ProcessingStep,
    handle_new_chat,
    create_new_session,
    ensure_chatsession
)


class TestSerializationFix:
    """Testes para garantir que a correção do erro de serialização está funcionando"""
    
    def test_chatsession_is_dataclass(self):
        """Verifica que ChatSession é uma dataclass válida"""
        session = create_new_session()
        
        # Verificação fundamental
        assert is_dataclass(session), "ChatSession deve ser uma dataclass"
        assert isinstance(session, ChatSession), "Deve ser instância de ChatSession"
        
        # Deve poder ser serializada por asdict()
        try:
            serialized = asdict(session)
            assert isinstance(serialized, dict)
        except TypeError as e:
            pytest.fail(f"ChatSession não pode ser serializada: {e}")

    def test_message_is_dataclass(self):
        """Verifica que Message é uma dataclass válida"""
        message = Message(role="user", content="Teste")
        
        assert is_dataclass(message), "Message deve ser uma dataclass"
        
        # Deve poder ser serializada
        try:
            serialized = asdict(message)
            assert isinstance(serialized, dict)
            assert "role" in serialized
            assert "content" in serialized
            assert "timestamp" in serialized
        except TypeError as e:
            pytest.fail(f"Message não pode ser serializada: {e}")

    def test_processing_step_is_dataclass(self):
        """Verifica que ProcessingStep é uma dataclass válida"""
        step = ProcessingStep(type="test", message="Teste de processamento")
        
        assert is_dataclass(step), "ProcessingStep deve ser uma dataclass"
        
        # Deve poder ser serializada
        try:
            serialized = asdict(step)
            assert isinstance(serialized, dict)
        except TypeError as e:
            pytest.fail(f"ProcessingStep não pode ser serializada: {e}")

    def test_timestamps_are_strings_not_datetime(self):
        """Verifica que todos os timestamps são strings ISO, não datetime objects"""
        # Testar ChatSession
        session = create_new_session()
        assert isinstance(session.created_at, str), "created_at deve ser string"
        assert isinstance(session.last_activity, str), "last_activity deve ser string"
        
        # Verificar formato ISO
        datetime.fromisoformat(session.created_at)  # Deve não falhar
        datetime.fromisoformat(session.last_activity)  # Deve não falhar
        
        # Testar Message
        message = Message(role="user", content="Teste")
        assert isinstance(message.timestamp, str), "Message.timestamp deve ser string"
        datetime.fromisoformat(message.timestamp)  # Deve não falhar
        
        # Testar ProcessingStep
        step = ProcessingStep(type="test", message="Teste")
        assert isinstance(step.timestamp, str), "ProcessingStep.timestamp deve ser string"
        datetime.fromisoformat(step.timestamp)  # Deve não falhar

    def test_complete_state_json_serializable(self):
        """Verifica que o estado completo do Mesop é serializável para JSON"""
        # Criar estado com dados reais
        state = State()
        
        # Adicionar uma sessão com mensagens
        session = create_new_session("Teste de Serialização")
        session.messages.append(Message(role="user", content="Teste user"))
        session.messages.append(Message(role="assistant", content="Teste assistant"))
        
        state.sessions[session.id] = session
        state.current_session = session
        
        # Adicionar steps de processamento
        state.processing_steps.append(
            ProcessingStep(type="test", message="Passo de teste")
        )
        
        # Tentar serializar o estado completo
        try:
            # Esta é a operação que falha com o erro original
            state_dict = asdict(state)
            json_str = json.dumps(state_dict)
            
            # Verificar que o JSON foi criado corretamente
            assert isinstance(json_str, str)
            assert len(json_str) > 0
            
            # Verificar que pode ser deserializado de volta
            parsed = json.loads(json_str)
            assert isinstance(parsed, dict)
            assert "sessions" in parsed
            assert "current_session" in parsed
            
        except TypeError as e:
            pytest.fail(f"Estado não é serializável para JSON: {e}")
        except Exception as e:
            pytest.fail(f"Erro inesperado na serialização: {e}")

    @patch('app.me.state')
    def test_new_chat_creates_serializable_state(self, mock_me_state):
        """Testa que handle_new_chat cria um estado que é serializável"""
        # Estado inicial
        state = State()
        state.sessions = {}
        mock_me_state.return_value = state
        
        # Mock do evento
        mock_click_event = Mock()
        
        # Executar handle_new_chat
        handle_new_chat(mock_click_event)
        
        # Verificar que o estado resultante é serializável
        try:
            state_dict = asdict(state)
            json_str = json.dumps(state_dict)
            assert len(json_str) > 0
        except TypeError as e:
            pytest.fail(f"Estado após handle_new_chat não é serializável: {e}")

    def test_state_with_multiple_sessions_serializable(self):
        """Testa serialização de estado com múltiplas sessões"""
        state = State()
        
        # Criar múltiplas sessões
        for i in range(3):
            session = create_new_session(f"Sessão {i}")
            session.messages.append(Message(role="user", content=f"Mensagem {i}"))
            state.sessions[session.id] = session
        
        # Definir sessão atual
        state.current_session = list(state.sessions.values())[0]
        
        # Tentar serializar
        try:
            state_dict = asdict(state)
            json_str = json.dumps(state_dict)
            
            # Verificar estrutura
            parsed = json.loads(json_str)
            assert len(parsed["sessions"]) == 3
            assert parsed["current_session"]["title"].startswith("Sessão")
            
        except Exception as e:
            pytest.fail(f"Estado com múltiplas sessões não é serializável: {e}")

    def test_specific_error_fields_resolved(self):
        """Testa que os campos específicos que causavam o erro foram corrigidos"""
        session = create_new_session()
        
        # Verificar que não temos objetos datetime nos campos críticos
        assert not isinstance(session.created_at, datetime), "created_at não deve ser datetime"
        assert not isinstance(session.last_activity, datetime), "last_activity não deve ser datetime"
        
        message = Message(role="test", content="teste")
        assert not isinstance(message.timestamp, datetime), "Message.timestamp não deve ser datetime"
        
        step = ProcessingStep(type="test", message="teste")
        assert not isinstance(step.timestamp, datetime), "ProcessingStep.timestamp não deve ser datetime"

    def test_ensure_chatsession_preserves_serializability(self):
        """Testa que ensure_chatsession mantém a capacidade de serialização"""
        # Teste com dict
        session_dict = {
            'id': str(uuid.uuid4()),
            'title': 'Teste Dict',
            'messages': [],
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat(),
            'context': '',
            'claude_session_id': None
        }
        
        session = ensure_chatsession(session_dict)
        
        # Verificar que resultado é serializável
        try:
            session_dict = asdict(session)
            json_str = json.dumps(session_dict)
            assert len(json_str) > 0
        except Exception as e:
            pytest.fail(f"ensure_chatsession não preserva serializabilidade: {e}")

    def test_no_datetime_objects_anywhere(self):
        """Teste abrangente para garantir que não há objetos datetime em lugar nenhum"""
        # Criar estado completo
        state = State()
        session = create_new_session()
        session.messages.extend([
            Message(role="user", content="Teste 1"),
            Message(role="assistant", content="Resposta 1"),
        ])
        state.sessions[session.id] = session
        state.current_session = session
        state.processing_steps.append(ProcessingStep(type="test", message="Teste"))
        
        # Converter para dict e procurar objetos datetime
        def find_datetime_objects(obj, path=""):
            """Busca recursivamente por objetos datetime"""
            datetime_found = []
            
            if isinstance(obj, datetime):
                datetime_found.append(f"datetime encontrado em: {path}")
            elif isinstance(obj, dict):
                for key, value in obj.items():
                    datetime_found.extend(find_datetime_objects(value, f"{path}.{key}"))
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    datetime_found.extend(find_datetime_objects(item, f"{path}[{i}]"))
            
            return datetime_found
        
        state_dict = asdict(state)
        datetime_objects = find_datetime_objects(state_dict)
        
        assert len(datetime_objects) == 0, f"Objetos datetime encontrados: {datetime_objects}"

    def test_json_roundtrip_preservation(self):
        """Testa que dados sobrevivem ao ciclo JSON completo sem perda"""
        # Criar estado com dados
        original_state = State()
        session = create_new_session("Teste Roundtrip")
        session.messages.append(Message(role="user", content="Mensagem original"))
        original_state.sessions[session.id] = session
        original_state.current_session = session
        
        # Serializar para JSON
        state_dict = asdict(original_state)
        json_str = json.dumps(state_dict)
        
        # Deserializar de volta
        parsed_dict = json.loads(json_str)
        
        # Verificar que dados importantes foram preservados
        assert len(parsed_dict["sessions"]) == 1
        session_data = list(parsed_dict["sessions"].values())[0]
        assert session_data["title"] == "Teste Roundtrip"
        assert len(session_data["messages"]) == 1
        assert session_data["messages"][0]["content"] == "Mensagem original"
        
        # Verificar formato de timestamps
        assert "T" in session_data["created_at"]  # Formato ISO
        assert "T" in session_data["messages"][0]["timestamp"]  # Formato ISO


if __name__ == "__main__":
    # Executar testes se executado diretamente
    pytest.main([__file__, "-v", "--tb=short"])