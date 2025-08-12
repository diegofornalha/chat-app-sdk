"""
Chat App com Claude Code SDK - Versão Melhorada
Backend Python com validação robusta, logging estruturado e tratamento de erros
"""
import mesop as me
import mesop.labs as mel
from anthropic import Anthropic
import os
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid
from pathlib import Path
import json
import base64

# Claude Code SDK
from claude_code_sdk import query, ClaudeCodeOptions

# Módulos de melhoria
from validators import (
    MessageValidator,
    SessionValidator,
    FileUploadValidator,
    ClaudeRequestValidator
)
from logger_config import app_logger, claude_logger, LoggerMixin
from error_handlers import (
    handle_errors,
    retry_on_failure,
    circuit_breaker,
    ErrorHandler,
    ValidationError,
    ClaudeAPIError,
    SessionError
)

# Inicializar cliente Anthropic (para uso direto da API se necessário)
anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


@me.stateclass
class State(LoggerMixin):
    """Estado da aplicação Mesop com logging integrado"""
    # Sessão atual
    current_session_id: str = ""
    current_session_title: str = "Nova Conversa"
    current_session_messages: str = "[]"  # JSON string de mensagens
    
    # Todas as sessões como JSON string
    sessions: str = "{}"  # JSON string de sessões
    
    # Estados da UI
    input_text: str = ""
    is_loading: bool = False
    error_message: str = ""
    show_sidebar: bool = True
    uploaded_file_content: str = ""
    uploaded_file_name: str = ""
    use_claude_sdk: bool = True
    
    # Passos de processamento como JSON string
    processing_steps: str = "[]"
    current_response: str = ""
    stream_content: str = ""


