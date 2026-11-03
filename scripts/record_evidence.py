"""Preserve small, scoped verification records without publishing local caches."""
from pathlib import Path
import json,hashlib,platform,sys
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]

def main():
    cfg=json.loads((ROOT/'course/config.json').read_text())
    def read(name):return json.loads((ROOT/name).read_text(encoding='utf-8'))
    def clean(value):
        if isinstance(value,dict):return {k:clean(v) for k,v in value.items()}
        if isinstance(value,list):return [clean(v) for v in value]
        if isinstance(value,str) and value.startswith('http://127.0.0.1:'):return 'LOCAL_TEST_BUILD'
        return value
    names=['outputs/video-verification.json','outputs/timing-report.json','outputs/course-checks.json']
    out=ROOT/'reports';out.mkdir(exist_ok=True)
    for name in names:(out/Path(name).name).write_text(json.dumps(read(name),indent=2)+'\n',encoding='utf-8')
    learning=[]
    for p in sorted((ROOT/'outputs/browser').glob('learning-*.json')):
        if p.name.endswith('-failure.json'):continue
        data=read(p.relative_to(ROOT));assert data['status']=='PASS'
        learning.append(dict(artifact=p.name,**clean(data)))
    website=clean(read('outputs/browser/course-results.json'));assert website['status']=='PASS'
    evidence=dict(recorded_at=datetime.now(timezone.utc).isoformat(),scope='Prepublication: local build with real YouTube streaming; not evidence of Pages deployment.',video_url=cfg['youtube_url'],python=sys.version.split()[0],platform=platform.platform(),source_hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['course/physics.py','course/publication_events.json','lab/Quantum_Formalism_Lab.ipynb','website/dist/h5p/formalism.html','h5p/Quantum_Formalism_Interactive.h5p']},website=website,learning=learning)
    (out/'prepublication.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(learning_reports=len(learning),website=website['status'],video=cfg['youtube_url'])))
if __name__=='__main__':main()
