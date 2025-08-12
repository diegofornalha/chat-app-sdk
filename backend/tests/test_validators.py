"""
Testes unitários para validadores
"""
import pytest
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from validators import (
    MessageValidator,
    SessionValidator,
    FileUploadValidator,
    ClaudeRequestValidator
)


class TestMessageValidator:
    """Testes para MessageValidator"""
    
    def test_valid_message(self):
        """Testa criação de mensagem válida"""
        msg = MessageValidator(content="Hello, world!")
        assert msg.content == "Hello, world!"
        assert msg.user_id is not None
        assert msg.session_id is not None
        assert isinstance(msg.timestamp, datetime)
    
    def test_empty_content_raises_error(self):
        """Testa que conteúdo vazio gera erro"""
        with pytest.raises(ValueError, match="não pode estar vazio"):
            MessageValidator(content="")
    
    def test_whitespace_content_raises_error(self):
        """Testa que conteúdo só com espaços gera erro"""
        with pytest.raises(ValueError, match="não pode estar vazio"):
            MessageValidator(content="   ")
    
    def test_content_too_long_raises_error(self):
        """Testa que conteúdo muito longo gera erro"""
        with pytest.raises(ValueError, match="excede limite"):
            MessageValidator(content="x" * 10001)
    
    def test_custom_ids(self):
        """Testa uso de IDs customizados"""
        msg = MessageValidator(
            content="Test",
            user_id="user123",
            session_id="session456"
        )
        assert msg.user_id == "user123"
        assert msg.session_id == "session456"
    
    def test_to_dict(self):
        """Testa conversão para dicionário"""
        msg = MessageValidator(content="Test message")
        result = msg.to_dict()
        
        assert result["content"] == "Test message"
        assert "user_id" in result
        assert "session_id" in result
        assert "timestamp" in result
        assert "metadata" in result


class TestSessionValidator:
    """Testes para SessionValidator"""
    
    def test_valid_session(self):
        """Testa criação de sessão válida"""
        session = SessionValidator(
            id="session123",
            title="Test Session"
        )
        assert session.id == "session123"
        assert session.title == "Test Session"
        assert isinstance(session.messages, list)
        assert len(session.messages) == 0
    
    def test_empty_id_raises_error(self):
        """Testa que ID vazio gera erro"""
        with pytest.raises(ValueError, match="ID da sessão é obrigatório"):
            SessionValidator(id="", title="Test")
    
    def test_empty_title_raises_error(self):
        """Testa que título vazio gera erro"""
        with pytest.raises(ValueError, match="não pode estar vazio"):
            SessionValidator(id="123", title="")
    
    def test_title_too_long_raises_error(self):
        """Testa que título muito longo gera erro"""
        with pytest.raises(ValueError, match="excede limite"):
            SessionValidator(id="123", title="x" * 201)
    
    def test_add_message(self):
        """Testa adição de mensagem à sessão"""
        session = SessionValidator(id="123", title="Test")
        msg = MessageValidator(content="Test message")
        
        session.add_message(msg)
        
        assert len(session.messages) == 1
        assert session.messages[0]["content"] == "Test message"
    
    def test_to_dict(self):
        """Testa conversão para dicionário"""
        session = SessionValidator(id="123", title="Test Session")
        result = session.to_dict()
        
        assert result["id"] == "123"
        assert result["title"] == "Test Session"
        assert "messages" in result
        assert "created_at" in result
        assert "updated_at" in result


class TestFileUploadValidator:
    """Testes para FileUploadValidator"""
    
    def test_valid_file(self):
        """Testa upload de arquivo válido"""
        file = FileUploadValidator(
            filename="test.txt",
            content=b"Hello, world!",
            content_type="text/plain"
        )
        assert file.filename == "test.txt"
        assert file.content == b"Hello, world!"
    
    def test_empty_filename_raises_error(self):
        """Testa que nome vazio gera erro"""
        with pytest.raises(ValueError, match="Nome do arquivo é obrigatório"):
            FileUploadValidator(filename="", content=b"test")
    
    def test_invalid_filename_raises_error(self):
        """Testa que nome inválido gera erro"""
        with pytest.raises(ValueError, match="caracteres inválidos"):
            FileUploadValidator(filename="../../etc/passwd", content=b"test")
    
    def test_file_too_large_raises_error(self):
        """Testa que arquivo muito grande gera erro"""
        with pytest.raises(ValueError, match="excede tamanho máximo"):
            FileUploadValidator(
                filename="large.bin",
                content=b"x" * (11 * 1024 * 1024),  # 11MB
                max_size_mb=10
            )
    
    def test_invalid_content_type_raises_error(self):
        """Testa que tipo inválido gera erro"""
        with pytest.raises(ValueError, match="não é permitido"):
            FileUploadValidator(
                filename="test.exe",
                content=b"test",
                content_type="application/x-msdownload"
            )
    
    def test_allowed_content_types(self):
        """Testa tipos de arquivo permitidos"""
        allowed_types = [
            ("test.jpg", "image/jpeg"),
            ("test.png", "image/png"),
            ("test.txt", "text/plain"),
            ("test.pdf", "application/pdf"),
            ("test.json", "application/json")
        ]
        
        for filename, content_type in allowed_types:
            file = FileUploadValidator(
                filename=filename,
                content=b"test",
                content_type=content_type
            )
            assert file.content_type == content_type


class TestClaudeRequestValidator:
    """Testes para ClaudeRequestValidator"""
    
    def test_valid_request(self):
        """Testa requisição válida"""
        req = ClaudeRequestValidator(
            prompt="Test prompt",
            max_tokens=1000,
            temperature=0.5
        )
        assert req.prompt == "Test prompt"
        assert req.max_tokens == 1000
        assert req.temperature == 0.5
    
    def test_empty_prompt_raises_error(self):
        """Testa que prompt vazio gera erro"""
        with pytest.raises(ValueError, match="não pode estar vazio"):
            ClaudeRequestValidator(prompt="")
    
    def test_invalid_max_tokens_raises_error(self):
        """Testa que max_tokens inválido gera erro"""
        with pytest.raises(ValueError, match="deve estar entre"):
            ClaudeRequestValidator(prompt="test", max_tokens=0)
        
        with pytest.raises(ValueError, match="deve estar entre"):
            ClaudeRequestValidator(prompt="test", max_tokens=100001)
    
    def test_invalid_temperature_raises_error(self):
        """Testa que temperature inválida gera erro"""
        with pytest.raises(ValueError, match="deve estar entre"):
            ClaudeRequestValidator(prompt="test", temperature=-0.1)
        
        with pytest.raises(ValueError, match="deve estar entre"):
            ClaudeRequestValidator(prompt="test", temperature=1.1)
    
    def test_with_system_prompt(self):
        """Testa requisição com system prompt"""
        req = ClaudeRequestValidator(
            prompt="Test",
            system_prompt="You are a helpful assistant"
        )
        assert req.system_prompt == "You are a helpful assistant"
    
    def test_to_dict(self):
        """Testa conversão para dicionário"""
        req = ClaudeRequestValidator(
            prompt="Test prompt",
            max_tokens=2000,
            temperature=0.8,
            system_prompt="System"
        )
        result = req.to_dict()
        
        assert result["prompt"] == "Test prompt"
        assert result["max_tokens"] == 2000
        assert result["temperature"] == 0.8
        assert result["system_prompt"] == "System"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])