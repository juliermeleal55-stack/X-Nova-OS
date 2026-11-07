# Revisão integral dos 19 patches tolerados

## Evidência recuperada

O build **42374299228**, do doador **SM-S926B/EUX**, executou 47 módulos e 46 tentativas de patch. O relatório original contém **19 patches falhos + 1 falha de módulo**, totalizando 20 eventos de falha. O módulo adicional é `unica/patches/signature`: o patch de assinatura falhou e a sequência tentou executar sed sem caminho resolvido.

A lista foi recuperada do artefato original pela execução de diagnóstico **42407896803**, sem baixar firmware ou recompilar a ROM. O diagnóstico confirma a lista; não é uma execução contra o S24 FE. O código do S24 FE declara o mesmo SDK 37; ainda não foi comprovado que o firmware selecionado seja uma base mais antiga ou que resolva estes problemas.

## Resultado do exame estático

- **3 patches:** o primeiro bloqueio era um defeito do nosso aplicador. Patches que criam classes (`--- /dev/null`) eram enviados ao resolvedor de classes existentes. A ausência da classe era esperada, mas tratada como erro. Corrigido o mecanismo de criação.
- **6 patches:** classes existentes não foram encontradas no artefato decodificado. É preciso localizar a implementação e o JAR/APK corretos no firmware real; não basta escolher outro número de DEX ou ignorar a classe.
- **10 patches:** a classe foi localizada, mas o contexto/instruções do hunk não correspondia ao doador. Deslocamento entre DEXes não resolve divergência semântica.

**Todos os 19 foram examinados. Nenhum foi declarado validado no S24 FE.** A correção no aplicador remove o bloqueio artificial dos três patches de criação; os patches mistos ainda podem falhar nos hunks restantes.

## Lista completa e ação por patch

| # | Área | Primeiro bloqueio observado | Revisão / próximo teste |
| :--- | :--- | :--- | :--- |
| 1 | `cutout` | Criação de classe recusada pelo aplicador | Rever implementação real de IndicatorGarden e todas as cinco classes; criação de classe corrigida no aplicador, contexto restante não comprovado. |
| 2 | `hotspot-dualap-service` | Contexto do hunk divergente | Adaptar isWifiApEnabledWithDualBand à implementação real; não trocar método inteiro sem inspecionar chamadas. |
| 3 | `hotspot-dualap-settings` | Contexto do hunk divergente | Rever WifiApFrameworkUtils e Utils como conjunto; deslocamento DEX já resolveu caminhos, não resolveu o hunk. |
| 4 | `virtual-vibration` | Contexto do hunk divergente | Confrontar isShowVibrateWhileRingingView e feature flags reais do doador/target. |
| 5 | `platform-signature` | Classe existente não encontrada | Localizar InstallPackageHelper e helpers de assinatura no pacote real; preservar autenticação esperada do port e validar todos os hunks. |
| 6 | `extra-dim-settings` | Contexto do hunk divergente | Rever property protected_contents e condição real de SecAccessibilityUtils. |
| 7 | `extra-dim-systemui` | Contexto do hunk divergente | Rever ReduceBrightColorsTile junto com Settings; não assumir alteração parcial como funcional. |
| 8 | `knox-attestation` | Classe existente não encontrada | Localizar AttestParameterSpec no artefato correto; não resolver escolhendo classe de outro pacote pelo nome. |
| 9 | `knox-props-hooks` | Criação de classe recusada pelo aplicador | Criação de classe corrigida no aplicador; rever Instrumentation/SystemProperties/Settings Global e interação com outro hook. |
| 10 | `hotspot-5ghz-country` | Contexto do hunk divergente | Rever supportWifiAp5GBasedOnCountry; mudanças regionais e suporte de hardware precisam de validação. |
| 11 | `secure-screenshot` | Classe existente não encontrada | Localizar WindowState e rever isSecureLocked; não presumir que a classe está no mesmo JAR. |
| 12 | `app-downgrade` | Classe existente não encontrada | Localizar PackageManagerServiceUtils; revalidar contratos e efeito da alteração no gerenciador de pacotes. |
| 13 | `pin-service` | Classe existente não encontrada | Localizar SyntheticPasswordManager e revisar contrato em conjunto com UI de PIN. |
| 14 | `zipped-overlays` | Classe existente não encontrada | Localizar InstallPackageHelper; compartilhar diagnóstico com assinatura sem duplicar correção cega. |
| 15 | `google-photos` | Contexto do hunk divergente | Rever ApplicationPackageManager e hooks de propriedades; contexto de fields já mudou. |
| 16 | `settings-props-hooks` | Criação de classe recusada pelo aplicador | Patch de criação pura: exercitado com arquivo upstream real e aplicação Git estrita em fixture; chamadas do customize e runtime ainda não validadas. |
| 17 | `pin-settings` | Contexto do hunk divergente | Rever ChooseLockPasswordFragment junto com limite no serviço; não entregar limites divergentes. |
| 18 | `gestures-settings` | Contexto do hunk divergente | Rever isGestureDefault e comportamento de região/first API em conjunto com SettingsProvider. |
| 19 | `gestures-provider` | Contexto do hunk divergente | Rever SecUpgradeController e migração/default de navegação em conjunto com Settings. |

