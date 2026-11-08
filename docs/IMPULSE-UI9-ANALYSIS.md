# ImpulseROM One UI 9 — análise para o X-Nova OS

## Resumo

**A indicação é relevante:** existe uma linha One UI 9 na ImpulseROM, usando o mesmo doador S24 FE `S721BXXSFEZJ1` do diagnóstico X-Nova. A melhor referência não é o README da branch padrão, mas a tag `v1.0-oneui9-alpha1` e a branch `feature/oneui9`.

O maior achado para nossas falhas é o tratamento de **DEX 041 com várias unidades lógicas no mesmo arquivo físico**. A Impulse enumera e decodifica essas unidades separadamente; nosso adaptador atual percorre os arquivos físicos `.dex`. Isso fornece uma hipótese concreta de decodificação incompleta para as classes centrais não encontradas, ainda não uma causa confirmada no firmware real.

Esta análise **não importou patches para o pipeline, não trocou kernel/vendor, não executou scripts upstream, não baixou firmware/ZIP e não iniciou build**. Os arquivos de referência e este relatório são a entrega desta etapa.

## 1. O que existe de fato

Consulta do repositório [TomasULR/ImpulseROM](https://github.com/TomasULR/ImpulseROM):

| Item | Evidência e limite |
| --- | --- |
| Branch padrão | `bringup/oneui85-d2s`; descrição/README ainda apresentam One UI 8.5/Android 16 |
| GitHub Releases | O endpoint `repos/TomasULR/ImpulseROM/releases` retornou `[]`; não havia uma Release/asset UI9 enumerada nessa consulta |
| Tag One UI 9 | [`v1.0-oneui9-alpha1`](https://github.com/TomasULR/ImpulseROM/tree/v1.0-oneui9-alpha1), commit `783909f0bc5854830a9a593c11077cc4e47f2fb7` |
| Branch One UI 9 | [`feature/oneui9`](https://github.com/TomasULR/ImpulseROM/tree/092fd6aa0abe743591d76cb018191a364aad6eda), revisão examinada `092fd6aa0abe743591d76cb018191a364aad6eda` |
| Outra tag encontrada | `v1.0-oneui85-alpha10-dev`; é da linha **8.5**, não uma Alpha 10 da UI9 |
| Versão do sistema | Script de survey declara `IMPULSE_DONOR_API=37`, `IMPULSE_DONOR_RELEASE=17`; versão UI9 é declarada pelo projeto, não medida por nós em um ZIP |

Tag de código, Release do GitHub e pacote externo são coisas diferentes. A ausência de uma Release listada **não significa que não exista um ZIP distribuído fora do GitHub**.

### Pacote registrado pelo projeto

A [proveniência na revisão UI9](https://github.com/TomasULR/ImpulseROM/blob/092fd6aa0abe743591d76cb018191a364aad6eda/docs/source-provenance.md) registra:

- Nome: `ImpulseROM_d2s_OneUI9-alpha1_20261102.zip`.
- Tamanho declarado: **6.141.227.412 bytes**.
- SHA-256 declarado: `853f0048296258b35b281332eb456cf18415c8460d98fcc54feb59b81a3d0cd9`.
- Código declarado: tag `v1.0-oneui9-alpha1`, commit `783909f0...`.
- Inputs: doador `S721BXXSFEZJ1`, multilib `S711BXXSGGZF2`, alvo `N975FXXS9HWHA`.
- Teste relatado: **boot no SM-N975F do desenvolvedor**. O TWRP teria mostrado `Unable to format to remove encryption`, portanto o próprio documento **não confirma boot com dados recém-formatados**.

Nome, data embutida, tamanho, hash e relato acima são registros upstream. O ZIP não foi baixado, seu hash não foi recalculado e o boot não foi verificado independentemente. Não é evidência de estabilidade completa, clean flash ou funcionamento no S10.

## 2. Compatibilidade com o nosso trabalho

| Aspecto | Impulse UI9 | X-Nova atual | Consequência |
| --- | --- | --- | --- |
| Doador principal | S24 FE, `S721BXXSFEZJ1` | Mesmo firmware no diagnóstico | Forte pertinência para ferramentas/framework; não garante mesmo estado final dos JARs |
| Aparelho alvo | Note10+ `SM-N975F/d2s`, Exynos 9825 | S10 `SM-G973F/beyond1lte`, Exynos 9820 | Não copiar vendor, HWC, kernel ou regras de partição do Note10+ |
| Base de build | Fork EternityROM/UN1CA | Base Artisan e adaptações próprias/ExtremeROM | Integrar por responsabilidade, não substituir a árvore inteira |
| Runtime legado | Input multilib S711B e fusão de APEX | Exige auditoria do conjunto realmente incluído no nosso build | Conferir símbolos, ABI, namespaces, APEX/assinaturas e SELinux; não basta copiar libs |
| Validação disponível | Boot relatado pelo autor, ressalva de formatação | Diagnóstico de aplicação; sem boot S24 FE | Fonte promissora, não prova transferível para S10 |

O script `run_build_oneui9_survey.sh` fixa o doador e API 37, mas também usa `PATCH_DRIFT_POLICY=skip`. Portanto, um ZIP concluído não demonstra que todos os patches herdados aplicaram. O documento `PATCH_STATUS_DZF3.md` é detalhado, porém trata do firmware **DZF3/API36**, não valida automaticamente o FEZJ1/API37.

## 3. Achado principal: DEX físico não é necessariamente DEX lógico

O [`scripts/apktool.sh` examinado](https://github.com/TomasULR/ImpulseROM/blob/092fd6aa0abe743591d76cb018191a364aad6eda/scripts/apktool.sh) contém:

1. `GET_LOGICAL_DEX_ENTRIES`, baseado em `baksmali list dex "$INPUT_FILE"`.
2. Enumeração de entradas físicas em ordem (`classes.dex`, `classes2.dex` etc.) e de suas unidades internas (`classes.dex/2`, `/3` etc.).
3. Um mapa explícito unidade de entrada → diretório smali → DEX de saída.
4. Decodificação de cada unidade e comparação de contagem de classes com inventário independente.
5. Proteção para não restaurar um contêiner DEX 041 completo e, ao mesmo tempo, emitir suas unidades como DEX adicionais: isso duplicaria conteúdo e poderia preservar código não modificado.

Nosso `integration/artisan/apktool.sh` atual usa `find ... -name '*.dex'` e chama baksmali para cada arquivo físico. Ter suporte à magic/version 041 não equivale a enumerar todas as suas unidades. O resolvedor posterior busca descritores exatos nos diretórios **que foram decodificados**; não consegue encontrar classes que não foram extraídas.

### Relação com as falhas anteriores

O diagnóstico não encontrou classes como `InstallPackageHelper`, `PackageManagerServiceUtils`, `WindowState` e `SyntheticPasswordManager` no services.jar decodificado. Esse padrão é compatível com uma inspeção incompleta de unidades DEX, além das outras possibilidades já documentadas (mudança de artefato/classe).

**Hipótese prioritária, não conclusão:** verificar no services.jar original a lista de unidades lógicas, headers e contagens. Se as classes estiverem em unidades internas omitidas, será necessário corrigir a decodificação antes de reavaliar assinatura, screenshot, downgrade, PIN e overlays. Isso pode remover erros de localização, **não garante que os hunks antigos passarão**.

O próximo teste deve comparar inventário original × todas as classes decodificadas, preservando ordem, unicidade de descritor e mapeamento de reconstrução. Não recomendo simplesmente chamar baksmali mais vezes e aceitar um resultado verde sem verificar duplicações/perdas.

## 4. Outras soluções relevantes — e os limites

### Assinatura: tratamento restrito, não liberação global

O patch Impulse altera `InstallPackageHelper` e `ScanPackageUtils`, verifica certificado e restringe pacotes sob `/system/`. O código enumera **sete** nomes de pacote, embora o cabeçalho ainda diga seis: SystemUI, Accessibility, BiometricSetting, EAD, Settings, SettingsProvider e SDHMS.

Há uma inconsistência que exige revisão: a lista de exceções de reconstrução de APKs inclui SamsungCamera, enquanto a lista do helper de assinatura inclui SDHMS, não Camera. O efeito depende do caminho efetivamente ativado e das permissões necessárias; não se pode afirmar que todas as exceções estão cobertas pelo bridge.

A receita ainda depende de um caminho explícito `smali_classes2/.../ScanPackageUtils.smali`; quando não existe, avisa e pula. Isso não resolve por si só a classe ausente no nosso pipeline. O mecanismo `KEEP_SIGNED_APKS_STOCK` também pode **descartar patches aplicados na árvore decodificada**, preservando o APK stock. Logo, aplicação, reconstrução e efeito final precisam ser reportados separadamente.

**Potencial:** melhor referência de desenho para nossa pendência crítica de assinatura, após inventariar todos os APKs modificados e portar contra as classes reais. Não aplicar parcialmente nem desabilitar validação global.

### Native boot: ueventd, TEE, BPF e gráficos

O alvo d2s adiciona regras de `/vendor/ueventd.rc` ao ueventd do sistema, citando acesso a `/dev/tzdev` e `/dev/tziwshmem` necessário ao TEE. Instala adaptações hash-pinned de NetBpfLoad/libservice-connectivity para kernel legado e um ajuste de `libui` para mapper legado. São problemas capazes de impedir serviços essenciais mesmo se todos os patches smali aplicarem.

**Potencial:** auditar esses mesmos contratos no S10. **Não copiar os binários, offsets ou gates de kernel**: o código é específico de hashes de entrada e capacidades de kernel/vendor. Um kernel anunciar uma versão de BPF não prova todos os recursos exigidos pelo userspace novo.

### APEX multilib

`merge_multilib_apex.py` conserva os caminhos do APEX principal e adiciona os que só existem no multilib, reconstruindo/reassinando o resultado. É uma referência concreta para o problema de runtime 64-bit moderno com HALs ELF32 antigos.

**Limite:** bibliotecas de gerações diferentes podem ter incompatibilidades de ABI mesmo sem colisão de nome. A aceitação do APEX reconstruído depende também da política efetiva de chaves/avb/apexd. O comentário do script não substitui validação de inicialização no nosso alvo.

### Resolução e mDNIe

A receita habilita `FW_SUPPORT_MULTI_RESOLUTION`, adapta três pontos da UI de resolução e mantém o graphics core novo para APIs >=36. O módulo d2s restaura HWC/gralloc do **próprio Note10+ stock**. Isso é mais amplo que trocar uma flag em CoreRune, e os blobs Exynos 9825 não são uma correção genérica do Exynos 9820.

Para mDNIe, o helper procura por basename e pode retornar sucesso apenas com um aviso quando o arquivo falta. A receita ainda anuncia a configuração de modos antes da substituição. Esse comportamento pode completar a coleta, mas não comprova integração do recurso. Nosso resolvedor estrito por descritor deve ser preservado.

O ramo UI9 também evita copiar o EAD legado acima de API 36. Isso merece análise de dependências e recursos, não importação cega ou remoção automática dos módulos existentes.

## 5. Ordem recomendada para aproveitar esta referência

1. **Investigar DEX 041/multicontêiner primeiro.** Adicionar teste de enumeração/contagem e prova de integridade; confirmar a hipótese no artefato original antes de declarar as classes movidas/inexistentes.
2. Reexecutar a análise dos patches dependentes de classes centrais após uma decodificação comprovadamente completa. Manter as correções ópticas próprias já testadas; não substituir pelo patch OneROM de semântica invertida.
3. Projetar bridge de assinatura restrito ao conjunto real de APKs reconstruídos, garantindo que o relatório diferencie patch aplicado, APK preservado stock e alteração efetivamente publicada.
4. Auditar fechamento ELF32/ELF64, APEX, ueventd/TEE, BPF e graphics mapper contra **kernel/vendor S10**. Sem transplante do Note10+ e sem mudar câmera nativa nesta análise.
5. Só depois validar display/mDNIe/resolução e repetir diagnóstico/reconstrução no escopo autorizado. Build flashável e teste de boot são etapas separadas; não foram iniciados aqui.

## Evidências locais

Foram preservados **16 arquivos upstream selecionados**, incluindo LICENSE, em [`reference/impulse-ui9`](../reference/impulse-ui9), com revisão, Git blob SHA e tamanho em [`manifests/impulse-ui9-audit.json`](../manifests/impulse-ui9-audit.json). Os scripts são material de referência e não estão sobrepostos ao pipeline ativo. Esta análise complementa o [relatório anterior de patches/boot](PATCH-BOOT-CROSS-AUDIT.md).

Validação desta entrega: **216 testes do repositório passaram em cópia limpa**, sem os quatro diffs locais preexistentes; **205 evidências de auditoria/build** passaram na verificação de hash/tamanho, incluindo as 16 novas referências Impulse. Sintaxe dos scripts shell de referência verificada com `bash -n`, sem executá-los. Esses testes não validam a hipótese DEX no JAR do doador nem o boot da Impulse/X-Nova.
