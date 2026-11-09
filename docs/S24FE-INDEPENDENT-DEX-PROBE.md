# S24 FE — conferência independente de contêineres DEX

## Implementação

Adaptada da sonda entregue pelo usuário como resultado do trabalho solicitado ao Claude (`dex_container_probe.py` e respectivos testes). O objetivo é conferir os cabeçalhos sem usar baksmali como fonte da contagem; não diagnosticar a instalação/recovery.

- `integration/dex_container_probe.py`: leitura independente dos cabeçalhos DEX 035/037/038/039/040/041, enumeração 041 por offsets/tamanhos de contêiner, contagem `class_defs_size`.
- Rejeita versões desconhecidas, endian não suportado, cabeçalhos/tamanhos inconsistentes, lixo extra em DEX legado, contêiner truncado, ausência/duplicação de DEX primário e divergência por unidade decodificada.
- A comparação de produção confere exatamente os seletores lógicos e os diretórios da tabela de decodificação, não só o total global de arquivos.
- `integration/dex_entries.py verify-decode`, já chamado pelo overlay APKTool da base atual, executa a conferência independente **antes** da verificação existente de descritores. Qualquer erro encerra a chamada; não é um aviso opcional.
- A verificação de descritores continua responsável por identidade, duplicação e integridade das classes. Contagens iguais isoladamente não provam identidade.
- JSON `*-independent.json` registra SHA256 do arquivo de entrada, cabeçalhos por unidade e contagens; a retenção existente `dex-inventory/*.json` inclui esses arquivos nos próximos builds.
- Não há importação/chamada de baksmali na sonda independente. O consumidor compara seu resultado com os seletores e a saída real do decodificador.

**Correção da análise inicial:** DEX **040 é válido** (mapeamento API 34 do projeto). A observação anterior de que 040 deveria ser rejeitado estava errada. Versões aceitas seguem a lista explícita acima.

### Limites

É uma conferência estrutural de cabeçalhos, fronteiras e contagens, não um verificador completo de offsets de todas as tabelas, checksums internos, instruções ou comportamento do Android. A identidade dos descritores, montagem/assinatura e verificações posteriores não foram substituídas. O modo experimental não deve transformar uma rejeição dessa integridade em uma decodificação marcada como completa.

## Validação local concluída

Em export limpo da revisão atual, com somente estas alterações adicionadas:

- **259 testes passaram**, incluindo 17 testes da sonda e testes de execução do overlay com fixtures sintéticas.
- **69 referências Artisan + 37 adicionais + 208 arquivos de evidência** verificados.
- Sintaxe dos scripts shell verificada.
- Casos negativos incluem versões/tamanhos inválidos, endian incorreto, arquivo extra, arquivo sem DEX, ZIP duplicado, ausência de pasta Smali, unidades trocadas com total global idêntico e mapa divergente.
- O teste do CLI de produção demonstra bloqueio antes da verificação dependente de baksmali e geração de evidência no caminho positivo. Essa parte usa mocks e não é prova de decodificação real.

## Validação em entradas reais

Fluxo separado `.github/workflows/validate-independent-dex-s24fe.yml`:

1. Prepara a base **SM-G973F/beyond1lte** atual e suas ferramentas fixadas.
2. Baixa/extrai **somente o firmware doador** configurado, sem baixar firmware alvo, aplicar patches, compilar kernel, criar imagens ou gerar ROM.
3. Captura arquivos originais e respectivos hashes; exige **SM-S721B / S721BXXSFEZJ1**, para não confundir entradas históricas S926B.
4. Para os JAR/APK capturados, verifica hash/tamanho, inspeciona cabeçalhos, enumera unidades pelo baksmali, decodifica cada unidade e compara contagens independentes e identidade dos descritores.
5. Apaga as árvores Smali temporárias após cada arquivo. Publica apenas evidências JSON e logs; nenhum binário do firmware é enviado como artefato por esse fluxo.
6. Exige a presença de framework.jar, services.jar, SystemUI.apk e SecSettings.apk; entrada necessária ausente ou qualquer falha reprova a validação.

**Resultado real ainda pendente na publicação desta implementação.** O número de testes locais acima não substitui a conclusão desse fluxo. Não declarar o probe validado no doador até a etapa de verificação real terminar com sucesso.

## Efeito sobre a ROM

A integração é fonte para próximos builds da base S24 FE. O ZIP Alpha 2 já publicado permanece inalterado. Nenhum build completo foi disparado para esta alteração. A sonda não modifica partições, formato EROFS, payload Brotli, kernel/vendor do S10 ou os 15 patches ainda pendentes e não corrige, por si só, a parada do instalador em 3%.
