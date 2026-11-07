#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Publish the ORIGINAL size sidecar from the successful alpha, not estimates.

Run on a GitHub runner with network access to artifact storage. Downloads the
artifact archive to disk but reads only its small JSON sidecar; never extracts
or rebuilds the ROM. Does not execute any artifact contents.
"""
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile

ARTIFACT = 13578335876
RUN = 42374299228
COMMIT = 'bff163ad03a1e208ca08bb6b727eb557b2d93243'
NAME = 'REQUIRED-IMAGE-SIZES.json'


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def main():
    repo = os.environ['GH_REPO']
    base = f'https://api.github.com/repos/{repo}'
    headers = {'Authorization': 'Bearer ' + os.environ['GH_TOKEN'],
               'Accept': 'application/vnd.github+json', 'User-Agent': 'X-Nova-OS-size-publisher'}
    def metadata(path):
        with urllib.request.urlopen(urllib.request.Request(base + path, headers=headers), timeout=60) as response:
            return json.load(response)
    run = metadata(f'/actions/runs/{RUN}')
    artifact = metadata(f'/actions/artifacts/{ARTIFACT}')
    if run['conclusion'] != 'success' or run['head_sha'] != COMMIT or artifact['expired'] or artifact['workflow_run']['id'] != RUN:
        raise ValueError('Unexpected, expired or unsuccessful source artifact')
    # Obtain the signed URL WITHOUT forwarding the GitHub token to blob storage.
    opener = urllib.request.build_opener(NoRedirect)
    try:
        opener.open(urllib.request.Request(base + f'/actions/artifacts/{ARTIFACT}/zip', headers=headers), timeout=60)
    except urllib.error.HTTPError as error:
        if error.code != 302:
            raise
        location = error.headers['Location']
    else:
        raise ValueError('Expected signed artifact storage redirect')
    if urllib.parse.urlsplit(location).scheme != 'https':
        raise ValueError('Insecure artifact storage redirect')
    with tempfile.TemporaryDirectory(prefix='xnova-size-report-') as tmp:
        archive = Path(tmp) / 'artifact.zip'
        with urllib.request.urlopen(location, timeout=300) as source, archive.open('wb') as output:
            shutil.copyfileobj(source, output, length=1024 * 1024)
        with zipfile.ZipFile(archive) as source:
            candidates = [item for item in source.infolist() if PurePosixPath(item.filename).name == NAME]
            if len(candidates) != 1 or not 0 < candidates[0].file_size <= 1024 * 1024:
                raise ValueError('Missing, ambiguous or oversized original size report')
            raw = source.read(candidates[0])
        data = json.loads(raw)
        sizes = data['image_size_bytes']
        if (data.get('layout') != 'content-sized' or data.get('model') != 'SM-G973F'
                or 'system' not in sizes or set(sizes) - {'system','vendor','product','odm','prism','optics'}
                or any(type(size) is not int or size <= 0 for size in sizes.values())):
            raise ValueError('Invalid original image requirements')
        Path(NAME).write_bytes(raw)  # Preserve the exact original bytes.
        for partition, size in sorted(sizes.items()):
            print(f'{partition}: {size} bytes | {size / 1048576:.2f} MiB | {size / 1073741824:.3f} GiB', flush=True)


if __name__ == '__main__':
    main()
