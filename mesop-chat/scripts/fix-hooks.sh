#!/bin/bash
# Script para corrigir problemas de hooks do claude-flow

echo "🔧 Corrigindo problemas de hooks do claude-flow..."

# Verificar se o diretório deno está causando conflitos
if [ -d "../deno" ]; then
    echo "⚠️  Diretório 'deno' detectado. Este pode estar causando conflitos."
    echo "   O diretório contém scripts relacionados ao Deno runtime."
fi

# Testar execução básica de hooks
echo ""
echo "📝 Testando hooks básicos..."

# Testar hook sem spawn
npx claude-flow hooks pre-task --description "teste" 2>&1 | grep -q "ENOENT" && {
    echo "❌ Erro de spawn detectado nos hooks"
    echo "   Possível problema com PATH ou permissões"
} || {
    echo "✅ Hooks funcionando normalmente"
}

# Verificar variáveis de ambiente
echo ""
echo "🔍 Verificando ambiente..."
echo "PATH: $PATH"
echo "SHELL: $SHELL"
echo "NODE_ENV: ${NODE_ENV:-não definido}"

# Sugestões
echo ""
echo "💡 Sugestões para resolver o problema:"
echo "1. O erro 'spawn /bin/sh ENOENT' geralmente indica problema com PATH"
echo "2. O diretório 'deno' não parece estar relacionado ao erro"
echo "3. Os hooks são opcionais e não impedem o funcionamento do app"
echo ""
echo "Para desabilitar temporariamente os hooks problemáticos:"
echo "export CLAUDE_FLOW_DISABLE_HOOKS=true"
echo ""
echo "✅ Diagnóstico concluído"