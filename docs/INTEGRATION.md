# Integração atual: Artisan S10, doador S24 FE e árvores OneROM

## Escopo do workspace

A **ArtisanROM histórica**, fixada em
`5638a7f66cdf8bc9dd43f087a96f7dfa4f9e6954`, continua sendo a base do build. O
alvo padrão é o Galaxy S10 normal **SM-G973F / `beyond1lte` / Exynos 9820**.
S10+, S10e e Snapdragon não são inferidos como suportados.

Em workspaces novos `beyond1lte`, o preparador importa as árvores completas do
OneROM fixado em `644f0aacc49ad2410e566de8deb05e6c8211d83d`:
`target/beyond1lte/` e `platform/exynos9820/`. São 474 blobs e 326.008.869 bytes
brutos. O repositório conserva os 283 arquivos textuais e os metadados de todos
os blobs; os 191 itens não textuais são obtidos pelo checkout Git filtrado no
momento da preparação, não adicionados ao Git.

O importador compara todos os caminhos, tamanhos e Git blob SHA-1 com o
manifesto antes de alterar o workspace. Arquivos Artisan substituídos são
preservados em `reference/artisan-before-onerom/`; originais OneROM de arquivos
adaptados pelo projeto e o `postinstall.edify` upstream ficam em
`reference/onerom-upstream/`, junto a créditos, licença e recibo. A importação
preserva inicialmente todos os marcadores upstream `disable` exatamente. Para o
build **SM-G973F / `beyond1lte`**, a preparação conserva o marcador original do
módulo `extremekrnl` em `reference/onerom-upstream/` e remove somente o marcador
ativo depois de instalar o hook de kernel pinado do projeto: o executor pula
`customize.sh` quando o marcador está presente, mas o firmware alvo extraído não
fornece `dtb.img`. Os outros módulos desabilitados mantêm seus marcadores ativos.
O hook exige os três artefatos e o empacotador continua validando os cabeçalhos;
veja [`ONEROM-AUDIT.md`](ONEROM-AUDIT.md) para a proveniência e limites.

**Limites de instalação:** o `target/beyond1lte/postinstall.edify` da OneROM
não substitui o recipe de instalação Artisan ativo. Nenhuma imagem/código de
recovery é modificada. A importação não publica uma ROM, não faz flash e não
afirma compatibilidade funcional. O módulo adaptador próprio de
`search_indexing` continua fora do build; o módulo upstream é importado com seu
marcador `disable` preservado.

## Doador e adaptações do projeto

O perfil declarativo selecionado para workspaces novos é **S24 FE
SM-S721B/EUX**, proveniente de código de referência OneROM/UN1CA. Essa
configuração continua pendente de confirmação no firmware extraído; seu SDK,
versão e propriedades não são certificados pelo perfil. O preparador lê o SDK
real do `build.prop` do doador para limitar o caminho histórico de Bluetooth.
Isso não transforma a configuração de um aparelho em prova de compatibilidade.

A base de build continua sendo Artisan; o perfil ativo do S10 vem da árvore
OneROM importada e é restringido a assertion de **somente SM-G973F**. O
preparador remapeia `TARGET_SINGLE_SYSTEM_IMAGE="r12s_native"` para o alias
Artisan `essi`, que seleciona o adaptador doador ativo
`unica/configs/essi_64.sh`; o config `r12s_native` não é instalado como imagem
ativa. Assim o workspace usa o fluxo Artisan sem perder a proveniência da árvore
OneROM. O kernel compilado continua sendo tratado pelo fluxo fixado do projeto;
os arquivos OneROM de kernel continuam presentes no workspace com a proveniência
registrada. Não há modificação do recovery nem autorização de instalação.

## Reproduzir a preparação

Requer Linux, Python >= 3.9, curl, Git, Bash e as dependências originais da
ArtisanROM. O arquivo Artisan tem aproximadamente 1,4 GiB comprimido; o
workspace recebe também os arquivos da portagem OneROM e precisará de espaço
adicional significativo. O destino deve ser novo e ficar fora deste repositório.

```bash
python3 scripts/prepare_workspace.py /caminho/externo/beyoud-workspace
python3 scripts/init_workspace_dependencies.py /caminho/externo/beyoud-workspace

# As etapas de build permanecem separadas e opcionais:
BEYOUD_JOBS=1 bash scripts/build_candidate.sh /caminho/externo/beyoud-workspace dependencies
bash scripts/build_candidate.sh /caminho/externo/beyoud-workspace source
bash scripts/build_candidate.sh /caminho/externo/beyoud-workspace target
```

A preparação não executa o build. Consulte [`BUILD-STAGES.md`](BUILD-STAGES.md)
para as etapas opcionais. Nenhuma mudança de código aqui aprova uma publicação,
um recovery ou um flash.

## Verificação registrada

A portagem de fontes foi exercitada em uma workspace temporária contra a revisão
OneROM fixada: **474 caminhos e 326.008.869 bytes**, todos conferidos por
caminho/tamanho/Git blob SHA-1; módulos e cópias protegidas de instalador foram
verificados estruturalmente. Isso não foi build da ROM nem teste no aparelho.

Verificações host após a correção do hook de kernel: **329 testes** passaram;
`verify_reference.py` confirmou 69 blobs Artisan e 37 referências OneROM;
`verify_audit.py` confirmou 494 arquivos, e `verify_onerom_port.py` verificou
286 arquivos de fonte/proveniência OneROM. A suíte inclui a regressão que prova
que o executor já alcança o hook ativo e que o marcador upstream continua
preservado. Também passaram `compileall`, validação JSON, `bash -n` e
`git diff --check`. São verificações de fontes/proveniência e fixtures, não
compilação real do kernel nem validação funcional no telefone.

As atribuições e limites de redistribuição das fontes OneROM estão em
[`ONEROM-AUDIT.md`](ONEROM-AUDIT.md). GPL para código-fonte não concede, por si
só, direitos de redistribuição de cada APK, biblioteca, imagem ou outro ativo
proprietário importado para a workspace.

## Saída experimental Alpha 3.2

A entrega planejada é **um ZIP de ROM instalável pela TWRP**, com imagens RAW
`.img` e `META-INF/com/google/android/update-binary`. O instalador usa a
interface padrão de atualização do TWRP; não empacota nem modifica TWRP/recovery.
O ZIP não usa OTA `new.dat.br`/`transfer.list` e não contém imagem de recovery.

Para `beyond1lte`, são exigidos `system`, `vendor`, `product`, `boot`, `dtb` e
`dtbo`; `system_ext` fica integrado a `system` segundo a configuração do alvo.
Outras partições só são incluídas quando a árvore e os metadados provam que são
necessárias. Os `.img` são intermediários validados; a entrega é o ZIP. Provas,
proveniência e SHA-256 ficam fora do artefato em `out/twrp-zip-proof/` e
`out/raw-image-proof/`.

O pacote ainda não foi construído nem testado no TWRP/aparelho; não há flash nem
boot validados. A origem de `dtb.img` e do chamado `build_fs_image.sh` continuam
pendentes de confirmação, e a lista de partições declarada não é uma auditoria
da tabela física do telefone. A Alpha 3.1 histórica não é reempacotada.
