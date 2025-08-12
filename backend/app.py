"""
Chat App with Claude Code SDK using Mesop
"""
import mesop as me
import mesop.labs as mel
from anthropic import Anthropic
import os
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import subprocess
import uuid
from pathlib import Path

# Initialize Anthropic client
anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

@dataclass
class Message:
    """Represents a chat message"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    role: str = "user"  # "user" or "assistant"
    content: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_streaming: bool = False

@dataclass
class ChatSession:
    """Manages a chat session"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    title: str = "New Chat"
    context: str = ""

@me.stateclass
class State:
    """Application state"""
    current_session: ChatSession = field(default_factory=ChatSession)
    sessions: Dict[str, ChatSession] = field(default_factory=dict)
    input_text: str = ""
    is_loading: bool = False
    error_message: str = ""
    show_sidebar: bool = False
    uploaded_file_content: str = ""
    uploaded_file_name: str = ""
    use_claude_cli: bool = True  # Use Claude CLI by default
    processing_steps: List[Dict[str, Any]] = field(default_factory=list)
    
def call_claude_cli(prompt: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """Call Claude CLI and return structured response"""
    try:
        # Build command
        cmd = ["claude", "-p", prompt, "--output-format", "json"]
        
        # Add session continuation if available
        if session_id:
            cmd.extend(["--resume", session_id])
        
        # Execute command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0 and result.stdout:
            # Parse JSON response
            response_data = json.loads(result.stdout)
            return {
                "success": True,
                "result": response_data.get("result", ""),
                "session_id": response_data.get("session_id"),
                "cost_usd": response_data.get("cost_usd", 0),
                "duration_ms": response_data.get("duration_ms", 0),
                "num_turns": response_data.get("num_turns", 0),
                "is_error": response_data.get("is_error", False)
            }
        else:
            error_msg = result.stderr if result.stderr else "Command failed"
            return {
                "success": False,
                "error": error_msg,
                "is_error": True
            }
            
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Request timed out after 120 seconds",
            "is_error": True
        }
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"Failed to parse response: {str(e)}",
            "is_error": True
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "is_error": True
        }

def call_anthropic_api(prompt: str, messages: List[Message]) -> str:
    """Call Anthropic API directly"""
    try:
        # Convert messages to API format
        api_messages = []
        for msg in messages:
            api_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Add current prompt
        api_messages.append({
            "role": "user",
            "content": prompt
        })
        
        # Make API call
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            messages=api_messages
        )
        
        return response.content[0].text
        
    except Exception as e:
        return f"Error calling Anthropic API: {str(e)}"

