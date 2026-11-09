# Alpha 3 S24 FE — instalador ArtisanROM S10 e integridade das imagens

## Diagnóstico e origem

Os logs recebidos mostram erro EROFS ao ler diretórios do system atualmente presente, mas não contêm a instalação parada em 3%. Não permitem provar a causa inicial, nem afirmar que trocar o updater resolverá o caso.

A revisão confirmou que o pacote anterior **já usava o procedimento e o binário OTA da ArtisanROM S10**, revisão `5638a7f66cdf8bc9dd43f087a96f7dfa4f9e6954`. O banner ExtremeROM está no próprio script Artisan junto com os créditos Artisan e UN1CA. Não é prova de outro instalador. Não foi feita uma falsa “troca de binário”: agora a origem exata é obrigatoriamente conferida antes de empacotar.

O binário original foi baixado diretamente da revisão fixada e conferido de fato, independentemente dos mocks de teste:

- Caminho: `prebuilts/bootable/deprecated-ota/updater`.
- Tamanho: **2.362.000 bytes**.
- Git blob: `1c284c9122280882fed25ce6e3f40747f938051e`.
- SHA256: `6932d5f1fbcc0215348cc39c7ac08e246b0eec340e90f33c1c92645794a0e6b3`.

## Mudanças implementadas

1. **Verificação de origem do updater Artisan** antes de copiá-lo para update-binary. Qualquer substituição ou diferença de bytes reprova o empacotamento.
2. **Checagem do filesystem antes de img2sdat**: expande temporariamente imagens sparse; EROFS passa por `fsck.erofs --extract` sem diretório de extração. Na versão fixada da ferramenta essa opção verifica todos os encodings dos arquivos sem extrair a árvore. Ext4 usa `e2fsck -f -n`, sem reparo. Formato desconhecido/falha de ferramenta é fatal.
3. **Roundtrip Brotli integral**: compara os bytes descomprimidos com o new.dat original, com memória limitada, antes de apagar o original. Não basta conferir CRC do ZIP externo.
4. **Preparação explícita no recovery**: solicita desmontagem dos aliases conhecidos, incluindo `/system_root`, `/system`, `/vendor` e `/product`. Não formata e não reparticiona.
5. **Proteção adicional no helper de leitura**: bloqueia uma partição alvo ainda montada (`ERR_MOUNTED`), mesmo que tenha capacidade suficiente; falha de leitura da tabela de mounts também bloqueia (`ERR_MOUNT_READ`). A verificação de capacidade física continua ativa.
6. **Mensagens de início/conclusão de system**, com instrução de preservar recovery.log em caso de E1001. Não é alegada medição contínua de escrita nem reparo de um eventual deadlock do updater.
7. Mantida a **sonda DEX independente** da base atual e a verificação de identidade dos descritores.

Não foram alterados o kernel/vendor Exynos9820 do S10, formato de armazenamento do usuário ou nomes de partições. Não foram removidos limites físicos de segurança. O build continua `content-sized`, sem teto fixo stock/ExtremeROM/7 GB e sem repartição automática. Patches/módulos individuais continuam experimentalmente tolerados; erros de integridade, montagem, assinatura, imagens ou ZIP não viram sucesso.

## Testes

Em export limpo, somente com estas alterações:

- **271 testes passaram**.
- **69 referências Artisan + 37 adicionais + 208 arquivos de evidência** conferidos.
- Todos os scripts shell passaram na verificação de sintaxe.
- Casos negativos incluem filesystem desconhecido, falha de fsck/conversão sparse, Brotli truncado/diferente/com bytes extras, alvo montado e tabela de mounts indisponível.
- Os testes unitários de fsck/Brotli usam processos simulados e NÃO demonstram uma imagem real válida. As ferramentas reais serão exigidas no empacotamento do build; qualquer falha interrompe a geração.
- A conferência do binário Artisan original acima foi real, não simulada.

A validação real da sonda DEX iniciada anteriormente (`42637545811`) ainda estava compilando ferramentas na última consulta desta revisão. Seu resultado final não foi presumido; o build novo também exige a sonda durante a decodificação.

## Build e lançamento

O pedido Alpha 3 mantém **SM-G973F/beyond1lte**, doador **SM-S721B/S24 FE**, modo experimental e layout content-sized. O job de publicação depende da conclusão bem-sucedida do build reutilizável, que inclui checagem do pacote e upload.

Somente então cria uma pré-release Alpha 3 com link para o artefato inteiro do Actions, sem dividir, editar ou recomprimir manualmente o ZIP. A nota informa tamanho/expiração reais, SHA256SUMS interno, requisitos físicos e ausência de validação de boot. Se o build ou a publicação falharem, não há alegação de ROM nova publicada. Os nomes internos legados Beyoud/alpha1 podem permanecer; Alpha 3 é a versão pública da nova execução.

**Não é uma correção comprovada do travamento em hardware.** É um endurecimento verificável do caminho Artisan contra imagens/payloads inválidos e gravação sobre filesystem ainda montado. Sem o log da tentativa real, o diagnóstico original permanece em aberto.

### Execução iniciada

- Código: `d5ca1a0`.
- [Build Alpha 3 e publicação condicionada — 42640152539](https://github.com/juliermeleal55-stack/X-Nova-OS/actions/runs/42640152539).
- Iniciado e em andamento na última consulta. Conclusão da compilação, geração do ZIP, checagens reais de imagem e publicação ainda não confirmadas.
