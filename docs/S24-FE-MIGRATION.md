# Migração do sistema doador — Galaxy S24 FE

## Escopo autorizado

Trocar somente o sistema/framework doador do S926B pelo **Galaxy S24 FE SM-S721B/EUX**. Permanecem a base de build ArtisanROM histórica, alvo SM-G973F/beyond1lte, kernel/vendor do S10 e os patches de integração. Nenhum build completo é iniciado por esta mudança: o arquivo de pedido de alpha não foi alterado.

**O ZIP Alpha 1 publicado permanece com o doador S926B.** Esta migração vale para workspaces novos e um próximo build autorizado. Não houve troca do binário de lançamento, checksum, tag ou identidade interna da ROM.

## Fonte fixada

- Configuração: `unica/configs/r12s_native.sh`, projeto `DaDevMikey/OneROM`.
- Commit: `541074191937f2d7c033be7a10cf5d99146cc98f`.
- Perfil/proveniência: `integration/donors/s24fe.json`.
- Configuração original preservada byte a byte: `integration/donors/s24fe.sh`.
- Modelo/região: **SM-S721B / EUX**.
- AP de referência: **S721BXXSFEZJ1**.
- A fonte declara SDK 37, shipping API 34, VNDK 34 e ausência de system_ext. **Essas são declarações ainda não confirmadas no firmware Samsung.** O nome One UI 9 usado pelo projeto de origem não é verificação independente da versão real.

O firmware completo não foi baixado nem inspecionado nesta migração. A disponibilidade do AP e a compatibilidade do framework não foram demonstradas. Créditos, licença e origem não são substituídos por autoria própria.

## Alterações de integração

1. O adaptador `integration/artisan/essi_64.sh` agora carrega a configuração S24 FE fixada, em vez de importar `integration/unica/essi.sh` do S926B. Mantém aliases de SDK/API usados pelas ferramentas. Não altera TARGET_PLATFORM ou firmware do S10.
2. Isso evita herdar os valores específicos do S926B: display QHD, faixas de frequência, NFC, impressão digital e flags nativas que não foram demonstradas no S24 FE. As declarações de origem passam a ser as do perfil r12s. São valores do **doador**, não habilitação de hardware novo no S10.
3. O preparador verifica o SHA-256 da configuração, registra perfil/commit do novo doador no marcador da workspace e mantém separada a revisão de tooling UN1CA usada pelas ferramentas. As referências antigas continuam para histórico; o fato de existirem não as torna o doador ativo.
4. O perfil fixa a versão completa de quatro partes em `reference_version`, registrada por uma consulta SmartDownload anterior. O probe consulta essa versão diretamente, verifica a resposta integral e o AP e só então grava o firmware lock. **Não há fallback para latest** no doador; se o pacote exato não puder ser consultado/baixado, a etapa deve parar. O firmware stock do alvo continua sendo resolvido separadamente.
5. A inspeção após extração confere modelo/região, SDK, AP, a versão completa exata e presença inesperada de system_ext. Divergências exigem adaptar explicitamente o perfil, não desativar a verificação nem declarar SDK falso.
6. Manifesto geral, coletor de evidências, verificação de auditoria, README e documentação passam a distinguir configuração futura S24 FE do pacote S926B já publicado.
7. Identidade/receita do build inclui o conteúdo da integração e manifesto; use workspace nova e novo firmware lock, sem reutilizar árvores extraídas ou resultados de recompilação do S926B.

## Validação feita

- **186 testes passaram** em cópia limpa contendo apenas as mudanças desta migração e o HEAD publicado.
- **69 referências Artisan, 37 referências da integração prévia e 65 evidências de auditoria verificadas.**
- Sintaxe Bash dos dois arquivos de configuração e compilação Python dos módulos alterados verificadas.
- Regressões novas: seleção SM-S721B/r12s, não herdar flags de display S926B, preservação do alvo SM-G973F, rejeição de SDK incorreto, system_ext inesperado, AP diferente, doador antigo e resolução/lock do novo par de firmwares.

Os testes usam fixtures e mocks. **Não comprovam download, patches aplicados ao S24 FE real, tamanho das imagens, instalação nem boot.** As quatro alterações locais alheias à migração não foram incorporadas.

## Próximos passos e limites

Após autorização para executar: consultar a disponibilidade real do SM-S721B/EUX, validar o AP, baixar/extrair, confrontar propriedades e arquivos com o schema e adaptar os patches aos resultados reais. Só então será possível verificar as imagens e um novo ZIP.

A troca do doador **não resolve por si só** os erros anteriores do recovery: falha de verificação de partição e `Invalid zip file format` ocorrem antes do boot do sistema. A revisão do instalador está documentada em [INSTALLER-REVIEW.md](INSTALLER-REVIEW.md) e permanece incluída no código do próximo build.
