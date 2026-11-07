<div align="center">

# Beyoud ROM
### Galaxy S10 · Exynos 9820

**Base ArtisanROM · Referências ExtremeROM · Integrações e correções próprias**

**One UI 9 experimental · SM-G973F / beyond1lte · Alpha 1**

[Download e instalação](https://github.com/juliermeleal55-stack/ArtisanRom_Beyoud/releases/tag/v0.1.0-alpha1-sm-g973f-test) · [Build concluído](https://github.com/juliermeleal55-stack/ArtisanRom_Beyoud/actions/runs/42374299228) · [Documentação](docs/BUILD-STAGES.md)

</div>

---

## Sobre o projeto

Beyoud é uma derivação experimental da base **ArtisanROM para Exynos 9820**, com referências e adaptações do ecossistema **ExtremeROM**, sistema doador **UN1CA S926B/EUX** e implementações próprias de integração, automação e correções para o Galaxy S10. Não é uma distribuição oficial dos projetos utilizados como base.

O objetivo é reunir essas adaptações em **um único ZIP completo**, com kernel integrado, patches específicos e um pipeline reproduzível. A aparência e os recursos do sistema ainda dependem de validação no aparelho; não há capturas de tela ou funcionalidades confirmadas nesta alpha.

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

Para desenvolvimento: [etapas do build](docs/BUILD-STAGES.md) · [integração](docs/INTEGRATION.md) · [pipeline alpha](docs/ALPHA.md).

```bash
python3 -m unittest discover -s tests -v
python3 scripts/verify_reference.py
python3 scripts/verify_audit.py
```

### Créditos e licenças

As integrações próprias não substituem a autoria dos componentes utilizados. Fontes, commits, créditos e licenças de terceiros permanecem nos [manifestos](manifests/), nos arquivos de referência e nas [auditorias técnicas](docs/CROSS-AUDIT.md). Respeite as licenças aplicáveis ao redistribuir código e componentes.
