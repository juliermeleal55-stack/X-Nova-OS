> **Fluxo atual:** consulte [BUILD-STAGES.md](BUILD-STAGES.md) e
> [CROSS-AUDIT.md](CROSS-AUDIT.md). O build S10 Alpha 3.2 #27 concluiu com
> sucesso a validação/entrega do ZIP no Actions; isso é validação de host,
> não de instalação, flash ou boot em aparelho.

# Estado de construção — S10 SM-G973F e candidato S10+ SM-G975F

> O registro histórico de pesquisa SM-G975F abaixo não é evidência de suporte.
> O build normal S10 #27 e o novo pedido S10+ são fluxos distintos, documentados
> separadamente. Consulte o README e `docs/ALPHA-REPAIR-STATUS.md`.

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
não textuais; cada caminho, tamanho e Git blob SHA-1 é verificado. Os
marcadores upstream são preservados; no workspace SM-G973F, somente o marcador
de `extremekrnl` é arquivado em `reference/onerom-upstream` e desativado no
módulo ativo para executar o hook de kernel pinado. O `postinstall.edify`
OneROM fica apenas em `reference/onerom-upstream`; isso não ativa o recipe
OneROM nem altera o instalador Artisan original. A Alpha 3.2 empacota
separadamente um `update-binary` para TWRP; nenhum recovery é distribuído ou
modificado.

O build S10 normal Alpha 3.2 #27 executou a integração completa do workspace
fixado e terminou com sucesso nas etapas de build, validação do TWRP ZIP e
upload do artifact. Isso comprova apenas o resultado host daquele commit/alvo;
**não houve flash nem teste de boot/aparelho**. Veja `docs/INTEGRATION.md` e
`docs/ONEROM-AUDIT.md` para escopo, créditos e limites de redistribuição.

## Novo contrato de entrega — Alpha 3.2

O fluxo configurado gera um **ZIP de ROM instalável por TWRP** com imagens RAW
`.img`, um `update-binary` próprio e guards de capacidade/montagem/hash. Não
inclui nem modifica TWRP/recovery e não usa `new.dat.br`/`transfer.list`. As
imagens requeridas para beyond1lte são `system`, `vendor`, `product`, `boot`,
`dtb` e `dtbo`; outras partições só entram quando o alvo e o perfil as sustentam.
`system_ext` fica em `system` conforme a configuração.

As execuções Alpha 3.2 #25 e #26 falharam em problemas diferentes de kernel/DTB.
A execução seguinte, [Build #27](https://github.com/juliermeleal55-stack/X-Nova-OS/actions/runs/43487807246),
concluiu com sucesso: etapas completas do build, validação do TWRP ZIP e upload
foram todas `success`. O artifact `14075714047` tem 7.382.847.089 bytes; seu
conteúdo não foi baixado neste sandbox, portanto o que se afirma é o resultado
registrado pelo Actions e pelos validadores do workflow. Não houve instalação
TWRP, flash ou boot em hardware; a Alpha 3.1 histórica permanece intacta.
Consulte [BUILD-STAGES.md](BUILD-STAGES.md).

## Solicitação separada do S10+ — SM-G975F / beyond2lte

A requisição S10+ foi comparada com o build completo S10 Alpha 3.2 bem-sucedido
[Build #27](https://github.com/juliermeleal55-stack/X-Nova-OS/actions/runs/43487807246).
Versão, doador S24 FE fixado, base Artisan, pipeline TWRP/RAW, tolerância
experimental de falhas de patch e perfil `content-sized` estão alinhados; o
alvo/codename, assets Artisan beyond2lte, hook de kernel e guarda de modelo do
instalador são específicos do S10+. Patches OneROM marcados como exclusivos de
beyond1lte não são copiados ao alvo S10+; os componentes comuns permanecem
pinados. Não há caps fixos nem reparticionamento/formatação automática. O TWRP
ZIP faz pré-checagem somente-leitura com os tamanhos reais das imagens e a
capacidade atual. Isso não verifica a tabela física do aparelho, instalação,
flash ou boot. O build S10+ continua experimental e não testado em hardware.

A [Build #7](https://github.com/juliermeleal55-stack/X-Nova-OS/actions/runs/44017401587)
faliu ao compilar ferramentas: o Gradle não resolveu
`com.vanniktech.maven.publish:0.33.0`. A falha ocorreu antes de baixar firmwares
ou criar pacote; validação do ZIP e upload foram ignorados. A nova tentativa,
[Build #8](https://github.com/juliermeleal55-stack/X-Nova-OS/actions/runs/44019396347),
passou pela compilação das ferramentas e estava baixando o firmware doador no
último check. Ainda não há ZIP S10+ validado. O workflow de validação de fontes
para o commit `3626d2f` concluiu com sucesso; isso não substitui o build.
