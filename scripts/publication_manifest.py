"""Explicit source allowlist for review before publishing. Never stages by directory."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
DIRECTORIES=('course','docs','h5p','lab','narration','quizzes','remotion','reports','scripts','tests','video','website','webtools','.github')
FILES=('README.md','.gitignore','LICENSE','CONTENT_LICENSE.md','build.py','requirements-ci.txt','requirements-lite.txt','requirements-neural.txt','requirements-neural-lock.txt','requirements-production.txt')
EXTENSIONS={'.py','.mjs','.cjs','.js','.ts','.tsx','.json','.md','.txt','.yml','.yaml','.html','.css','.srt','.vtt','.ipynb','.toml','.h5p','.woff','.woff2','.ttf','.svg','.gitkeep','.csv'}
EXCLUDED={'node_modules','__pycache__','.bundle','.cache','neural','media','manim','.venv','outputs','tools','.git'}

def files():
    paths=[ROOT/name for name in FILES]
    for name in DIRECTORIES:
        folder=ROOT/name
        if folder.exists():
            paths.extend(p for p in folder.rglob('*') if p.is_file() and not EXCLUDED.intersection(p.relative_to(ROOT).parts) and (p.suffix.lower() in EXTENSIONS or p.name=='LICENSE'))
    result=[]
    for p in sorted(set(paths)):
        relative=p.relative_to(ROOT).as_posix()
        if not p.exists():raise ValueError('Missing source: '+relative)
        assert p.stat().st_size<20*1024**2,'Review unusually large file: '+relative
        assert not any(s in p.name.lower() for s in ('credential','secret','token')),'Review sensitive filename: '+relative
        result.append(dict(path=relative,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    return result

if __name__=='__main__':
    out=ROOT/'outputs/publication-manifest.json';out.parent.mkdir(exist_ok=True)
    records=files();out.write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(files=len(records),bytes=sum(r['bytes'] for r in records),manifest=out.name)))
