#!/usr/bin/env python3
"""
Mesop-Chat: Servidor Unificado
Interface de Chat com Claude Code SDK + A2A Protocol
Versão completamente nova e simplificada

Autor: Claude Code Assistant
Data: 2024
"""

import os
import sys
import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from contextlib import asynccontextmanager
from dataclasses import dataclass, field, asdict

# ===== CONFIGURAÇÃO DO AMBIENTE =====
os.environ.setdefault('A2A_UI_PORT', '32123')
os.environ.setdefault('A2A_UI_HOST', '0.0.0.0')
os.environ.setdefault('MESOP_DISABLE_HOT_RELOAD', '1')

# ===== IMPORTS PRINCIPAIS =====
try:
    import mesop as me
    import mesop.labs as mel
    MESOP_AVAILABLE = True
except ImportError:
    print("⚠️ Mesop não instalado. Execute: pip install mesop")
    MESOP_AVAILABLE = False

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.wsgi import WSGIMiddleware
    from fastapi.responses import JSONResponse, FileResponse
    from fastapi.staticfiles import StaticFiles
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    print("⚠️ FastAPI/Uvicorn não instalado. Execute: pip install fastapi uvicorn")
    FASTAPI_AVAILABLE = False

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    print("⚠️ HTTPX não instalado. Execute: pip install httpx")
    HTTPX_AVAILABLE = False

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    print("ℹ️ Anthropic não instalado - funcionalidade Claude limitada")
    ANTHROPIC_AVAILABLE = False

try:
    from claude_code_sdk import query, ClaudeCodeOptions
    CLAUDE_SDK_AVAILABLE = True
except ImportError:
    print("ℹ️ Claude Code SDK não instalado - usando modo fallback")
    CLAUDE_SDK_AVAILABLE = False

# ===== DATACLASSES =====
@dataclass
class Message:
    """Mensagem do chat"""
    role: str  # 'user' ou 'assistant'
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

@dataclass
class ChatSession:
    """Sessão de chat"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "Nova Conversa"
    messages: List[Message] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_activity: str = field(default_factory=lambda: datetime.now().isoformat())
    model: str = "claude-3-5-sonnet-20241022"
    temperature: float = 0.7

# ===== ESTADO GLOBAL =====
@me.stateclass
class AppState:
    """Estado global da aplicação"""
    # Chat
    current_session: Any = field(default_factory=lambda: ChatSession())
    sessions: Dict[str, Any] = field(default_factory=dict)
    input_text: str = ""
    is_loading: bool = False
    error_message: str = ""
    
    # UI
    show_sidebar: bool = True
    theme_mode: str = "light"
    
    # A2A
    agent_name: str = "mesop-chat-agent"
    agent_version: str = "1.0.0"
    
    # Claude
    use_claude_sdk: bool = True
    api_key: str = ""

# ===== FUNÇÕES AUXILIARES =====
def create_new_session(title: str = "Nova Conversa") -> ChatSession:
    """Cria nova sessão de chat"""
    return ChatSession(
        id=str(uuid.uuid4()),
        title=title,
        messages=[],
        created_at=datetime.now().isoformat(),
        last_activity=datetime.now().isoformat()
    )

def ensure_session(obj: Any) -> ChatSession:
    """Garante que o objeto é uma ChatSession válida"""
    if isinstance(obj, ChatSession):
        return obj
    elif isinstance(obj, dict):
        # Converter dict para ChatSession
        session = ChatSession()
        for key, value in obj.items():
            if hasattr(session, key):
                setattr(session, key, value)
        return session
    else:
        return create_new_session()

# ===== FUNÇÕES CLAUDE =====
async def call_claude(prompt: str, state: AppState) -> str:
    """Chama Claude usando SDK ou API direta"""
    
    # Tentar Claude Code SDK primeiro
    if CLAUDE_SDK_AVAILABLE and state.use_claude_sdk:
        try:
            options = ClaudeCodeOptions(
                max_turns=3,
                system_prompt="Você é um assistente útil e amigável."
            )
            
            response = ""
            async for message in query(prompt=prompt, options=options):
                if hasattr(message, 'content'):
                    response += message.content
            
            return response if response else "Resposta vazia do Claude Code SDK"
            
        except Exception as e:
            print(f"Erro no Claude Code SDK: {e}")
            # Fallback para API direta
    
    # Tentar API Anthropic direta
    if ANTHROPIC_AVAILABLE and state.api_key:
        try:
            client = Anthropic(api_key=state.api_key)
            
            # Preparar mensagens
            messages = []
            if hasattr(state.current_session, 'messages'):
                for msg in state.current_session.messages[-10:]:  # Últimas 10 mensagens
                    messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
            
            # Adicionar prompt atual
            messages.append({"role": "user", "content": prompt})
            
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                messages=messages,
                temperature=0.7
            )
            
            return response.content[0].text
            
        except Exception as e:
            print(f"Erro na API Anthropic: {e}")
    
    # Fallback - resposta simulada
    return f"""Recebi sua mensagem: "{prompt}"

