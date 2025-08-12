# Correção do Erro asdict() no Mesop

## Problema
O erro `TypeError: asdict() should be called on dataclass instances` ocorria porque o Mesop tentava serializar objetos que não eram dataclasses usando a função `asdict()`.

## Causa Raiz
O Mesop usa internamente `asdict()` para serializar o estado da aplicação. Quando o estado contém objetos que não são dataclasses, o serializador falha.

## Solução Implementada

### Abordagem Final: Estado Direto com @me.stateclass
Após testar diferentes abordagens, a solução foi usar `@me.stateclass` diretamente:

```python
@me.stateclass
class State:
    """Estado da aplicação Mesop"""
    current_session: ChatSession = field(default_factory=ChatSession)
    sessions: Dict[str, ChatSession] = field(default_factory=dict)
    input_text: str = ""
    is_loading: bool = False
    error_message: str = ""
    # ... outros campos ...
```

### Por que a separação não funcionou
A tentativa inicial de separar em `StateData` e `State` causou um erro `AttributeError` porque:
1. O decorador `@dataclass` conflitava com `@me.stateclass`
2. O Mesop espera trabalhar diretamente com a classe decorada
3. A encapsulação extra criava problemas de serialização

### Como funciona agora
1. **Mesop gerencia a serialização**: O decorador `@me.stateclass` cuida de tudo internamente
2. **Classes aninhadas são dataclasses**: `Message`, `ChatSession` e `ProcessingStep` permanecem como dataclasses
3. **Sem camadas extras**: Acesso direto aos campos do estado

## Benefícios
1. **Serialização correta**: Todos os dados agora são dataclasses válidas
2. **Separação de responsabilidades**: Estado Mesop vs dados da aplicação
3. **Compatibilidade**: Funciona com o sistema de serialização do Mesop
4. **Manutenibilidade**: Código mais claro e organizado

## Verificação
Para testar se a correção funciona:
```bash
cd backend
python app.py
```

O servidor deve iniciar sem erros de `asdict()`.