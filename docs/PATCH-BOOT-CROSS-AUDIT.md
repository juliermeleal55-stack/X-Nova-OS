# X-Nova OS — patches, comparação de fontes e risco de boot

## Conclusão executiva

**Não há evidência de boot que permita afirmar que estes erros causam — ou não causam — bootloop.** O diagnóstico S24 FE concluiu a coleta, não uma ROM funcional. A maioria das falhas representa uma modificação que não entrou; isso não equivale automaticamente a código inválido instalado. Entretanto, continuar depois de um módulo parcialmente aplicado pode deixar configurações, APKs e serviços incompatíveis entre si.

Os maiores riscos encontrados são **assinatura dos APKs modificados**, estado parcial de `product_feature`, integração de display/biometria e consistência dos hooks no framework. Screenshots, downgrade, gestos e Google Photos não são, por sua finalidade, requisitos para iniciar o Android; isso não torna qualquer alteração em services.jar/framework.jar inofensiva.

Foram encontradas alternativas upstream que realmente se aplicam aos snapshots do S24 FE, além de um erro lógico comum às três fontes. **Aplicar um diff não valida o seu funcionamento, a reconstrução do APK/JAR ou o boot.** Nenhum firmware foi baixado de novo, nenhum kernel/ZIP foi construído, nenhum ZIP publicado foi alterado por esta investigação.

## 1. Evidência e escopo

