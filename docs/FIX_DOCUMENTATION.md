# 📚 Documentação da Correção: Serialização de Dataclasses no Mesop

## 🎯 O Que Foi Mudado

### 1. Tipos de Campos de Data/Hora

**Problema:** Objetos `datetime` não são serializáveis pelo Mesop  
**Solução:** Usar strings ISO 8601

```python
# ❌ ANTES (causava erro)
timestamp: datetime = field(default_factory=datetime.now)

# ✅ DEPOIS (funciona)
timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
```

### 2. Sistema de Validação

**Adicionado:** Validação proativa de tipos antes da serialização

```python
def validate_sessions(self):
    """Valida e corrige sessões para garantir que são objetos ChatSession"""
    # Teste de serialização
    try:
        test_dict = asdict(self.current_session)
        print(f"[DEBUG] current_session é serializável", file=sys.stderr)
    except Exception as e:
        print(f"[ERROR] current_session NÃO é serializável: {e}", file=sys.stderr)
        self.current_session = ChatSession()  # Reset para estado válido
```

### 3. Conversão de Timestamps

**Implementado:** Tratamento inteligente de diferentes formatos

```python
# Aceita string ISO
if isinstance(msg['timestamp'], str):
    new_msg.timestamp = msg['timestamp']
    
# Converte datetime para string ISO
elif isinstance(msg['timestamp'], datetime):
    new_msg.timestamp = msg['timestamp'].isoformat()
    
# Fallback para timestamp atual
else:
    new_msg.timestamp = datetime.now().isoformat()
```

## 🔧 Por Que Essas Mudanças

### Requisitos do Mesop Framework

O Mesop usa `dataclasses.asdict()` internamente para:
1. Sincronizar estado entre servidor e cliente
2. Serializar para transmissão via WebSocket
3. Persistir estado entre requisições

### Limitações de Serialização

`asdict()` só funciona com:
- Tipos primitivos: `str`, `int`, `float`, `bool`
- Coleções: `list`, `dict`, `tuple`
- Dataclasses aninhadas

NÃO funciona com:
- ❌ `datetime` objects
- ❌ Classes customizadas (não-dataclass)
- ❌ Funções/métodos
- ❌ File handles

## 📋 Checklist de Validação

Ao trabalhar com Mesop, sempre verifique:

- [ ] Todos os campos de dataclass usam tipos serializáveis
- [ ] Timestamps são strings ISO, não objetos datetime
- [ ] Estado é validado antes de renderização
- [ ] Conversões dict ↔ dataclass preservam tipos corretos
- [ ] Logging adequado para debug de serialização

## 🚀 Como Aplicar em Outros Projetos

### 1. Template de Dataclass Mesop-Safe

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class MesopSafeModel:
    """Template para dataclass compatível com Mesop"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    data: Dict[str, Any] = field(default_factory=dict)
    items: List[str] = field(default_factory=list)
    
    # ❌ EVITAR
    # timestamp: datetime  # Não serializável
    # custom_obj: MyClass  # Não serializável
```

### 2. Função de Validação Genérica

```python
def validate_dataclass_serialization(obj):
    """Valida se um dataclass pode ser serializado"""
    from dataclasses import is_dataclass, asdict
    
    if not is_dataclass(obj):
        return False, "Não é um dataclass"
    
    try:
        asdict(obj)
        return True, "OK"
    except Exception as e:
        return False, str(e)
```

### 3. Decorator para Auto-Validação

```python
def mesop_safe(cls):
    """Decorator que garante que dataclass é Mesop-safe"""
    original_init = cls.__init__
    
    def new_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        # Validar após inicialização
        try:
            asdict(self)
        except Exception as e:
            raise TypeError(f"Dataclass não é Mesop-safe: {e}")
    
    cls.__init__ = new_init
    return cls

@mesop_safe
@dataclass
class SafeModel:
    # ...campos...
```

## 📊 Impacto da Correção

### Antes
- ❌ Erro ao criar nova sessão de chat
- ❌ Estado inconsistente após conversões
- ❌ Difícil debug sem logging adequado

### Depois
- ✅ Criação de sessões funciona perfeitamente
- ✅ Estado sempre válido e serializável
- ✅ Debug facilitado com logging detalhado
- ✅ Código mais robusto e maintível

## 🔗 Referências

- [Mesop Documentation - State Management](https://google.github.io/mesop/guides/state_management/)
- [Python dataclasses.asdict()](https://docs.python.org/3/library/dataclasses.html#dataclasses.asdict)
- [ISO 8601 DateTime Format](https://en.wikipedia.org/wiki/ISO_8601)