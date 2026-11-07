# Revisão do instalador — aguardando autorização para novo build

## Evidências e limites

A foto IMG-20261107-WA0222 mostra duas tentativas: a primeira executou o instalador e abortou no verificador; a segunda retornou `Invalid zip file format!` antes de imprimir o cabeçalho da ROM. São falhas distintas. Sem recovery.log e medições do aparelho, não há comprovação de qual partição falhou, nem de que houve falta real de espaço. A configuração de repartição fotografada não comprova que seus valores foram aplicados.

O pacote original passou pela verificação de CRC no coletor. A foto não permite concluir se o pacote da segunda tentativa foi reempacotado incorretamente, truncado na transferência, trocado pelo contêiner externo do Actions ou rejeitado por outro motivo do recovery. Não se atribui esse erro a uma causa específica sem log.

## Alterações propostas e implementadas no código

1. **Mensagem final correta:** substituída a afirmação genérica `Partition too small` por falha de verificação com indicação de `/tmp/partition-layout-check.log` e `recovery.log`.
2. **Diagnóstico por partição:** o helper registra nome, caminho configurado para gravação, tamanho requerido, tamanho real quando disponível e leitor utilizado.
3. **Falhas separadas:** `ERR_MISSING` para dispositivo de bloco ausente; `ERR_READ` para capacidade ilegível; `ERR_TOO_SMALL` somente após uma medição válida menor que a imagem. Uma falha de leitura não é mais descrita como falta de espaço.
4. **Leitores compatíveis:** tenta `blockdev --getsize64`, depois os applets de busybox e toybox. Se necessário, resolve o bloco e consulta `/sys/class/block/<bloco>/size`, convertendo setores de 512 bytes com awk. Se nenhum método funcionar, falha explicitamente, sem inventar tamanho.
5. **Comparação sem overflow de inteiros do shell:** a comparação é decimal, dígito por dígito, para não depender de suporte aritmético de 64 bits em shells de recovery. Os requisitos continuam sendo os bytes finais das imagens, não limites fixos stock/ExtremeROM.
6. **Relatório completo:** verifica todas as partições declaradas e só então retorna falha se qualquer uma falhar. Não interrompe o diagnóstico na primeira partição.
7. **Alvos preservados:** consulta o mesmo caminho que o instalador usará para gravar. Não substitui silenciosamente os destinos por outros aliases nem cria links em /dev.
8. **ZIP mais estrito:** além do teste de CRC já existente, o coletor rejeita entradas duplicadas, arquivos criptografados, compressões diferentes de Store/Deflate e componentes obrigatórios vazios. Isso detecta classes de empacotamento incorreto, mas não garante compatibilidade com qualquer recovery nem impede corrupção após o download.
9. **Novos testes:** cobrem system de 15 GiB contra requisito de 8481766531 bytes, números acima de 4 GiB, igualdade, zeros iniciais, product pequeno, ODM ausente, leitura ilegível, alternativas busybox/toybox/sysfs e ZIPs ambíguos/incompatíveis. Não são medições reais do aparelho.

## O que não mudou

- Nenhum novo build da ROM foi solicitado nesta revisão; o arquivo de pedido de alpha não foi alterado.
- O ZIP publicado, seu checksum, artefato e release não foram modificados.
- As imagens continuam dimensionadas pelo conteúdo; não há teto fixo de repartição no build solicitado.
- Não se removeu a proteção contra gravar imagem maior que a partição física.
- Não há repartição, formatação ou apagamento automático novo.
- Kernel, payload da ROM, propriedades Android e branding interno permanecem inalterados.
- As quatro alterações preexistentes e alheias à revisão ficaram fora do commit.

## Validação

Cópia limpa do HEAD com apenas as alterações desta revisão: **179 testes passaram**; **69 referências Artisan, 37 referências da integração adicional e 64 evidências de auditoria verificadas**. O helper passou em `sh -n`; a suíte também exercita o script gerado e a transformação do updater-script. A árvore local completa tem uma divergência preexistente em runtime_paths que afeta a importação de seu teste; essa mudança não faz parte desta revisão nem foi enviada com ela.

Ainda pendente: aprovação do proprietário para solicitar outro build e teste real do instalador no recovery. Não há confirmação de correção em hardware nem garantia de boot.