ℹ️ **Modo Demonstração** - Claude não está disponível.

Para ativar o Claude:
1. Instale: `pip install anthropic claude-code-sdk`
2. Configure: `claude auth login` ou defina ANTHROPIC_API_KEY
3. Reinicie o servidor

Este é o Mesop-Chat rodando em http://localhost:32123 🚀"""

# ===== PÁGINAS MESOP =====
@me.page(
    path="/",
    title="Mesop-Chat - Claude Code SDK",
    on_load=lambda e: initialize_app()
)
def main_page():
    """Página principal do chat"""
    state = me.state(AppState)
    
    with me.box(style=me.Style(
        display="flex",
        height="100vh",
        width="100%",
        background="#f5f5f5"
    )):
        # Sidebar
        if state.show_sidebar:
            render_sidebar()
        
        # Área principal
        with me.box(style=me.Style(
            flex=1,
            display="flex",
            flex_direction="column",
            background="#ffffff"
        )):
            render_header()
            render_messages()
            render_input()

def initialize_app():
    """Inicializa a aplicação"""
    state = me.state(AppState)
    
    # Criar sessão inicial se não existir
    if not state.sessions:
        session = create_new_session("Bem-vindo ao Mesop-Chat!")
        state.sessions[session.id] = session
        state.current_session = session
    
    # Garantir que current_session é válida
    state.current_session = ensure_session(state.current_session)

def render_sidebar():
    """Renderiza sidebar com sessões"""
    state = me.state(AppState)
    
    with me.box(style=me.Style(
        width=280,
        background="#fafafa",
        border=me.Border(right=me.BorderSide(width=1, color="#e0e0e0")),
        padding=me.Padding.all(16),
        overflow_y="auto"
    )):
        # Logo/Título
        me.text("🤖 Mesop-Chat", style=me.Style(
            font_size=20,
            font_weight="bold",
            margin=me.Margin(bottom=8)
        ))
        
        me.text("Claude Code SDK + A2A", style=me.Style(
            font_size=12,
            color="#666",
            margin=me.Margin(bottom=20)
        ))
        
        # Botão novo chat
        me.button(
            "➕ Novo Chat",
            on_click=handle_new_chat,
            style=me.Style(
                width="100%",
                background="#1976d2",
                color="#ffffff",
                padding=me.Padding.all(12),
                border_radius=8,
                margin=me.Margin(bottom=20)
            )
        )
        
        # Lista de sessões
        me.text("💬 Conversas", style=me.Style(
            font_weight="600",
            margin=me.Margin(bottom=12)
        ))
        
        for session_id, session in state.sessions.items():
            is_active = False
            if hasattr(state.current_session, 'id'):
                is_active = state.current_session.id == session_id
            
            with me.box(
                key=f"session_{session_id}",
                on_click=lambda sid=session_id: select_session(sid),
                style=me.Style(
                    padding=me.Padding.all(12),
                    margin=me.Margin(bottom=8),
                    background="#e3f2fd" if is_active else "transparent",
                    border_radius=8,
                    cursor="pointer"
                )
            ):
                title = session.title if hasattr(session, 'title') else "Conversa"
                me.text(title[:30] + "..." if len(title) > 30 else title)