Os caminhos completos dos 19 patches, hashes de origem e estados estão em [`integration/tolerated_patch_review.json`](../integration/tolerated_patch_review.json). Os patches upstream examinados estão preservados com manifesto em [`manifests/tolerated-patch-sources.json`](../manifests/tolerated-patch-sources.json), fixados na revisão Artisan histórica. Não foram publicados snapshots Smali do firmware Samsung.

## Correção implementada no aplicador

- Distingue criação explícita de arquivo de edição de classe existente.
- Exige que o descriptor `.class` adicionado corresponda ao caminho e que o hunk seja de criação a partir de `/dev/null`.
- Recusa sobrescrever/criar duplicata de classe que já existe em qualquer DEX.
- Preserva o DEX solicitado quando já existe; caso contrário, aloca o próximo índice após o maior DEX existente, evitando introduzir classes6 quando faltam classes2..5.
- Mantém verificação estrita de todos os hunks com `git apply --check` antes da aplicação; falha em outro hunk não deixa a nova classe parcialmente aplicada.
- Não substitui classes ausentes por stubs e não flexibiliza busca por basename, pacote ou descriptor.
- Mantém proteção contra traversal e symlinks para fora da árvore.

O patch upstream real de criação `io/mesalabs/unica/SamsungPropsHooks` passou na aplicação Git em fixture. Isso valida a criação do arquivo, **não** a ligação de chamadas no customize.sh nem o funcionamento em runtime. Os dois hooks de propriedades têm namespaces distintos e ambos podem tocar a cadeia Instrumentation; a convivência exige inspeção e teste do resultado combinado.

## Acompanhamento no próximo preflight

O relatório passa a conter `prior_failure_review`, acompanhando separadamente os mesmos 19 patches como **passed**, **failed** ou **not-executed**. Uma feature não selecionada, módulo interrompido ou patch não alcançado não aparece como corrigido. Falha de módulo e falha de patch não são contadas como dois patches diferentes. Se um patch falhar e posteriormente passar em outra tentativa da mesma coleta, a falha não desaparece do resumo.

Não foi desativado o modo experimental nem foram removidos patches. Não se alteraram os retornos de métodos de assinatura, atestação, PIN ou outros serviços sem verificar seu contrato. Os pares serviço/UI de PIN, Settings/SystemUI Extra Dim e Settings/SettingsProvider de gestos devem ser validados juntos.

## Validação e pendências

**196 testes passaram em cópia limpa**, com **69 referências Artisan, 37 referências adicionais e 84 evidências de auditoria verificadas**. Dez testes novos cobrem criação de classe real, colisões, descriptor, DEX, symlink/traversal, aplicação atômica e cobertura dos 19 estados. Os quatro arquivos locais alheios ao trabalho não foram incorporados.

Ainda pendente: baixar/inspecionar o S24 FE real em execução autorizada, localizar as seis classes existentes ausentes, adaptar os dez contextos diferentes, testar os três patches de criação com todos os seus hunks e chamadas e recompilar/validar os APKs/JARs resultantes. Nenhum build completo foi iniciado nesta revisão. A Alpha 1 publicada permanece inalterada; não se promete boot.
