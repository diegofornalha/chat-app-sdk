#!/usr/bin/env python3
"""
Chat App com Claude Code SDK usando Mesop - Versão Simplificada
"""
import os
import sys
import uuid
import json
import base64
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict, is_dataclass

import mesop as me
import mesop.labs as mel
from anthropic import Anthropic
from claude_code_sdk import query, ClaudeCodeOptions

# Cliente Anthropic
anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

@dataclass
class Message:
    """Representa uma mensagem do chat"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    role: str = "user"
    content: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_streaming: bool = False
    in_progress: bool = False

@dataclass  
class ChatSession:
    """Gerencia uma sessão de chat"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[Message] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_activity: str = field(default_factory=lambda: datetime.now().isoformat())
    title: str = "Nova Conversa"
    context: str = ""
    claude_session_id: Optional[str] = None

@dataclass
class ProcessingStep:
    """Representa um passo do processamento"""
    type: str
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class State:
    """Estado da aplicação"""
    current_session: ChatSession = field(default_factory=ChatSession)
    sessions: Dict[str, ChatSession] = field(default_factory=dict)
    input_text: str = ""
    is_loading: bool = False
    show_sidebar: bool = True
    processing_steps: List[ProcessingStep] = field(default_factory=list)
    error_message: str = ""
    settings: Dict[str, Any] = field(default_factory=dict)
    uploaded_files: List[Dict[str, Any]] = field(default_factory=list)

# Configurações de estilo - TEMA CLARO
THEME_STYLES = {
    "background": "#ffffff",
    "surface": "#f5f5f5",
    "primary": "#1976d2",
    "primary_dark": "#115293",
    "text_primary": "#212121",
    "text_secondary": "#757575",
    "border": "#e0e0e0",
    "hover": "#f0f0f0",
    "message_user": "#e3f2fd",
    "message_assistant": "#f5f5f5",
    "sidebar_bg": "#fafafa",
    "header_bg": "#ffffff",
}

@me.page(
    path="/",
    title="Chat App - Claude Code SDK",
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
    ]
)
def main():
    """Página principal da aplicação"""
    state = me.state(State)
    
    # Inicializar sessão se necessário
    if not state.sessions:
        initial_session = ChatSession()
        state.sessions[initial_session.id] = initial_session
        state.current_session = initial_session
    
    # Estilos CSS
    me.style(f"""
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: {THEME_STYLES['background']};
            color: {THEME_STYLES['text_primary']};
            margin: 0;
            padding: 0;
        }}
        
        .header {{
            background-color: {THEME_STYLES['header_bg']};
            border-bottom: 1px solid {THEME_STYLES['border']};
            padding: 1rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        
        .sidebar {{
            background-color: {THEME_STYLES['sidebar_bg']};
            border-right: 1px solid {THEME_STYLES['border']};
            height: 100vh;
            overflow-y: auto;
            padding: 1rem;
        }}
        
        .main-content {{
            background-color: {THEME_STYLES['background']};
            height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        
        .chat-container {{
            flex: 1;
            overflow-y: auto;
            padding: 2rem;
        }}
        
        .message {{
            padding: 1rem;
            margin-bottom: 1rem;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        
        .message-user {{
            background-color: {THEME_STYLES['message_user']};
            margin-left: auto;
            max-width: 70%;
        }}
        
        .message-assistant {{
            background-color: {THEME_STYLES['message_assistant']};
            max-width: 70%;
        }}
        
        .input-container {{
            padding: 1rem;
            background-color: {THEME_STYLES['surface']};
            border-top: 1px solid {THEME_STYLES['border']};
        }}
        
        .btn-primary {{
            background-color: {THEME_STYLES['primary']};
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 6px;
            font-weight: 500;
            cursor: pointer;
            transition: background-color 0.2s;
        }}
        
        .btn-primary:hover {{
            background-color: {THEME_STYLES['primary_dark']};
        }}
        
        .session-item {{
            padding: 0.75rem;
            margin-bottom: 0.5rem;
            border-radius: 6px;
            cursor: pointer;
            background-color: {THEME_STYLES['background']};
            border: 1px solid {THEME_STYLES['border']};
            transition: all 0.2s;
        }}
        
        .session-item:hover {{
            background-color: {THEME_STYLES['hover']};
            transform: translateX(2px);
        }}
        
        .session-item.active {{
            background-color: {THEME_STYLES['primary']};
            color: white;
        }}
    """)
    
    with me.box(style="display: flex; height: 100vh;"):
        # Sidebar
        if state.show_sidebar:
            with me.box(style="width: 250px;", classes="sidebar"):
                render_sidebar(state)
        
        # Main content
        with me.box(style="flex: 1; display: flex; flex-direction: column;", classes="main-content"):
            # Header
            with me.box(classes="header"):
                render_header(state)
            
            # Chat area
            with me.box(classes="chat-container"):
                render_chat_messages(state)
            
            # Input area
            with me.box(classes="input-container"):
                render_input_area(state)

