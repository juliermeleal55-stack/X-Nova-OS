# Build por etapas — ZIP de ROM para TWRP

## Contrato da Alpha 3.2

O fluxo experimental para **Galaxy S10 Exynos SM-G973F / `beyond1lte`** monta
um único ZIP de ROM que usa a interface `META-INF/com/google/android/update-binary`
do TWRP. O ZIP carrega imagens RAW expandidas, o instalador e verificações
estruturais. **Não inclui nem modifica o recovery**. Não usa o empacotador OTA
`new.dat.br`/`transfer.list`.

- Artefato principal: `out/twrp-zips/<codename>/*.zip`.
- Imagens intermediárias e validação: `out/raw-images/<codename>/*.img` e
  `out/raw-image-proof/<codename>.json`; não são enviadas como artefato separado.
- Prova privada do ZIP: `out/twrp-zip-proof/<codename>.json`; fica fora do ZIP
  final e do artefato de instalação.
- O ZIP do Actions pode vir dentro de um ZIP de transporte; o arquivo de ROM
  instalável está dentro dele.
- É um pacote experimental, sem assinatura externa e **não testado no TWRP ou
  em hardware**. Isso não é uma recomendação para instalar o candidato atual.

O método escolhido é instalar o ZIP pelo TWRP. O instalador usa a interface
Android `update-binary`, exige ferramentas e recursos presentes no recovery,
verifica o modelo `SM-G973F`, capacidade e estado desmontado das partições,
valida os hashes das imagens antes de qualquer escrita e faz leitura/hash após
cada gravação. A rotina não formata, não redimensiona, não reparte e não grava
`recovery`, `userdata`, modem ou EFS. As gravações não são atômicas; falha ou
interrupção depois do início pode deixar o aparelho sem boot. O instalador também
exige userdata montada e espaço livre para armazenar temporariamente todas as
imagens. A assinatura do ZIP pode ser exigida por configurações específicas do
TWRP; este candidato não recebe assinatura externa.

A Alpha 3.1 e seus artefatos históricos permanecem inalterados.

## Imagens do alvo e limites da auditoria

A configuração fixada declara layout estático (`TARGET_SUPER_PARTITION_SIZE=0`),
ext4 e `TARGET_HAS_SYSTEM_EXT=false`. O pacote exige `system.img`, `vendor.img`,
`product.img`, `boot.img`, `dtb.img` e `dtbo.img`. `system_ext` deve estar
incorporado em `system`, não ser criado como imagem separada. Outras imagens
filesystem (`odm`, `prism`, `optics`, `vendor_dlkm`, `odm_dlkm`, `system_dlkm`)
e componentes de boot (`init_boot`, `vendor_boot`) só são incluídos se a árvore
e o perfil do firmware confirmarem esses papéis. A validação rejeita imagens
inesperadas, sparse não expandidas e payload OTA.

A lista provém das fontes/configuração do builder, não de uma auditoria atual da
tabela física de um telefone. Alpha 3.2 #25 confirmou que o firmware stock alvo
fornece `boot.img` e `dtbo.img`, mas não `dtb.img`: o marcador `disable` do
módulo `extremekrnl` fazia o executor pular o hook de kernel. A preparação foi
corrigida para preservar esse marcador em `reference/onerom-upstream/` e ativar
o hook pinado somente no workspace SM-G973F. Alpha #26 avançou até o
empacotamento e rejeitou o `dtb.img` por cabeçalho. A causa está no validador:
o kernel fixado usa `mkdtimg cfg_create`, que envolve FDTs em uma imagem Android
DT table com magic `d7b7ab1e`; o código esperava `d00dfeed`, a magic de um FDT
isolado. Os validadores RAW e ZIP foram corrigidos para exigir o magic da DT
table emitida pelo builder e rejeitar um FDT isolado. A próxima execução precisa
confirmar o pacote inteiro. Nada disso audita a tabela física ou comprova
instalação/boot; o instalador consulta as capacidades expostas pelo TWRP e falha
se não confirmar os destinos.

## Etapas e reprodução local

Requer Linux, dependências host do workflow, Java 17, Rust/Cargo compatíveis e
bastante espaço em disco: durante `package`, as imagens RAW intermediárias e o
ZIP sem compressão coexistem, além de arquivos temporários. Prepare o workspace
em destino novo, fora deste repositório.

```bash
export WORKSPACE="$HOME/beyoud-work-s10"
export BEYOUD_OUTPUT_FORMAT=twrp-zip
export BEYOUD_ALPHA_VERSION=3.2
python3 scripts/prepare_workspace.py "$WORKSPACE" --target beyond1lte --discard-archive
python3 scripts/init_workspace_dependencies.py "$WORKSPACE"
bash scripts/build_smart_downloader.sh "$WORKSPACE"
bash scripts/probe_firmware.sh "$WORKSPACE"

# Execute em ordem e pare ao primeiro erro.
BEYOUD_JOBS=1 bash scripts/build_candidate.sh "$WORKSPACE" dependencies
BEYOUD_JOBS=1 bash scripts/build_candidate.sh "$WORKSPACE" source
BEYOUD_JOBS=1 bash scripts/build_candidate.sh "$WORKSPACE" target
BEYOUD_JOBS=1 bash scripts/build_candidate.sh "$WORKSPACE" patch
BEYOUD_JOBS=1 bash scripts/build_candidate.sh "$WORKSPACE" retire
BEYOUD_JOBS=1 bash scripts/build_candidate.sh "$WORKSPACE" package
python3 scripts/validate_twrp_zip.py "$WORKSPACE"
```

- `source` e `target` baixam e extraem firmware conforme o lock e o modelo.
- `patch` executa o builder Artisan/OneROM com `--no-rom-zip`; evita o gerador
  legado OTA/recovery. O ZIP TWRP deste fluxo é montado separadamente, a partir
  das imagens RAW verificadas.
- `retire` preserva os identificadores/provas antes de remover somente as
  árvores extraídas gerenciadas em `out/fw`.
- `package` gera e valida imagens RAW, monta o ZIP TWRP e grava uma prova privada.
  O pacote precisa conter exatamente as imagens suportadas, o atualizador TWRP,
  os guards de capacidade/montagem e a proveniência esperada.

O estágio é fail-closed e não substitui outputs existentes. Se um ZIP ou uma
prova anterior existir e não corresponder ao build atual, preserve os arquivos e
use workspace nova em vez de sobrescrever evidência.

## Verificações e estado

Os testes do empacotador e do instalador usam arquivos sintéticos e mocks; não
chamam TWRP, não abrem dispositivos de bloco e não fazem flash. Após a correção,
**330/330 testes** passaram; `verify_reference.py`, `verify_audit.py`,
`verify_onerom_port.py`, `compileall`, validação JSON, `bash -n` e
`git diff --check` também passaram. A suíte inclui imagens DTB sintéticas com
cabeçalho válido e rejeita DTB ausente/inválido. Ela não compila o kernel real.
A Alpha 3.2 #25 falhou no empacotamento e não produziu ZIP. A próxima execução,
com o hook ativo, ainda precisa confirmar o build e o ZIP; não houve instalação,
flash nem boot testado.
