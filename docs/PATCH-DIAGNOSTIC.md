# Diagnóstico real do doador S24 FE sem gerar ROM

A execução é solicitada por `.github/workflows/s24fe-patch-diagnostic-request.yml`, reutilizando o pipeline alpha com `diagnostic_only: true`. O pedido de build completo existente não foi alterado.

## Etapas

1. Preparar base Artisan e tooling fixados; consultar disponibilidade e versão dos firmwares selecionados.
2. Compilar somente as ferramentas necessárias para download, extração e análise.
3. Baixar/extrair o doador S24 FE e o firmware stock do alvo SM-G973F; verificar identidade, SDK e layout declarados.
4. Executar uma única passagem de módulos/patches em preflight, registrando falhas de patches e módulos e continuando pelos módulos seguintes quando permitido.
5. Gerar e preservar relatórios, logs por módulo e os snapshots limitados de falha já capturados pelo pipeline.

**Não compila kernel, não reconstrói APKs/JARs modificados, não gera imagens/ZIP da ROM e não altera o lançamento atual.** A passagem de diagnóstico edita apenas a árvore de trabalho descartável do runner. Não é validação de assembly/runtime/boot.

## Relatórios

Artefato `beyond1lte-alpha-build-diagnostics`:

- `patch-diagnostic-summary.json`: estado global, perfil selecionado, lock de firmware, inspeção de propriedades, recibos de etapas, falhas e situação dos 19 patches anteriores.
- `patch-preflight.json` / `.jsonl`: eventos completos da execução, quando ela alcança a aplicação de patches.
- `patch-preflight-modules/**/*.log`: saída por módulo.
- Logs de consulta/download/extração e snapshots de falha já limitados pelo coletor.

O resumo também aparece no Summary do Actions. Se a consulta do firmware, o SDK ou outra etapa anterior falhar, os patches aparecem como **não executados**, não como aprovados. O artefato é preservado mesmo em falha. Uma falha de cobertura do preflight continua fatal; falhas individuais são relatadas pelo modo experimental, não escondidas como sucesso.

## Separação de checkpoints

O estágio CLI `diagnostic` usa os pré-requisitos de `patch`, mas grava somente `diagnostic.json` com status `diagnostic-complete`. Não grava `patch.json` de sucesso, não serve para autorizar retire/package e não reutiliza alterações de diagnóstico como resultado de build real. O build completo continua exigindo sua própria passagem e os checkpoints normais.

## Validação local

**200 testes passaram em cópia limpa**, com 69 referências Artisan, 37 referências adicionais e 84 evidências de auditoria verificadas. Os testes novos garantem passagem única, separação de checkpoints, bloqueio de todas as etapas produtoras de ROM no workflow e resumo correto para diagnóstico ausente/incompleto. Isso não demonstra disponibilidade real do firmware Samsung.