def render_sidebar(state: State):
    """Renderiza a barra lateral com sessões"""
    me.text("Conversas", style="font-size: 1.2rem; font-weight: 600; margin-bottom: 1rem;")
    
    # Botão novo chat
    me.button(
        "➕ Novo Chat",
        on_click=handle_new_chat,
        classes="btn-primary",
        style="width: 100%; margin-bottom: 1rem;"
    )
    
    # Lista de sessões
    for session_id, session in state.sessions.items():
        is_active = state.current_session.id == session_id if state.current_session else False
        
        with me.box(
            classes=f"session-item {'active' if is_active else ''}",
            on_click=lambda sid=session_id: handle_select_session(sid),
            style="cursor: pointer;"
        ):
            me.text(session.title, style="font-weight: 500;")
            me.text(
                f"{len(session.messages)} mensagens",
                style=f"font-size: 0.85rem; color: {'white' if is_active else THEME_STYLES['text_secondary']};"
            )

def render_header(state: State):
    """Renderiza o cabeçalho"""
    with me.box(style="display: flex; align-items: center; gap: 1rem;"):
        me.button(
            "☰",
            on_click=toggle_sidebar,
            style="background: none; border: none; font-size: 1.5rem; cursor: pointer;"
        )
        me.text(
            state.current_session.title if state.current_session else "Chat App",
            style="font-size: 1.25rem; font-weight: 600;"
        )
    
    me.text(
        "Powered by Claude Code SDK",
        style=f"color: {THEME_STYLES['text_secondary']}; font-size: 0.9rem;"
    )

def render_chat_messages(state: State):
    """Renderiza as mensagens do chat"""
    if not state.current_session or not state.current_session.messages:
        me.text(
            "Comece uma conversa enviando uma mensagem...",
            style=f"color: {THEME_STYLES['text_secondary']}; text-align: center; margin-top: 4rem;"
        )
        return
    
    for message in state.current_session.messages:
        with me.box(
            classes=f"message message-{message.role}",
            style=f"margin-{'left' if message.role == 'user' else 'right'}: {'auto' if message.role == 'user' else '0'};"
        ):
            me.markdown(message.content)
            
            # Metadata
            if message.metadata:
                render_message_metadata(message.metadata)

def render_message_metadata(metadata: Dict[str, Any]):
    """Renderiza metadata da mensagem"""
    if not metadata:
        return
    
    with me.box(style=f"margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px solid {THEME_STYLES['border']};"):
        items = []
        
        if "input_tokens" in metadata:
            items.append(f"📥 {metadata['input_tokens']} tokens")
        
        if "output_tokens" in metadata:
            items.append(f"📤 {metadata['output_tokens']} tokens")
        
        if "duration_ms" in metadata:
            duration = metadata["duration_ms"] / 1000
            items.append(f"⏱️ {duration:.1f}s")
        
        if items:
            me.text(
                " • ".join(items),
                style=f"font-size: 0.85rem; color: {THEME_STYLES['text_secondary']};"
            )

