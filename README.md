<div align="center">

# X-Nova OS
### Galaxy S10 · Exynos 9820

**Base ArtisanROM · Referências OneROM/ExtremeROM · Integrações próprias**

**Alpha 3.2 · SM-G973F / `beyond1lte` · ZIP para TWRP · NÃO TESTADA**

[Build e limites](docs/BUILD-STAGES.md) · [Integração e proveniência](docs/INTEGRATION.md) · [Auditoria OneROM](docs/ONEROM-AUDIT.md) · [Alpha histórica](https://github.com/juliermeleal55-stack/X-Nova-OS/releases/tag/v0.1.0-alpha3.1-sm-g973f-s24fe-test-43117943493)

</div>

---

## O significado de X-Nova

| Elemento | Significado |
| :--- | :--- |
| **X** | O número romano **10**, em homenagem ao **Galaxy S10**, e uma referência ao **Exynos**. |
| **Nova** | A ideia de uma **supernova**: energia pura e renovada. |

**X-Nova OS — uma nova energia para o Galaxy S10.**

## Estado da entrega

O artefato da Alpha 3.2 é **um ZIP de ROM instalável pelo protocolo de atualização do TWRP**, contendo imagens de partição RAW `.img` e um `update-binary` do instalador. O pacote **não inclui nem modifica o recovery**. A Alpha 3.1 histórica não foi substituída nem modificada. O ZIP desta Alpha ainda não foi gerado nem validado em aparelho.

| Item | Situação do fluxo novo |
| :--- | :--- |
| Alvo principal | **Galaxy S10 Exynos SM-G973F — `beyond1lte`** |
| Entrega | Um ZIP instalável pelo TWRP; imagens `.img` RAW dentro do pacote |
| Recovery | TWRP é o método; nenhum recovery é incluído ou alterado |
| Instalador | Usa a interface `META-INF/com/google/android/update-binary`; pacote experimental e não assinado |
| Flash, instalação e boot no aparelho | **Não executados nem validados** |
| Publicação | Sem release automática |

O ZIP de ROM dentro do Actions pode vir dentro de outro ZIP de transporte ao baixar o artefato. O arquivo de ROM instalável estará dentro desse contêiner. O instalador verifica modelo, espaço/capacidade, partições desmontadas e hashes antes de gravar; ainda assim, as gravações não são atômicas e uma interrupção pode deixar o aparelho sem boot.

## Imagens incluídas

Para o alvo principal, são exigidos `system.img`, `vendor.img`, `product.img`, `boot.img`, `dtb.img` e `dtbo.img`. A configuração S10 declara layout estático, ext4 e `TARGET_HAS_SYSTEM_EXT=false`, então `system_ext` é tratado dentro de `system`, não como partição separada.

Outras imagens filesystem (`odm`, `prism`, `optics`, `vendor_dlkm`, `odm_dlkm`, `system_dlkm`) e componentes de boot opcionais (`init_boot`, `vendor_boot`) só entram se a árvore do build e os metadados do alvo sustentarem esses papéis. O pacote não contém `recovery.img`, `userdata`, EFS, modem, `new.dat.br` ou `transfer.list`; ele não redimensiona nem reparte o dispositivo.

A lista acima decorre das fontes/configuração e não substitui a confirmação da tabela/capacidades físicas do aparelho. **Não instale o ZIP** até que o procedimento seja testado no modelo exato, com backup e método de restauração.

## Sobre o projeto

X-Nova OS é uma derivação experimental da base **ArtisanROM para Exynos 9820**, com referências e adaptações do ecossistema OneROM/ExtremeROM, sistema doador **S24 FE SM-S721B/EUX em migração** e implementações próprias de integração, automação e correções para o Galaxy S10. Não é uma distribuição oficial dos projetos utilizados como base.

Workspaces novas do S10 normal recebem as árvores OneROM fixadas de `target/beyond1lte/` e `platform/exynos9820/`, com créditos, licenças, proveniência e preservação dos arquivos Artisan substituídos. Isso não valida a portagem nem modifica ou distribui recovery. Consulte [a auditoria OneROM](docs/ONEROM-AUDIT.md) e [a integração](docs/INTEGRATION.md).

O projeto não afirma que a ROM inicia ou que chamadas, câmera, biometria, criptografia e outros recursos funcionam. Esta configuração é para SM-G973F; não infira suporte ao S10+, S10e ou variantes Snapdragon.

## Organização do código

```text
devices/       Configurações e estado dos aparelhos
integration/   Adaptações, patches e políticas de build
scripts/       Preparação, compilação e validação do ZIP
manifests/     Fontes, revisões fixadas e proveniência
reference/     Referências upstream preservadas
tests/         Regressões da integração
docs/          Instruções, auditorias e histórico técnico
```

Identidade do projeto: [nome e política de transição](docs/X-NOVA-OS.md).

Para desenvolvimento: [etapas do build](docs/BUILD-STAGES.md) · [integração](docs/INTEGRATION.md) · [pipeline alpha](docs/ALPHA.md).

```bash
python3 -m unittest discover -s tests -v
python3 scripts/verify_reference.py
python3 scripts/verify_audit.py
```

### Créditos e licenças

As integrações próprias não substituem a autoria dos componentes utilizados. Fontes, commits, créditos e licenças de terceiros permanecem nos [manifestos](manifests/), nos arquivos de referência e nas [auditorias técnicas](docs/CROSS-AUDIT.md). Respeite as licenças aplicáveis ao redistribuir código e componentes.
