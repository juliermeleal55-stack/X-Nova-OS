# Galaxy S10+ (beyond2lte) — pesquisa de OTA legado

**Estado: research-only; não é uma ROM pronta para instalação.** O usuário confirmou
nesta conversa o modelo **SM-G975F / beyond2lte**. Isso confirma apenas o modelo-alvo;
firmware, partições, kernel, compatibilidade vendor e boot continuam sem validação.
Não se presume suporte a SM-G975N, variantes Snapdragon ou outros modelos.

## Formato de referência

A release Alpha 3 indicada aponta para o artifact Actions `13692849127`
(`Beyoud-beyond1lte-alpha1-UNTESTED`, 5.897.467.179 bytes; expiração informada
`2026-11-16T16:58:05Z`). A API confirmou os metadados, mas o ZIP **não foi
baixado nem inspecionado**: `gh run download` terminou com `EOF` no host de
armazenamento de artifacts do GitHub, fora da allowlist de rede deste sandbox.
Portanto, a composição exata do ZIP Alpha 3 ainda não está comprovada.

O histórico da pipeline da Alpha 3 chama `scripts/internal/build_flashable_zip.sh`,
com payloads `img2sdat`/Brotli (`*.new.dat.br`), transfer lists, updater Artisan e
assinatura `signapk`. A via local `artisan-ota` foi adaptada para esse fluxo
legado; o output TWRP/RAW da Alpha 3.2 continua separado e restrito a
SM-G973F / beyond1lte.

## Gatilhos e proteções da via experimental

- Preparação S10+ exige `BEYOUD_OUTPUT_FORMAT=artisan-ota`; o default TWRP não
  é aceito para beyond2lte. O formato também fica registrado no marcador da
  workspace e nos checkpoints.
- O empacotador legado é selecionado somente para os candidatos Exynos
  SM-G973F / beyond1lte e SM-G975F / beyond2lte. Outras combinações falham
  fechadas.
- A validação estrutural exige `system.new.dat.br`, transfer lists e operações
  `block_image_update` correspondentes; valida o alvo de cada payload e rejeita
  imagens RAW de sistema de arquivos, imagens de recovery, `super` e comandos de
  redimensionamento/formatação/reparticionamento não auditados.
- O kernel histórico é ativado somente após conferir os arquivos do módulo com
  o manifesto Artisan pinado; a geração de `boot.img`, `dtb.img` e `dtbo.img`
  ainda não foi executada nem validada.
- O `postinstall.edify` histórico executa `e2fsck`/`resize2fs` em seis partições.
  A preparação o exclui do candidato apenas se ele corresponder byte a byte à
  referência retida e registra seu SHA-256. Um arquivo divergente interrompe a
  preparação. Nenhum resize, formatação ou reparticionamento automático é
  incluído.
- A checagem de capacidade é somente leitura e antecede as gravações do OTA;
  não certifica o layout físico do telefone. O perfil `content-sized` exige
  reparticionamento externo manual, baseado nos tamanhos finais, sem alterar
  automaticamente as partições.
- O doador continua pinado em `SM-S721B/EUX/S721BXXSFEZJ1`; esta mudança não
  altera o firmware doador nem os créditos/licenças/proveniência ArtisanROM e
  OneROM.

## Resultado do primeiro build S10+

O run [43628169508](https://github.com/juliermeleal55-stack/X-Nova-OS/actions/runs/43628169508)
passou pela validação de integração, compilação das ferramentas, download e extração
verificados dos firmwares S721B/EUX e G975F/AUT e pelos checks de identidade/layout.
Parou no preflight estrito, antes da compilação de kernel/APKs/JARs ou da geração
do OTA: vários hunks/âncoras não correspondiam às versões extraídas de
`framework`, Wi-Fi, `SettingsProvider`, `SecSettings` e `SystemUI`. Nenhuma
alteração foi forçada para satisfazer esses patches. O run não produziu ZIP de
ROM nem artifact OTA; só publicou `beyond2lte-alpha-build-diagnostics`.

O download desse artifact via `gh run download` também terminou em `EOF` no host
externo de armazenamento do Actions. As anotações do run confirmam as falhas,
mas não fornecem aqui o relatório integral. O ZIP Alpha 3 original continua
sem inspeção; não foi substituído por suposições como se fosse evidência.

A próxima tentativa ativa `experimental_patch_failures: true` explicitamente:
se a cobertura do preflight estiver completa, os erros ficam registrados como
`experimental-with-failures` e a pipeline pode tentar a compilação/empacotamento.
Isso **não** chama patches rejeitados de sucesso nem os força a aplicar. Falhas
de compilação, verificação de integridade, capacidade, identificadores ou
montagem/validação do pacote continuam bloqueantes. Um ZIP eventual ainda será
experimental e **UNTESTED**; divergências podem deixar alterações parciais,
causar regressões ou impedir o boot.

## Validações ainda pendentes

O pacote Alpha 3 real, layout/aliases físicos de partições do beyond2lte e
compatibilidade real de firmware/kernel/vendor não foram validados. Isso não
bloqueia a tentativa de build, mas impede alegações de instalação segura. A
confirmação do modelo SM-G975F já foi recebida. Não incluir nem modificar
recovery, não usar Odin/Heimdall e não interpretar testes estruturais como
validação de flash ou boot.

O primeiro run não produziu ZIP OTA; não houve flash, teste de boot ou validação
em hardware. O erro histórico `Failed to unmount /system: No such volume` não foi
reintroduzido: a via OTA não emite `unmount()` Edify incondicional.
