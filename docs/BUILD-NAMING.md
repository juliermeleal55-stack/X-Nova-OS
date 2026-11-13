# Numeração e identidade dos builds X-NovaOS

## Fluxo experimental atual — Alpha 3.2

A identidade planejada para o Galaxy S10 normal é:

**X-NovaOS Alpha 3.2 — Build #N — Attempt-A — SM-G973F — TWRP ROM ZIP / UNTESTED**

- `N` vem de `github.run_number`; falhas também permanecem registradas.
- `Attempt-A` vem de `github.run_attempt`, para distinguir retries.
- O artefato do Actions é nomeado `...-TWRP-ROM-ZIP-UNTESTED` e contém um ZIP
  de ROM instalável por TWRP. O container externo criado pelo Actions é apenas
  transporte; o ZIP de ROM fica dentro dele.
- O ZIP inclui imagens RAW, um `update-binary` e guards de instalação; não inclui
  nem modifica TWRP/recovery.
- O pacote é experimental e sem assinatura externa. As provas, hashes e
  proveniência ficam fora do artefato, em `out/twrp-zip-proof/` e
  `out/raw-image-proof/`.
- Não há release automática. Não houve build/flash/boot validados em hardware.

O contrato atual é **SM-G973F / `beyond1lte`**. A lista de imagens, o mapa e a
capacidade física das partições ainda requerem confirmação independente. Veja
[BUILD-STAGES.md](BUILD-STAGES.md).

## Histórico Alpha 3.1

A Alpha 3.1 e seus artefatos antigos permanecem inalterados. Seus nomes, avisos
e conteúdo descrevem o fluxo histórico, não o ZIP TWRP Alpha 3.2. Não renomeamos
nem reempacotamos um binário antigo para aparentar que ele contém o novo formato.
