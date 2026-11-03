"""Reproducible local production entry point. Full video is deliberately not a Pages job."""
from pathlib import Path
import argparse,os,subprocess,sys,shutil
ROOT=Path(__file__).resolve().parent
def run(args,**kwargs):subprocess.run([str(x) for x in args],cwd=kwargs.pop('cwd',ROOT),check=True,**kwargs)
def main():
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['samples','audio','manim','sync','lab','h5p','site','sample','stills','video','verify','test','all']);a=p.parse_args()
    node=os.environ.get('NODE_BINARY') or shutil.which('node');python=sys.executable
    def stage(name):
        if name in ['samples','audio']:
            tts=os.environ.get('NEURAL_PYTHON') or ROOT/('.venv-tts/Scripts/python.exe' if os.name=='nt' else '.venv-tts/bin/python')
            if not Path(tts).exists():raise RuntimeError('Install the isolated speech environment or set NEURAL_PYTHON.')
            run([tts,'scripts/neural_narration.py','samples' if name=='samples' else 'render'])
        elif name in ['manim','sync','lab','site','verify']:run([python,{'manim':'scripts/render_manim.py','sync':'scripts/sync_course.py','lab':'scripts/build_lab.py','site':'scripts/build_pages.py','verify':'scripts/verify_video.py'}[name]])
        elif name=='h5p':
            run([python,'scripts/author_h5p.py']);assert node,'Install Node or set NODE_BINARY';run([node,'webtools/h5p-build.cjs']);run([python,'scripts/sync_course.py'])
        elif name in ['sample','stills','video']:
            assert node,'Install Node or set NODE_BINARY';env=dict(os.environ,PYTHON=python);run([node,'remotion/render.mjs','full' if name=='video' else name],env=env)
        elif name=='test':
            run([python,'-m','unittest','discover','-s','tests','-v']);run([python,'scripts/check_course.py']);assert node;run([node,'remotion/node_modules/typescript/bin/tsc','--noEmit','-p','remotion/tsconfig.json']);run([node,'--test','remotion/test/manifest.test.mjs'])
    if a.stage=='all':
        for name in ['lab','samples','audio','manim','sync','h5p','stills','sample','video','verify','test','site']:stage(name)
    else:stage(a.stage)
if __name__=='__main__':main()
