# X-Nova OS

## Nome e significado

**X-Nova OS** é a identidade pública do projeto anteriormente apresentado como Beyoud.

| Elemento | Significado |
| :--- | :--- |
| **X** | O número romano **10**, representando o **Galaxy S10**, e uma referência ao **Exynos**. |
| **Nova** | Uma **supernova**: energia pura e renovada. |

**Uma nova energia para o Galaxy S10.**

## Quando a identidade entra na ROM

A apresentação pública, o README e o título do lançamento passam a usar **X-Nova OS**. Por decisão do proprietário, a aplicação do nome e da identidade visual **dentro do sistema fica reservada para uma futura versão estável**. Não há data definida nem uma versão estável validada neste momento.

A Alpha 1 atual permanece experimental e sem alterações binárias. Não se modificam retroativamente:

- O ZIP já compilado, seus checksums e seu conteúdo.
- O nome do artefato do Actions e os caminhos usados para download.
- A tag e o commit da alpha publicada.
- Nomes de pacotes, propriedades Android, interfaces do sistema e recursos visuais da ROM.
- Identificadores técnicos `Beyoud`/`BEYOUD_*`, caminhos de scripts e contratos de testes existentes.

Esses identificadores legados mantêm a compatibilidade do pipeline e não significam que a ROM já recebeu a nova identidade. A futura migração interna deve ser implementada, revisada e testada separadamente antes de publicar uma versão estável. Não se deve usar substituição global de texto para alterar propriedades, caminhos ou componentes do sistema.

## Base e estado

O projeto usa a base ArtisanROM para Exynos 9820, referências ExtremeROM, doador UN1CA S926B/EUX e integrações/correções próprias. Créditos, licenças e proveniência dos componentes continuam preservados. A mudança de nome não altera a autoria desses componentes.

O alvo da alpha é **SM-G973F / beyond1lte**. Build concluído não comprova boot, estabilidade ou funcionamento em hardware. O pacote atual exige repartição personalizada conforme `REQUIRED-IMAGE-SIZES.json` e não reparticiona automaticamente.

[Voltar à apresentação](../README.md) · [Alpha de teste](https://github.com/juliermeleal55-stack/ArtisanRom_Beyoud/releases/tag/v0.1.0-alpha1-sm-g973f-test)
