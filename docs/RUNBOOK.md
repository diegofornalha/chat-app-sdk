# 🚨 Runbook: Erro de Serialização no Mesop

## 🎯 Identificação do Problema

### Sintomas
- **Erro:** `TypeError: asdict() should be called on dataclass instances`
- **Quando ocorre:** Ao interagir com estado do Mesop (criar sessão, mudar página, etc.)
- **Componente:** Aplicações Mesop usando `@me.stateclass`

### Diagnóstico Rápido

Execute este comando no console Python:
```python
from dataclasses import asdict, is_dataclass
asdict(state.current_session)  # Substitua pelo objeto problemático
```

Se der erro, o objeto não é serializável.

## 🔧 Solução Passo a Passo

### Passo 1: Identificar o Campo Problemático

```python
# Script de diagnóstico
def check_serialization(obj, path="root"):
    from dataclasses import is_dataclass, fields, asdict
    
    if not is_dataclass(obj):
        print(f"❌ {path} não é dataclass: {type(obj)}")
        return False
    
    try:
        asdict(obj)
        print(f"✅ {path} é serializável")
        return True
    except Exception as e:
        print(f"❌ {path} falhou: {e}")
        
        # Verificar cada campo
        for field in fields(obj):
            value = getattr(obj, field.name)
            print(f"  Testando {path}.{field.name}: {type(value)}")
            
            if is_dataclass(value):
                check_serialization(value, f"{path}.{field.name}")
        
        return False

# Usar:
check_serialization(state)
```

### Passo 2: Corrigir Tipos Não-Serializáveis

#### A. Datetime → String ISO

```python
# ❌ ERRADO
from datetime import datetime
@dataclass
class Model:
    timestamp: datetime = field(default_factory=datetime.now)

# ✅ CORRETO
@dataclass
class Model:
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
```

#### B. Objetos Customizados → Dict

```python
# ❌ ERRADO
@dataclass
class Model:
    custom_obj: MyCustomClass

# ✅ CORRETO
@dataclass
class Model:
    custom_data: Dict[str, Any]  # Armazene como dict
```

#### C. Enum → String

```python
# ❌ ERRADO
from enum import Enum
class Status(Enum):
    ACTIVE = "active"

@dataclass
class Model:
    status: Status

# ✅ CORRETO
@dataclass
class Model:
    status: str = "active"  # Use string literal
```

### Passo 3: Adicionar Validação

Adicione este método à sua classe State:

```python
@me.stateclass
class State:
    # ... campos ...
    
    def validate_serialization(self):
        """Valida que o estado pode ser serializado"""
        from dataclasses import asdict, is_dataclass
        
        try:
            # Tentar serializar
            state_dict = asdict(self)
            return True
        except Exception as e:
            print(f"[ERROR] Estado não serializável: {e}", file=sys.stderr)
            
            # Resetar para estado válido
            self.__init__()  # Re-inicializar com valores padrão
            return False
```

### Passo 4: Instrumentar o Código

Adicione logging em pontos críticos:

```python
def validate_state_before_render(state: State):
    """Validar antes de cada renderização"""
    import sys
    from dataclasses import asdict
    
    print(f"[DEBUG] Validando estado...", file=sys.stderr)
    
    try:
        test = asdict(state)
        print(f"[DEBUG] ✅ Estado válido", file=sys.stderr)
    except Exception as e:
        print(f"[ERROR] ❌ Estado inválido: {e}", file=sys.stderr)
        # Corrigir ou resetar estado
        state = State()  # Reset completo
```

## 🛠️ Ferramentas de Debug

### 1. Logger de Serialização

```python
import functools
import sys
from dataclasses import asdict

def log_serialization(func):
    """Decorator para logar problemas de serialização"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        
        # Se retornar um state, validar
        if hasattr(result, '__dataclass_fields__'):
            try:
                asdict(result)
            except Exception as e:
                print(f"[WARN] {func.__name__} retornou objeto não-serializável: {e}", 
                      file=sys.stderr)
        
        return result
    return wrapper

# Usar:
@log_serialization
def handle_click(state):
    # ... código ...
    return state
```

### 2. Validador em Tempo Real

```python
class SerializationValidator:
    """Monitora mudanças no estado e valida serialização"""
    
    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        
        # Validar após cada mudança
        try:
            from dataclasses import asdict
            asdict(self)
        except Exception as e:
            print(f"[WARN] Campo {name} tornou objeto não-serializável: {e}")
```

### 3. Script de Teste Automatizado

```python
# test_serialization.py
def test_all_handlers():
    """Testa serialização em todos os handlers"""
    from app import State, handle_new_chat, handle_send_message
    from dataclasses import asdict
    
    state = State()
    handlers = [handle_new_chat, handle_send_message]  # etc
    
    for handler in handlers:
        try:
            # Simular evento
            class FakeEvent:
                value = "test"
            
            # Executar handler
            handler(FakeEvent())
            
            # Validar estado
            asdict(state)
            print(f"✅ {handler.__name__} OK")
            
        except Exception as e:
            print(f"❌ {handler.__name__} falhou: {e}")
```

## 📋 Checklist de Prevenção

Antes de fazer deploy:

- [ ] Todos os campos datetime são strings ISO
- [ ] Nenhum objeto customizado em dataclasses
- [ ] Função de validação implementada
- [ ] Logging adequado nos handlers
- [ ] Testes de serialização passando
- [ ] Conversões dict ↔ dataclass testadas

## 🚑 Recuperação de Emergência

Se a aplicação estiver travada:

### 1. Reset Rápido
```python
# Adicione este endpoint de emergência
@me.page(path="/reset")
def reset_page():
    state = me.state(State)
    # Reset completo
    state.__init__()
    me.redirect("/")
```

### 2. Modo Safe
```python
# Adicione flag de modo seguro
SAFE_MODE = os.getenv("MESOP_SAFE_MODE", "false") == "true"

if SAFE_MODE:
    # Desabilitar features problemáticas
    # Usar tipos mais simples
    # Adicionar mais validação
```

### 3. Fallback para Dict
```python
# Se dataclass falhar, use dict simples
try:
    state = State()
except:
    state = {
        "current_session": {},
        "messages": [],
        # ... valores padrão ...
    }
```

## 📞 Quando Escalar

Escale o problema se:
- O erro persiste após aplicar correções
- Afeta múltiplos componentes
- Causa perda de dados
- Ocorre em produção

## 📚 Referências Úteis

- [Mesop State Management](https://google.github.io/mesop/guides/state_management/)
- [Python Dataclasses](https://docs.python.org/3/library/dataclasses.html)
- [Debug com pdb](https://docs.python.org/3/library/pdb.html)
- Este runbook: `/docs/RUNBOOK.md`

---

**Última atualização:** 2025-01-12  
**Autor:** Claude Debug Assistant  
**Versão:** 1.0