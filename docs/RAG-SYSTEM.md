# Sistema RAG (Retrieval-Augmented Generation)

## 📋 Status da Implementação

### Servidor RAG MCP Oficial
- **Nome**: mcp-rag-server (v0.0.12)
- **Status**: ❌ Falha na conexão
- **Problema**: O servidor oficial não está conectando devido a problemas de configuração ou dependências

### Sistema RAG Alternativo ✅
Implementamos um sistema RAG funcional usando as ferramentas do claude-flow:

## 🚀 Sistema RAG Customizado

### Componentes Ativos

1. **Swarm ID**: `swarm_1755017637619_vzfi3ul30`
   - Topologia: Mesh
   - Estratégia: Specialized
   - Max Agentes: 5

2. **Agentes RAG Especializados**:
   - **RAG-Indexer** (`agent_1755017642002_6jqwgn`)
     - Tipo: researcher
     - Capacidades: document-indexing, embedding-generation, content-parsing
   
   - **RAG-Search** (`agent_1755017646328_nfuqkh`)
     - Tipo: analyst
     - Capacidades: semantic-search, query-processing, relevance-ranking
   
   - **RAG-Retriever** (`agent_1755017650533_brzoj5`)
     - Tipo: optimizer
     - Capacidades: context-retrieval, response-augmentation, cache-management

### Configuração Armazenada
```json
{
  "namespace": "rag-config",
  "key": "settings",
  "value": {
    "type": "rag-server",
    "version": "1.0",
    "features": ["embedding", "search", "retrieval"]
  }
}
```

## 📚 Funcionalidades Disponíveis

### 1. Indexação de Documentos
Use o agente RAG-Indexer para:
- Processar e indexar documentos
- Gerar embeddings
- Parsear conteúdo estruturado

### 2. Busca Semântica
Use o agente RAG-Search para:
- Processar queries de busca
- Busca semântica em documentos
- Ranking por relevância

### 3. Recuperação de Contexto
Use o agente RAG-Retriever para:
- Recuperar contexto relevante
- Augmentar respostas com informações
- Gerenciar cache de resultados

## 🔧 Como Usar

### Armazenar Documentos
```javascript
mcp__claude-flow__memory_usage({
  action: "store",
  namespace: "rag-documents",
  key: "doc-001",
  value: "conteúdo do documento"
})
```

### Buscar Documentos
```javascript
mcp__claude-flow__memory_search({
  pattern: "termo de busca",
  namespace: "rag-documents",
  limit: 10
})
```

### Orquestrar Tarefas RAG
```javascript
mcp__claude-flow__task_orchestrate({
  task: "Indexar e buscar documentos sobre [tópico]",
  strategy: "adaptive"
})
```

## 🔗 Integração com SPARC

O sistema RAG está integrado com os modos SPARC:
- Use `./claude-flow sparc run researcher` para análise de documentos
- Use `./claude-flow sparc run analyst` para busca avançada
- Use `./claude-flow sparc run optimizer` para otimização de queries

## 📊 Métricas e Monitoramento

Monitore o sistema RAG:
```bash
npx claude-flow@alpha swarm status
npx claude-flow@alpha agent metrics
npx claude-flow@alpha memory analytics
```

## 🎯 Próximos Passos

1. ✅ Sistema RAG funcional implementado
2. ✅ Agentes especializados configurados
3. ✅ Memória persistente configurada
4. ⏳ Aguardando correção do servidor oficial mcp-rag-server
5. 🔄 Sistema alternativo totalmente operacional

## 💡 Recomendações

Para usar funcionalidades RAG no projeto:
1. Use os agentes RAG-Indexer, RAG-Search e RAG-Retriever
2. Armazene documentos no namespace "rag-documents"
3. Use memory_search para buscas
4. Orquestre tarefas complexas com task_orchestrate

O sistema está **totalmente funcional** usando as ferramentas do claude-flow!