# AGENTS.md

## Regra principal
Este projeto deve ser alterado com edicao cirurgica e minuciosa.
A prioridade maxima e preservar o comportamento existente fora do escopo pedido.

## Fonte de verdade
- O arquivo PLANS.md e obrigatorio.
- Antes de editar qualquer arquivo, releia PLANS.md.
- Antes de implementar, registre no PLANS.md o passo atual.
- Depois de implementar, atualize o status no PLANS.md.

## Regras obrigatorias
- Nao apagar codigo sem registrar o motivo no PLANS.md.
- Nao reescrever arquivos inteiros sem necessidade.
- Nao refatorar fora do escopo.
- Nao renomear arquivos, funcoes, classes ou variaveis publicas sem necessidade explicita.
- Nao alterar arquitetura sem estar previsto no plano.
- Sempre fazer o menor delta possivel.
- Sempre listar os arquivos alterados.
- Sempre registrar o que foi preservado.
- Em caso de duvida, preservar vence.

## Fluxo por passo
1. Ler PLANS.md
2. Registrar intencao da mudanca
3. Informar arquivos alvo
4. Fazer a menor alteracao possivel
5. Validar impacto local
6. Atualizar PLANS.md com resultado e checkpoint
7. Parar e aguardar

## Proibicoes
- Nao fazer “limpezas” espontaneas
- Nao remover comentarios, funcoes ou blocos aparentemente antigos sem autorizacao
- Nao substituir implementacoes funcionando por versoes “mais bonitas”
- Nao tocar em arquivos fora do escopo sem registrar