class ChatApplication(LoggerMixin):
    """Classe principal da aplicação com melhorias"""
    
    def __init__(self):
        self.error_handler = ErrorHandler()
        self.log_info("Chat application initialized")
    
    @handle_errors(default_return=[], log_errors=True)
    def get_messages_list(self, state: State) -> List[Dict[str, Any]]:
        """Converte string JSON de mensagens para lista com validação"""
        try:
            messages = json.loads(state.current_session_messages)
            return messages
        except json.JSONDecodeError as e:
            self.log_error(f"Failed to parse messages JSON: {e}")
            return []
    
    @handle_errors(log_errors=True)
    def set_messages_list(self, state: State, messages: List[Dict[str, Any]]):
        """Converte lista de mensagens para string JSON com validação"""
        try:
            # Validar cada mensagem antes de salvar
            validated_messages = []
            for msg in messages:
                try:
                    validator = MessageValidator(
                        content=msg.get("content", ""),
                        user_id=msg.get("user_id"),
                        session_id=msg.get("session_id")
                    )
                    validated_messages.append(validator.to_dict())
                except ValueError as e:
                    self.log_warning(f"Skipping invalid message: {e}")
                    continue
            
            state.current_session_messages = json.dumps(validated_messages)
        except Exception as e:
            self.log_error(f"Failed to set messages: {e}")
            raise
    
    @handle_errors(default_return={}, log_errors=True)
    def get_sessions_dict(self, state: State) -> Dict[str, Dict[str, Any]]:
        """Converte string JSON de sessões para dicionário com validação"""
        try:
            sessions = json.loads(state.sessions)
            return sessions
        except json.JSONDecodeError as e:
            self.log_error(f"Failed to parse sessions JSON: {e}")
            return {}
    
    @handle_errors(log_errors=True)
    def set_sessions_dict(self, state: State, sessions: Dict[str, Dict[str, Any]]):
        """Converte dicionário de sessões para string JSON com validação"""
        try:
            # Validar cada sessão antes de salvar
            validated_sessions = {}
            for session_id, session_data in sessions.items():
                try:
                    validator = SessionValidator(
                        id=session_id,
                        title=session_data.get("title", "Untitled"),
                        messages=session_data.get("messages", [])
                    )
                    validated_sessions[session_id] = validator.to_dict()
                except ValueError as e:
                    self.log_warning(f"Skipping invalid session {session_id}: {e}")
                    continue
            
            state.sessions = json.dumps(validated_sessions)
        except Exception as e:
            self.log_error(f"Failed to set sessions: {e}")
            raise
    
    @retry_on_failure(max_retries=3, delay=1.0, backoff=2.0)
    @circuit_breaker(failure_threshold=5, recovery_timeout=60)
    async def call_claude_code_sdk(
        self,
        prompt: str,
        session_id: Optional[str] = None
    ) -> tuple[str, Dict[str, Any]]:
        """
        Chama o Claude Code SDK com retry e circuit breaker
        """
        try:
            # Validar requisição
            request_validator = ClaudeRequestValidator(
                prompt=prompt,
                max_tokens=4096,
                temperature=0.7
            )
            
            claude_logger.info(
                "Calling Claude Code SDK",
                extra={'request': request_validator.to_dict()}
            )
            
            # Configurar opções
            options = ClaudeCodeOptions(
                max_turns=3,
                system_prompt=None,
            )
            
            response_text = ""
            metadata = {}
            messages = []
            
            # Executar query assíncrona
            async for message in query(prompt=prompt, options=options):
                messages.append(message)
                if hasattr(message, 'text'):
                    response_text += message.text
                if hasattr(message, 'metadata'):
                    metadata.update(message.metadata)
            
            claude_logger.info(
                "Claude Code SDK response received",
                extra={
                    'response_length': len(response_text),
                    'metadata': metadata
                }
            )
            
            return response_text, metadata
            
        except Exception as e:
            claude_logger.error(
                f"Claude Code SDK error: {str(e)}",
                exc_info=True
            )
            raise ClaudeAPIError(f"Failed to call Claude: {str(e)}")
    
    @handle_errors(log_errors=True)
    async def process_message(
        self,
        state: State,
        message: str,
        use_sdk: bool = True
    ) -> str:
        """
        Processa mensagem do usuário com validação e logging
        """
        try:
            # Validar mensagem
            msg_validator = MessageValidator(
                content=message,
                session_id=state.current_session_id
            )
            
            self.log_info(
                "Processing message",
                session_id=state.current_session_id,
                message_length=len(message)
            )
            
            # Adicionar mensagem do usuário
            messages = self.get_messages_list(state)
            messages.append({
                "role": "user",
                "content": message,
                "timestamp": datetime.now().isoformat()
            })
            self.set_messages_list(state, messages)
            
            # Processar com Claude
            if use_sdk:
                response, metadata = await self.call_claude_code_sdk(
                    message,
                    state.current_session_id
                )
            else:
                # Fallback para API direta se SDK falhar
                response = await self.call_anthropic_direct(message)
                metadata = {}
            
            # Adicionar resposta
            messages.append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata
            })
            self.set_messages_list(state, messages)
            
            self.log_info(
                "Message processed successfully",
                session_id=state.current_session_id,
                response_length=len(response)
            )
            
            return response
            
        except ValidationError as e:
            self.log_error(f"Validation error: {e}")
            return f"Erro de validação: {str(e)}"
        except ClaudeAPIError as e:
            self.log_error(f"Claude API error: {e}")
            return "Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente."
        except Exception as e:
            self.log_error(f"Unexpected error: {e}")
            return "Ocorreu um erro inesperado. Por favor, tente novamente."
    
    @retry_on_failure(max_retries=2, delay=0.5)
    async def call_anthropic_direct(self, message: str) -> str:
        """
        Fallback para chamada direta da API Anthropic
        """
        try:
            response = anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                messages=[{"role": "user", "content": message}]
            )
            return response.content[0].text
        except Exception as e:
            self.log_error(f"Direct API call failed: {e}")
            raise ClaudeAPIError(f"Direct API call failed: {str(e)}")
    
    @handle_errors(log_errors=True)
    def handle_file_upload(
        self,
        state: State,
        filename: str,
        content: bytes
    ) -> bool:
        """
        Processa upload de arquivo com validação
        """
        try:
            # Validar arquivo
            file_validator = FileUploadValidator(
                filename=filename,
                content=content,
                content_type=self.get_content_type(filename)
            )
            
            self.log_info(
                "File uploaded",
                filename=filename,
                size_bytes=len(content)
            )
            
            # Salvar conteúdo (base64 para armazenamento em string)
            state.uploaded_file_content = base64.b64encode(content).decode('utf-8')
            state.uploaded_file_name = filename
            
            return True
            
        except ValidationError as e:
            self.log_error(f"File validation error: {e}")
            state.error_message = str(e)
            return False
        except Exception as e:
            self.log_error(f"File upload error: {e}")
            state.error_message = "Erro ao processar arquivo"
            return False
    
    def get_content_type(self, filename: str) -> str:
        """Determina content-type baseado na extensão"""
        ext = Path(filename).suffix.lower()
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.txt': 'text/plain',
            '.md': 'text/markdown',
            '.pdf': 'application/pdf',
            '.json': 'application/json',
            '.csv': 'text/csv'
        }
        return content_types.get(ext, 'application/octet-stream')


