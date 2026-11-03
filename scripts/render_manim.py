"""Render original chapter panels and extract their final, readable stills."""
from pathlib import Path
import subprocess,sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
def main():
    import av
    public=ROOT/'remotion/public/manim';public.mkdir(parents=True,exist_ok=True)
    report=[]
    import manim
    key=hashlib.sha256(b'1000x700@30/cairo'+manim.__version__.encode()+(ROOT/'video/scenes.py').read_bytes()+(ROOT/'course/physics.py').read_bytes()).hexdigest()
    for i in range(1,8):
        target=public/f'chapter-{i}.mp4'
        cache=public/f'chapter-{i}.json'
        if not target.exists() or not cache.exists() or json.loads(cache.read_text()).get('source_sha256')!=key:
            subprocess.run([sys.executable,'-m','manim','render','--renderer=cairo','--disable_caching','-r','1000,700','--fps','30','--media_dir',str(ROOT/'outputs/manim'),str(ROOT/'video/scenes.py'),f'Chapter{i}'],cwd=ROOT,check=True)
            candidates=list((ROOT/'outputs/manim').rglob(f'Chapter{i}.mp4'));assert len(candidates)==1,candidates
            import shutil;shutil.copyfile(candidates[0],target)
            cache.write_text(json.dumps(dict(source_sha256=key,manim=manim.__version__))+'\n')
        container=av.open(str(target));last=None
        for frame in container.decode(video=0):last=frame
        assert last is not None;last.to_image().save(public/f'chapter-{i}.png')
        report.append(dict(chapter=i,frames=container.streams.video[0].frames,seconds=float(container.streams.video[0].duration*container.streams.video[0].time_base)))
    (ROOT/'outputs/manim-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
