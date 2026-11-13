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

## Correção do bloqueio IMEI/SN — execução 42408707845

A consulta SmartDownload confirmou SM-S721B/EUX e a versão completa
`S721BXXSFEZJ1/S721BOXMFEZJ1/S721BXXSFEZJ1/S721BXXSFEZJ1`, tamanho de download
22911343072 bytes. O download não chegou a iniciar: o parser compartilhado
legado tratou o AP de referência no terceiro campo como IMEI/SN obrigatório.

O preparador agora adapta `PARSE_FIRMWARE_STRING` no helper compartilhado por
**download e extração**, não apenas a invocação do cliente. Ele aceita modelo/CSC
com terceiro token opcional de compatibilidade, não trata esse token como
identificador, limpa IMEI/SERIAL_NO a cada chamada e rejeita descritores inválidos
sem imprimir seu conteúdo. Nenhum identificador real ou fictício foi acrescentado.
A versão continua vindo exclusivamente do firmware lock e as verificações do
modelo/região/AP do doador permanecem. O original em reference/ ficou intacto.

Validação limpa: **204 testes passaram**, incluindo execução do helper real
transformado com o descritor exato que falhou, formato de dois campos, legado
do target e entradas inválidas. Sintaxe Bash, 69 referências Artisan, 37
referências adicionais e 84 evidências verificadas. Isso corrige o bloqueio
observado, não comprova download/extração nem SDK real ou aplicação dos patches.
O retry solicitado continua **somente diagnóstico**, sem kernel/ZIP da ROM.

## Correção e revisão do caminho até os patches — execução 42412918817

Nesta execução, **ambos os firmwares foram baixados, verificados e extraídos**.
A falha exibida na etapa do target ocorreu na inspeção posterior: o adaptador
interpretava `SOURCE_HAS_SYSTEM_EXT=false` como ausência total de system_ext e
recusava o diretório embutido. Não foi falta de espaço (cerca de 95,7 GB livres
após extração), falha de download ou rejeição de patch. Os 19 continuaram não
executados.

Revisado o fluxo configuração -> lock -> download/extração -> inspeção ->
create_work_dir -> caminhos APKTool -> módulos/preflight -> saída diagnóstica.
O copier Artisan original possui caminhos explícitos para system_ext separado
ou embutido e roteia conforme TARGET_HAS_SYSTEM_EXT. O alvo S10 permanece sem
partição system_ext separada; o conteúdo embutido é copiado com metadata para
system/system/system_ext, sem inventar outra partição no aparelho.

Mudanças:

- A inspeção distingue system_ext **separado**, **embutido** e **ausente**.
  O perfil sem partição separada pode ter o diretório embutido. Não se trocou
  apenas a declaração para true, nem se removeu a inspeção.
- Aliases locais para a mesma árvore são reconhecidos sem contagem dupla;
  árvores independentes ambíguas e aliases escapando da extração são rejeitados.
- SDK, AP, modelo/CSC e marcadores de extração continuam conferidos.
- A inspeção grava observações parciais e a causa **mesmo quando falha**,
  incluindo propriedades opcionais de Android/One UI/incremental quando presentes.
  Não infere a versão de One UI apenas do comentário da configuração.
- O copier original foi preservado/fixado como referência adicional. Um teste
  executa sua função original com filesystem sintético e shim de rsync,
  comprovando o caminho de SystemUI e a preservação de metadata no caso embutido.
  Esse teste não usa um APK Samsung real nem substitui o próximo diagnóstico.
- Mantidas as portas de saída antes de compilar kernel, reconstruir APK/JAR,
  gerar imagens e empacotar ROM. A execução solicitada segue só diagnóstica.

**209 testes passaram em cópia limpa; 69 referências Artisan, 37 referências
adicionais e 85 evidências auditadas.** Não se promete ausência de outras
incompatibilidades: o próximo passo necessário ainda é executar os patches
contra os arquivos S24 FE reais. O runner anterior já terminou e as árvores
extraídas não foram publicadas/cacheadas; a nova execução precisa baixar de novo.

## Resolver diretamente o firmware S24 FE fixado — execução Alpha 3.2 #24

A execução `43439258857` resolveu `S721BXXUFEZJ6` como latest, mas o perfil
aprovado exige `S721BXXSFEZJ1`. O guard interrompeu a tentativa antes de baixar
firmware, compilar ferramentas da ROM ou produzir ZIP. O usuário confirmou que
não deve haver troca silenciosa para a versão latest.

Uma consulta anterior registrou o pacote exato como
`S721BXXSFEZJ1/S721BOXMFEZJ1/S721BXXSFEZJ1/S721BXXSFEZJ1` (22.911.343.072
bytes). O perfil agora fixa a string completa e o probe solicita diretamente
essa versão ao SmartDownload, verificando igualdade integral antes de criar o
lock. A checagem após extração também exige a string completa. Não há fallback
para `S721BXXUFEZJ6` nem para outro AP.

Isso muda o método de consulta, não atesta disponibilidade atual. A nova
consulta SmartDownload e o download efetivo do pacote exato ainda precisam
passar; caso contrário, o fluxo permanece bloqueado e deve-se pedir orientação.
Nenhuma ROM Alpha 3.2 foi gerada por aquela execução.
