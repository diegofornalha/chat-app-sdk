"""
Validadores de dados para o backend Flask
Implementa validação robusta usando dataclasses e typing
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
import re
import uuid


@dataclass
class MessageValidator:
    """Validador para mensagens do chat"""
    content: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: Optional[datetime] = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validação após inicialização"""
        # Validar conteúdo
        if not self.content or not self.content.strip():
            raise ValueError("Conteúdo da mensagem não pode estar vazio")
        
        if len(self.content) > 10000:
            raise ValueError("Conteúdo da mensagem excede limite de 10000 caracteres")
        
        # Gerar IDs se não fornecidos
        if not self.user_id:
            self.user_id = str(uuid.uuid4())
        
        if not self.session_id:
            self.session_id = str(uuid.uuid4())
        
        # Validar timestamp
        if not isinstance(self.timestamp, datetime):
            raise TypeError("Timestamp deve ser um objeto datetime")
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            "content": self.content,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class SessionValidator:
    """Validador para sessões do chat"""
    id: str
    title: str
    messages: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validação após inicialização"""
        # Validar ID
        if not self.id:
            raise ValueError("ID da sessão é obrigatório")
        
        # Validar título
        if not self.title or not self.title.strip():
            raise ValueError("Título da sessão não pode estar vazio")
        
        if len(self.title) > 200:
            raise ValueError("Título da sessão excede limite de 200 caracteres")
        
        # Validar mensagens
        if not isinstance(self.messages, list):
            raise TypeError("Mensagens devem ser uma lista")
        
        # Validar timestamps
        if not isinstance(self.created_at, datetime):
            raise TypeError("created_at deve ser um objeto datetime")
        
        if not isinstance(self.updated_at, datetime):
            raise TypeError("updated_at deve ser um objeto datetime")
    
    def add_message(self, message: MessageValidator):
        """Adiciona uma mensagem validada à sessão"""
        self.messages.append(message.to_dict())
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            "id": self.id,
            "title": self.title,
            "messages": self.messages,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class FileUploadValidator:
    """Validador para upload de arquivos"""
    filename: str
    content: bytes
    content_type: Optional[str] = None
    max_size_mb: int = 10
    
    # Tipos permitidos
    ALLOWED_TYPES = {
        'image/jpeg', 'image/png', 'image/gif', 'image/webp',
        'text/plain', 'text/markdown', 'application/pdf',
        'application/json', 'text/csv'
    }
    
    def __post_init__(self):
        """Validação após inicialização"""
        # Validar nome do arquivo
        if not self.filename:
            raise ValueError("Nome do arquivo é obrigatório")
        
        # Validar extensão
        if not re.match(r'^[\w\-. ]+$', self.filename):
            raise ValueError("Nome do arquivo contém caracteres inválidos")
        
        # Validar tamanho
        size_mb = len(self.content) / (1024 * 1024)
        if size_mb > self.max_size_mb:
            raise ValueError(f"Arquivo excede tamanho máximo de {self.max_size_mb}MB")
        
        # Validar tipo se fornecido
        if self.content_type and self.content_type not in self.ALLOWED_TYPES:
            raise ValueError(f"Tipo de arquivo {self.content_type} não é permitido")
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            "filename": self.filename,
            "size_bytes": len(self.content),
            "content_type": self.content_type
        }


@dataclass
class ClaudeRequestValidator:
    """Validador para requisições ao Claude"""
    prompt: str
    max_tokens: int = 4096
    temperature: float = 0.7
    system_prompt: Optional[str] = None
    
    def __post_init__(self):
        """Validação após inicialização"""
        # Validar prompt
        if not self.prompt or not self.prompt.strip():
            raise ValueError("Prompt não pode estar vazio")
        
        # Validar max_tokens
        if not 1 <= self.max_tokens <= 100000:
            raise ValueError("max_tokens deve estar entre 1 e 100000")
        
        # Validar temperature
        if not 0.0 <= self.temperature <= 1.0:
            raise ValueError("temperature deve estar entre 0.0 e 1.0")
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            "prompt": self.prompt,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "system_prompt": self.system_prompt
        }