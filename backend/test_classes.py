#!/usr/bin/env python3
"""
Teste isolado das classes sem dependências externas
"""
import json
from dataclasses import dataclass, field, asdict, is_dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid

# Recriar as classes aqui para teste isolado
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

def test_all():
    print("🧪 Testando serialização das classes com timestamps como strings ISO...")
    
    # Teste 1: Message
    print("\n1. Message:")
    msg = Message(content="Olá!")
    print(f"   timestamp type: {type(msg.timestamp)} = {msg.timestamp[:19]}...")
    try:
        json.dumps(asdict(msg))
        print("   ✅ Serializável!")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False
    
    # Teste 2: ChatSession com mensagens
    print("\n2. ChatSession com Message:")
    session = ChatSession()
    session.messages.append(msg)
    print(f"   created_at type: {type(session.created_at)} = {session.created_at[:19]}...")
    print(f"   messages count: {len(session.messages)}")
    try:
        json.dumps(asdict(session))
        print("   ✅ Serializável!")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False
    
    # Teste 3: ProcessingStep
    print("\n3. ProcessingStep:")
    step = ProcessingStep(type="test", message="Testing")
    print(f"   timestamp type: {type(step.timestamp)} = {step.timestamp[:19]}...")
    try:
        json.dumps(asdict(step))
        print("   ✅ Serializável!")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False
    
    # Teste 4: Estado complexo simulando Mesop
    print("\n4. Estado complexo (simulando State do Mesop):")
    @dataclass
    class State:
        current_session: ChatSession = field(default_factory=ChatSession)
        sessions: Dict[str, ChatSession] = field(default_factory=dict)
        processing_steps: List[ProcessingStep] = field(default_factory=list)
        input_text: str = ""
        is_loading: bool = False
    
    state = State()
    state.sessions[session.id] = session
    state.current_session = session
    state.processing_steps.append(step)
    
    print(f"   current_session is dataclass: {is_dataclass(state.current_session)}")
    print(f"   sessions count: {len(state.sessions)}")
    
    try:
        state_dict = asdict(state)
        json_str = json.dumps(state_dict)
        print(f"   ✅ Estado completo serializável! ({len(json_str)} bytes)")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False
    
    # Teste 5: Novo chat (problema reportado)
    print("\n5. Simulando 'Novo Chat':")
    new_session = ChatSession()
    new_session.messages = []
    state.sessions[new_session.id] = new_session
    state.current_session = new_session
    
    print(f"   Nova sessão é dataclass: {is_dataclass(new_session)}")
    print(f"   Nova sessão tem messages: {hasattr(new_session, 'messages')}")
    
    try:
        json.dumps(asdict(state))
        print("   ✅ Estado após novo chat é serializável!")
    except Exception as e:
        print(f"   ❌ Erro após novo chat: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("="*70)
    print("TESTE: Serialização com timestamps como strings ISO")
    print("="*70)
    
    if test_all():
        print("\n✅ SUCESSO! Todos os testes passaram.")
        print("As classes com timestamps como strings ISO são totalmente serializáveis.")
    else:
        print("\n❌ FALHA! Algum teste não passou.")
    
    print("="*70)