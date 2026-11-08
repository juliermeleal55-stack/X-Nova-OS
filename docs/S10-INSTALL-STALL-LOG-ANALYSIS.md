# SM-G973F — análise dos logs fornecidos após instalação parada em 3%

## Resultado: causa do travamento ainda não determinada

Arquivos analisados: `recovery.log` (33.826 bytes) e `kernel-recovery.log` (528.530 bytes). Os arquivos originais não são publicados neste repositório, pois incluem identificadores privados.

### Evidência efetivamente presente

- Recovery: **TWRP 3.7.1_12-ExtremeXT_v4**, kernel recovery 4.14.356-openela-rc1-ExtremeKernel-TWRP+, compilação de agosto de 2025.
- `recovery.log`, linha 1: inicialização do TWRP. Até a linha 945, apenas inicialização/menu e gerenciamento da tela. Não há início de instalação, nome de ZIP selecionado, execução de update-binary, `Patching system`, relatório de capacidade ou E1001.
- O log do kernel começa em uptime 0 e termina em aproximadamente **142,82 segundos**. Portanto, não registra por si só uma instalação prolongadamente parada. Não prova quando/por que houve eventual reinicialização.
- Kernel, linhas 5664, 5833 e 6156: `erofs: (device sda25): find_target_block_classic: corrupted dir block 0 @ nid 1151`. O primeiro evento ocorre em aproximadamente 12,63 segundos, durante a inicialização/montagem da imagem presente.
- Recovery, `/system_image`: **15360 MB** de capacidade reportada para `/dev/block/sda25`. `/system_root`: filesystem EROFS reportado como **5211 MB**. São medidas diferentes: não interpretar `Free: 0MB` de EROFS somente-leitura como partição fisicamente cheia. O tamanho lógico exigido pela imagem final deve ser comparado com a capacidade física, não com o espaço livre do filesystem antigo/parcial.
- Kernel, fim da captura: bateria em **3%**, carregando por USB. Isso é risco para uma próxima gravação, mas não prova ser a causa da parada da foto anterior.
- Não encontrados, nessa captura, eventos explícitos de OOM/`Killed process` do instalador, erro de I/O do armazenamento ou crash de update-binary. A mensagem genérica libprocessgroup no boot não identifica um instalador morto.

### O que significa o erro EROFS

Confirma que **este kernel de recovery não conseguiu interpretar corretamente um diretório da imagem atualmente presente**. É compatível com imagem parcialmente gravada/corrompida ou problema de compatibilidade do leitor; não distingue essas hipóteses, nem prova que o ZIP publicado esteja corrompido. Não autoriza formatar, trocar filesystem, desativar verificações ou atribuir o travamento aos patches Smali.

### Revisão do instalador do build publicado

Fonte do build: `1d6a34ebc5f0cd5deec3c2d3c5221d27f447f1a2`.

- A mensagem fotografada precede `block_image_update(..., system.transfer.list, system.new.dat.br, system.patch.dat)`.
- A política usa Brotli para o payload e verificação física antes das gravações.
- O sucesso das verificações de ZIP no runner não comprova a integridade da cópia local, compatibilidade com esse recovery ou escrita no aparelho.
- Logs recebidos **não contêm a execução dessa chamada**. Não há base para declarar uma correção de ROM validada, substituir o update-binary ou iniciar um rebuild como se a causa já fosse conhecida.

## Próximo passo sem reinstalar nem apagar dados

Primeiro tente recuperar os logs da tentativa anterior, ainda no recovery:

```sh
adb pull /cache/recovery/last_log last_log.txt
adb pull /cache/recovery/log cache-recovery.log
adb pull /cache/recovery/last_log.1 last_log-1.txt
```

Arquivo ausente é um resultado possível. Não montar/formatar `/cache` para tentar criar esses arquivos, nem iniciar outra instalação só para coletar. Não reiniciar antes da coleta.

Alternativamente, use o coletor Python deste repositório no computador com ADB e o telefone no recovery:

```sh
python scripts/collect_recovery_stall.py
```

Se ADB não estiver no PATH, por exemplo no Windows:

```sh
python scripts/collect_recovery_stall.py --adb C:\platform-tools\adb.exe
```

O coletor lê logs atuais/retidos, dmesg, processos, memória, mounts e duas amostras de contadores de disco separadas por 15 segundos. Não reinicia, não mata processos, não monta, não formata e não escreve em partições do aparelho. Erros/arquivos ausentes ficam registrados no manifesto; cada chamada ADB tem timeout. Gera `recovery-stall.zip` no computador; pode conter dados privados, portanto enviar apenas para diagnóstico, não publicar em issue/release aberta.

Se não houver logs anteriores, será necessária uma captura durante uma tentativa monitorada, somente depois de carregar a bateria e avaliar o estado atual. Não é recomendação para repetir o flash imediatamente.

## Estado da correção

**Análise e coleta melhorada implementadas; defeito causador do travamento não localizado. Nenhuma alteração no payload/instalador da ROM, nenhum rebuild disparado e nenhuma alegação de boot corrigido.** A próxima correção deve ser direcionada pelo erro da instalação real, não pelo percentual da interface.
