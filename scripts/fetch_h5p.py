"""Fetch free upstream H5P code; never downloads the hosted lecture video."""
import hashlib
import io
import json
from pathlib import Path
import zipfile
import requests
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'tools' / 'h5p'
DEST.mkdir(parents=True, exist_ok=True)
records = []
lock_path = ROOT / 'h5p' / 'upstream-lock.json'
locked = {item['file']: item for item in json.loads(lock_path.read_text(encoding='utf-8'))} if lock_path.exists() else {}
native=ROOT/'h5p/Quantum_Formalism_Interactive.h5p'
# A published native package preserves its complete library versions even if Hub updates.
for name in ([] if native.exists() else ['H5P.InteractiveVideo', 'H5P.MultiChoice', 'H5P.Summary']):
    url = 'https://api.h5p.org/v1/content-types/' + name
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    assert zipfile.is_zipfile(io.BytesIO(response.content)), f'Not an H5P ZIP: {url}'
    filename = name + '.h5p'
    if filename in locked:
        assert hashlib.sha256(response.content).hexdigest() == locked[filename]['sha256'], 'H5P Hub changed: preserve the committed native package, or review and update upstream-lock.json explicitly.'
    (DEST / filename).write_bytes(response.content)
    records.append(dict(file=filename, url=url, sha256=hashlib.sha256(response.content).hexdigest()))
    print(filename, len(response.content), flush=True)
for repo, folder in [('h5p-php-library', 'core'), ('h5p-editor-php-library', 'editor')]:
    if folder in locked:
        revision = locked[folder]['revision']
    else:
        metadata = requests.get(f'https://api.github.com/repos/h5p/{repo}/commits/master', timeout=60)
        metadata.raise_for_status()
        revision = metadata.json()['sha']
    url = f'https://codeload.github.com/h5p/{repo}/zip/{revision}'
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    if folder in locked:
        assert hashlib.sha256(response.content).hexdigest() == locked[folder]['sha256'], 'Pinned upstream archive checksum changed'
    archive = zipfile.ZipFile(io.BytesIO(response.content))
    prefix = archive.namelist()[0]
    for item in archive.infolist():
        relative = Path(item.filename.removeprefix(prefix))
        target = DEST / folder / relative
        assert target.resolve().is_relative_to((DEST / folder).resolve())
        if not item.is_dir():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(item))
    records.append(dict(file=folder, url=url, revision=revision, sha256=hashlib.sha256(response.content).hexdigest()))
    print(folder, revision, flush=True)
records.extend(item for name,item in locked.items() if name not in {r['file'] for r in records})
(ROOT / 'h5p' / 'upstream-lock.json').write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
subprocess.run([sys.executable,str(ROOT/'scripts/fetch_h5p_video.py')],check=True)
