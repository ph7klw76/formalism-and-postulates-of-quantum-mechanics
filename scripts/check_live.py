"""Verify the actual public site and compare distinguishing served files with source."""
from pathlib import Path
import json,os,time,hashlib
from urllib.request import Request,urlopen
from urllib.parse import urljoin
ROOT=Path(__file__).resolve().parents[1];cfg=json.loads((ROOT/'course/config.json').read_text())
base=os.environ.get('SITE_URL',cfg['website_url']).rstrip('/')+'/'
assert base==cfg['website_url']
resources=['','config.js','h5p/formalism.html','h5p/Quantum_Formalism_Interactive.h5p','h5p/question-1.html','lecture.srt','lab/lab/index.html','lab/files/Quantum_Formalism_Lab.ipynb','Quantum_Formalism_Lab.ipynb','assessment.html'];rows=[]
for name in resources:
    for attempt in range(12):
        try:
            with urlopen(Request(urljoin(base,name),headers={'User-Agent':'Quantum-formalism-course-verification'}),timeout=30) as r:
                data=r.read();assert r.status==200 and data
                if name=='config.js':assert cfg['youtube_url'].encode() in data
                if name in ['config.js','h5p/formalism.html']:
                    assert hashlib.sha256(data).digest()==hashlib.sha256((ROOT/'website/dist'/name).read_bytes()).digest()
                if name.endswith('.ipynb'):assert json.loads(data)['nbformat']==4
                rows.append(dict(path=name or '/',status=200,bytes=len(data)));break
        except Exception:
            if attempt==11:raise
            time.sleep(5)
print(json.dumps(dict(status='PASS',url=base,video_url=cfg['youtube_url'],resources=rows),indent=2))
