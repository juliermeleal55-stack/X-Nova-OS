# S24 FE — resultado após correção dos DEX lógicos

> **Registro histórico do diagnóstico completo.** Quatro destas falhas receberam adaptações ativas e passaram posteriormente no replay dos inputs reais. Veja [correções de assinatura, DualAP e SoundPicker](S24-FE-SCOPED-FIXES.md). O diagnóstico completo não foi reexecutado; os números abaixo permanecem os daquela execução.

Diagnóstico [42433286986](https://github.com/juliermeleal55-stack/X-Nova-OS/actions/runs/42433286986), código `98128c9`. Coleta concluída com **experimental-with-failures**. A leitura [42437306068](https://github.com/juliermeleal55-stack/X-Nova-OS/actions/runs/42437306068) recuperou o relatório do artefato original, sem baixar firmware de novo. [Evidência JSON com resultados individuais e erros limitados aos últimos 600 caracteres](evidence/s24fe-logical-dex-diagnostic.json).

## Resultado comparado

| Métrica | Antes: 42419957346 | Agora: 42433286986 |
| --- | ---: | ---: |
| Módulos percorridos | 47 | 47 |
| Tentativas de patch | 45 | **54** |
| Aplicações sem falha | 26 | **35** |
| Falhas de patch | 19 | **19** |
| Falhas de módulo | 2 | **0** |
| Lista histórica de 19: passou | 2 | **4** |
| Lista histórica de 19: falhou | 13 | **15** |
| Lista histórica de 19: não executado | 4 | **0** |

**Não é regressão simplesmente porque o número histórico de falhas passou de 13 para 15:** dois itens antes falhando passaram e quatro antes não executados foram alcançados, mas falharam. No conjunto global, quatro falhas anteriores passaram e quatro falhas antes ocultas foram reveladas, mantendo 19. Outras cinco tentativas adicionais passaram; o crescimento total de tentativas foi nove.

O resultado verde significa que o coletor experimental terminou, não que todos os patches ou a ROM estejam corretos.

## O que foi confirmado no firmware real

### Decodificação incompleta era um problema real

Após enumerar as unidades lógicas e verificar seus descritores, classes que bloqueavam os patches agora aparecem na árvore decodificada:

- `WindowState`: screenshot agora aplica.
- `PackageManagerServiceUtils`: equivalente corrigido de downgrade agora aplica.
- `InstallPackageHelper`: agora localizado; assinatura e overlays chegam à comparação dos hunks. A assinatura também alcança ScanPackageUtils, em vez de parar já na resolução de InstallPackageHelper.
- `SyntheticPasswordManager`: encontrado em outro DEX; patch ainda rejeita o contexto.
- `AttestParameterSpec`: encontrado; patch ainda rejeita o contexto.
- `SemMdnieManagerService`: a resolução não interrompe mais a receita, que alcança os quatro itens antes não executados.

Os logs registram inventários verificados com múltiplas unidades lógicas — inclusive artefatos com 2, 3, 4, 5 e 7 unidades. Isso confirma a utilidade da enumeração completa e da conferência dos descritores. Não demonstra que todas as classes desejadas existam no mesmo JAR: `GameManagerService$DisplayListener` continua não encontrado em gamemanager.jar.

### Quatro falhas anteriores agora passaram

1. Fingerprint óptico / services.jar: equivalente próprio aplicado no doador real.
2. Fingerprint óptico / SystemUI: equivalente próprio aplicado no doador real.
3. Secure screenshot / services.jar: aplicado após localizar WindowState.
4. Downgrade / services.jar: equivalente corrigido aplicado após localizar PackageManagerServiceUtils.

**Impressão digital:** as quatro tentativas do conjunto framework (mSensorType), services, BiometricSetting e SystemUI passaram. Não foi usado o candidato OneROM/SystemUI que desligava in-display no snapshot analisado. Ainda não houve reconstrução dos APKs/JARs, teste de HAL, cadastro de dedo ou desbloqueio no S10.

Os dois SamsungPropsHooks também continuam aplicando. Aplicação/criação de classe não valida execução das chamadas no classpath final.

## As 19 falhas restantes

| # | Área | Causa observada agora |
| --- | --- | --- |
| 1 | Resolução / framework.jar | Contexto de CoreRune divergente |
| 2 | Resolução / gamemanager.jar | `GameManagerService$DisplayListener` não encontrado no artefato examinado |
| 3 | HDR / SecSettings | Contexto de AdvancedFeatureItem divergente |
| 4 | HDR/EAD / SettingsProvider | Contexto de SecUpgradeController divergente |
| 5 | Cutout / SystemUI | Contexto de IndicatorGarden divergente; criação da classe auxiliar não basta para portar os demais hunks |
| 6 | DualAP / serviço | Contexto de SemSoftApConfiguration divergente |
| 7 | DualAP / SecSettings | Contextos de Utils/WifiApFrameworkUtils divergentes; relocação DEX identificada |
| 8 | Vibração virtual / SecSoundPicker | Contexto de Utils divergente |
| 9 | Assinatura de plataforma | Classes agora localizadas; contexto de ScanPackageUtils/applyPolicy incompatível |
| 10 | Extra Dim / SecSettings | Contexto de SecAccessibilityUtils divergente |
| 11 | Extra Dim / SystemUI | Contexto de ReduceBrightColorsTile divergente |
| 12 | Knox ICD/attestation / services.jar | AttestParameterSpec encontrado, mas contexto incompatível |
| 13 | Hotspot 5 GHz / país | Contexto de SemWifiApServiceImpl divergente |
| 14 | PIN / serviço | SyntheticPasswordManager encontrado; comparação/registradores/contexto mudaram |
| 15 | Zipped overlays | InstallPackageHelper encontrado; fluxo de política diferente |
| 16 | Google Photos | Contexto de ApplicationPackageManager divergente |
| 17 | PIN / SecSettings | Contexto de ChooseLockPasswordFragment divergente |
| 18 | Gestos / SecSettings | Contexto de NavigationBarSettingsUtil divergente |
| 19 | Gestos / SettingsProvider | Contexto de SecUpgradeController divergente |

Assim, **18 falhas são agora de contexto e uma permanece de classe não encontrada**. Não se resolve isso renomeando diretórios smali: o resolvedor já identifica várias relocações corretamente. É necessário analisar os métodos, campos, callers e booleanos reais antes do rebase.

## O ponto mais crítico: zero falhas de módulo não significa assinatura corrigida

`product_feature` e `signature` não terminam mais com os erros de receita anteriores. Porém, o patch de assinatura **ainda está na lista de falhas**. Em modo experimental, a receita pode continuar, e uma substituição sed sem correspondência pode terminar com status zero. Isso não instala a política que faltou nem prova que o placeholder foi substituído.

Portanto:

- não considerar o bridge de assinatura funcional;
- não reassinar o conjunto de APKs e inferir que PackageManager os aceitará;
- validar a política aplicada, certificado, pacote/caminho, shared UID e permissões como um conjunto;
- não apagar a verificação global de assinatura para conseguir um status verde.

O mesmo cuidado vale para mDNIe: a resolução da classe e o término da receita não demonstram HDR/EAD funcional, porque os patches dessas contrapartes ainda falharam e configurações podem ter sido alteradas antes das falhas.

## Próxima ordem de correção

1. **Assinatura/PackageManager:** agora há classes reais retidas nos snapshots, permitindo testar alternativas e portar a política restrita sem novo download de firmware. Verificar também o resultado efetivo da receita, não somente seu status.
2. **Rebase dos pares UI/backend:** PIN, DualAP, gestos e display, preservando migrações e contratos.
3. **Resolução/HDR/mDNIe e Extra Dim:** portar condições/recursos reais e conferir compatibilidade com vendor/kernel S10. Investigar a implementação atual do GameManager sem criar classe fictícia.
4. **Cutout e vibração virtual:** adaptar as implementações atuais, sem confundir suporte à criação de classe com compatibilidade de todas as alterações.
5. Repetir a análise de aplicação e só depois, no escopo autorizado, validar reconstrução, assinatura e execução. **Nenhum ZIP foi produzido e não existe boot S24 FE comprovado no S10.**

As alternativas upstream reavaliadas em snapshots são candidatos, não uma alteração automática dos patches ativos. A análise não iniciou novo build de ROM nem outra coleta completa de firmware.

## Reavaliação dos candidatos nas evidências novas

Além da leitura do relatório, a execução [42437408373](https://github.com/juliermeleal55-stack/X-Nova-OS/actions/runs/42437408373) reexecutou alternativas em cópias temporárias dos snapshots, exigindo os SHA-256 exatos registrados no diagnóstico. Não baixou firmware e não alterou o pipeline de patches ativos. [Resultado JSON](evidence/s24fe-logical-dex-candidate-replay.json).

| Candidato | Resultado isolado no snapshot novo |
| --- | --- |
| Assinatura OneROM | **Aplicou**; antes não havia inputs completos das classes |
| Assinatura Impulse UI9 | **Aplicou** |
| Extra Dim/SystemUI ExtremeROM | **Aplicou**, como no replay anterior |
| Hotspot/país OneROM | **Aplicou**, como no replay anterior |
| Resolução/framework OneROM | Rejeitado |
| Extra Dim/Settings ExtremeROM | Rejeitado |
| PIN/serviço OneROM | Rejeitado; não resolveu só pela nova localização da classe |
| Resolução/GameManager OneROM | Indisponível, sem input da classe esperada |
| Quatro testes de alternativas/equivalentes ópticos | Indisponíveis para replay: os hashes originais anteriores aos patches que passaram não estão presentes nos snapshots de falhas |

Total: **12 testes, 4 aplicações isoladas, 3 rejeições e 5 indisponíveis**. A indisponibilidade dos inputs de fingerprint neste replay não contradiz o relatório da execução completa, que registra os quatro patches de fingerprint como aplicados. Não equivale a uma nova falha desses patches.

### Assinatura: há candidatos concretos, mas não são drop-in

A alternativa OneROM restringe a exceção ao Settings; não cobre automaticamente todos os APKs que nosso pipeline reassina. A alternativa Impulse considera mais pacotes, mas tem uma incompatibilidade direta com nossa receita atual:

- Impulse usa o placeholder **`CONFIG_CUSTOM_PLATFORM_SIGNATURE` em ScanPackageUtils**.
- A receita Artisan atual tenta substituir **`PUT SIGNATURE HERE` em InstallPackageHelper**.

Copiar somente o patch Impulse deixaria sua string de certificado sem resolver, mesmo se o sed da receita retornasse zero. Também é necessário reconciliar a lista de pacotes reconstruídos com a lista de pacotes autorizados (a análise Impulse identificou divergência Camera/SDHMS), preservar controles de pacote/caminho/certificado, revisar callers e validar permissões/shared UID.

Assim, a nova evidência dá uma rota de correção mais concreta para o bloqueio de maior risco, **mas as 19 falhas do diagnóstico permanecem o resultado publicado**. Nenhuma das quatro alternativas acima foi ativada automaticamente e a aplicação isolada não valida o DEX reconstruído nem o boot.

Validação da análise/replay: **228 testes passaram em cópia limpa**, sem os quatro diffs locais preexistentes; referências e evidências verificadas por hash/tamanho. Esses testes não equivalem à reconstrução dos APKs/JARs do doador ou ao boot.