- Diagnóstico real: [42419957346](https://github.com/juliermeleal55-stack/X-Nova-OS/actions/runs/42419957346), código `c3b6b4842408696ed6f722c79b4de9502e7381eb`.
- Resultado: **47 módulos, 45 tentativas, 26 aplicações sem falha, 19 falhas de patch e 2 falhas de módulo**. Estado `experimental-with-failures`.
- Da lista histórica de 19: **2 passaram, 13 falharam, 4 não foram executados**. Há **6 falhas novas**, mantendo 19 falhas atuais no total. Ver [resultados individuais](S24-FE-PATCH-RESULTS.md).
- A coleta pulou kernel, reconstrução de APKs/JARs, imagens e ZIP. Não houve teste de instalação, boot, desbloqueio ou hardware.
- Doador: SM-S721B/EUX/S721BXXSFEZJ1, somente sistema/framework. Alvo mantido: SM-G973F/beyond1lte, kernel/vendor/adaptações Exynos 9820. Configuração de outro aparelho não substitui esta base.

### Fontes fixadas, e não branches móveis

| Fonte | Revisão examinada | Uso na análise |
| --- | --- | --- |
| [ArtisanROM original](https://github.com/ArtisanROM-archive/ArtisanROM_old/tree/5638a7f66cdf8bc9dd43f087a96f7dfa4f9e6954) | `5638a7f66cdf8bc9dd43f087a96f7dfa4f9e6954` | Patches/receitas da base S10 |
| [ExtremeROM](https://github.com/ExtremeXT/ExtremeROM/tree/2056320784b7d1d88f9e7025f86f7bbd39945d6b) | `2056320784b7d1d88f9e7025f86f7bbd39945d6b` | Implementações alternativas das mesmas famílias |
| [OneROM](https://github.com/DaDevMikey/OneROM/tree/541074191937f2d7c033be7a10cf5d99146cc98f) | `541074191937f2d7c033be7a10cf5d99146cc98f` | Candidatos mais recentes, incluindo configuração S721B |

As 104 evidências selecionadas estão em [`reference/boot-patch-audit`](../reference/boot-patch-audit), com repositório, revisão, caminho, tamanho e Git blob SHA em [`manifests/boot-patch-audit.json`](../manifests/boot-patch-audit.json). São 36 arquivos Artisan, 34 Extreme, 34 OneROM, incluindo licenças; não constituem uma auditoria completa dos três projetos. Créditos/autorias dos patches foram preservados.

Na amostra, 20 arquivos da OneROM são byte a byte iguais aos correspondentes Artisan; 5 da Extreme são iguais. Estes números incluem a licença e não significam “20 patches corrigidos”. Arquivos diferentes também podem diferir apenas em cabeçalho/contexto. Por exemplo, PIN do serviço usa o mesmo limiar pretendido, mas o patch OneROM tem contexto/registrador de comparação diferentes.

## 2. Como o mecanismo funciona — e o que realmente falhou

1. A receita decide o que adaptar comparando capacidades/configurações do doador e do S10; pode escrever floating features, copiar arquivos e depois aplicar patches.
2. O APK/JAR é decodificado. O resolvedor procura **o descritor exato da classe**, inclusive em outros diretórios DEX. Encontrar um basename parecido não é suficiente.
3. O patch precisa casar com o código/contexto presente. Mudanças de método, fluxo, instruções e registradores exigem um rebase semântico, não apenas trocar o número de linha.
4. A aplicação de um patch é protegida contra aplicação parcial dos seus hunks. **O módulo inteiro, porém, não é uma transação**: configurações e patches anteriores podem permanecer quando a receita para.
5. Em um build completo ainda viriam assembly DEX, reconstrução, assinatura, montagem das imagens e execução real. Essas etapas não foram feitas neste diagnóstico.

### Três situações diferentes

- **`patch does not apply`**: a classe foi encontrada, mas o trecho esperado não corresponde ao doador. Extra Dim, HDR, PIN/gestos de Settings mostram inclusive relocação DEX bem-sucedida antes da rejeição. Não são resolvidos simplesmente trocando `smali_classes4` por `smali_classes3`.
- **`Expected exactly one ...; found 0`**: o descritor não foi encontrado **no artefato decodificado examinado**. Não prova ausência em todo o firmware. Pode haver reorganização entre JARs, classe substituída ou inspeção/decodificação incompleta. Não autoriza criar classes centrais vazias para esconder o erro.
- **Falha de receita**: além do patch rejeitado, uma operação posterior como `sed` usa um arquivo não resolvido. Continuar o coletor é útil para descobrir outros problemas, mas não torna esse módulo consistente.

## 3. As 19 falhas atuais: função, erro e encaminhamento

Na coluna “risco”, o risco é **condicional à integração**, não diagnóstico de bootloop observado. “Recurso” significa que a finalidade não é iniciar o sistema; ainda exige validação se o patch toca código central.

| # | Patch/área | O que pretende fazer | Erro observado e comparação | Risco e correção necessária |
| --- | --- | --- | --- | --- |
| 1 | Fingerprint / services.jar | Desativar a interpretação óptica para a biometria ultrassônica do S10 | Contexto de `SemBiometricFeature` mudou. OneROM tem contexto atualizado que aplica, mas os valores não foram provados pela análise conservadora | Biometria/lockscreen; adaptação própria força apenas óptico=false com local novo, sem alterar outras flags |
| 2 | Fingerprint / SystemUI | Não tratar a impressão digital como óptica | Contexto antigo de `LsRune`. OneROM oferece patch diferente que diz ativar in-display, mas no input real **desativa in-display e mantém óptico=true** | Pode afetar interface de bloqueio. Candidato upstream descartado como correção pronta; adaptação própria desativa apenas óptico e preserva in-display |
| 3 | Resolução / framework.jar | Habilitar controle dinâmico de resolução/QHD em `CoreRune` | Contexto mudou. A alternativa OneROM também foi rejeitada no snapshot | Integração de display; portar campos/fluxos reais, sem copiar registradores booleanos por número |
| 4 | Resolução / gamemanager.jar | Adequar política de resolução no GameManager | `GameManagerService$DisplayListener` não encontrado. Há variante upstream, mas falta input exato para reexecutá-la | Display/jogos; localizar implementação atual e conferir IPC/política. Não criar listener fictício |
| 5 | HDR / SecSettings | Expor e persistir configuração HDR | Contexto de `AdvancedFeatureItem` incompatível. Arquivo OneROM é idêntico ao Artisan | Recurso/display; adaptar serializers/keys e a contraparte provider, não somente mostrar menu |
| 6 | HDR/EAD / SettingsProvider | Ajustar valores/migração das configurações de display | Contexto de `SecUpgradeController` incompatível. OneROM reutiliza o mesmo patch | Provider é componente essencial; não substituir métodos de migração inteiros sem análise |
| 7 | Assinatura de plataforma | Permitir tratamento controlado do certificado usado nos APKs modificados | `InstallPackageHelper` não encontrado; receita termina em `sed` sem arquivo. OneROM muda a política, mas mantém dependência da classe ausente | **Prioridade máxima**: APKs reassinados podem perder aceitação, shared UID ou permissões. Portar política e todos os callers/contratos em conjunto |
| 8 | Extra Dim / SecSettings | Remover exclusões por dispositivo e habilitar ajuste | `SecAccessibilityUtils` encontrado, contexto rejeitado. OneROM e Artisan coincidem; Extreme alternativo também rejeitado | Recurso/acessibilidade; rebase no método atual, preservando demais condições |
| 9 | Extra Dim / SystemUI | Liberar tile e ajustar condição de disponibilidade | `ReduceBrightColorsTile` encontrado, contexto rejeitado. Variante Extreme **aplica no input real** | Recurso/composição; também força a condição ligada a protected contents. Aplicação não prova suporte do compositor/vendor |
| 10 | Knox / attestation | Alterar comportamento de `AttestParameterSpec` relacionado à verificação/SAK | Classe não encontrada em services.jar. OneROM reutiliza o patch; existe patch distinto da mesma classe em samsungkeystoreutils.jar | Serviços Samsung/segurança; não mover um patch de outro JAR cegamente. Inventariar classe, constructor e callers atuais |
| 11 | Hotspot / país 5 GHz | Alterar o resultado da disponibilidade por país | Contexto de `SemWifiApServiceImpl` incompatível. OneROM possui versão diferente que **aplica no input real** | Recurso Wi-Fi; alternativa remove checagem de permissão junto da política. Preservar controle de acesso e revisar limites regulatórios/hardware |
| 12 | Secure screenshot | Retornar que a janela não é segura | `WindowState` não encontrado. OneROM contém o mesmo patch | Não é requisito de boot. Reduz privacidade de captura; preferir escopo explícito, nunca recriar WindowState |
| 13 | Downgrade de apps | Retornar autorização para instalar versão anterior | `PackageManagerServiceUtils` não encontrado. As três versões calculam `true` em v0, mas retornam v1 | Não é requisito de boot; há erro lógico upstream. Equivalente corrigido e hash-pinned foi implementado, sem resolver a classe ausente |
| 14 | PIN / serviço | Reduzir limiar de confirmação automática de 6 para 4 dígitos | `SyntheticPasswordManager` não encontrado. OneROM troca contexto/registrador, não resolve ausência da classe | Caminho de desbloqueio é sensível. Não alterar derivação de chave/credenciais; manter UI/serviço em acordo |
| 15 | Zipped overlays | Alterar a política de aceitação de APKs overlay comprimidos | `InstallPackageHelper` não encontrado. OneROM tem o mesmo patch | Pode ser mais que cosmético se overlays essenciais forem rejeitados; verificar overlays realmente incluídos e política atual do PackageManager |
| 16 | Google Photos | Alterar identificação/capacidades expostas por `ApplicationPackageManager` para o mod | Contexto incompatível. Variante OneROM não é prova de compatibilidade; não foi reexecutada nesta rodada | Não é requisito de boot nem garantia de benefício no serviço Google. Evitar alterações globais indevidas e verificar hooks |
| 17 | PIN / SecSettings | Oferecer configuração de confirmação com 4 dígitos | `ChooseLockPasswordFragment` encontrado em outro DEX; contexto rejeitado. OneROM igual ao Artisan | Desbloqueio/setup; portar junto com backend, sem tocar arbitrariamente credenciais existentes |
| 18 | Gestos / SecSettings | Alterar padrão/controle de navegação | `NavigationBarSettingsUtil` encontrado em outro DEX; contexto rejeitado. OneROM igual ao Artisan | Normalmente preferência; pode causar UI inconsistente com provider/overlays |
| 19 | Gestos / SettingsProvider | Alterar defaults/migração da navegação | Contexto de `SecUpgradeController` rejeitado. OneROM igual ao Artisan | Alteração em provider exige cautela; mudar apenas keys/condições necessárias e preservar migrações |

## 4. Os dois módulos que pararam e os quatro patches não executados

### `product_feature`: mDNIe e estado parcial

A receita alterou `SEC_FLOATING_FEATURE_COMMON_CONFIG_MDNIE_MODE` para `65303` antes de falhar ao localizar `SemMdnieManagerService` em services.jar. As três receitas examinadas continuam com caminho explícito para essa classe. A OneROM adicionou um helper para algumas substituições, mas **esse laço específico continua usando sed diretamente**. Copiar a receita não elimina o problema.

O encaminhamento correto é localizar o descritor/serviço efetivo em um inventário completo do doador, conferir se o contrato de modos é o mesmo e aplicar configuração/código como uma unidade. Se a implementação antiga foi substituída, é necessário portar a integração correspondente ao vendor do S10, não inventar a classe ou apenas ignorar o sed. A receita OneROM também contém diferenças funcionais em HW mDNIe e um ramo que evita certas adaptações de resolução no alvo/API 37; não é uma receita equivalente para transplantar inteira.

Os quatro itens não alcançados são:

| Item | Função | Risco e estado real |
| --- | --- | --- |
| Cutout / SystemUI | Adaptar alinhamento à câmera/recorte do S10; adiciona classe auxiliar | Layout/status bar. **Não testado** nesta execução; criação de classe suportada pelo motor não prova compatibilidade deste patch |
| DualAP / semwifi-service | Desabilitar recurso de hotspot incompatível com o alvo | Wi-Fi/tethering. **Não testado**; revisar junto das capacidades reais do chipset/vendor |
| DualAP / SecSettings | Ajustar o controle correspondente na UI | **Não testado**; deve acompanhar o serviço |
| Virtual vibration / SecSettings | Remover controle de vibração virtual não suportada | **Não testado**; conferir áudio/vibração e contraparte SoundPicker quando ativada pela receita |

Esses quatro não podem ser contados como “falharam no S24 FE” nem “foram corrigidos”. Suas versões OneROM selecionadas são iguais às Artisan.

### `signature`: falha antes da política necessária

A política antiga espera classes de PackageManager em services.jar, e a receita substitui um placeholder de certificado em `InstallPackageHelper`. A versão OneROM adiciona uma restrição de pacote/caminho/certificado para SecSettings e modifica a assinatura de `ScanPackageUtils.applyPolicy` e seus callers. É um desenho a examinar, **não um patch isolado que se pode aplicar parcialmente**.

O ponto decisivo está em `integration/artisan/apktool.sh`: no caminho de reconstrução, os arquivos `.apk` são assinados com o certificado `aosp_platform` ou `extremerom_platform`. Preservar META-INF antes de reconstruir não equivale a preservar uma assinatura Samsung válida depois de modificar o conteúdo. O diagnóstico não executou essa reconstrução, portanto não existe rejeição de APK observada; o risco surge no próximo build completo.

Mesmo a política OneROM limitada ao SecSettings precisa ser confrontada com **todos** os APKs efetivamente modificados/reassinados, seus certificados, shared UIDs e permissões. Não recomendo desligar a verificação global de assinaturas, substituir classes essenciais por stubs ou considerar essa falha cosmética.

## 5. SamsungPropsHooks: os dois passaram, mas o contrato importa

Os patches Knox e Settings aplicaram no diagnóstico real. São classes diferentes:

- `Lcom/ocin4ever/spoof/SamsungPropsHooks;`, com hooks de inicialização, propriedades e interfaces Samsung;
- `Lio/mesalabs/unica/SamsungPropsHooks;`, introduzida pelo mod Settings, com chamadas de inicialização inseridas pela receita em `Instrumentation.newApplication`.

Não é correto remover uma classe porque “o patch é opcional” e deixar `invoke-static` apontando para ela. Falta de classe/método ou erro de inicialização nesses caminhos pode derrubar processos que criam Application e comprometer a interface utilizável. É preciso validar referências, signatures, localização no classpath e comportamento conjunto. O sucesso da aplicação/criação das classes não valida execução ou promessa de serviços Knox/Google funcionais.

## 6. Busca de correções: resultados reproduzíveis

O script [`scripts/replay_upstream_candidates.py`](../scripts/replay_upstream_candidates.py) reconstitui cada input por **SHA-256 registrado no diagnóstico**, usa uma cópia temporária e aplica a alternativa upstream com resolução estrita de descritor/contexto. Inputs ausentes ou classes adicionais não capturadas viram **indisponível**, nunca “passou”. Nenhum snapshot Samsung foi incluído nesta documentação/Git; a saída publicada contém somente resultados/metadados e provas limitadas de constantes.

A primeira rodada, [42431632481](https://github.com/juliermeleal55-stack/X-Nova-OS/actions/runs/42431632481), testou 8 candidatos: **3 aplicaram, 2 foram rejeitados e 3 ficaram sem input suficiente**. A rodada seguinte inclui hotspot e verifica conservadoramente a origem dos booleanos de fingerprint. A checagem de constantes só aceita registrador definido por constante no bloco de entrada e sem escrita divergente antes do campo; caso contrário informa `unknown`, não adivinha que v2/v3 significam true/false.

### Achado decisivo: o patch pode aplicar e inverter o comportamento desejado

Na rodada [42431773264](https://github.com/juliermeleal55-stack/X-Nova-OS/actions/runs/42431773264), os 9 candidatos upstream tiveram **4 aplicações, 2 rejeições e 3 indisponíveis**. O teste de constantes do SystemUI mostrou:

| Campo em LsRune | Antes | Depois do patch OneROM |
| --- | --- | --- |
| `SECURITY_FINGERPRINT_IN_DISPLAY` | true | **false** |
| `SECURITY_FINGERPRINT_IN_DISPLAY_OPTICAL` | true | **true**, sem alteração |

Portanto, embora o patch upstream diga “Enable in-display fingerprint for S10 ultrasonic sensor”, ele não produz esse resultado no input capturado. A análise deriva valores do próprio código, sem presumir que v2 seja true e v3 false. Não considero este candidato uma correção válida para integrar. No serviço, a prova conservadora retornou `unknown`; isso não significa false, falha de aplicação ou prova de equivalência.

### Correção própria e restrita para fingerprint

Foram implementados equivalentes hash-pinned para os dois patches originais que pretendem desligar o modo óptico. Em vez de reutilizar v2/v3, a adaptação:

1. exige descritor exato, declaração booleana e uma única escrita do campo no inicializador estático;
2. exige método concreto `static constructor <clinit>()V`, diretiva `.locals` suportada e orçamento de registradores compatível;
3. aloca **um local novo**, carrega false e grava somente o campo óptico correspondente;
4. não altera o booleano antigo, flags in-display ou outros usos do registrador do doador;
5. rejeita ambiguidades/ausências e mantém o patch original imutável, verificado pelo Git blob SHA.

A verificação do replay também reconhece uma constante imediatamente anterior ao store, sem label/instrução entre ambos. Assim ela pode provar o valor da escrita produzida sem depender de inferência global de fluxo. Os testes sintéticos verificam preservação de um booleano vivo, idempotência, ausência/duplicação de campo, limite de registradores, mudança DEX e adulteração do patch.

### Resultado final do replay, sem nova coleta de firmware

Execução [42432014268](https://github.com/juliermeleal55-stack/X-Nova-OS/actions/runs/42432014268), código `4f01d546bb1d9a760b658e06d89bae38ba7ff2d0`. Resultado completo: [`evidência JSON`](evidence/s24fe-upstream-candidate-replay.json).

| Candidato | Resultado de aplicação no input exato | Decisão/limite |
| --- | --- | --- |
| OneROM fingerprint / serviço | Aplicou | Valor dos campos não provado pela checagem conservadora; não promovido automaticamente |
| OneROM fingerprint / SystemUI | Aplicou | **Descartado como correção pronta**: in-display=false e óptico=true no input capturado |
| OneROM resolução / framework | Rejeitado | Ainda exige rebase no código real |
| OneROM resolução / GameManager | Indisponível | Input da classe necessária não foi retido |
| Extreme Extra Dim / Settings | Rejeitado | Ainda exige rebase |
| Extreme Extra Dim / SystemUI | Aplicou | Candidato não ativado; falta validar contraparte Settings/compositor/vendor |
| OneROM assinatura | Indisponível | Falta classe/input; continua bloqueio prioritário |
| OneROM PIN / serviço | Indisponível | Falta classe/input; não é correção demonstrada |
| OneROM hotspot / país | Aplicou | Não ativado: também remove checagem de permissão; revisar política/hardware/regulamentação |
| **Integração própria fingerprint / serviço** | **Aplicou** | Escrita óptico=false comprovada; in-display continua não inferido pela checagem, sem alteração feita nesse campo |
| **Integração própria fingerprint / SystemUI** | **Aplicou** | **in-display=true preservado e óptico=false comprovado**, sem reutilizar booleano vivo do doador |

Total: **11 testes de candidatos/adaptações, 6 aplicações, 2 rejeições e 3 indisponíveis**. Isso **não significa 6 patches da ROM corrigidos**: o total inclui alternativas para o mesmo patch e um candidato semanticamente inadequado. Os dois equivalentes ópticos próprios estão implementados e passaram no replay de inputs reais. Falta uma nova passagem completa pela sequência de módulos e posterior reconstrução/runtime. Os totais históricos de 45 tentativas/19 falhas não foram recalculados a partir desse replay isolado.

### Correção de downgrade já implementada no código de integração

As três fontes mantêm este resultado após aplicar o patch original:

```smali
.method public static isDowngradePermitted(IZ)Z
    .locals 1
    const/4 v0, 0x1
    return v1
.end method
```

Em um método estático `(IZ)` com um local, **v1 é alias de p0**, o primeiro argumento inteiro. Não é um registrador automaticamente inexistente; alegar “VerifyError garantido” seria incorreto. O problema comprovável é que o método retorna o argumento, não o `true` calculado.

Foi cadastrado em `integration/semantic_smali.json` um equivalente que retorna `v0`, com hash do patch Artisan original, descritor e assinatura exatos, exigência de método estático concreto e rejeição de layouts não suportados. Não toca outros métodos nem cria PackageManagerServiceUtils quando ausente. Os testes verificam retorno correto, recusa de patch alterado e ausência de criação fictícia da classe.

**Limite:** corrige o erro lógico do patch, não a localização da classe no S24 FE. Não aumenta a contagem dos 26 patches aplicados no diagnóstico anterior. O recurso continua relaxando a política de downgrade; a correção não o transforma em proteção de segurança.

## 7. Ordem recomendada antes de um build completo

1. **Inventário real de classes/artefatos**: localizar descritores ausentes entre todos os JARs/DEX relevantes e confirmar decodificação. Várias classes centrais ausentes no mesmo services.jar justificam investigar empacotamento antes de portar métodos individualmente.
2. **Assinaturas e PackageManager**: mapear todos os APKs modificados, conferir certificado/UID/permissões e portar uma política restrita e consistente com callers atuais. Prioridade maior que screenshot, downgrade ou Photos.
3. **Atomicidade de módulo/configuração**: manter coleta experimental, mas registrar ou reverter alterações dependentes quando parte de um módulo falhar. Não promover um estado parcialmente anunciado como se o recurso inteiro tivesse sido adaptado.
4. **Display e biometria**: adaptar mDNIe, resolver os quatro itens não alcançados, validar a integração das correções ópticas próprias e rejeitar a alternativa SystemUI invertida, portar resolução/HDR/Extra Dim aos métodos atuais e ao vendor S10.
5. **Locksettings e SettingsProvider**: manter pares de UI/backend e migrações. Validar hooks no classpath e não apagar referências dependentes.
6. **Novo diagnóstico e reconstrução controlada**, somente no escopo autorizado: repetir aplicação, montar os DEX/APKs/JARs para identificar erros de assinatura/verificação; isso ainda não é boot.
7. **Build/instalação/boot no aparelho** dependem de autorização posterior e evidência própria: PackageManager, system_server, SystemUI, provider, desbloqueio, biometria, display e câmera. Logs necessários para associar erro a bootloop real.

Não houve alteração de kernel/vendor/câmera nativa, reparticionamento automático, limite artificial de tamanho ou novo pacote flashável nesta análise. O Alpha publicado continua sendo o pacote antigo, não um S24 FE reconstruído com estas conclusões.

## 8. Validação do trabalho de integração

- **216 testes passaram** em uma cópia limpa do commit com as alterações desta análise; os quatro diffs locais preexistentes e não relacionados foram preservados e não participaram dessa validação.
- **69 referências Artisan, 37 referências adicionais e 189 evidências de auditoria/build** verificadas por hash/tamanho; as 104 novas evidências de comparação estão incluídas nas 189.
- Verificação de fontes da revisão com as correções ópticas no GitHub: [42432014258](https://github.com/juliermeleal55-stack/X-Nova-OS/actions/runs/42432014258), **sucesso**; replay final [42432014268](https://github.com/juliermeleal55-stack/X-Nova-OS/actions/runs/42432014268), **sucesso como coleta**, com resultados individuais acima.
- Os testes do repositório incluem fixtures e smoke tests de ferramentas. Não significam que os APKs/JARs Android 17 modificados tenham sido reconstruídos ou validados no ART do doador.
- As alternativas Extreme Extra Dim/SystemUI e OneROM hotspot ficam **como evidência de candidatos**, não ativadas automaticamente. A primeira ainda exige conferir compositor/vendor e Settings; a segunda remove também uma checagem de permissão e não deve ser incorporada cegamente.
