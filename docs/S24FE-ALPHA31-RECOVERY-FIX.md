# Alpha 3.1 — regressão de desmontagem confirmada no recovery

## Evidência recebida

`recovery-1.log` registra uma tentativa real via ADB sideload de um ZIP de 5.897.462.985 bytes:

```
Unmounting System...
ArtisanROM S10: preparing static partitions (no formatting/repartition).
Failed to unmount /system: No such volume
script aborted (no error message)
Updater process ended with ERROR: 1
I:Install took 1 second(s).
```

O script aborta na primeira chamada `unmount("/system")`, ANTES de extrair/executar o helper de capacidade e antes de qualquer chamada de gravação de imagem. A origem é a lista de desmontagens incondicionais introduzida pela integração Alpha 3, não espaço insuficiente nem falha comprovada de Brotli nesta tentativa. O próprio recovery já executa a desmontagem inicial de System e usa `/system_root` em sua tabela de volumes.

`kernel-recovery-1.log` também contém o erro EROFS de diretório da imagem já presente, desde cerca de 12,64 segundos do boot. Não demonstra que esta tentativa curta tenha gravado/corrompido system. Esse erro continua separado do aborto por alias e não foi declarado corrigido.

Os logs completos não são incluídos no Git porque contêm identificadores privados.

## Correção

- Removidas TODAS as chamadas Edify incondicionais a `/system`, `/system_root`, `/vendor`, `/product` e demais aliases. Não basta ignorar o retorno com `||`: esse updater pode abortar dentro da chamada ao encontrar volume inexistente.
- O TWRP continua responsável por gerenciar seus volumes/desmontagem, como no procedimento Artisan original.
- Mantido o helper somente-leitura que compara os dispositivos de bloco e bloqueia `ERR_MOUNTED` se o alvo ainda estiver montado; não é permitido escrever sobre filesystem montado.
- Mantidas as verificações de capacidade física, ausência/erro de leitura, origem exata do updater, fsck da imagem, Brotli integral, DEX e integridade ZIP.
- Nenhuma formatação, wipe de dados, repartição, troca de recovery ou edição manual de ZIP é necessária para corrigir esta regressão no código.

## Testes e alcance

Teste de regressão executa o gerador real do preâmbulo em bash e exige zero chamadas `unmount()`/`umount` emitidas, preservando a extração/execução obrigatória do helper. Os testes de alvo ainda montado e de tabela de mounts ilegível continuam exigindo bloqueio.

**272 testes passaram** em export limpo, mais verificações de referências/evidências e sintaxe shell. Não são teste de instalação em hardware nem prova de que a parada antiga em 3% esteja resolvida.

A versão corrigida será identificada publicamente como **Alpha 3.1**, com outro run/tag, preservando os bytes da Alpha 3 anterior. A pré-release anterior recebe aviso de defeito confirmado. O novo lançamento só pode ser criado após sucesso do novo build e suas verificações; não considerar o ZIP antigo corrigido.

## Validação DEX separada

O fluxo diagnóstico anterior `42637545811` terminou com falha na etapa de validação real; não é anunciado como validação completa bem-sucedida dos originais. O build Alpha 3 `42640447138` terminou com sucesso e incluiu os checks da sonda durante suas decodificações, mas esse fato não transforma o fluxo separado em sucesso. O motivo específico dessa falha diagnóstica ainda precisa ser inspecionado; não foi tratado como falha do instalador.
