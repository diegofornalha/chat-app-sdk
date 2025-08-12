"""
Chat App com Claude Code SDK usando Mesop - Versão Simplificada
Backend Python com integração completa ao Claude Code
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

# Inicializar cliente Anthropic (para uso direto da API se necessário)
anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

@me.stateclass
class State:
    """Estado da aplicação Mesop - APENAS tipos primitivos"""
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

def get_messages_list(state: State) -> List[Dict[str, Any]]:
    """Converte string JSON de mensagens para lista"""
    try:
        return json.loads(state.current_session_messages)
    except:
        return []

def set_messages_list(state: State, messages: List[Dict[str, Any]]):
    """Converte lista de mensagens para string JSON"""
    state.current_session_messages = json.dumps(messages)

def get_sessions_dict(state: State) -> Dict[str, Dict[str, Any]]:
    """Converte string JSON de sessões para dicionário"""
    try:
        return json.loads(state.sessions)
    except:
        return {}

def set_sessions_dict(state: State, sessions: Dict[str, Dict[str, Any]]):
    """Converte dicionário de sessões para string JSON"""
    state.sessions = json.dumps(sessions)

def get_processing_steps(state: State) -> List[Dict[str, Any]]:
    """Converte string JSON de passos para lista"""
    try:
        return json.loads(state.processing_steps)
    except:
        return []

def set_processing_steps(state: State, steps: List[Dict[str, Any]]):
    """Converte lista de passos para string JSON"""
    state.processing_steps = json.dumps(steps)

async def call_claude_code_sdk(prompt: str, session_id: Optional[str] = None) -> tuple[str, Dict[str, Any]]:
    """
    Chama o Claude Code SDK usando autenticação do CLI (igual ao backend Node.js)
    Não requer ANTHROPIC_API_KEY - usa 'claude auth login' configurado globalmente
    """
    try:
        
        # Configurar opções conforme documentação
        options = ClaudeCodeOptions(
            max_turns=3,
            system_prompt=None,
        )
        
        response_text = ""
        metadata = {}
        messages = []
        
        # Executar query assíncrona conforme documentação oficial
        async for message in query(prompt=prompt, options=options):
            messages.append(message)
            
            # Processar mensagens - verificar se é dicionário ou objeto
            if hasattr(message, '__dict__'):
                # É um objeto, usar dot notation
                # Verificar se é um ResultMessage pelo subtype
                if hasattr(message, 'subtype') and getattr(message, 'subtype', '') == 'success':
                    # É um ResultMessage de sucesso
                    response_text = getattr(message, 'result', '')
                    
                    # Extrair dados de uso se disponível
                    usage_data = getattr(message, 'usage', {})
                    if isinstance(usage_data, dict):
                        input_tokens = usage_data.get('input_tokens', 0)
                        output_tokens = usage_data.get('output_tokens', 0)
                    else:
                        input_tokens = 0
                        output_tokens = 0
                    
                    metadata = {
                        "cost_usd": getattr(message, 'total_cost_usd', 0),
                        "duration_ms": getattr(message, 'duration_ms', 0),
                        "num_turns": getattr(message, 'num_turns', 0),
                        "session_id": getattr(message, 'session_id', None),
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens
                    }
                elif hasattr(message, 'type') and message.type == "result":
                    if not getattr(message, 'is_error', False):
                        response_text = getattr(message, 'result', '')
                        metadata = {
                            "cost_usd": getattr(message, 'total_cost_usd', 0),
                            "duration_ms": getattr(message, 'duration_ms', 0),
                            "num_turns": getattr(message, 'num_turns', 0),
                            "session_id": getattr(message, 'session_id', None),
                            "input_tokens": getattr(message, 'input_tokens', 0),
                            "output_tokens": getattr(message, 'output_tokens', 0)
                        }
                    else:
                        response_text = f"Erro: {getattr(message, 'error', 'Erro desconhecido')}"
                        metadata["is_error"] = True
            elif isinstance(message, dict):
                # É um dicionário, usar chaves
                if message.get("type") == "result":
                    if not message.get("is_error", False):
                        response_text = message.get("result", "")
                        metadata = {
                            "cost_usd": message.get("total_cost_usd", 0),
                            "duration_ms": message.get("duration_ms", 0),
                            "num_turns": message.get("num_turns", 0),
                            "session_id": message.get("session_id"),
                            "input_tokens": message.get("input_tokens", 0),
                            "output_tokens": message.get("output_tokens", 0)
                        }
                    else:
                        response_text = f"Erro: {message.get('error', 'Erro desconhecido')}"
                        metadata["is_error"] = True
                
        # Se não temos resposta, usar a última mensagem válida ou fornecer resposta padrão
        if not response_text:
            if messages:
                last_message = messages[-1]
                if isinstance(last_message, dict):
                    response_text = str(last_message)
                else:
                    response_text = str(last_message)
            else:
                response_text = "⚠️ Nenhuma resposta recebida do Claude Code SDK. Verifique a configuração da API."
                
        return response_text, metadata
        
    except Exception as e:
        error_msg = str(e)
        
        # Dar mensagens mais específicas para erros comuns
        if "exit code 1" in error_msg:
            return ("❌ **Claude Code não está autenticado OU seu limite acabou**\n\n" +
                   "O Claude Code CLI precisa estar autenticado para funcionar ou você atingiu seu limite de uso.\n\n" +
                   "**Como resolver:**\n" +
                   "1. Execute no terminal: `claude auth login`\n" +
                   "2. Siga as instruções para fazer login\n" +
                   "3. Reinicie o servidor\n" +
                   "4. Se já está autenticado, aguarde o reset do limite mensal\n\n" +
                   "**Alternativa:** Use o modo 'API Direta' no toggle do header"), {"is_error": True, "needs_setup": True}
        elif "CLINotFoundError" in error_msg or "command not found" in error_msg:
            return ("❌ **Claude Code CLI não encontrado**\n\n" +
                   "O Claude Code CLI não está instalado ou não está no PATH.\n\n" +
                   "**Como instalar:**\n" +
                   "1. Execute: `npm install -g @anthropic-ai/claude-code`\n" +
                   "2. Ou baixe em: https://claude.ai/download\n" +
                   "3. Execute: `claude auth login`\n\n" +
                   "**Alternativa:** Use o modo 'API Direta' no toggle do header"), {"is_error": True, "needs_setup": True}
        elif "Command failed" in error_msg:
            return ("❌ **Comando falhou**\n\n" +
                   f"Erro: {error_msg}\n\n" +
                   "Tente usar o modo 'API Direta' como alternativa."), {"is_error": True}
        else:
            return f"Erro ao chamar Claude Code SDK: {error_msg}", {"is_error": True}

def call_anthropic_api(prompt: str, messages: List[Dict[str, Any]]) -> tuple[str, Dict[str, Any]]:
    """
    Chama a API Anthropic diretamente
    """
    try:
        # Converter mensagens para formato da API
        api_messages = []
        for msg in messages:
            if msg.get('content'):  # Ignorar mensagens vazias
                api_messages.append({
                    "role": msg.get('role', 'user'),
                    "content": msg.get('content', '')
                })
        
        # Adicionar prompt atual
        api_messages.append({
            "role": "user",
            "content": prompt
        })
        
        # Fazer chamada à API
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            messages=api_messages
        )
        
        # Calcular tokens aproximados
        input_tokens = sum(len(msg["content"].split()) * 1.3 for msg in api_messages)
        output_tokens = len(response.content[0].text.split()) * 1.3
        
        metadata = {
            "model": "claude-3-5-sonnet",
            "input_tokens": int(input_tokens),
            "output_tokens": int(output_tokens),
            "cost_usd": (input_tokens * 0.003 + output_tokens * 0.015) / 1000
        }
        
        return response.content[0].text, metadata
        
    except Exception as e:
        return f"Erro ao chamar API Anthropic: {str(e)}", {"is_error": True}

@me.page(
    path="/",
    title="Chat com Claude Code",
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap",
        "https://fonts.googleapis.com/icon?family=Material+Icons"
    ]
)
def main_page():
    state = me.state(State)
    
    with me.box(
        style=me.Style(
            display="flex",
            height="100vh",
            width="100%",
            background="linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 100%)",
            font_family="'Inter', sans-serif"
        )
    ):
        # Sidebar
        if state.show_sidebar:
            render_sidebar(state)
        
        # Área principal do chat
        with me.box(
            style=me.Style(
                flex=1,
                display="flex",
                flex_direction="column",
                height="100%"
            )
        ):
            # Header
            render_header(state)
            
            # Área de mensagens
            with me.box(
                style=me.Style(
                    flex=1,
                    overflow_y="auto",
                    padding=me.Padding.all(20),
                    display="flex",
                    flex_direction="column",
                    gap=15
                )
            ):
                # Passos de processamento
                steps = get_processing_steps(state)
                if steps and state.is_loading:
                    render_processing_steps(steps)
                
                # Mensagens do chat
                messages = get_messages_list(state)
                for message in messages:
                    render_message(message)
                
                # Indicador de carregamento
                if state.is_loading:
                    render_loading_indicator()
                
                # Mensagem de erro
                if state.error_message:
                    render_error(state.error_message)
            
            # Área de input
            render_input_area(state)

def render_sidebar(state: State):
    """Renderiza a sidebar com sessões"""
    with me.box( 
        style=me.Style( 
            width=280, 
            background="rgba(30, 30, 30, 0.95)", 
            border=me.Border(right=me.BorderSide(width=1, color="rgba(255, 255, 255, 0.1)")), 
            padding=me.Padding.all(20),
            display="flex",
            flex_direction="column",
            gap=20
        )
    ):
        # Botão novo chat
        with me.box(
            style=me.Style(
                padding=me.Padding.all(12),
                background="linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)",
                border_radius=8,
                cursor="pointer",
                text_align="center"
            ),
            on_click=handle_new_chat
        ):
            me.text(
                "✨ Novo Chat",
                style=me.Style(
                    color="white",
                    font_weight=600
                )
            )
        
        # Lista de sessões
        me.text(
            "CONVERSAS RECENTES",
            style=me.Style(
                color="rgba(255, 255, 255, 0.6)",
                font_size=12,
                letter_spacing="0.05em"
            )
        )
        
        with me.box(
            style=me.Style(
                flex=1,
                overflow_y="auto",
                display="flex",
                flex_direction="column",
                gap=8
            )
        ):
            sessions = get_sessions_dict(state)
            if sessions:
                for session_id, session in sessions.items():
                    render_session_item(session, session_id == state.current_session_id, session_id)
            else:
                me.text(
                    "Nenhuma conversa ainda",
                    style=me.Style(
                        color="rgba(255, 255, 255, 0.4)",
                        font_size=13,
                        text_align="center",
                        margin=me.Margin(top=20)
                    )
                )

def render_session_item(session: Dict[str, Any], is_active: bool, session_id: str):
    """Renderiza um item de sessão na sidebar"""
    
    title = session.get('title', 'Nova Conversa')
    messages_count = len(session.get('messages', []))
    last_activity = session.get('last_activity', '')
    
    # Formatar timestamp
    if last_activity:
        try:
            dt = datetime.fromisoformat(last_activity)
            last_activity = dt.strftime('%H:%M')
        except:
            last_activity = "00:00"
    else:
        last_activity = "00:00"
    
    with me.box(
        key=session_id,
        style=me.Style(
            padding=me.Padding.all(12),
            background="rgba(255, 255, 255, 0.05)" if is_active else "transparent",
            border_radius=6,
            cursor="pointer",
            border=me.Border.all(me.BorderSide(width=1, color="rgba(255, 255, 255, 0.1)")) if is_active else None
        ),
        on_click=lambda e: load_session(e, session_id)
    ):
        me.text(
            title[:30] + "..." if len(title) > 30 else title,
            style=me.Style(
                color="white" if is_active else "rgba(255, 255, 255, 0.7)",
                font_size=14
            )
        )
        me.text(
            f"{messages_count} mensagens • {last_activity}",
            style=me.Style(
                color="rgba(255, 255, 255, 0.4)",
                font_size=12
            )
        )

def render_header(state: State):
    """Renderiza o header"""
    with me.box(
        style=me.Style(
            padding=me.Padding.all(20),
            border=me.Border(bottom=me.BorderSide(width=1, color="rgba(255, 255, 255, 0.1)")),
            display="flex",
            align_items="center",
            gap=20
        )
    ):
        # Botão menu
        with me.box(
            style=me.Style(
                cursor="pointer",
                padding=me.Padding.all(8)
            ),
            on_click=toggle_sidebar
        ):
            me.icon(
                "menu" if not state.show_sidebar else "menu_open",
                style=me.Style(
                    color="white",
                    font_size=24
                )
            )
        
        # Título
        me.text(
            "Chat com Claude Code",
            style=me.Style(
                color="white",
                font_size=20,
                font_weight=600,
                flex=1
            )
        )
        
        # Toggle de modo
        with me.box(
            style=me.Style(
                display="flex",
                align_items="center",
                gap=10
            )
        ):
            me.text(
                "Modo:",
                style=me.Style(
                    color="rgba(255, 255, 255, 0.6)",
                    font_size=14
                )
            )
            
            mode_text = "Claude Code CLI" if state.use_claude_sdk else "API Direta"
            with me.box(
                style=me.Style(
                    padding=me.Padding(left=12, right=12, top=6, bottom=6),
                    background="rgba(79, 70, 229, 0.2)",
                    border=me.Border.all(me.BorderSide(width=1, color="rgba(79, 70, 229, 0.5)")),
                    border_radius=20,
                    cursor="pointer"
                ),
                on_click=toggle_mode
            ):
                me.text(
                    mode_text,
                    style=me.Style(
                        color="#a78bfa",
                        font_size=13,
                        font_weight=500
                    )
                )

def render_message(message: Dict[str, Any]):
    """Renderiza uma mensagem do chat"""
    is_user = message.get('role', 'user') == "user"
    
    with me.box(
        style=me.Style(
            display="flex",
            gap=12,
            align_items="flex-start",
            margin=me.Margin(bottom=15)
        )
    ):
        # Avatar
        with me.box(
                            style=me.Style(
                    width=36,
                    height=36,
                    border_radius="50%",
                    background="linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)" if is_user 
                              else "linear-gradient(135deg, #f97316 0%, #f59e0b 100%)",
                    display="flex",
                    align_items="center",
                    justify_content="center"
                )
        ):
            me.icon(
                "person" if is_user else "smart_toy",
                style=me.Style(
                    color="white",
                    font_size=20
                )
            )
        
        # Conteúdo da mensagem
        with me.box(
            style=me.Style(
                flex=1,
                display="flex",
                flex_direction="column",
                gap=8
            )
        ):
            # Role e timestamp
            with me.box(
                style=me.Style(
                    display="flex",
                    align_items="center",
                    gap=10
                )
            ):
                me.text(
                    "Você" if is_user else "Claude",
                    style=me.Style(
                        color="white",
                        font_weight=600,
                        font_size=14
                    )
                )
                
                # Converter timestamp string para datetime se necessário
                timestamp_str = message.get('timestamp', '')
                if timestamp_str:
                    try:
                        dt = datetime.fromisoformat(timestamp_str)
                        timestamp_str = dt.strftime("%H:%M")
                    except:
                        timestamp_str = "00:00"
                else:
                    timestamp_str = "00:00"
                    
                me.text(
                    timestamp_str,
                    style=me.Style(
                        color="rgba(255, 255, 255, 0.4)",
                        font_size=12
                    )
                )
                
                # Indicador de progresso
                if message.get('in_progress', False):
                    me.progress_spinner(
                        size=16,
                        color="primary"
                    )
            
            # Texto da mensagem
            with me.box(
                style=me.Style(
                    padding=me.Padding.all(12),
                    background="rgba(255, 255, 255, 0.05)",
                    border_radius=8,
                    border=me.Border.all(me.BorderSide(width=1, color="rgba(255, 255, 255, 0.1)"))
                )
            ):
                content = message.get('content', '')
                if content:
                    me.markdown(
                        content,
                        style=me.Style(
                            color="rgba(255, 255, 255, 0.9)",
                            font_size=14,
                            line_height="1.6"
                        )
                    )
                elif message.get('in_progress', False):
                    me.text(
                        "Digitando...",
                        style=me.Style(
                            color="rgba(255, 255, 255, 0.5)",
                            font_size=14,
                            font_style="italic"
                        )
                    )
            
            # Metadados
            metadata = message.get('metadata', {})
            if metadata and not message.get('in_progress', False):
                render_message_metadata(metadata)

def render_message_metadata(metadata: Dict[str, Any]):
    """Renderiza metadados da mensagem"""
    with me.box(
        style=me.Style(
            display="flex",
            gap=15,
            margin=me.Margin(top=8),
            flex_wrap="wrap"
        )
    ):
        # Mostrar tokens se disponível
        if "input_tokens" in metadata and metadata["input_tokens"]:
            me.text(
                f"📥 {metadata['input_tokens']} tokens",
                style=me.Style(
                    color="rgba(255, 255, 255, 0.5)",
                    font_size=12
                )
            )
        
        if "output_tokens" in metadata and metadata["output_tokens"]:
            me.text(
                f"📤 {metadata['output_tokens']} tokens",
                style=me.Style(
                    color="rgba(255, 255, 255, 0.5)",
                    font_size=12
                )
            )
        
        # Mostrar custo apenas se não tiver info de tokens
        if "cost_usd" in metadata and metadata["cost_usd"] and not metadata.get("input_tokens"):
            me.text(
                f"💰 ${metadata['cost_usd']:.4f}",
                style=me.Style(
                    color="rgba(255, 255, 255, 0.5)",
                    font_size=12
                )
            )
        
        if "duration_ms" in metadata and metadata["duration_ms"]:
            duration_seconds = metadata['duration_ms'] / 1000
            me.text(
                f"⏱️ {duration_seconds:.1f}s",
                style=me.Style(
                    color="rgba(255, 255, 255, 0.5)",
                    font_size=12
                )
            )
        
        if "num_turns" in metadata and metadata["num_turns"]:
            me.text(
                f"🔄 {metadata['num_turns']} turno{'s' if metadata['num_turns'] > 1 else ''}",
                style=me.Style(
                    color="rgba(255, 255, 255, 0.5)",
                    font_size=12
                )
            )
            
        if "tools_used" in metadata:
            tools = ", ".join(metadata["tools_used"][:3])
            if len(metadata["tools_used"]) > 3:
                tools += f" +{len(metadata['tools_used']) - 3}"
            me.text(
                f"🔧 {tools}",
                style=me.Style(
                    color="rgba(255, 255, 255, 0.5)",
                    font_size=12
                )
            )

def render_processing_steps(steps: List[Dict[str, Any]]):
    """Renderiza passos de processamento"""
    with me.box(
        style=me.Style(
            padding=me.Padding.all(12),
            background="rgba(79, 70, 229, 0.1)",
            border=me.Border.all(me.BorderSide(width=1, color="rgba(79, 70, 229, 0.3)")),
            border_radius=8,
            margin=me.Margin(bottom=20)
        )
    ):
        me.text(
            "Processando...",
            style=me.Style(
                color="rgba(167, 139, 250, 1)",
                font_weight=600,
                font_size=14,
                margin=me.Margin(bottom=10)
            )
        )
        
        for step in steps[-5:]:  # Mostrar últimos 5 passos
            with me.box(
                style=me.Style(
                    display="flex",
                    align_items="center",
                    gap=8,
                    margin=me.Margin(bottom=6)
                )
            ):
                me.text(
                    "→",
                    style=me.Style(
                        color="rgba(167, 139, 250, 0.6)",
                        font_size=12
                    )
                )
                me.text(
                    step.get('message', ''),
                    style=me.Style(
                        color="rgba(255, 255, 255, 0.7)",
                        font_size=13
                    )
                )

def render_loading_indicator():
    """Renderiza indicador de carregamento"""
    with me.box(
        style=me.Style(
            display="flex",
            align_items="center",
            gap=10,
            padding=me.Padding.all(12)
        )
    ):
        me.progress_spinner(
            color="primary"
        )
        me.text(
            "Claude está pensando...",
            style=me.Style(
                color="rgba(255, 255, 255, 0.6)",
                font_size=14
            )
        )

def render_error(error_message: str):
    """Renderiza mensagem de erro"""
    with me.box(
        style=me.Style(
            padding=me.Padding.all(12),
            background="rgba(239, 68, 68, 0.1)",
            border=me.Border.all(me.BorderSide(width=1, color="rgba(239, 68, 68, 0.3)")),
            border_radius=8
        )
    ):
        me.text(
            f"❌ {error_message}",
            style=me.Style(
                color="#f87171",
                font_size=14
            )
        )

def render_input_area(state: State):
    """Renderiza área de input"""
    with me.box(
        style=me.Style(
            padding=me.Padding.all(20),
            border=me.Border(top=me.BorderSide(width=1, color="rgba(255, 255, 255, 0.1)")),
            display="flex",
            gap=12,
            align_items="flex-end"
        )
    ):
        # Upload de arquivo
        with me.box(
            style=me.Style(
                display="flex",
                align_items="center"
            )
        ):
            me.uploader(
                label="📎",
                on_upload=handle_file_upload,
                type="flat",
                color="primary",
                style=me.Style(
                    background="transparent",
                    color="rgba(255, 255, 255, 0.6)"
                )
            )
        
        # Input de texto
        with me.box(style=me.Style(flex=1)):
            me.textarea(
                label="",
                placeholder="Digite sua mensagem aqui... (Shift+Enter para nova linha)",
                value=state.input_text,
                on_input=update_input,
                rows=1,
                max_rows=5,
                style=me.Style(
                    width="100%",
                    background="rgba(255, 255, 255, 0.05)",
                    border=me.Border.all(me.BorderSide(width=1, color="rgba(255, 255, 255, 0.2)")),
                    border_radius=8,
                    padding=me.Padding.all(12),
                    color="white",
                    font_size=14
                )
            )
        
        # Botão enviar
        with me.content_button(
            type="icon",
            on_click=handle_send_message,
            disabled=state.is_loading or not state.input_text.strip(),
            style=me.Style(
                opacity=0.5 if (state.is_loading or not state.input_text.strip()) else 1
            )
        ):
            me.icon(
                "send",
                style=me.Style(
                    color="white" if not state.is_loading else "rgba(255, 255, 255, 0.5)"
                )
            )

# Handlers de eventos
def toggle_sidebar(e: me.ClickEvent):
    """Toggle visibilidade da sidebar"""
    state = me.state(State)
    state.show_sidebar = not state.show_sidebar

def toggle_mode(e: me.ClickEvent):
    """Toggle entre Claude Code CLI e API Direta"""
    state = me.state(State)
    state.use_claude_sdk = not state.use_claude_sdk

def handle_new_chat(e: me.ClickEvent):
    """Criar nova sessão de chat"""
    state = me.state(State)
    
    # Criar nova sessão como dicionário simples
    new_session_id = str(uuid.uuid4())
    new_session = {
        'id': new_session_id,
        'title': 'Nova Conversa',
        'messages': [],
        'created_at': datetime.now().isoformat(),
        'last_activity': datetime.now().isoformat()
    }
    
    # Salvar sessão
    sessions = get_sessions_dict(state)
    sessions[new_session_id] = new_session
    set_sessions_dict(state, sessions)
    
    # Definir como sessão atual
    state.current_session_id = new_session_id
    state.current_session_title = 'Nova Conversa'
    set_messages_list(state, [])
    
    # Limpar estados
    set_processing_steps(state, [])
    state.error_message = ""
    state.input_text = ""

def load_session(e: me.ClickEvent, session_id: str):
    """Carregar uma sessão existente"""
    state = me.state(State)
    sessions = get_sessions_dict(state)
    
    if session_id in sessions:
        session = sessions[session_id]
        state.current_session_id = session_id
        state.current_session_title = session.get('title', 'Nova Conversa')
        set_messages_list(state, session.get('messages', []))
        state.error_message = ""
        set_processing_steps(state, [])

def update_input(e: me.InputEvent):
    """Atualizar texto de input"""
    state = me.state(State)
    state.input_text = e.value

def handle_file_upload(e: me.UploadEvent):
    """Lidar com upload de arquivo"""
    state = me.state(State)
    try:
        file_content = e.file.read()
        
        # Tentar decodificar como texto
        try:
            text_content = file_content.decode('utf-8')
            state.uploaded_file_content = text_content
            state.uploaded_file_name = e.file.name
            
            # Adicionar ao input
            state.input_text += f"\n\nArquivo: {e.file.name}\n```\n{text_content[:1000]}\n```"
            if len(text_content) > 1000:
                state.input_text += f"\n... (truncado, {len(text_content)} caracteres totais)"
        except UnicodeDecodeError:
            # Se não for texto, converter para base64
            b64_content = base64.b64encode(file_content).decode('utf-8')
            state.input_text += f"\n\nArquivo binário: {e.file.name} (base64)"
            
    except Exception as error:
        state.error_message = f"Erro ao fazer upload do arquivo: {str(error)}"

def handle_send_message(e: me.ClickEvent):
    """Lidar com envio de mensagem"""
    state = me.state(State)
    
    if not state.input_text.strip() or state.is_loading:
        return
    
    # Se não há sessão atual, criar uma
    if not state.current_session_id:
        new_session_id = str(uuid.uuid4())
        state.current_session_id = new_session_id
        state.current_session_title = 'Nova Conversa'
        set_messages_list(state, [])
        
        sessions = get_sessions_dict(state)
        sessions[new_session_id] = {
            'id': new_session_id,
            'title': 'Nova Conversa',
            'messages': [],
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat()
        }
        set_sessions_dict(state, sessions)
    
    # Limpar erro
    state.error_message = ""
    
    # Adicionar mensagem do usuário como dicionário
    messages = get_messages_list(state)
    user_message = {
        'id': str(uuid.uuid4()),
        'role': 'user',
        'content': state.input_text,
        'timestamp': datetime.now().isoformat(),
        'metadata': {},
        'in_progress': False
    }
    messages.append(user_message)
    
    # Guardar prompt e limpar input
    prompt = state.input_text
    state.input_text = ""
    
    # Definir carregando
    state.is_loading = True
    set_processing_steps(state, [])
    
    # Adicionar mensagem vazia do assistente para mostrar progresso
    assistant_message = {
        'id': str(uuid.uuid4()),
        'role': 'assistant',
        'content': '',
        'timestamp': datetime.now().isoformat(),
        'metadata': {},
        'in_progress': True
    }
    messages.append(assistant_message)
    set_messages_list(state, messages)
    
    # Processar mensagem de forma assíncrona
    for _ in process_message_async(state, prompt, assistant_message):
        pass

def process_message_async(state: State, prompt: str, assistant_message: Dict[str, Any]):
    """Processar mensagem de forma assíncrona"""
    try:
        # Adicionar passo de processamento como dicionário
        steps = get_processing_steps(state)
        steps.append({
            'type': 'inicio',
            'message': 'Iniciando processamento...',
            'timestamp': datetime.now().isoformat()
        })
        set_processing_steps(state, steps)
        
        if state.use_claude_sdk:
            # Usar Claude Code SDK
            steps = get_processing_steps(state)
            steps.append({
                'type': 'sdk',
                'message': 'Chamando Claude Code SDK...',
                'timestamp': datetime.now().isoformat()
            })
            set_processing_steps(state, steps)
            
            # Executar de forma assíncrona
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Pegar session_id se existir
            session_id = None
            sessions = get_sessions_dict(state)
            if state.current_session_id in sessions:
                session_id = sessions[state.current_session_id].get('claude_session_id')
            
            response_text, metadata = loop.run_until_complete(
                call_claude_code_sdk(prompt, session_id)
            )
            
            # Atualizar session_id se fornecido
            if metadata.get("session_id") and state.current_session_id in sessions:
                sessions[state.current_session_id]['claude_session_id'] = metadata["session_id"]
                set_sessions_dict(state, sessions)
                
        else:
            # Usar API Anthropic
            steps = get_processing_steps(state)
            steps.append({
                'type': 'api',
                'message': 'Chamando API Anthropic...',
                'timestamp': datetime.now().isoformat()
            })
            set_processing_steps(state, steps)
            
            # Converter mensagens para formato da API
            messages = get_messages_list(state)
            messages_for_api = messages[:-2] if len(messages) > 2 else []
            
            response_text, metadata = call_anthropic_api(
                prompt, 
                messages_for_api
            )
        
        # Atualizar mensagem do assistente
        messages = get_messages_list(state)
        if messages and messages[-1]['id'] == assistant_message['id']:
            messages[-1]['content'] = response_text
            messages[-1]['metadata'] = metadata
            messages[-1]['in_progress'] = False
            set_messages_list(state, messages)
        
        # Atualizar sessão
        sessions = get_sessions_dict(state)
        if state.current_session_id in sessions:
            sessions[state.current_session_id]['last_activity'] = datetime.now().isoformat()
            sessions[state.current_session_id]['messages'] = messages
            
            # Atualizar título se for primeira mensagem
            if state.current_session_title == "Nova Conversa" and len(prompt) > 0:
                new_title = prompt[:50] + "..." if len(prompt) > 50 else prompt
                state.current_session_title = new_title
                sessions[state.current_session_id]['title'] = new_title
            
            set_sessions_dict(state, sessions)
        
    except Exception as error:
        state.error_message = f"Erro: {str(error)}"
        # Remover mensagem vazia do assistente em caso de erro
        messages = get_messages_list(state)
        if messages and messages[-1].get('in_progress', False):
            messages.pop()
            set_messages_list(state, messages)
    finally:
        state.is_loading = False
        set_processing_steps(state, [])
        
    yield

# Mesop executa automaticamente quando o arquivo é importado
# Não precisa de if __name__ == "__main__"