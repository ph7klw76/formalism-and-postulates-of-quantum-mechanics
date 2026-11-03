"""One measured frame manifest drives all media, quizzes, captions and chapters."""
from pathlib import Path
import sys,json,math,csv,hashlib,shutil,argparse
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from course.lesson import SEGMENTS,CHAPTERS
from course.assessment import QUESTIONS,SUMMARY
from course.visuals import FORMULAS,NOTES
from course.physics import fixtures,state,observable,expectation
import srt

def stamp(t):
    seconds=round(t);return f'{seconds//60:02}:{seconds%60:02}'
def generate(draft=False):
    cfg=json.loads((ROOT/'course/config.json').read_text());fps=cfg['fps'];total=round(cfg['target_seconds']*fps)
    if not draft:
        timeline=json.loads((ROOT/'narration/timeline.json').read_text(encoding='utf-8'))
        assert len(timeline)==len(SEGMENTS)
        assert round(sum(s['duration'] for s in timeline)*fps)==total
    else:
        timeline=[dict(**s,start=round(i*total/len(SEGMENTS))/fps,speech_end=(round((i+1)*total/len(SEGMENTS))-220)/fps) for i,s in enumerate(SEGMENTS)]
    scenes=[];narration=[];words=[]
    if not draft:
        for slot in timeline:
            for chunk in slot.get('chunks',[]):
                at=slot['start']+chunk['start'];narration.append(dict(scene=slot['index'],start_seconds=at,end_seconds=at+chunk['duration'],start_frame=round(at*fps),end_frame=round((at+chunk['duration'])*fps),text=chunk['text']))
                meta=(ROOT/chunk['file']).with_suffix('.json')
                if meta.exists():
                    data=json.loads(meta.read_text(encoding='utf-8'))
                    words.extend(dict(scene=slot['index'],word=w['word'],start_seconds=at+w['start'],end_seconds=at+w['end']) for w in data['asr']['words'])
        if words:(ROOT/'narration/words.json').write_text(json.dumps(words,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        elif (ROOT/'narration/words.json').exists():words=json.loads((ROOT/'narration/words.json').read_text(encoding='utf-8'))
    for i,(slot,canonical) in enumerate(zip(timeline,SEGMENTS)):
        assert slot['text']==canonical['text']
        start=round(slot['start']*fps);end=round(timeline[i+1]['start']*fps) if i+1<len(timeline) else total
        term=['state','eigenvalues','probability','expectation','measurement','phase','model'][i//4]
        beat=next((w for w in words if w['scene']==i and w['word'].lower().strip('.,:;!?')==term),None)
        scenes.append(dict(**canonical,start_frame=start,end_frame=end,duration_frames=end-start,speech_end_frame=math.ceil(slot['speech_end']*fps),formulas=FORMULAS[i],note=NOTES[i],highlight_term=term,highlight_frame=round(beat['start_seconds']*fps) if beat else None,phase='PREDICT' if canonical['kind']=='predict' else ['EXPLAIN','COMPUTE','EXPLAIN','APPLY','CRITIQUE','COMPUTE','CRITIQUE'][i//4]))
    questions=[]
    for q in QUESTIONS:
        slot=timeline[q['scene']];scene=scenes[q['scene']];at=math.ceil(slot['speech_end']+.25)
        row=dict(q,time_seconds=at,frame=at*fps,review_seconds=scenes[q['review_scene']]['start_frame']/fps,hold_start_frame=scene['speech_end_frame'],reveal_frame=scene['end_frame'],timestamp=stamp(at))
        assert row['frame']<row['reveal_frame']-4*fps
        questions.append(row)
    cues=[]
    if not draft:
        cues=[dict(id=c.index,start_seconds=c.start.total_seconds(),end_seconds=c.end.total_seconds(),text=c.content,start_frame=math.floor(c.start.total_seconds()*fps),end_frame=math.ceil(c.end.total_seconds()*fps)) for c in srt.parse((ROOT/'narration/lecture.srt').read_text(encoding='utf-8'))]
        assert ' '.join(c['text'] for c in cues).split()==' '.join(s['text'] for s in SEGMENTS).split()
        assert all(0<=c['start_seconds']<c['end_seconds']<=total/fps for c in cues)
    manim=json.loads((ROOT/'outputs/manim-report.json').read_text()) if (ROOT/'outputs/manim-report.json').exists() else []
    chapters=[dict(index=i,title=title,start_frame=scenes[4*i]['start_frame'],start_seconds=scenes[4*i]['start_frame']/fps,animation_frames=manim[i]['frames'] if manim else 180) for i,title in enumerate(CHAPTERS)]
    manifest=dict(schema_version=1,status='DRAFT' if draft else 'MEASURED',title=cfg['title'],slug=cfg['slug'],website_url=cfg['website_url'],fps=fps,width=cfg['width'],height=cfg['height'],duration_frames=total,duration_seconds=total/fps,scenes=scenes,narration=narration,quizzes=questions,captions=cues,chapters=chapters,summary=SUMMARY,physics=fixtures(),narration_words=sum(len(s['text'].split()) for s in SEGMENTS))
    for target in [ROOT/'course/publication_events.json',ROOT/'remotion/src/generated/events.json']:
        target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
    (ROOT/'quizzes/quizzes.json').write_text(json.dumps(questions,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    with (ROOT/'quizzes/youtube_quizzes.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f);w.writerow(['id','timestamp','question','option_A','option_B','option_C','answer','explanation'])
        for q in questions:w.writerow([q['id'],q['timestamp'],q['question'],*q['options'],chr(65+q['correct']),q['explanation']])
    lines=['# Original formative YouTube quiz entries\n\nEnter manually where the channel supports native quizzes. These are not the QMFPS instrument.\n']
    for q in questions:lines.append(f"## {q['timestamp']} / {q['id']}\n\n{q['question']}\n\n"+'\n'.join(f'{chr(65+i)}. {o}' for i,o in enumerate(q['options']))+f"\n\nAnswer: {chr(65+q['correct'])}. {q['explanation']}\n")
    (ROOT/'quizzes/youtube_quizzes.md').write_text('\n'.join(lines),encoding='utf-8')
    (ROOT/'website/dist/config.js').write_text('window.COURSE_CONFIG='+json.dumps(cfg,separators=(',',':'))+';\n',encoding='utf-8',newline='\n')
    for file in ['publication_events.json','config.json']:shutil.copyfile(ROOT/'course'/file,ROOT/'website/dist'/file)
    if not draft:
        shutil.copyfile(ROOT/'narration/lecture.srt',ROOT/'outputs/Quantum_Formalism_Lecture.srt');shutil.copyfile(ROOT/'narration/lecture.srt',ROOT/'website/dist/lecture.srt')
        def ts(t):
            n=round(t*1000);h,n=divmod(n,3600000);m,n=divmod(n,60000);s,n=divmod(n,1000);return f'{h:02}:{m:02}:{s:02}.{n:03}'
        vtt='WEBVTT\n\n'+'\n\n'.join(f"{ts(c['start_seconds'])} --> {ts(c['end_seconds'])}\n{c['text']}" for c in cues)+'\n'
        for file in [ROOT/'outputs/Quantum_Formalism_Lecture.vtt',ROOT/'website/dist/lecture.vtt']:file.write_text(vtt,encoding='utf-8')
    meta=[';FFMETADATA1'];chapter_text=[]
    for i,c in enumerate(chapters):
        end=chapters[i+1]['start_frame'] if i+1<len(chapters) else total
        meta.extend(['[CHAPTER]','TIMEBASE=1/'+str(fps),'START='+str(c['start_frame']),'END='+str(end),'title='+c['title']]);chapter_text.append(stamp(c['start_seconds'])+' '+c['title'])
    (ROOT/'outputs/chapters.ffmetadata').write_text('\n'.join(meta)+'\n',encoding='utf-8')
    (ROOT/'outputs/chapters.txt').write_text('\n'.join(chapter_text)+'\n',encoding='utf-8')
    description=f"{cfg['title']}\n\nA 12-minute foundation and an extended computational investigation for undergraduate physics.\n\nCourse and interactive questions: {cfg['website_url']}\nSource and reproducible builds: https://github.com/{cfg['repository']}\n\nCHAPTERS\n"+'\n'.join(chapter_text)+'\n\nModel: pure finite-dimensional states, ideal projective measurements and isolated unitary evolution. Spin units are explicit. Synthetic sampling is labelled.\n\nLearning design informed by Marshman & Singh, Phys. Rev. Phys. Educ. Res. 15, 020128 (2019), https://doi.org/10.1103/PhysRevPhysEducRes.15.020128. The original formative quizzes are not the validated QMFPS instrument.\n\nCode MIT; original educational content CC BY 4.0. Narration generated locally using licensed Chatterbox/Kokoro voices.\n'
    (ROOT/'outputs/youtube_description.md').write_text(description,encoding='utf-8')
    report=dict(status='DRAFT' if draft else 'TIMELINE_VERIFIED_RENDER_PENDING',duration_frames=total,duration_seconds=total/fps,scenes=len(scenes),quizzes=[dict(id=q['id'],time_seconds=q['time_seconds'],review_seconds=q['review_seconds'],reasoning_hold_seconds=(q['reveal_frame']-q['hold_start_frame'])/fps) for q in questions],subtitle_cues=len(cues),video_url=cfg['youtube_url'],baseline='New course; no prior lecture timestamp baseline exists.')
    verification=ROOT/'outputs/video-verification.json'
    video=ROOT/'outputs/Quantum_Formalism_Lecture.mp4'
    if not draft and verification.exists() and video.exists():
        verified=json.loads(verification.read_text())
        manifest_hash=hashlib.sha256((ROOT/'course/publication_events.json').read_bytes()).hexdigest()
        video_hash=hashlib.sha256(video.read_bytes()).hexdigest()
        if verified.get('status')=='PASS' and verified.get('edition')=='full' and verified.get('timeline_sha256')==manifest_hash and verified.get('video_sha256')==video_hash:
            report.update(status='PASS',render_verification=verification.name,video_sha256=video_hash,timeline_sha256=manifest_hash)
    (ROOT/'outputs/timing-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
    return manifest
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--draft',action='store_true');generate(p.parse_args().draft)
