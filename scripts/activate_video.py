"""Activate a real manually uploaded video; no upload or merge is claimed here."""
from pathlib import Path
import argparse,json,re,subprocess,sys,os,shutil
from urllib.parse import urlparse,parse_qs
import requests
ROOT=Path(__file__).resolve().parents[1]
def video_id(url):
    u=urlparse(url)
    if u.scheme!='https':raise ValueError('Use an HTTPS YouTube URL.')
    if u.hostname=='youtu.be':identifier=u.path.strip('/')
    elif u.hostname in ['youtube.com','www.youtube.com']:identifier=parse_qs(u.query).get('v',[''])[0]
    else:raise ValueError('Use a real YouTube share or watch URL.')
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}',identifier):raise ValueError('Invalid video ID.')
    return identifier
def main():
    p=argparse.ArgumentParser();p.add_argument('--url',required=True);a=p.parse_args();identifier=video_id(a.url)
    report=json.loads((ROOT/'outputs/video-verification.json').read_text());assert report['status']=='PASS' and report['edition']=='full'
    r=requests.get('https://www.youtube.com/oembed',params={'url':'https://www.youtube.com/watch?v='+identifier,'format':'json'},timeout=30);r.raise_for_status();data=r.json();assert identifier in data['html']
    path=ROOT/'course/config.json';cfg=json.loads(path.read_text());cfg['youtube_url']=a.url;cfg['status']='video-confirmed';path.write_text(json.dumps(cfg,indent=2)+'\n')
    node=os.environ.get('NODE_BINARY') or shutil.which('node');assert node,'Install Node or set NODE_BINARY'
    for args in [[sys.executable,'scripts/sync_course.py'],[sys.executable,'scripts/author_h5p.py'],[node,'webtools/h5p-build.cjs'],[sys.executable,'scripts/sync_course.py']]:subprocess.run(args,cwd=ROOT,check=True)
    print(json.dumps(dict(video_id=identifier,title=data['title'],activated=True,note='Metadata is verified. Real playback and learning-path tests must pass before publication.')))
if __name__=='__main__':main()
