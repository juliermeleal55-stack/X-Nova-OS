# Novo instalador X-Nova RAW v1 — candidato separado, sem novo build de ROM

## Estado

A pedido do proprietário, **Alpha 3.1 / execução 42696050466 foi cancelada**. O cancelamento direto retornou 403; o workflow restrito `stop-alpha31.yml`, com actions:write somente para esse run, terminou com sucesso e a API confirmou `completed / cancelled`.

**Nenhum novo build de ROM foi solicitado para este instalador. Ele não está ligado ao gerador de ZIP/release atual e não está aprovado para flash.** Foi implementado como candidato separado para análise/testes antes de autorizar integração ou nova compilação.

## Análise do caminho anterior

O updater antigo chama `block_image_update` com `transfer.list` e `new.dat.br`. A parada original em 3% não ficou registrada nos logs entregues inicialmente, portanto sua causa não está comprovada. O erro EROFS ao ler o system atualmente presente pode ser consequência de gravação parcial ou incompatibilidade e permanece separado.

Na Alpha 3, a desmontagem Edify incondicional de `/system` introduzida pela integração abortou com `No such volume`; a regressão foi identificada nos logs reais e corrigida no código. O novo candidato elimina toda essa dependência Edify em vez de apenas mudar um banner.

## Arquitetura implementada

- **Shell entrypoint próprio** (`update-binary.sh`), protocolo de UI do recovery. Sem binário OTA antigo, Edify, `block_image_update`, Brotli ou img2sdat.
- Payloads **RAW** preservando os bytes das imagens prontas: não altera kernel/vendor, APKs, chaves, permissões ou metadados internos do filesystem.
- Gerador separado (`scripts/build_raw_installer.py`): aceita imagens de um build concluído, converte sparse no host quando necessário, executa o verificador de filesystem real e cria um único ZIP, sem compressão de imagens. Registra tamanho e SHA256 por imagem.
- **Modelo exclusivo SM-G973F**, root, ferramentas e bateria >=30% verificados antes da preparação. Não desbloqueia bootloader nem contorna assinaturas.
- Exige `/data` já montado como ext4/f2fs. Cria staging privado em `/data/local/tmp`, rejeita symlinks e confere espaço livre para TODAS as imagens mais reserva. Não extrai imagens de vários GB para RAM e não monta/formata/decripta dados automaticamente.
- Testa ZIP64 com uma entrada pequena colocada no final do arquivo, testa opções exatas de dd em arquivo privado e exige shell com pipefail.
- **Antes da primeira gravação:** valida manifesto, nomes/duplicações/ordem, capacidades, mounts e colisões de aliases; extrai TODOS os payloads, confere tamanho e SHA256. Falha de ZIP, espaço, ferramenta ou hash termina antes de escrever partições.
- Reutiliza o helper de capacidade somente-leitura já testado, agora incluindo boot/dtbo. Alvo ainda montado, ausente ou sem capacidade legível bloqueia. Não chama unmount em aliases inexistentes.
- Escrita em trechos de **32 MiB**, com `fsync`, progresso após cada trecho e timeout de 180 s por chamada. Código 124 fica identificado como timeout. Capacidade/mounts são rechecados antes de cada partição.
- **Leitura de volta** do número exato de bytes e SHA256 após cada imagem, com timeout. Só passa à próxima partição se a verificação for bem-sucedida. DTBO/boot ficam no final; boot obrigatoriamente por último.
- Mantém log de fases/comandos em `/tmp/xnova-installer.*.log` e staging privado em `/data/local/tmp/xnova-stage.*`. Nenhum log usa número de série deliberadamente. Preserva staging para análise; não faz limpeza recursiva de userdata.

## Limites e riscos ainda existentes

**Instalação não é atômica.** Falha/queda de energia durante escrita pode deixar o aparelho sem boot; não existe rollback prometido. Timeout limita espera, não desfaz gravação parcial. Leitura de volta prova bytes, não que o kernel conseguirá montar EROFS ou que o Android iniciará.