def render_header():
    """Renderiza header"""
    state = me.state(AppState)
    
    with me.box(style=me.Style(
        padding=me.Padding.all(16),
        border=me.Border(bottom=me.BorderSide(width=1, color="#e0e0e0")),
        display="flex",
        align_items="center",
        justify_content="space-between"
    )):
        with me.box(style=me.Style(display="flex", align_items="center")):
            # Toggle sidebar
            me.button(
                "☰",
                on_click=toggle_sidebar,
                style=me.Style(
                    background="transparent",
                    font_size=24,
                    margin=me.Margin(right=16)
                )
            )
            
            # Título da sessão
            title = "Nova Conversa"
            if hasattr(state.current_session, 'title'):
                title = state.current_session.title
            
            me.text(title, style=me.Style(
                font_size=18,
                font_weight="600"
            ))
        
        # Status
        with me.box(style=me.Style(display="flex", align_items="center", gap=12)):
            # Indicador Claude
            if CLAUDE_SDK_AVAILABLE:
                me.text("🟢 Claude SDK", style=me.Style(
                    font_size=12,
                    color="#4caf50"
                ))
            elif ANTHROPIC_AVAILABLE:
                me.text("🟡 API Direta", style=me.Style(
                    font_size=12,
                    color="#ff9800"
                ))
            else:
                me.text("🔴 Demo Mode", style=me.Style(
                    font_size=12,
                    color="#f44336"
                ))
            
            # Porta
            me.text("📍 :32123", style=me.Style(
                font_size=12,
                color="#666"
            ))

def render_messages():
    """Renderiza área de mensagens"""
    state = me.state(AppState)
    
    with me.box(style=me.Style(
        flex=1,
        overflow_y="auto",
        padding=me.Padding.all(20),
        background="#ffffff"
    )):
        messages = []
        if hasattr(state.current_session, 'messages'):
            messages = state.current_session.messages
        
        if not messages:
            # Mensagem de boas-vindas
            with me.box(style=me.Style(
                text_align="center",
                padding=me.Padding.all(40),
                color="#666"
            )):
                me.text("👋 Olá! Eu sou o Mesop-Chat", style=me.Style(
                    font_size=24,
                    font_weight="600",
                    margin=me.Margin(bottom=16)
                ))
                
                me.text("Powered by Claude Code SDK + A2A Protocol", style=me.Style(
                    font_size=14,
                    margin=me.Margin(bottom=8)
                ))
                
                me.text("Digite uma mensagem para começar...", style=me.Style(
                    font_size=14,
                    color="#999"
                ))
        else:
            # Renderizar mensagens
            for msg in messages:
                render_message(msg)

def render_message(msg: Message):
    """Renderiza uma mensagem"""
    is_user = msg.role == "user"
    
    with me.box(style=me.Style(
        display="flex",
        justify_content="flex-end" if is_user else "flex-start",
        margin=me.Margin(bottom=16)
    )):
        with me.box(style=me.Style(
            max_width="70%",
            padding=me.Padding.all(12),
            background="#1976d2" if is_user else "#f5f5f5",
            color="#ffffff" if is_user else "#212121",
            border_radius=12
        )):
            # Avatar e nome
            with me.box(style=me.Style(
                display="flex",
                align_items="center",
                margin=me.Margin(bottom=8)
            )):
                me.text(
                    "👤 Você" if is_user else "🤖 Claude",
                    style=me.Style(
                        font_weight="600",
                        font_size=13
                    )
                )
            
            # Conteúdo
            me.markdown(msg.content)
            
            # Timestamp
            if hasattr(msg, 'timestamp'):
                try:
                    dt = datetime.fromisoformat(msg.timestamp)
                    time_str = dt.strftime("%H:%M")
                    me.text(time_str, style=me.Style(
                        font_size=11,
                        opacity=0.7,
                        margin=me.Margin(top=4)
                    ))
                except:
                    pass