def render_input_area(state: State):
    """Renderiza área de entrada"""
    with me.box(style="display: flex; gap: 1rem; align-items: flex-end;"):
        # Upload de arquivos
        with me.box(style="flex: 0;"):
            me.uploader(
                label="📎",
                on_upload=handle_file_upload,
                style="min-width: 100px;"
            )
        
        # Campo de texto
        me.textarea(
            value=state.input_text,
            on_input=handle_input_change,
            placeholder="Digite sua mensagem...",
            style="flex: 1; min-height: 50px; max-height: 200px; padding: 0.75rem; border-radius: 6px; border: 1px solid #e0e0e0;"
        )
        
        # Botão enviar
        me.button(
            "Enviar" if not state.is_loading else "Enviando...",
            on_click=handle_send_message,
            disabled=state.is_loading or not state.input_text.strip(),
            classes="btn-primary"
        )
    
    # Mostrar arquivos carregados
    if state.uploaded_files:
        with me.box(style="margin-top: 0.5rem;"):
            for file in state.uploaded_files:
                me.chip(
                    label=file['name'],
                    on_delete=lambda f=file: handle_remove_file(f)
                )

# Event handlers
def handle_new_chat(e: me.ClickEvent):
    """Cria nova sessão de chat"""
    state = me.state(State)
    new_session = ChatSession()
    state.sessions[new_session.id] = new_session
    state.current_session = new_session
    state.input_text = ""
    state.uploaded_files = []

def handle_select_session(session_id: str):
    """Seleciona uma sessão existente"""
    state = me.state(State)
    if session_id in state.sessions:
        state.current_session = state.sessions[session_id]
        state.input_text = ""
        state.uploaded_files = []

def toggle_sidebar(e: me.ClickEvent):
    """Alterna visibilidade da sidebar"""
    state = me.state(State)
    state.show_sidebar = not state.show_sidebar

def handle_input_change(e: me.InputEvent):
    """Atualiza texto de entrada"""
    state = me.state(State)
    state.input_text = e.value

def handle_file_upload(e: me.UploadEvent):
    """Processa upload de arquivo"""
    state = me.state(State)
    file_data = {
        'name': e.file.name,
        'size': e.file.size,
        'content': base64.b64encode(e.file.read()).decode('utf-8'),
        'mime_type': e.file.mime_type
    }
    state.uploaded_files.append(file_data)

def handle_remove_file(file: Dict[str, Any]):
    """Remove arquivo carregado"""
    state = me.state(State)
    state.uploaded_files = [f for f in state.uploaded_files if f != file]

def handle_send_message(e: me.ClickEvent):
    """Envia mensagem"""
    state = me.state(State)
    
    if not state.input_text.strip():
        return
    
    # Adicionar mensagem do usuário
    user_message = Message(
        role="user",
        content=state.input_text
    )
    state.current_session.messages.append(user_message)
    
    # Limpar entrada
    message_text = state.input_text
    state.input_text = ""
    state.is_loading = True
    
    # Processar resposta (simplificada por enquanto)
    assistant_message = Message(
        role="assistant",
        content="Processando sua mensagem...",
        is_streaming=True
    )
    state.current_session.messages.append(assistant_message)
    
    # TODO: Integrar com Claude Code SDK
    # Por enquanto, apenas uma resposta simulada
    assistant_message.content = f"Recebi sua mensagem: '{message_text}'. Esta é uma resposta de teste."
    assistant_message.is_streaming = False
    
    state.is_loading = False
    
    # Atualizar título da sessão se for a primeira mensagem
    if len(state.current_session.messages) == 2:
        state.current_session.title = message_text[:50] + ("..." if len(message_text) > 50 else "")

if __name__ == "__main__":
    print("Starting Mesop app...")