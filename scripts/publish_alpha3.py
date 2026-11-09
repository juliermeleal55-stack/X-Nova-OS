#!/usr/bin/env python3
"""Publish an Actions-linked prerelease only after the package build job succeeds."""
import json
import os
from pathlib import Path
import subprocess
import tempfile


def gh(*args):
    return subprocess.check_output(['gh', *args], text=True)


def release_notes(artifact, repo, run_id, sha):
    size = artifact['size_in_bytes']
    if artifact.get('expired') or size <= 0:
        raise ValueError('Missing/expired/empty ROM artifact')
    url = f'https://github.com/{repo}/actions/runs/{run_id}'
    return f'''# X-Nova OS — Alpha 3.1 S24 FE — SM-G973F — TESTE / UNTESTED

> **Sem validação de instalação/boot em hardware. Não usar como sistema principal.**

## Download completo, sem divisão

**[BAIXAR PELO ACTIONS]({url}/artifacts/{artifact['id']})**

O artefato `{artifact['name']}` tem **{size:,} bytes**. Pode exigir login GitHub.
Extraia o contêiner do Actions e use o ZIP instalável que está dentro dele, não o contêiner externo.
O binário ultrapassa o limite por arquivo do Releases; é distribuído inteiro pelo Actions, como nas versões anteriores.
**Expira em {artifact['expires_at']}**, podendo ser removido antes. Não é hospedagem permanente.

## Esta versão

- Exclusiva para **Galaxy S10 Exynos SM-G973F / beyond1lte**.
- Sistema/framework doador **S24 FE SM-S721B S721BXXSFEZJ1**; kernel/vendor Exynos9820 do S10 preservados.
- Procedimento/binary OTA da **ArtisanROM S10**, com origem exata conferida no build. O instalador anterior já tinha essa origem; não é alegada troca por um binário diferente.
- Corrigido aborto confirmado da Alpha 3: removidas chamadas Edify incondicionais a aliases ausentes como `/system`. O recovery gerencia a desmontagem; a proteção bloqueia qualquer alvo ainda montado antes da gravação.
- Verificação do filesystem gerado, incluindo descompressão dos arquivos EROFS no host antes de converter a imagem.
- Comparação integral do payload Brotli descomprimido com a saída original img2sdat.
- Mensagens de início/conclusão da escrita de system e preservação de verificações físicas de capacidade.
- Sonda DEX independente integrada, além da identidade dos descritores.

**O relato de parada em 3% e o erro EROFS posterior motivaram estas proteções. A causa original não foi comprovada pelos logs disponíveis; esta versão não é anunciada como correção de travamento ou boot validada.**

## Antes de instalar

Faça backup e tenha um procedimento independente de retorno ao stock. Carregue a bateria.
Confira `SHA256SUMS`, `WARNING.txt` e **REQUIRED-IMAGE-SIZES.json** dentro do pacote.
O modo **content-sized** não impõe teto stock/ExtremeROM/7 GB, mas cada partição física deve comportar sua imagem ANTES da instalação.
**Não há reparticionamento automático. Não remova as proteções nem altere/recompacte o ZIP.**
O modo experimental tolera falhas individuais de patches/módulos; não significa que todos foram aplicados.
Montagem de APK/DEX, assinatura, imagens, integridade do payload e ZIP continuam podendo reprovar o build.
Câmera, rádio, biometria, criptografia, gráficos e demais funções não foram validados no aparelho.

Alpha 3.1 é a identificação pública; nomes internos Beyoud/alpha1 legados do pipeline podem permanecer. Não houve edição manual pós-build do ZIP.
Base Artisan/Extreme e demais créditos/licenças/proveniência permanecem preservados no código.

## Fonte e evidência

- [Execução do build]({url})
- [Código exato](https://github.com/{repo}/tree/{sha})
- [Revisão do instalador](https://github.com/{repo}/blob/{sha}/docs/S24FE-ALPHA3-INSTALLER.md)
- Checksum do ZIP instalável: consulte `SHA256SUMS` no pacote.
- Digest do contêiner Actions, **não do ZIP interno**: `{artifact.get('digest', 'não informado pela API')}`.
'''


def main():
    repo = os.environ['GITHUB_REPOSITORY']
    run_id = os.environ['GITHUB_RUN_ID']
    sha = os.environ['GITHUB_SHA']
    data = json.loads(gh('api', f'repos/{repo}/actions/runs/{run_id}/artifacts?per_page=100'))
    artifacts = [a for a in data['artifacts'] if a['name'] == 'Beyoud-beyond1lte-alpha1-UNTESTED']
    if len(artifacts) != 1:
        raise ValueError('Expected exactly one validated complete-ROM artifact')
    notes = release_notes(artifacts[0], repo, run_id, sha)
    # Run suffix prevents overwriting an older binary/release on a later rebuild.
    tag = f'v0.1.0-alpha3.1-sm-g973f-s24fe-test-{run_id}'
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / 'notes.md'
        path.write_text(notes)
        subprocess.run(['gh', 'release', 'create', tag, '--repo', repo, '--target', sha,
                        '--prerelease', '--title', 'X-Nova OS — Galaxy S10 — Alpha 3.1 S24 FE — TESTE / UNTESTED',
                        '--notes-file', str(path)], check=True)


if __name__ == '__main__':
    main()
