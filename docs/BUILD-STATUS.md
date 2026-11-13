> **Fluxo atual:** consulte [BUILD-STAGES.md](BUILD-STAGES.md) e
> [CROSS-AUDIT.md](CROSS-AUDIT.md). As tentativas e comandos anteriores abaixo
> são históricos; não comprovam sucesso do fluxo atual.

# Estado de construção — histórico SM-G975F e portagem atual SM-G973F

> O bloco SM-G975F abaixo é um registro antigo, não o estado global do projeto.
> A branch contém artefatos Alpha anteriores para o SM-G973F; consulte o README
> e `docs/ALPHA-REPAIR-STATUS.md`. A portagem completa OneROM descrita ao fim é
> posterior a esses builds e ainda precisa de sua própria execução.

## Implementado no registro histórico SM-G975F

- Modelo SM-G975F confirmado pelo usuário e selecionado no perfil.
- Importados 68 textos originais da plataforma Exynos 9820 e do target
  beyond2lte: overlays, configuração, câmera, vendor, áudio, fstab, VINTF,
  integração de kernel e postinstall, para revisão/migração.
- Inventariados 251 arquivos dessas árvores com IDs de blobs e tamanhos.
- Localizado ExtremeKernel pela referência original da ArtisanROM e fixado
  commit no manifesto, sem alegar compatibilidade já testada.
- CI de integridade, testes Python e sintaxe shell (não compila ROM).

## Bloqueios reais ao build de ROM

1. A API dos módulos históricos não foi migrada para o build system seventeen.
   O diretório reference não é um target compilável.
2. Não há firmware doador nem firmware stock SM-G975F extraídos no ambiente.
   Também não há versão de firmware doador verificada como One UI 9.
3. O script build.sh do ExtremeKernel consultado usa clang-r547379 e baixa a
   toolchain de android.googlesource.com, host fora da allowlist desta sessão.
   A revisão foi fixada no manifesto; o script legado importado permanece
   intacto para fins de comparação, não como integração reproduzível.
4. Partições do aparelho, recovery, bootloader e compatibilidade de kernel/HALs
   com o novo framework não foram verificados.
5. Ambiente observado: ~20 GiB livres, 3.8 GiB RAM e sem swap. Não foi medido
   o espaço total necessário ao conjunto completo de firmwares e workdirs.

Na execução histórica descrita acima não foi iniciada compilação de firmware.
Isso não descreve os builds Alpha posteriores do SM-G973F; a CI e os ZIPs
anteriores continuam documentados separadamente. Nenhum build anterior valida a
portagem completa OneROM adicionada agora.

## Próxima implementação do registro histórico

Comparar os consumidores de config e helpers do build antigo e novo; migrar
primeiro extração e layout estático ext4 e depois módulos Exynos 9820. Fixar
firmwares reais, transitive dependencies e toolchain. Só executar make_rom
quando existir uma árvore integrada e revisada; uma mistura mecânica não
constitui port funcional.

## Estado atual deste branch — SM-G973F / beyond1lte

Os itens sobre SM-G975F/beyond2lte acima são registros históricos, não o alvo
atual. Workspaces novos usam **SM-G973F / beyond1lte** e mantêm Artisan como
base. O preparador importa todas as 474 entradas fixadas de
`target/beyond1lte/` e `platform/exynos9820/` da OneROM, incluindo os 191 itens
não textuais; cada caminho, tamanho e Git blob SHA-1 é verificado. Marcadores
`disable` são preservados; o `postinstall.edify` OneROM fica apenas em
`reference/onerom-upstream`; isso não ativa o recipe OneROM nem altera o
instalador Artisan original. A Alpha 3.2 empacota separadamente um `update-binary`
para TWRP; nenhum recovery é distribuído ou modificado.

Uma importação integral para workspace temporária foi conferida estruturalmente;
**não houve build da ROM, flash ou teste de boot/aparelho**. As verificações
host do repositório não são validação funcional. Veja `docs/INTEGRATION.md` e
`docs/ONEROM-AUDIT.md` para escopo, créditos e limites de redistribuição.

## Novo contrato de entrega — Alpha 3.2

O fluxo configurado gera um **ZIP de ROM instalável por TWRP** com imagens RAW
`.img`, um `update-binary` próprio e guards de capacidade/montagem/hash. Não
inclui nem modifica TWRP/recovery e não usa `new.dat.br`/`transfer.list`. As
imagens requeridas para beyond1lte são `system`, `vendor`, `product`, `boot`,
`dtb` e `dtbo`; outras partições só entram quando o alvo e o perfil as sustentam.
`system_ext` fica em `system` conforme a configuração.

Esta é uma alteração de código/configuração, não um build. O instalador foi
exercitado apenas com testes host sintéticos; nenhum build de firmware, ZIP
Alpha 3.2, instalação TWRP, flash ou boot em hardware foi executado/validado. A
origem de `dtb.img` e do script `build_fs_image.sh` ainda precisa ser confirmada.
A Alpha 3.1 histórica permanece intacta. Consulte [BUILD-STAGES.md](BUILD-STAGES.md).
