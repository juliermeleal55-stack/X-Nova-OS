# Resultados reais — diagnóstico S24 FE

> Resultado mais recente: [diagnóstico após correção dos DEX lógicos](S24-FE-LOGICAL-DEX-RESULTS.md). Este documento preserva o registro da etapa anterior.

Execução [42419957346](https://github.com/juliermeleal55-stack/X-Nova-OS/actions/runs/42419957346), código c3b6b4842408696ed6f722c79b4de9502e7381eb. Relatório recuperado do artefato original pelas leituras 42431093976/42431154284, sem nova compilação ou download de firmware.

## Resultado global

- Diagnóstico concluído: **experimental-with-failures**, não patch pass limpo.
- **47 módulos**, **45 tentativas de patch**.
- **26 aplicações sem falha e 19 falhas de patch**; adicionalmente **2 módulos falharam**, totalizando 21 eventos de falha.
- Dos 19 patches que falharam no S926B: **2 passaram, 13 falharam e 4 não foram executados**.
- Kernel, reconstrução de APKs/JARs, imagens e ZIP da ROM foram pulados. Não há validação de assembly/runtime/boot.

Os dois SamsungPropsHooks (Knox e Settings) passaram na aplicação real. Isso confirma o avanço do mecanismo de criação de classe; não prova que a ROM compila ou que os hooks funcionam em runtime. O patch de cutout com criação de classe não foi alcançado e não pode ser chamado de corrigido.

## Situação individual dos 19 anteriores

| # | Área | Resultado no S24 FE |
| :--- | :--- | :--- |
| 1 | `cutout` | **Não executado** |
| 2 | `hotspot-dualap-service` | **Não executado** |
| 3 | `hotspot-dualap-settings` | **Não executado** |
| 4 | `virtual-vibration` | **Não executado** |
| 5 | `platform-signature` | **Falhou** |
| 6 | `extra-dim-settings` | **Falhou** |
| 7 | `extra-dim-systemui` | **Falhou** |
| 8 | `knox-attestation` | **Falhou** |
| 9 | `knox-props-hooks` | **Aplicado** |
| 10 | `hotspot-5ghz-country` | **Falhou** |
| 11 | `secure-screenshot` | **Falhou** |
| 12 | `app-downgrade` | **Falhou** |
| 13 | `pin-service` | **Falhou** |
| 14 | `zipped-overlays` | **Falhou** |
| 15 | `google-photos` | **Falhou** |
| 16 | `settings-props-hooks` | **Aplicado** |
| 17 | `pin-settings` | **Falhou** |
| 18 | `gestures-settings` | **Falhou** |
| 19 | `gestures-provider` | **Falhou** |

## Por que quatro não foram testados

O módulo `unica/patches/product_feature` parou ao não localizar `com/samsung/android/hardware/display/SemMdnieManagerService` em services.jar. Os trechos seguintes de cutout, DualAP (serviço e Settings) e vibração virtual não foram alcançados. Isso não é prova de incompatibilidade nem de sucesso desses quatro patches. O módulo seguinte foi tentado pelo coletor.

O segundo módulo com falha é `unica/patches/signature`, após o patch de assinatura não localizar InstallPackageHelper; a receita também tentou sed sem caminho resolvido.

## Seis falhas que apareceram além da lista antiga

- `unica/patches/product_feature/fingerprint/services.jar/0001-Set-FP_FEATURE_SENSOR_IS_OPTICAL-to-false.patch`
- `unica/patches/product_feature/fingerprint/SystemUI.apk/0001-Set-SECURITY_FINGERPRINT_IN_DISPLAY_OPTICAL-to-false.patch`
- `unica/patches/product_feature/resolution/framework.jar/0001-Enable-FW_DYNAMIC_RESOLUTION_CONTROL.patch`
- `unica/patches/product_feature/resolution/gamemanager.jar/0001-Enable-dynamic-resolution-control.patch`
- `unica/patches/product_feature/mdnie/hdr/SecSettings.apk/0001-Enable-HDR-Settings.patch`
- `unica/patches/product_feature/mdnie/hdr/SettingsProvider.apk/0001-Enable-HDR-And-EAD-Settings.patch`

São dois patches de fingerprint óptico -> ultrassônico, dois de resolução dinâmica/QHD e dois de HDR/configurações mDNIe. Essas rotas passaram a ser exercitadas com as diferenças do novo doador; a troca de base não eliminou incompatibilidades de contexto. No total global ainda existem 19 falhas de patch, mas não são exatamente as mesmas 19 anteriores.

## Próxima ordem de correção proposta

1. Resolver a localização real do serviço mDNIe e completar o módulo product_feature, liberando os quatro patches não executados.
2. Localizar classes de assinatura/gerenciamento de pacotes/locksettings no artefato correto; não adivinhar pelo nome do arquivo.
3. Adaptar fingerprint, resolução/HDR e Extra Dim aos métodos reais do S24 FE, verificando chamadas e resultado combinado.
4. Revisar hotspot, PIN, gestos, screenshots, downgrade, overlays e Photos; manter pares serviço/UI consistentes.
5. Repetir diagnóstico e só depois autorizar build completo, que também precisará validar reconstrução dos APKs/JARs.

A execução verde significa que a coleta foi concluída sob modo experimental, não que as falhas possam ser ignoradas para uma versão estável. Nenhum ZIP publicado foi alterado por esta leitura.

## Investigação posterior, sem alterar estes totais

A [comparação de patches e risco de boot](PATCH-BOOT-CROSS-AUDIT.md) examina ArtisanROM, ExtremeROM e OneROM, testa alternativas nos inputs retidos e documenta duas adaptações ópticas próprias aplicadas aos snapshots reais. Também identifica uma alternativa upstream que aplica mas inverte o comportamento de fingerprint e um erro lógico comum no patch de downgrade. O replay isolado não substitui uma nova execução completa, reconstrução dos APKs/JARs ou teste de boot.
