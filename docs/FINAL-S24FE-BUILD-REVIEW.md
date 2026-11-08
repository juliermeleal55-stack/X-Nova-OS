# Revisão geral antes do build completo S24 FE

## Autorização e configuração

O proprietário autorizou iniciar o build completo experimental, após a análise dos patches e do instalador. O pedido está em `.github/workflows/s10-alpha-request.yml`:

- alvo **SM-G973F/beyond1lte**, kernel/vendor e correções nativas de câmera S10/Exynos 9820;
- sistema/framework doador **SM-S721B/EUX/S721BXXSFEZJ1**;
- `diagnostic_only: false`: agora inclui kernel, assembly/reconstrução de APK/JAR, imagens e ZIP;
- `experimental_patch_failures: true`: coleta e continua após falhas individuais de patch/módulo, sem apresentá-las como sucesso;
- `partition_layout: content-sized`: nenhuma capacidade fixa stock/ExtremeROM/7 GB é usada como teto do build;
- um ZIP completo e sidecars, sem reparticionamento automático e sem recompactação manual após a geração.

## Estado exato das correções

Base revisada: `eac111f8c82d6d87585db10207890b52dc9f9359`. A revisão usou uma cópia limpa dessa revisão do Git, preservando as alterações locais preexistentes e evitando que cópias locais antigas revertessem as correções já publicadas.

Estão ativos o decoder de unidades DEX lógicas com inventário de descritores, os dois equivalentes ópticos próprios, a correção lógica do downgrade e o lote de assinatura restrita/DualAP serviço+UI/vibração virtual. Esse último lote tem evidência isolada em [S24-FE-SCOPED-FIXES.md](S24-FE-SCOPED-FIXES.md).

**Não foram corrigidos todos os erros.** Existem 15 itens conhecidos daquele conjunto ainda sem rebase validado: resolução/CoreRune; resolução/GameManager; HDR/Settings; HDR-EAD/SettingsProvider; cutout; Extra Dim/Settings e SystemUI; Knox attestation; hotspot/país; PIN/serviço; zipped overlays; Photos; PIN/Settings; gestos/Settings e SettingsProvider. Não criamos classe fictícia nem removemos controles de país/permissão para simular sucesso. O build autorizado é experimental e sua própria passagem de patches deve produzir a nova contagem; não presumimos 39 sucessos/15 falhas como resultado medido.

## Instalador: o que foi verificado e o que não podemos prometer

Os dois problemas históricos são diferentes: o erro de capacidade anterior e `Invalid zip file format` depois da edição manual do ZIP. Não foi demonstrada a causa específica do segundo.

O código atual:

1. gera `REQUIRED-IMAGE-SIZES.json` com bytes lógicos das imagens, não tamanho comprimido;
2. coloca a verificação de capacidade antes das gravações das imagens;
3. compara com a capacidade física lida no aparelho, sem usar valores stock como teto;
4. tenta blockdev, busybox, toybox e sysfs; usa comparação decimal para evitar overflow de shell 32-bit;
5. distingue partição ausente, leitura impossível e capacidade comprovadamente insuficiente, com nome/caminho/bytes no log;
6. valida CRC de todos os membros do ZIP, compressão suportada, ausência de entradas duplicadas, componentes do instalador, payload e afirmação do modelo correto antes de publicar;
7. produz checksum SHA-256 do ZIP entregue.

**Não podemos garantir que o instalador nunca bloqueará.** Ele deve bloquear se a imagem realmente não couber ou se a capacidade não puder ser verificada. Sem medidas reais do aparelho não há prova de que as partições comportam o pacote. O proprietário fará o dimensionamento físico depois; o build não reparticiona. O objetivo é evitar falsos limites/diagnósticos e pacote adulterado, não liberar uma escrita que ultrapasse a partição.

## Reconstrução/assinatura e continuidade

O bridge exige pacote+caminho preinstalado+certificado, confere marcador, métodos, callers e recibo. A montagem dos DEX respeita unidades independentes e a presença/unicidade das classes originais. Esses contratos não foram substituídos por uma liberação global.

Falhas conhecidas de aplicação podem ser toleradas para o teste experimental. **Compilador, montagem DEX, assinatura inválida, geração de imagem e ZIP corrompido continuam sendo erros fatais.** Uma ROM incompleta não deve ser publicada como pacote concluído. O novo build será o primeiro teste completo de reconstrução desse conjunto de alterações; sucesso não está garantido.

## Validação prévia realizada

- **238 testes passaram** em uma cópia limpa da revisão acima, incluindo testes do helper de recovery, geração do guard antes das gravações, tamanhos acima de 4 GiB, ausência de teto fixo e rejeição de ZIP ambíguo/corrompido.
- **69 referências Artisan, 37 referências adicionais e 208 evidências de auditoria/build** verificadas por hash/tamanho.
- Sintaxe de todos os scripts shell de referência/integração/scripts conferida com `bash -n`, sem executá-los.
- A inspeção confirmou o caminho full-build e a tolerância experimental explícita, mantendo as validações de assinatura e pacote.
- Foi acrescentada a preservação dos inventários DEX nos artefatos diagnósticos do build completo.

Ainda não há resultado deste build, instalação ou boot validado. O Alpha anteriormente publicado não foi alterado. Branding interno estável permanece para uma etapa futura.

## Execução iniciada

Build completo [42439039231](https://github.com/juliermeleal55-stack/X-Nova-OS/actions/runs/42439039231), revisão `1d6a34e`. Na primeira conferência o job `build / alpha` estava em andamento, a etapa **Validate integration passou**, e o runner instalava as dependências. Ainda não havia kernel, imagem ou ZIP concluído; o resultado final deve ser lido nessa execução, não presumido por esta autorização.
