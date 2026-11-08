# S24 FE — primeiro lote de correções integradas

**Implementação parcial, não uma ROM pronta.** Quatro patches que falharam no diagnóstico completo receberam adaptações ativas e passaram nos snapshots reais. As outras **15 falhas daquele conjunto ainda não estão corrigidas**.

## Evidência real, sem novo firmware

O [replay 42438490691](https://github.com/juliermeleal55-stack/X-Nova-OS/actions/runs/42438490691), código `0a5ae6b`, reutilizou os snapshots do diagnóstico **42433286986**. Cada input foi recuperado pelo SHA-256 original antes de aplicar a integração em cópia temporária. [Resultados individuais e identificação da execução](evidence/s24fe-scoped-fixes-replay.json).

| Integração ativa | Resultado no input real retido |
| --- | --- |
| Assinatura / services.jar | Patch restrito aplicou; certificado de teste inserido; política e callers conferidos |
| DualAP / semwifi-service.jar | Método booleano de dual-band adaptado para `false` |
| DualAP / SecSettings | Flag da interface e atribuição da contagem de bandas adaptadas em conjunto |
| Vibração virtual / SecSoundPicker | Método estático booleano adaptado para `false` |

O conjunto de comparação tem **16 casos: 8 aplicações, 3 rejeições e 5 indisponíveis**. Só **quatro** dessas aplicações são as novas integrações acima. As outras quatro são alternativas upstream já analisadas, **não ativadas automaticamente**. Inputs indisponíveis de fingerprint não são regressões: o diagnóstico completo anterior já registrou os quatro patches desse grupo como aplicados.

**Não recalculamos o diagnóstico completo como se fosse 39/15.** O histórico permanece 47 módulos, 54 tentativas, 35 aplicações e 19 falhas. O replay é uma prova isolada de aplicação/configuração de quatro correções, não a execução completa atualizada.

## Assinatura: política restrita e falha explícita

- Integração de scan/comparação derivada do [ImpulseROM fixado por commit](../manifests/signature-bridge.json), preservando proveniência/licença.
- O replacement restrito e verificado por hash tem preferência obrigatória. Não há fallback automático para o patch legado mais amplo, mesmo se ele encaixar em outro doador.
- [Allowlist explícita](../integration/signature_policy.json) de oito identidades: SystemUI, Accessibility, BiometricSetting, EnvironmentAdaptiveDisplay, SecSettings, SettingsProvider, SamsungCamera e SecSoundPicker. **SDHMS não foi incluído.**
- A exceção exige **pacote exato + caminho preinstalado exato + certificado configurado**. O caminho pode ser o APK ou seu diretório exato, conforme o contrato de `ParsedPackage.getPath()`. Não há autorização por prefixo, para `/data/app` ou para atualizações instaladas ali.
- A receita usa o marcador real `CONFIG_CUSTOM_PLATFORM_SIGNATURE` em **ScanPackageUtils**, com o certificado selecionado por `ROM_IS_OFFICIAL` (`aosp`/`extremerom`). A configuração exige marcador único, três métodos esperados e callers presentes; sed sem correspondência não é sucesso.
- Antes de reassinar APK modificado, o builder verifica ponte, certificado, política e recibo. Se essa pré-condição falhar, a assinatura é interrompida. O teste negativo executa esse trecho real do shell e confirma que `signapk` não é alcançado com recibo inválido.

O replay usou certificado **efêmero e exclusivamente de teste**; não assinou APK nem publicou chave privada. A aplicação/configuração no donor não comprova aceitação por PackageManager, compatibilidade de todos os APKs reconstruídos, certificados originais, shared UIDs ou concessão de permissões em execução. Esses contratos continuam pendentes de validação. A conferência estática dos callers foi reforçada também contra troca de `invoke-static` por outra modalidade.

## DualAP: preservar os registradores e os controles de país

A análise do método real `isBandSeekBarUxSupported(Context)Z` mostrou que o registrador com valor `2` também participa da comparação final. Substituir sua constante por `1` alteraria essa comparação.

A adaptação modifica **somente `move v0, v1` para `move v0, v2`**, no método cujo conteúdo foi previamente inspecionado e fixado por SHA-256 normalizado. Assim a contagem inicial passa a uma banda, mas o limiar final e as chamadas de verificação de país para 5/6 GHz permanecem intactos. Nenhuma permissão ou verificação de país foi removida.

A flag `SPF_SupportMobileApDualAp` recebe `false` usando local novo, sem reutilizar o registrador vivo de outras flags. As duas classes do patch de SecSettings são validadas antes de qualquer gravação; mudança no método do donor rejeita o par sem alterar a primeira classe. O serviço usa o método exato `isWifiApEnabledWithDualBand()Z` retornando `false`.

Isso confirma a aplicação das duas contrapartes, **não o funcionamento do hotspot no S10**.

## Validações e limites

- **238 testes passaram em cópia limpa**, excluindo os quatro diffs locais preexistentes e não relacionados. A suíte contém testes sintéticos/mocks; não constitui reconstrução real do doador.
- **208 arquivos de auditoria/evidência verificados**, referências verificadas, shell conferido e `git diff --check` sem erros.
- O replay real confirmou os quatro patches acima; não executou montagem dos DEX completos, reconstrução/assinatura dos APKs/JARs, kernel, imagens ou ZIP.
- Não houve novo download de firmware, ROM ZIP, release, reparticionamento ou teste de boot. Kernel/vendor S10 e correções nativas de câmera foram preservados.

## Trabalho ainda aberto

As 15 falhas restantes são: resolução/CoreRune; resolução/GameManager; HDR/Settings; HDR-EAD/SettingsProvider; cutout/SystemUI; Extra Dim/Settings; Extra Dim/SystemUI; Knox attestation; hotspot/país; PIN/serviço; zipped overlays; Photos; PIN/Settings; gestos/Settings; gestos/SettingsProvider.

`GameManagerService$DisplayListener` continua sem implementação localizada nos inputs disponíveis; **não foi criada classe fictícia**. HDR/EAD/mDNIe, resolução e Extra Dim ainda exigem conciliação com vendor/kernel do Exynos 9820. Não foram ativados o bypass de `protected_contents`/helper dummy do Extra Dim nem a remoção upstream de permissões/controles de país do hotspot. As migrações de SettingsProvider e os pares PIN/gestos precisam de análise de fluxo antes do port, não substituição global de constantes.
