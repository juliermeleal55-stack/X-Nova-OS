# Avanço: decodificação integral de DEX lógico

> Resultado mais recente: [diagnóstico após correção dos DEX lógicos](S24-FE-LOGICAL-DEX-RESULTS.md). Este documento preserva o registro da etapa anterior.

## Implementado nesta revisão

A hipótese identificada na [análise da Impulse UI9](IMPULSE-UI9-ANALYSIS.md) agora tem uma implementação própria no pipeline ativo:

- Enumeração pelo `baksmali list dex` do APK/JAR original, incluindo unidades internas como `classes.dex/2`.
- Ordem numérica dos arquivos físicos e das unidades internas, com mapa explícito para diretórios smali e arquivos de saída distintos.
- Rejeição de seletores duplicados, ausentes, não contíguos ou fora dos arquivos físicos presentes no ZIP.
- Comparação dos **descritores completos**, não somente da contagem, entre cada unidade original (`baksmali list classes`) e o smali decodificado. Rejeição de perdas, duplicações e cabeçalhos que não correspondam ao caminho.
- Metadados de API por unidade lógica preservados. Todos os DEX são remontados separadamente; não há restauração de contêiner físico antigo junto de suas unidades remontadas.
- Validação pré-assembly da presença das classes originais e da unicidade entre DEX. Novos DEX contíguos adicionados por patches de classe, como SamsungPropsHooks, recebem API explícita baseada nas unidades de origem, em vez de falhar por ausência de metadata.
- Cache de decodificação só é reutilizado quando há marcador de conclusão. Diretório criado por uma tentativa incompleta ou decoder anterior não é tratado como sucesso pelo helper DECODE_APK.
- Evidência pequena em `out/beyoud-logs/dex-inventory`: hash SHA-256 do APK/JAR, magic dos arquivos físicos, mapa lógico, contagens e status. Não publica classes Samsung no Git.

Arquivos principais: `integration/dex_entries.py`, `integration/artisan/apktool.sh`, `integration/preflight_policy.py`.

## Validação e limites

**225 testes passaram em cópia limpa**, excluindo os quatro diffs locais preexistentes. Os testes novos cobrem ordenação, contêiner com unidade interna + outro DEX físico, execução dos loops shell de decode/assembly com ferramentas simuladas, integridade de descritores, metadados dos novos DEX, perda/duplicação de classes e cache incompleto. As referências continuam verificadas por hash/tamanho; sintaxe shell verificada.

Esses testes **não constituem execução do decoder novo no firmware Samsung**. A confirmação depende da nova rodada diagnóstica. O fato de o decoder anterior não enumerar explicitamente as unidades internas está corrigido no código; a conclusão de que isso causava todas as classes ausentes ainda precisa dos inventários reais.

Os totais anteriores de 45 tentativas, 19 falhas de patch e 2 falhas de módulo continuam sendo os últimos resultados completos conhecidos. Não os substituímos por contagem de testes sintéticos.

## O que continua pendente

- Confirmar no doador quais classes centrais reaparecem após a enumeração completa e reavaliar os patches correspondentes.
- Adaptar assinatura, mDNIe, resolução/HDR, Extra Dim e demais contextos que continuarem divergentes.
- Completar os quatro patches antes não alcançados e validar consistência de módulo/configuração.
- As duas correções ópticas próprias continuam ativas; não foi importado o patch OneROM/SystemUI de semântica invertida.
- O erro lógico do downgrade foi corrigido anteriormente; localizar a classe e validar a aplicação real continua necessário.
- Reconstrução de APK/JAR da ROM, imagens, ZIP, instalação e boot não estão validados por esta entrega.

## Nova execução autorizada

O pedido de diagnóstico S24 FE continua com `diagnostic_only: true` e tolerância explícita aos erros individuais para coletá-los. A rodada se limita a preparação/download/extração/decodificação/aplicação/relatório. **Não compila kernel, não reconstrói os APKs/JARs finais da ROM e não gera imagens ou ZIP flashável.**

Execução iniciada com esta implementação: [42433286986](https://github.com/juliermeleal55-stack/X-Nova-OS/actions/runs/42433286986), código `98128c9`. No registro inicial, a validação da integração já havia passado e o runner preparava dependências. O resultado dos patches ainda não estava disponível; nenhum ganho de contagem foi presumido.