def render_input():
    """Renderiza área de input"""
    state = me.state(AppState)
    
    with me.box(style=me.Style(
        padding=me.Padding.all(16),
        background="#ffffff",
        border=me.Border(top=me.BorderSide(width=1, color="#e0e0e0"))
    )):
        # Erro se houver
        if state.error_message:
            with me.box(style=me.Style(
                padding=me.Padding.all(12),
                background="#ffebee",
                color="#c62828",
                border_radius=8,
                margin=me.Margin(bottom=12)
            )):
                me.text(f"⚠️ {state.error_message}")
        
        # Input e botão
        with me.box(style=me.Style(display="flex", gap=12)):
            me.textarea(
                label="",
                value=state.input_text,
                placeholder="Digite sua mensagem...",
                on_input=handle_input,
                rows=2,
                style=me.Style(flex=1)
            )
            
            me.button(
                "Enviar" if not state.is_loading else "...",
                on_click=handle_send,
                disabled=state.is_loading or not state.input_text.strip(),
                type=me.ButtonType.RAISED,
                style=me.Style(
                    background="#1976d2" if not state.is_loading else "#ccc"
                )
            )

# ===== HANDLERS =====
def handle_input(e: me.InputEvent):
    """Handle input change"""
    state = me.state(AppState)
    state.input_text = e.value

def handle_send(e: me.ClickEvent):
    """Envia mensagem"""
    state = me.state(AppState)
    
    if not state.input_text.strip():
        return
    
    # Garantir sessão válida
    state.current_session = ensure_session(state.current_session)
    
    # Adicionar mensagem do usuário
    user_msg = Message(
        role="user",
        content=state.input_text.strip()
    )
    state.current_session.messages.append(user_msg)
    
    # Atualizar título se primeira mensagem
    if len(state.current_session.messages) == 1:
        state.current_session.title = state.input_text[:50]
        state.sessions[state.current_session.id] = state.current_session
    
    # Limpar input e marcar loading
    prompt = state.input_text
    state.input_text = ""
    state.is_loading = True
    state.error_message = ""
    
    # Yield para atualizar UI
    yield
    
    # Chamar Claude
    try:
        loop = asyncio.new_event_loop()
        response = loop.run_until_complete(call_claude(prompt, state))
        
        # Adicionar resposta
        assistant_msg = Message(
            role="assistant",
            content=response
        )
        state.current_session.messages.append(assistant_msg)
        
        # Atualizar última atividade
        state.current_session.last_activity = datetime.now().isoformat()
        
    except Exception as e:
        state.error_message = f"Erro: {str(e)}"
    finally:
        state.is_loading = False

def handle_new_chat(e: me.ClickEvent):
    """Cria novo chat"""
    state = me.state(AppState)
    
    session = create_new_session()
    state.sessions[session.id] = session
    state.current_session = session
    state.input_text = ""
    state.error_message = ""

def select_session(session_id: str):
    """Seleciona uma sessão"""
    state = me.state(AppState)
    
    if session_id in state.sessions:
        state.current_session = state.sessions[session_id]
        state.input_text = ""
        state.error_message = ""

def toggle_sidebar():
    """Toggle sidebar"""
    state = me.state(AppState)
    state.show_sidebar = not state.show_sidebar