# Instância global da aplicação
chat_app = ChatApplication()


@me.page(
    security_policy=me.SecurityPolicy(
        allowed_iframe_parents=["https://localhost:*", "https://*.claude.ai"],
        dangerously_disable_trusted_types=True,
    ),
    path="/",
    title="Chat App - Claude Code SDK (Melhorado)",
)
def main():
    """Página principal da aplicação com melhorias"""
    state = me.state(State)
    
    with me.box(
        style=me.Style(
            display="flex",
            flex_direction="column",
            height="100vh",
            background="#f5f5f5",
        )
    ):
        # Header
        render_header(state)
        
        # Main content
        with me.box(
            style=me.Style(
                display="flex",
                flex="1",
                overflow="hidden",
            )
        ):
            # Sidebar
            if state.show_sidebar:
                render_sidebar(state)
            
            # Chat area
            render_chat_area(state)
    
    # Error display
    if state.error_message:
        render_error_message(state)


def render_header(state: State):
    """Renderiza header com informações de status"""
    with me.box(
        style=me.Style(
            padding=me.Padding.all(16),
            background="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            color="white",
            box_shadow="0 2px 4px rgba(0,0,0,0.1)",
        )
    ):
        me.text(
            "🚀 Chat App - Claude Code SDK (v2.0 Melhorado)",
            style=me.Style(font_size=24, font_weight="bold")
        )
        
        # Status indicators
        with me.box(style=me.Style(display="flex", gap=16, margin=me.Margin(top=8))):
            me.text(
                f"✅ SDK: {'Ativo' if state.use_claude_sdk else 'Inativo'}",
                style=me.Style(font_size=12)
            )
            me.text(
                f"📊 Sessões: {len(chat_app.get_sessions_dict(state))}",
                style=me.Style(font_size=12)
            )
            if state.is_loading:
                me.text("⏳ Processando...", style=me.Style(font_size=12))


def render_sidebar(state: State):
    """Renderiza sidebar com sessões"""
    with me.box(
        style=me.Style(
            width=250,
            background="white",
            padding=me.Padding.all(16),
            border=me.Border(right=me.BorderSide(width=1, color="#e0e0e0")),
            overflow_y="auto",
        )
    ):
        me.button(
            "➕ Nova Conversa",
            on_click=lambda e: create_new_session(state),
            style=me.Style(width="100%", margin=me.Margin(bottom=16))
        )
        
        me.text("Sessões Recentes", style=me.Style(font_weight="bold", margin=me.Margin(bottom=8)))
        
        sessions = chat_app.get_sessions_dict(state)
        for session_id, session_data in sessions.items():
            render_session_item(state, session_id, session_data)


def render_session_item(state: State, session_id: str, session_data: Dict[str, Any]):
    """Renderiza item de sessão"""
    is_active = session_id == state.current_session_id
    
    with me.box(
        on_click=lambda e: load_session(state, session_id),
        style=me.Style(
            padding=me.Padding.all(8),
            background="#f0f0f0" if is_active else "transparent",
            border_radius=4,
            cursor="pointer",
            margin=me.Margin(bottom=4),
        )
    ):
        me.text(
            session_data.get("title", "Sem título"),
            style=me.Style(font_weight="bold" if is_active else "normal")
        )
        me.text(
            f"{len(session_data.get('messages', []))} mensagens",
            style=me.Style(font_size=12, color="#666")
        )


def render_chat_area(state: State):
    """Renderiza área principal do chat"""
    with me.box(
        style=me.Style(
            flex="1",
            display="flex",
            flex_direction="column",
            background="white",
        )
    ):
        # Messages area
        render_messages(state)
        
        # Input area
        render_input_area(state)


def render_messages(state: State):
    """Renderiza mensagens do chat"""
    with me.box(
        style=me.Style(
            flex="1",
            overflow_y="auto",
            padding=me.Padding.all(16),
        )
    ):
        messages = chat_app.get_messages_list(state)
        
        if not messages:
            me.text(
                "Inicie uma conversa digitando uma mensagem abaixo",
                style=me.Style(color="#999", text_align="center", margin=me.Margin(top=100))
            )
        else:
            for msg in messages:
                render_message(msg)


