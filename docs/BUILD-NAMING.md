# Numeração e identidade dos builds X-NovaOS

Os próximos builds do Galaxy S10 devem usar uma identificação externa explícita:

**X-NovaOS Alpha 3.1 — Build #N — SM-G973F — TESTE / UNTESTED**

## Como a numeração funciona

- `N` vem de `github.run_number` no workflow solicitante. Cada nova execução recebe um número crescente; falhas também ficam registradas e não devem ser renomeadas como builds bem-sucedidos.
- Uma nova tentativa da mesma execução mantém o número do build e acrescenta `Attempt-A`, derivado de `github.run_attempt`. Assim, um retry não é confundido com uma nova versão.
- `3.1` é a versão pública Alpha desta linha. O número do build muda automaticamente; uma mudança de versão Alpha precisa ser deliberada no input `alpha_version`.
- Para o S10 normal, a identificação aparece no título do Actions, no nome do artefato e do ZIP externo, no resumo da execução e em `BUILD-INFO.json`. `SHA256SUMS` cobre o ZIP entregue.

## Integridade e limites

A coleta apenas valida e dá nome ao ZIP produzido. Ela copia/linka os mesmos bytes: não reescreve o instalador, a ROM, os metadados internos, os créditos, as licenças ou a proveniência Artisan/OneROM. Por isso, identificadores internos históricos como `Beyoud` ou `alpha1` ainda podem existir dentro do pacote; não significam outra versão pública.

“Alpha”, build numerado e verificações estruturais **não** significam boot validado, instalação segura, release publicado ou autorização para flash. O build continua experimental, sem publicação de release por esse workflow. Para o perfil `content-sized`, a repartição física correspondente continua sendo requisito manual antes de qualquer instalação; o instalador não reparticiona.

A execução que já estava ativa quando esta convenção foi adicionada não é cancelada nem reiniciada só para mudar seu título/artefato. A numeração e os nomes novos passam a valer para as execuções seguintes, sem duplicar o build em andamento.