@me.page(
    path="/",
    title="Chat with Claude Code",
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
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
        
        # Main chat area
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
            
            # Messages area
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
                # Processing steps
                if state.processing_steps:
                    render_processing_steps(state)
                
                # Chat messages
                for message in state.current_session.messages:
                    render_message(message)
                
                # Loading indicator
                if state.is_loading:
                    render_loading_indicator()
                
                # Error message
                if state.error_message:
                    render_error(state.error_message)
            
            # Input area
            render_input_area(state)

def render_sidebar(state: State):
    """Render the sidebar with sessions"""
    with me.box(
        style=me.Style(
            width=280,
            background="rgba(30, 30, 30, 0.95)",
            border_right="1px solid rgba(255, 255, 255, 0.1)",
            padding=me.Padding.all(20),
            display="flex",
            flex_direction="column",
            gap=20
        )
    ):
        # New chat button
        with me.box(
            style=me.Style(
                padding=me.Padding.all(12),
                background="linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)",
                border_radius=8,
                cursor="pointer",
                text_align="center"
            ),
            on_click=lambda e: handle_new_chat(e, state)
        ):
            me.text(
                "✨ New Chat",
                style=me.Style(
                    color="white",
                    font_weight=600
                )
            )
        
        # Sessions list
        me.text(
            "Recent Chats",
            style=me.Style(
                color="rgba(255, 255, 255, 0.6)",
                font_size=12,
                text_transform="uppercase",
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
            for session_id, session in state.sessions.items():
                render_session_item(session, session_id == state.current_session.id)

def render_session_item(session: ChatSession, is_active: bool):
    """Render a session item in the sidebar"""
    with me.box(
        style=me.Style(
            padding=me.Padding.all(12),
            background="rgba(255, 255, 255, 0.05)" if is_active else "transparent",
            border_radius=6,
            cursor="pointer",
            border="1px solid rgba(255, 255, 255, 0.1)" if is_active else "none"
        )
    ):
        me.text(
            session.title[:30] + "..." if len(session.title) > 30 else session.title,
            style=me.Style(
                color="white" if is_active else "rgba(255, 255, 255, 0.7)",
                font_size=14
            )
        )
        me.text(
            f"{len(session.messages)} messages",
            style=me.Style(
                color="rgba(255, 255, 255, 0.4)",
                font_size=12
            )
        )

def render_header(state: State):
    """Render the header"""
    with me.box(
        style=me.Style(
            padding=me.Padding.all(20),
            border_bottom="1px solid rgba(255, 255, 255, 0.1)",
            display="flex",
            align_items="center",
            gap=20
        )
    ):
        # Menu button
        with me.box(
            style=me.Style(
                cursor="pointer",
                padding=me.Padding.all(8)
            ),
            on_click=lambda e: toggle_sidebar(e, state)
        ):
            me.text(
                "☰",
                style=me.Style(
                    color="white",
                    font_size=24
                )
            )
        
        # Title
        me.text(
            "Chat with Claude Code",
            style=me.Style(
                color="white",
                font_size=20,
                font_weight=600,
                flex=1
            )
        )
        
        # Mode toggle
        with me.box(
            style=me.Style(
                display="flex",
                align_items="center",
                gap=10
            )
        ):
            me.text(
                "Mode:",
                style=me.Style(
                    color="rgba(255, 255, 255, 0.6)",
                    font_size=14
                )
            )
            
            mode_text = "Claude CLI" if state.use_claude_cli else "API Direct"
            with me.box(
                style=me.Style(
                    padding=me.Padding(left=12, right=12, top=6, bottom=6),
                    background="rgba(79, 70, 229, 0.2)",
                    border="1px solid rgba(79, 70, 229, 0.5)",
                    border_radius=20,
                    cursor="pointer"
                ),
                on_click=lambda e: toggle_mode(e, state)
            ):
                me.text(
                    mode_text,
                    style=me.Style(
                        color="#a78bfa",
                        font_size=13,
                        font_weight=500
                    )
                )

def render_message(message: Message):
    """Render a chat message"""
    is_user = message.role == "user"
    
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
                justify_content="center",
                flex_shrink=0
            )
        ):
            me.text(
                "U" if is_user else "C",
                style=me.Style(
                    color="white",
                    font_weight=600,
                    font_size=16
                )
            )
        
        # Message content
        with me.box(
            style=me.Style(
                flex=1,
                display="flex",
                flex_direction="column",
                gap=8
            )
        ):
            # Role and timestamp
            with me.box(
                style=me.Style(
                    display="flex",
                    align_items="center",
                    gap=10
                )
            ):
                me.text(
                    "You" if is_user else "Claude",
                    style=me.Style(
                        color="white",
                        font_weight=600,
                        font_size=14
                    )
                )
                me.text(
                    message.timestamp.strftime("%H:%M"),
                    style=me.Style(
                        color="rgba(255, 255, 255, 0.4)",
                        font_size=12
                    )
                )
            
            # Message text
            with me.box(
                style=me.Style(
                    padding=me.Padding.all(12),
                    background="rgba(255, 255, 255, 0.05)",
                    border_radius=8,
                    border="1px solid rgba(255, 255, 255, 0.1)"
                )
            ):
                me.markdown(
                    message.content,
                    style=me.Style(
                        color="rgba(255, 255, 255, 0.9)",
                        font_size=14,
                        line_height="1.6"
                    )
                )
            
            # Metadata
            if message.metadata:
                render_message_metadata(message.metadata)

def render_message_metadata(metadata: Dict[str, Any]):
    """Render message metadata"""
    with me.box(
        style=me.Style(
            display="flex",
            gap=15,
            margin=me.Margin(top=8)
        )
    ):
        if "cost_usd" in metadata:
            me.text(
                f"💰 ${metadata['cost_usd']:.4f}",
                style=me.Style(
                    color="rgba(255, 255, 255, 0.5)",
                    font_size=12
                )
            )
        
        if "duration_ms" in metadata:
            me.text(
                f"⏱️ {metadata['duration_ms']:.0f}ms",
                style=me.Style(
                    color="rgba(255, 255, 255, 0.5)",
                    font_size=12
                )
            )
        
        if "num_turns" in metadata:
            me.text(
                f"🔄 {metadata['num_turns']} turns",
                style=me.Style(
                    color="rgba(255, 255, 255, 0.5)",
                    font_size=12
                )
            )

def render_processing_steps(state: State):
    """Render processing steps"""
    with me.box(
        style=me.Style(
            padding=me.Padding.all(12),
            background="rgba(79, 70, 229, 0.1)",
            border="1px solid rgba(79, 70, 229, 0.3)",
            border_radius=8,
            margin=me.Margin(bottom=20)
        )
    ):
        me.text(
            "Processing Steps",
            style=me.Style(
                color="rgba(167, 139, 250, 1)",
                font_weight=600,
                font_size=14,
                margin=me.Margin(bottom=10)
            )
        )
        
        for step in state.processing_steps[-5:]:  # Show last 5 steps
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
                    step.get("message", "Processing..."),
                    style=me.Style(
                        color="rgba(255, 255, 255, 0.7)",
                        font_size=13
                    )
                )

