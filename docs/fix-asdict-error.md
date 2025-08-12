# Correção do Erro asdict() no Mesop

## Problema
O erro `TypeError: asdict() should be called on dataclass instances` ocorria porque o Mesop tentava serializar objetos que não eram dataclasses usando a função `asdict()`.

## Causa Raiz
O Mesop usa internamente `asdict()` para serializar o estado da aplicação. Quando o estado contém objetos que não são dataclasses, o serializador falha.

## Solução Implementada

### 1. Separação de Estado
Criamos duas classes separadas:
- `StateData`: Uma dataclass pura que contém todos os dados serializáveis
- `State`: A classe decorada com `@me.stateclass` que encapsula `StateData`

```python
@dataclass
class StateData:
    """Dados serializáveis do estado"""
    current_session: ChatSession = field(default_factory=ChatSession)
    sessions: Dict[str, ChatSession] = field(default_factory=dict)
    # ... outros campos ...

@me.stateclass 
class State:
    """Estado da aplicação Mesop"""
    data: StateData = field(default_factory=StateData)
```

### 2. Atualização de Referências
Todas as funções foram atualizadas para:
- Acessar `state.data` em vez de `state` diretamente
- Passar `StateData` como parâmetro em vez de `State`
- Verificar se `state.data` existe antes de usar

### 3. Garantia de Compatibilidade
Adicionamos verificações defensivas:
```python
if not hasattr(state, 'data'):
    state.data = StateData()
```

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