# ===== FASTAPI + A2A =====
if FASTAPI_AVAILABLE:
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Gerencia ciclo de vida da aplicação"""
        print("\n" + "="*60)
        print("🚀 Mesop-Chat Server v1.0")
        print("="*60)
        
        # Status das dependências
        print("\n📦 Dependências:")
        print(f"  Mesop: {'✅' if MESOP_AVAILABLE else '❌'}")
        print(f"  FastAPI: {'✅' if FASTAPI_AVAILABLE else '❌'}")
        print(f"  Claude SDK: {'✅' if CLAUDE_SDK_AVAILABLE else '❌'}")
        print(f"  Anthropic: {'✅' if ANTHROPIC_AVAILABLE else '❌'}")
        
        # Configurações
        host = os.environ.get('A2A_UI_HOST', '0.0.0.0')
        port = int(os.environ.get('A2A_UI_PORT', '32123'))
        
        print(f"\n🌐 Servidor:")
        print(f"  URL: http://localhost:{port}")
        print(f"  Host: {host}")
        print(f"  A2A: /.well-known/agent.json")
        
        # Montar Mesop
        if MESOP_AVAILABLE:
            mesop_app = me.create_wsgi_app(debug_mode=False)
            app.mount('/', WSGIMiddleware(mesop_app))
            print("\n✅ Interface Mesop montada")
        
        print("\n" + "="*60)
        print("✨ Servidor pronto! Acesse http://localhost:32123")
        print("="*60 + "\n")
        
        yield
        
        print("\n👋 Encerrando servidor...")
    
    # Criar app FastAPI
    app = FastAPI(
        title="Mesop-Chat",
        description="Claude Code SDK + A2A Protocol",
        version="1.0.0",
        lifespan=lifespan
    )
    
    @app.get("/health")
    async def health():
        """Health check"""
        return JSONResponse({
            "status": "healthy",
            "service": "mesop-chat",
            "version": "1.0.0",
            "port": int(os.environ.get('A2A_UI_PORT', '32123')),
            "features": {
                "mesop": MESOP_AVAILABLE,
                "claude_sdk": CLAUDE_SDK_AVAILABLE,
                "anthropic": ANTHROPIC_AVAILABLE,
                "a2a": True
            }
        })
    
    @app.get("/.well-known/agent.json")
    async def agent_json():
        """A2A Protocol Discovery"""
        agent_file = Path(__file__).parent / ".well-known" / "agent.json"
        
        if agent_file.exists():
            return FileResponse(agent_file, media_type="application/json")
        
        # Retornar agent card padrão
        return JSONResponse({
            "name": "mesop-chat-agent",
            "version": "1.0.0",
            "description": "Claude Code SDK Chat with A2A Protocol",
            "capabilities": [
                "chat",
                "code-generation",
                "multi-turn-conversation",
                "streaming"
            ],
            "endpoint": f"http://localhost:{os.environ.get('A2A_UI_PORT', '32123')}",
            "protocols": ["a2a/1.0", "claude-code-sdk/0.0.20"],
            "status": "active"
        })

# ===== MAIN =====
def main():
    """Função principal"""
    
    # Verificar dependências mínimas
    if not MESOP_AVAILABLE:
        print("\n❌ Mesop é necessário!")
        print("Execute: pip install mesop")
        sys.exit(1)
    
    # Escolher modo de execução
    if FASTAPI_AVAILABLE:
        # Modo completo com FastAPI
        host = os.environ.get('A2A_UI_HOST', '0.0.0.0')
        port = int(os.environ.get('A2A_UI_PORT', '32123'))
        
        print(f"\n🚀 Iniciando servidor completo (FastAPI + Mesop)...")
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info"
        )
    else:
        # Modo simples só com Mesop
        print("\n🚀 Iniciando servidor simples (apenas Mesop)...")
        print("ℹ️  Para funcionalidade completa, instale: pip install fastapi uvicorn")
        
        # Executar Mesop diretamente
        import subprocess
        subprocess.run(["mesop", __file__, "--port", "32123"])

if __name__ == "__main__":
    main()