<div align="center">

# X-Nova OS
### Galaxy S10 · Exynos 9820

**Base ArtisanROM · Referências ExtremeROM · Integrações e correções próprias**

**One UI 9 experimental · SM-G973F / beyond1lte · Alpha 1**

[Download e instalação](https://github.com/juliermeleal55-stack/ArtisanRom_Beyoud/releases/tag/v0.1.0-alpha1-sm-g973f-test) · [Build concluído](https://github.com/juliermeleal55-stack/ArtisanRom_Beyoud/actions/runs/42374299228) · [Documentação](docs/BUILD-STAGES.md)

</div>

---

## O significado de X-Nova

| Elemento | Significado |
| :--- | :--- |
| **X** | O número romano **10**, em homenagem ao **Galaxy S10**, e uma referência ao **Exynos**. |
| **Nova** | A ideia de uma **supernova**: energia pura e renovada. |

**X-Nova OS — uma nova energia para o Galaxy S10.**

> **Identidade em transição:** X-Nova OS é o novo nome público do projeto. O nome e a identidade visual **dentro da ROM serão incorporados somente em uma futura versão estável**. A Alpha 1 já compilada permanece sem alterações: ZIP, checksum, artefatos e identificadores técnicos ainda podem apresentar o nome legado **Beyoud**. Isso não indica outro pacote nem uma versão estável.

## Sobre o projeto

X-Nova OS é uma derivação experimental da base **ArtisanROM para Exynos 9820**, com referências e adaptações do ecossistema **ExtremeROM**, sistema doador **S24 FE SM-S721B/EUX em migração** e implementações próprias de integração, automação e correções para o Galaxy S10. Não é uma distribuição oficial dos projetos utilizados como base.

O objetivo é reunir essas adaptações em **um único ZIP completo**, com kernel integrado, patches específicos e um pipeline reproduzível. A aparência e os recursos do sistema ainda dependem de validação no aparelho; não há capturas de tela ou funcionalidades confirmadas nesta alpha.

## Migração do doador

O código do próximo build está configurado para **Galaxy S24 FE (SM-S721B/EUX)**. O firmware e a compatibilidade ainda precisam de validação real; a referência declara API 37, mas isso não comprova a versão do pacote Samsung. **O download Alpha 1 continua sendo o build anterior com doador S926B**, não uma ROM S24 FE recompilada. Kernel/vendor do S10, alvo SM-G973F e base de build Artisan permanecem. [Detalhes da migração](docs/S24-FE-MIGRATION.md).

## Estado da alpha

| Item | Situação |
| :--- | :--- |
| Aparelho desta versão | **Galaxy S10 SM-G973F — beyond1lte** |
| Plataforma | Exynos 9820 |
| Build e empacotamento | **Concluídos** — Alpha 1 |
| Pacote | ZIP único · `CUSTOM-REPARTITION-REQUIRED` · `UNTESTED` |
| Boot e recursos no aparelho | **Não validados** |
| Uso recomendado | Testes avançados; não usar em celular principal |

> **Atenção:** o build tolerou falhas de patches/módulos em modo experimental. Compilação concluída não comprova que todas as alterações foram aplicadas, que a ROM inicia ou que chamadas, câmera, biometria e criptografia funcionam. Esta versão não é destinada ao S10+, S10e, Snapdragon ou outros modelos.

## Layout da ROM

A alpha usa **partições estáticas**, com imagens dimensionadas pelo conteúdo — sem impor os tamanhos fixos stock ou Default da ExtremeROM durante o build.

| Partição | Dimensionamento |
| :--- | :--- |
| `system` | Conforme a imagem final gerada |
| `vendor` | Conforme a imagem final gerada |
| `product` | Conforme a imagem final gerada |
| `odm` | Conforme a imagem final gerada |
| `prism` | Conforme a imagem final gerada |
| `optics` | Conforme a imagem final gerada |

**Os requisitos reais em bytes estão em `REQUIRED-IMAGE-SIZES.json`, distribuído com o pacote.** Não use o tamanho comprimido do ZIP para dimensionar partições. O testador precisa preparar um layout compatível **antes de instalar**. O instalador confere a capacidade física antes das gravações e **não reparticiona automaticamente**.

## Download e instalação

1. Abra a [pré-release de teste](https://github.com/juliermeleal55-stack/ArtisanRom_Beyoud/releases/tag/v0.1.0-alpha1-sm-g973f-test) e leia todos os avisos e pré-requisitos.
2. Baixe o artefato do Actions e extraia o contêiner externo. O instalável é o **ZIP interno da ROM**.
3. Confira `SHA256SUMS`, faça backup externo e prepare a repartição conforme `REQUIRED-IMAGE-SIZES.json`.
4. Siga o roteiro experimental da pré-release usando recovery compatível com o **SM-G973F**. Não é um pacote Odin nem uma atualização validada sobre outra ROM.

**Download temporário:** o artefato atual expira em **14/11/2026, às 14:34 UTC / 11:34 de Brasília**, salvo remoção antecipada. O lançamento aponta para o arquivo do Actions; não há binário hospedado permanentemente no Releases.

## Organização do código

```text
devices/       Configurações e estado dos aparelhos
integration/   Adaptações, patches e políticas de build
scripts/       Preparação, compilação e coleta do pacote
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
