"""Fetch the pinned upstream H5P.Video fix for current YouTube players."""
import hashlib
import io
import json
from pathlib import Path
import zipfile
import requests

ROOT=Path(__file__).resolve().parents[1]
REVISION='0293f342d757b5d7623ba841e1e513365ae42495'
URL=f'https://codeload.github.com/h5p/h5p-video/zip/{REVISION}'
TARGET=ROOT/'tools/h5p/video-upstream'
LOCK=ROOT/'h5p/upstream-lock.json'

def main():
    response=requests.get(URL,timeout=90);response.raise_for_status()
    digest=hashlib.sha256(response.content).hexdigest()
    records=json.loads(LOCK.read_text(encoding='utf-8'))
    previous=next((r for r in records if r['file']=='video-upstream'),None)
    if previous:
        assert previous['revision']==REVISION and previous['sha256']==digest,'Pinned video library checksum mismatch'
    archive=zipfile.ZipFile(io.BytesIO(response.content));prefix=archive.namelist()[0]
    for item in archive.infolist():
        target=TARGET/Path(item.filename.removeprefix(prefix))
        assert target.resolve().is_relative_to(TARGET.resolve())
        if not item.is_dir():
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(archive.read(item))
    metadata=json.loads((TARGET/'library.json').read_text(encoding='utf-8'))
    assert (metadata['majorVersion'],metadata['minorVersion'],metadata['patchVersion'])==(1,6,81)
    script=(TARGET/'scripts/youtube.js').read_text(encoding='utf-8')
    assert 'player.getIframe().style' in script and 'player.g.style' not in script
    records=[r for r in records if r['file']!='video-upstream']
    records.append(dict(file='video-upstream',url=URL,revision=REVISION,sha256=digest,version='1.6.81'))
    LOCK.write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
    print('Pinned official H5P.Video 1.6.81:',digest)

if __name__=='__main__':main()