Ferramentas `unzip` (incluindo ZIP64 real), timeout, dd com fsync, shell/pipefail e acesso ao dispositivo precisam ser validados no TWRP real. Preflight rejeita ferramentas incompatíveis, mas os testes em Linux não substituem essa validação. O probe ZIP64 testa indexação/local header; a integridade de cada payload gigante só é aceita após extração/tamanho/hash completos.

O staging exige espaço livre adicional em userdata aproximadamente igual à soma das imagens. O ZIP RAW será maior que o pacote Brotli e pode ainda ocupar esse mesmo armazenamento. Não há teto stock/ExtremeROM/7 GB: a limitação continua sendo capacidade física real e espaço de staging. Não é fornecido PIT/reparticionamento.

O novo gerador **não faz assinatura externa do ZIP** nem incorpora todas as rotas atuais de OTA, cleanup/postinstall e proveniência do pipeline automaticamente. Não executa scripts arbitrários de expansão e não aplica resize2fs a EROFS. Essas diferenças precisam ser revisadas antes da integração; não é um substituto de produção já ativado. Não orientar o usuário a desativar verificações para usá-lo.

O gerador confere filesystem com ferramentas do host; isso não certifica compatibilidade com o leitor EROFS antigo do recovery/kernel. A causa original da parada em 3% continua não comprovada.

## Testes executados

Testes novos usam ZIP/unzip, hashes, dd, timeout, leitura e escrita de **arquivos temporários reais**, nunca dispositivos de bloco:

- Staging completo e comparação de todos os bytes extraídos.
- Manifesto inválido, nome perigoso, duplicação, tamanho/hash/ordem incorretos.
- Hash incorreto impede chegar à fase de escrita.
- Escrita real de **32 MiB + trecho parcial**, SHA256 da leitura de volta e preservação dos bytes além do fim da imagem.
- Simulação de timeout de dd: nenhum byte do alvo de teste muda.
- Simulação de hash de leitura de volta divergente: interrompe antes de vendor/boot.
- Gerador recusa roles de recovery/data/EFS, base insegura e sobrescrita de pacote existente; remove pacote parcial em falha de fsck.
- Sintaxe dos dois scripts checada.

**Os filesystems das fixtures do gerador são sintéticos; apenas o fsck dessas fixtures é mockado.** O teste de escrita usa arquivos comuns e substitui a checagem física no harness, sem adicionar flag de bypass ao instalador de produção. Isso não é teste no S10 nem prova de segurança do flash.

## Uso de desenvolvimento, não recomendação de instalação

Somente depois de obter imagens de um build confiável e disponibilizar as ferramentas host fixadas:

```
python3 scripts/build_raw_installer.py --images /caminho/imagens --output /caminho/candidato.zip --experimental
```

São obrigatórias system.img, vendor.img, product.img, dtbo.img e boot.img. Outras roles permitidas são odm, prism, optics e system_ext, apenas quando houver alvo físico correspondente. Não passar imagens Odin do S24 FE: kernel/vendor/boot devem ser os já preparados para o S10.

Próximas etapas antes de qualquer ROM: validar ferramentas/ZIP64 no recovery sem gravar, revisar assinatura e integração, conferir disponibilidade real de staging, testar falhas em dispositivos de bloco descartáveis e só então solicitar autorização para build e teste de hardware. **Não gerar/publicar outra ROM automaticamente.**

## Resultado local desta implementação

**282 testes passaram** em export limpo; 69 referências Artisan, 37 adicionais e 208 arquivos de evidência conferidos; sintaxe shell aprovada. Dez testes novos exercitam o candidato. O CI remoto deve confirmar isso após o push; resultado remoto ainda não presumido.

Há também `integration/new_installer/probe-recovery.sh`, uma sonda opcional separada que apenas relata ferramentas/modelo/bateria/mount de data e testa dd/fsync em arquivo minúsculo privado em `/tmp`. Não escreve em partições, não monta, não formata e não prova suporte a ZIP64 gigante nem funcionamento do instalador. Serve à próxima fase de análise sem flash de ROM.
