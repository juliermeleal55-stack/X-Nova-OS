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

## Próximos bloqueios

Antes de iniciar build: inspecionar o ZIP Alpha 3 real, auditar o firmware e o
layout/aliases de partições do beyond2lte e revisar o updater legado. A
confirmação do modelo SM-G975F já foi recebida. Não incluir nem modificar
recovery, não usar Odin/Heimdall e não interpretar testes estruturais como
validação de flash ou boot.

Até aqui não houve build S10+, flash, teste de boot ou validação em hardware.
O erro histórico `Failed to unmount /system: No such volume` não foi reintroduzido:
a via OTA não emite `unmount()` Edify incondicional.
