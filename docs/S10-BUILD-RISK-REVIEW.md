# Revisão de risco do build — Galaxy S10 SM-G973F

## Snapshot da execução acompanhada

- Workflow: [run 43117943493](https://github.com/juliermeleal55-stack/X-Nova-OS/actions/runs/43117943493), **Build #23 / Attempt 1**.
- Código testado pelo runner: `573a466a0a0b1645166edc3768ac291fc8cf2e6d`.
- Alvo: **SM-G973F / beyond1lte**; base de build Artisan, integração OneROM e doador S24 FE SM-S721B/EUX.
- Na consulta desta revisão, `Validate integration`, dependências do host, montagem do S10, inicialização das dependências, SmartDownload e verificação de metadados passaram. **`Compile build tools` ainda estava em andamento.** Nenhum download/extrato final de firmware doador/alvo, patch, kernel, imagem, ZIP ou upload do artefato tinha sido confirmado.
- A validação de fontes separada, run `43117943520`, passou. Isso não completa o build ROM.

O estado acima é uma fotografia da consulta, não o resultado final. A execução não deve ser declarada bem-sucedida até que o Actions termine e os artefatos/checagens do pacote sejam conferidos.

## Riscos que podem interromper ou comprometer o resultado

| Risco | Efeito possível | Controles existentes / leitura atual |
| --- | --- | --- |
| Compilação de ferramentas e recursos do runner | Erro de dependência, compilador, memória, espaço em disco ou limite de tempo | Job tem timeout de 360 minutos, coleta de espaço/diagnósticos e compilação serial. A montagem e dependências passaram; ferramentas ainda estavam compilando no último estado. |
| Firmware/serviços de download | AP/CSC indisponível, limitador/rede, divergência de modelo, CSC, SDK ou fingerprint pode parar antes dos patches | O probe de metadados passou, mas as etapas posteriores ainda precisam baixar, extrair e validar os pacotes reais `SM-S721B/EUX` e `SM-G973F/AUT`. O perfil do doador contém declarações que só são confirmadas contra o firmware baixado. |
| Compatibilidade do doador e patches | O framework S24 FE pode divergir do que o adaptador/paches S10 esperam | O pedido habilita `experimental_patch_failures: true`: falhas registradas de patch/módulo podem ser toleradas para tentar produzir um ZIP. Isso **não** transforma o patch em sucesso e uma receita pode deixar alterações parciais. É o maior risco de um ZIP compilado ainda ter integração incompleta, regressões ou não iniciar. |
| Compilação/empacotamento depois de falhas toleradas | O kernel, APK/JAR, imagens ou instalador ainda podem falhar | A tolerância não ignora erros fatais de compilação, integridade, identificadores ou criação/verificação do ZIP. Esses gates precisam terminar em sucesso; nenhum resultado verde parcial basta. |
| Tamanho e layout das partições | Uma ou mais imagens podem exceder o espaço físico do aparelho, ou o build pode ficar sem armazenamento | `content-sized` evita aplicar um limite fixo de repartição no build. Um pacote concluído deve incluir `REQUIRED-IMAGE-SIZES.json`; o dono precisa comparar/reparticionar manualmente antes de qualquer instalação. O workflow/instalador não reparticiona automaticamente. |
| Inicialização e hardware real | Wi-Fi, câmera, biometria, criptografia, telefonia, recovery ou boot podem falhar mesmo se build e verificações estruturais passarem | Não há teste físico/boot. O pacote é `UNTESTED`; não instalar/flash nem anunciar estabilidade com base no CI. |
| Retenção do artefato | O ZIP pode expirar no Actions | O artefato do workflow tem retenção de **7 dias** e não é copiado para release. Se houver sucesso, é preciso preservar o artefato e seus hashes dentro desse prazo; nenhuma publicação está autorizada nesta tarefa. |
| Correção de identidade e nome | Build #23 foi iniciado antes da convenção pública de nomes | O alias `r12s_native` foi mapeado para `essi` e a montagem remota passou. O Build #23 não é renomeado/reiniciado. A numeração/identidade X-NovaOS automatizada aplica-se às próximas execuções. |

## Critério de conclusão

Para considerar este build concluído, esperar `completed / success`, confirmar que validação e coleta do ZIP passaram, verificar `SHA256SUMS`, modelo SM-G973F e quaisquer sidecars de tamanho/layout. O sucesso só demonstra que os gates automatizados passaram; **não** prova boot, instalação segura ou funcionamento das features. Não publicar release, fazer flash, modificar recovery ou alterar o instalador Artisan ativo.