def render_message(message: Dict[str, Any]):
    """Renderiza uma mensagem individual"""
    is_user = message.get("role") == "user"
    
    with me.box(
        style=me.Style(
            display="flex",
            justify_content="flex-end" if is_user else "flex-start",
            margin=me.Margin(bottom=16),
        )
    ):
        with me.box(
            style=me.Style(
                max_width="70%",
                padding=me.Padding.all(12),
                background="#007bff" if is_user else "#f0f0f0",
                color="white" if is_user else "black",
                border_radius=8,
            )
        ):
            me.markdown(message.get("content", ""))
            
            # Timestamp
            if "timestamp" in message:
                me.text(
                    message["timestamp"],
                    style=me.Style(
                        font_size=10,
                        opacity=0.7,
                        margin=me.Margin(top=4)
                    )
                )


def render_input_area(state: State):
    """Renderiza área de input"""
    with me.box(
        style=me.Style(
            padding=me.Padding.all(16),
            border=me.Border(top=me.BorderSide(width=1, color="#e0e0e0")),
        )
    ):
        with me.box(style=me.Style(display="flex", gap=8)):
            me.input(
                label="Digite sua mensagem",
                value=state.input_text,
                on_blur=lambda e: setattr(state, "input_text", e.value),
                style=me.Style(flex="1"),
                disabled=state.is_loading,
            )
            
            me.button(
                "Enviar",
                on_click=lambda e: handle_send_message(state),
                disabled=state.is_loading or not state.input_text.strip(),
            )
            
            me.button(
                "📎",
                on_click=lambda e: trigger_file_upload(state),
                disabled=state.is_loading,
            )


def render_error_message(state: State):
    """Renderiza mensagem de erro"""
    with me.box(
        style=me.Style(
            position="fixed",
            bottom=20,
            right=20,
            background="#dc3545",
            color="white",
            padding=me.Padding.all(12),
            border_radius=4,
            box_shadow="0 2px 8px rgba(0,0,0,0.2)",
        )
    ):
        me.text(state.error_message)
        me.button(
            "✕",
            on_click=lambda e: setattr(state, "error_message", ""),
            style=me.Style(margin=me.Margin(left=8))
        )


def create_new_session(state: State):
    """Cria nova sessão"""
    session_id = str(uuid.uuid4())
    state.current_session_id = session_id
    state.current_session_title = "Nova Conversa"
    state.current_session_messages = "[]"
    
    # Salvar sessão
    sessions = chat_app.get_sessions_dict(state)
    sessions[session_id] = {
        "id": session_id,
        "title": "Nova Conversa",
        "messages": [],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    chat_app.set_sessions_dict(state, sessions)
    
    app_logger.info(f"New session created: {session_id}")


def load_session(state: State, session_id: str):
    """Carrega uma sessão existente"""
    sessions = chat_app.get_sessions_dict(state)
    
    if session_id in sessions:
        session = sessions[session_id]
        state.current_session_id = session_id
        state.current_session_title = session.get("title", "Sem título")
        state.current_session_messages = json.dumps(session.get("messages", []))
        
        app_logger.info(f"Session loaded: {session_id}")


def handle_send_message(state: State):
    """Handler para envio de mensagem"""
    if not state.input_text.strip():
        return
    
    # Criar sessão se não existir
    if not state.current_session_id:
        create_new_session(state)
    
    # Processar mensagem
    message = state.input_text
    state.input_text = ""
    state.is_loading = True
    state.error_message = ""
    
    # Processar de forma assíncrona
    asyncio.create_task(
        process_message_async(state, message)
    )


async def process_message_async(state: State, message: str):
    """Processa mensagem de forma assíncrona"""
    try:
        response = await chat_app.process_message(
            state,
            message,
            use_sdk=state.use_claude_sdk
        )
        
        # Atualizar título da sessão se for a primeira mensagem
        messages = chat_app.get_messages_list(state)
        if len(messages) <= 2:  # User + Assistant
            state.current_session_title = message[:50] + ("..." if len(message) > 50 else "")
            
            # Atualizar na lista de sessões
            sessions = chat_app.get_sessions_dict(state)
            if state.current_session_id in sessions:
                sessions[state.current_session_id]["title"] = state.current_session_title
                sessions[state.current_session_id]["updated_at"] = datetime.now().isoformat()
                chat_app.set_sessions_dict(state, sessions)
        
    except Exception as e:
        state.error_message = f"Erro ao processar mensagem: {str(e)}"
        app_logger.error(f"Message processing error: {e}")
    finally:
        state.is_loading = False


def trigger_file_upload(state: State):
    """Trigger para upload de arquivo"""
    # Esta função seria conectada a um input de arquivo real
    # Por enquanto, apenas demonstração
    state.error_message = "Upload de arquivo em desenvolvimento"


if __name__ == "__main__":
    app_logger.info("Starting Chat App server...")
    # O Mesop inicia automaticamente quando o arquivo é importado