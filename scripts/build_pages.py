"""Build the complete subpath-safe site without media masters or model weights."""
from pathlib import Path
import argparse,json,shutil,subprocess,sys,hashlib,re
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--skip-lab',action='store_true');p.add_argument('--base-path');a=p.parse_args()
    cfg=json.loads((ROOT/'course/config.json').read_text());base=a.base_path or cfg['base_path'];base='/'+base.strip('/')+'/'
    source=ROOT/'website/dist';dest=ROOT/'outputs/pages';dest.mkdir(parents=True,exist_ok=True)
    # Version the bytes actually copied, including the active source configuration.
    index=(source/'index.html').read_text(encoding='utf-8')
    for name in ['config.js','app.js','physics.js','style.css']:
        digest=hashlib.sha256((source/name).read_bytes()).hexdigest()[:12]
        index=re.sub(r'(?<=["\'])'+re.escape(name)+r'(?:\?[^"\s]*)?(?=["\'])',name+'?v='+digest,index)
    (source/'index.html').write_text(index,encoding='utf-8',newline='\n')
    for item in source.iterdir():
        if item.name=='lab' or item.suffix in ['.mp4','.wav']:continue
        if item.is_dir():shutil.copytree(item,dest/item.name,dirs_exist_ok=True)
        else:shutil.copy2(item,dest/item.name)
    if cfg['youtube_url']:
        shutil.copy2(ROOT/'h5p/Quantum_Formalism_Interactive.h5p',dest/'h5p/Quantum_Formalism_Interactive.h5p')
    if not a.skip_lab:subprocess.run([sys.executable,'-m','jupyterlite_core','build','--lite-dir',str(ROOT/'lab'),'--contents',str(ROOT/'lab/files'),'--output-dir',str(dest/'lab'),'--base-url',base+'lab/'],check=True,cwd=ROOT)
    assert not list(dest.rglob('*.mp4')) and not list(dest.rglob('*.wav'))
    (dest/'.nojekyll').touch();report=dict(base_path=base,video_url=cfg['youtube_url'],notebook='lab/lab/index.html?path=Quantum_Formalism_Lab.ipynb',files=sum(p.is_file() for p in dest.rglob('*')))
    (dest/'build-info.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