def render_loading_indicator():
    """Render loading indicator"""
    with me.box(
        style=me.Style(
            display="flex",
            align_items="center",
            gap=10,
            padding=me.Padding.all(12)
        )
    ):
        me.text(
            "⏳",
            style=me.Style(
                font_size=20,
                animation="spin 1s linear infinite"
            )
        )
        me.text(
            "Claude is thinking...",
            style=me.Style(
                color="rgba(255, 255, 255, 0.6)",
                font_size=14
            )
        )

def render_error(error_message: str):
    """Render error message"""
    with me.box(
        style=me.Style(
            padding=me.Padding.all(12),
            background="rgba(239, 68, 68, 0.1)",
            border="1px solid rgba(239, 68, 68, 0.3)",
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
    """Render input area"""
    with me.box(
        style=me.Style(
            padding=me.Padding.all(20),
            border_top="1px solid rgba(255, 255, 255, 0.1)",
            display="flex",
            gap=12,
            align_items="flex-end"
        )
    ):
        # File upload
        with me.box(
            style=me.Style(
                display="flex",
                align_items="center"
            )
        ):
            me.uploader(
                label="📎",
                on_upload=lambda e: handle_file_upload(e, state),
                type="flat",
                color="primary",
                style=me.Style(
                    background="transparent",
                    color="rgba(255, 255, 255, 0.6)"
                )
            )
        
        # Text input
        with me.box(style=me.Style(flex=1)):
            me.textarea(
                label="",
                placeholder="Type your message here... (Shift+Enter for new line)",
                value=state.input_text,
                on_input=lambda e: update_input(e, state),
                rows=1,
                max_rows=5,
                style=me.Style(
                    width="100%",
                    background="rgba(255, 255, 255, 0.05)",
                    border="1px solid rgba(255, 255, 255, 0.2)",
                    border_radius=8,
                    padding=me.Padding.all(12),
                    color="white",
                    font_size=14
                )
            )
        
        # Send button
        with me.box(
            style=me.Style(
                padding=me.Padding(left=16, right=16, top=12, bottom=12),
                background="linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)",
                border_radius=8,
                cursor="pointer" if not state.is_loading else "not-allowed",
                opacity=0.5 if state.is_loading else 1
            ),
            on_click=lambda e: handle_send_message(e, state) if not state.is_loading else None
        ):
            me.text(
                "Send",
                style=me.Style(
                    color="white",
                    font_weight=600
                )
            )

# Event handlers
def toggle_sidebar(e: me.ClickEvent, state: State):
    """Toggle sidebar visibility"""
    state.show_sidebar = not state.show_sidebar

def toggle_mode(e: me.ClickEvent, state: State):
    """Toggle between Claude CLI and API mode"""
    state.use_claude_cli = not state.use_claude_cli

def handle_new_chat(e: me.ClickEvent, state: State):
    """Create a new chat session"""
    new_session = ChatSession()
    state.sessions[new_session.id] = new_session
    state.current_session = new_session
    state.processing_steps = []
    state.error_message = ""

def update_input(e: me.InputEvent, state: State):
    """Update input text"""
    state.input_text = e.value

def handle_file_upload(e: me.UploadEvent, state: State):
    """Handle file upload"""
    try:
        file_content = e.file.read().decode('utf-8')
        state.uploaded_file_content = file_content
        state.uploaded_file_name = e.file.name
        
        # Add to input
        state.input_text += f"\n\nFile: {e.file.name}\n```\n{file_content[:1000]}\n```"
        if len(file_content) > 1000:
            state.input_text += f"\n... (truncated, {len(file_content)} total characters)"
            
    except Exception as error:
        state.error_message = f"Error uploading file: {str(error)}"

def handle_send_message(e: me.ClickEvent, state: State):
    """Handle sending a message"""
    if not state.input_text.strip() or state.is_loading:
        return
    
    # Clear error
    state.error_message = ""
    
    # Add user message
    user_message = Message(
        role="user",
        content=state.input_text
    )
    state.current_session.messages.append(user_message)
    
    # Clear input
    prompt = state.input_text
    state.input_text = ""
    
    # Set loading
    state.is_loading = True
    state.processing_steps = []
    
    # Process message
    try:
        if state.use_claude_cli:
            # Add processing step
            state.processing_steps.append({
                "message": "Calling Claude CLI...",
                "timestamp": datetime.now()
            })
            
            # Call Claude CLI
            session_id = None
            if len(state.current_session.messages) > 1:
                session_id = state.current_session.id
            
            response = call_claude_cli(prompt, session_id)
            
            if response["success"]:
                # Add assistant message
                assistant_message = Message(
                    role="assistant",
                    content=response["result"],
                    metadata={
                        "cost_usd": response.get("cost_usd"),
                        "duration_ms": response.get("duration_ms"),
                        "num_turns": response.get("num_turns")
                    }
                )
                state.current_session.messages.append(assistant_message)
                
                # Update session ID if provided
                if response.get("session_id"):
                    state.current_session.id = response["session_id"]
            else:
                state.error_message = response.get("error", "Unknown error")
        else:
            # Use Anthropic API
            state.processing_steps.append({
                "message": "Calling Anthropic API...",
                "timestamp": datetime.now()
            })
            
            response_text = call_anthropic_api(prompt, state.current_session.messages[:-1])
            
            # Add assistant message
            assistant_message = Message(
                role="assistant",
                content=response_text
            )
            state.current_session.messages.append(assistant_message)
        
        # Update session
        state.current_session.last_activity = datetime.now()
        if state.current_session.title == "New Chat" and len(prompt) > 0:
            state.current_session.title = prompt[:50] + "..." if len(prompt) > 50 else prompt
        
        # Save session
        state.sessions[state.current_session.id] = state.current_session
        
    except Exception as error:
        state.error_message = f"Error: {str(error)}"
    finally:
        state.is_loading = False
        state.processing_steps = []

if __name__ == "__main__":
    me.run()