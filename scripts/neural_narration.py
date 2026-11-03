"""Local Chatterbox/Kokoro speech, measured timing, and reproducible voice samples.

Run with .venv-tts/Scripts/python.exe. Network is needed only by `fetch`.
`samples` and `render` use local snapshots in HF offline mode.
"""
from pathlib import Path
import argparse,contextlib,difflib,gc,hashlib,json,math,os,re,shutil,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
CACHE=ROOT/'tools/neural-cache';CACHE.mkdir(parents=True,exist_ok=True)
os.environ.setdefault('HF_HOME',str(CACHE/'huggingface'))
os.environ.setdefault('HF_HUB_DISABLE_XET','1')
os.environ.setdefault('HF_HUB_DISABLE_TELEMETRY','1')
os.environ.setdefault('DO_NOT_TRACK','1')
os.environ.setdefault('TOKENIZERS_PARALLELISM','false')
os.environ.setdefault('HF_HUB_DOWNLOAD_TIMEOUT','180')
from course.narration_utils import chunks,speech_text,word_error_rate,cache_key,frame_duration,normalized_words

CONFIG=json.loads((ROOT/'narration/voice-config.json').read_text(encoding='utf-8'))
SAMPLE_TEXT=("What can one quantum measurement tell us? Pause and make a prediction. "
             "Dirac notation uses a bra and a ket. A Hermitian operator has real eigenvalues. "
             "The Born rule converts amplitudes into probabilities. Pauli matrices describe spin one-half. "
             "The Schrödinger equation controls time evolution, and h-bar is Planck's constant divided by two pi. "
             "A relative phase can change a later measurement. An expectation value is not necessarily a single outcome.")
REFERENCE_TEXT=('Let us look closely at the evidence. An interesting question deserves a careful answer. '
                'Pause and think about your prediction, and then we will test it together.')

def write_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8')

def ffmpeg():
    return shutil.which('ffmpeg') or __import__('imageio_ffmpeg').get_ffmpeg_exe()

def balance_samples():
    """Loudness-match comparison files so louder does not masquerade as better."""
    import soundfile as sf,pyloudnorm as pyln
    target=ROOT/'outputs/voice_samples/comparison.json'
    report=json.loads(target.read_text(encoding='utf-8'))
    for row in report['samples']:
        path=ROOT/row['file'];temporary=path.with_name(path.stem+'-mastered.wav')
        first=subprocess.run([ffmpeg(),'-hide_banner','-i',str(path),'-af','loudnorm=I=-18:TP=-1.5:LRA=7:print_format=json','-f','null','-'],capture_output=True,text=True,check=True)
        measured=json.loads(re.findall(r'\{[^{}]+"input_i"[^{}]+\}',first.stderr,re.S)[-1])
        filt=('loudnorm=I=-18:TP=-1.5:LRA=7:linear=true:'+':'.join(f'{a}={measured[b]}' for a,b in [('measured_I','input_i'),('measured_TP','input_tp'),('measured_LRA','input_lra'),('measured_thresh','input_thresh'),('offset','target_offset')]))
        subprocess.run([ffmpeg(),'-hide_banner','-loglevel','error','-y','-i',str(path),'-af',filt,'-ar','24000','-c:a','pcm_s24le',str(temporary)],check=True)
        temporary.replace(path)
        data,rate=sf.read(path);row['measured_integrated_lufs']=float(pyln.Meter(rate).integrated_loudness(data))
    report['comparison_mastering']='Loudness matched to nominal -18 LUFS, -1.5 dBTP; native 24 kHz 24-bit PCM.'
    write_json(target,report)
    print('Balanced comparison levels:',[(r['profile'],round(r['measured_integrated_lufs'],2)) for r in report['samples']],flush=True)

@contextlib.contextmanager
def offline_guard():
    """Fail rather than contact any service during synthesis/ASR."""
    import socket
    original=socket.socket.connect
    def reject(*args,**kwargs):raise RuntimeError('Network access disabled during local inference; run fetch first.')
    socket.socket.connect=reject
    try:yield
    finally:socket.socket.connect=original

def fetch():
    # Use the OS trust roots as pip does; never disable certificate verification.
    import truststore
    truststore.inject_into_ssl()
    from huggingface_hub import HfApi,snapshot_download
    lock=ROOT/'narration/model-lock.json'
    old=json.loads(lock.read_text(encoding='utf-8')) if lock.exists() else {}
    pins={};api=HfApi()
    repos={
      'chatterbox':('ResembleAI/chatterbox',['ve.safetensors','t3_cfg.safetensors','s3gen.safetensors','tokenizer.json','conds.pt','README.md','LICENSE*']),
      'kokoro':('hexgrad/Kokoro-82M',['config.json','kokoro-v1_0.pth','voices/af_heart.pt','README.md','VOICES.md','LICENSE*']),
      'asr':('Systran/faster-whisper-small.en',['config.json','model.bin','tokenizer.json','vocabulary.*','preprocessor_config.json','README.md'])}
    for key,(repo,patterns) in repos.items():
        rev=old.get(key,{}).get('revision') or api.model_info(repo).sha
        local=snapshot_download(repo,revision=rev,allow_patterns=patterns,max_workers=3)
        pins[key]={'repo_id':repo,'revision':rev,'path':Path(local).resolve().relative_to(ROOT).as_posix()}
        print('FETCHED',key,rev,flush=True)
        write_json(ROOT/'narration/model-lock.json',pins)
    # Save upstream license evidence; no API keys, accounts or paid endpoints.
    import requests
    notices=ROOT/'docs/tts-licenses';notices.mkdir(parents=True,exist_ok=True)
    for name,url in {
      'Chatterbox-MIT.txt':'https://raw.githubusercontent.com/resemble-ai/chatterbox/master/LICENSE',
      'Kokoro-Apache-2.0.txt':'https://www.apache.org/licenses/LICENSE-2.0.txt',
      'Kokoro-model-card.md':'https://huggingface.co/hexgrad/Kokoro-82M/raw/main/README.md',
      'Chatterbox-model-card.md':'https://huggingface.co/ResembleAI/chatterbox/raw/main/README.md'}.items():
        r=requests.get(url,timeout=60);r.raise_for_status();(notices/name).write_text(r.text,encoding='utf-8')
    # Some dependency components lazily load bundled tokenizer assets on first use.
    for name in ['kokoro_heart','chatterbox_warm']:
        engine=Engine(name,offline=False)
        if name=='kokoro_heart':
            import soundfile as sf
            ref=CACHE/'references/kokoro_heart.wav';ref.parent.mkdir(parents=True,exist_ok=True)
            sf.write(ref,engine.synthesize(REFERENCE_TEXT,seed=2026),engine.sr,subtype='PCM_24')
        else:engine.synthesize('This is an offline quantum mechanics lecture.',seed=1)
        engine.close()
    print('Model snapshots and first-use assets cached.',flush=True)

class Engine:
    def __init__(self,profile,offline=True):
        import torch
        self.profile=CONFIG['profiles'][profile];self.name=profile;self.kind=self.profile['engine']
        torch.set_num_threads(6)
        if offline:
            os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
        pins=json.loads((ROOT/'narration/model-lock.json').read_text(encoding='utf-8'))
        self.pin=pins[self.kind];folder=asset(self.pin['path'])
        self.device='cuda' if torch.cuda.is_available() and CONFIG['device']=='cuda' else 'cpu'
        print('LOAD',profile,self.device,flush=True)
        if self.kind=='chatterbox':
            from chatterbox.tts import ChatterboxTTS
            self.model=ChatterboxTTS.from_local(folder,device=self.device)
            self.sr=self.model.sr
            self.reference_sha256=None
            if self.profile['voice']=='synthetic_kokoro_heart':
                ref=asset('tools/neural-cache/references/kokoro_heart.wav')
                if not ref.exists():raise RuntimeError('Run fetch to generate the licensed synthetic Kokoro conditioning reference.')
                self.model.prepare_conditionals(str(ref),exaggeration=self.profile['exaggeration'])
                self.reference_sha256=hashlib.sha256(ref.read_bytes()).hexdigest()
        else:
            # espeak is only a phonemizer for out-of-dictionary words, never the voice.
            import espeakng_loader
            from phonemizer.backend.espeak.wrapper import EspeakWrapper
            EspeakWrapper.set_library(espeakng_loader.get_library_path())
            os.environ['ESPEAK_DATA_PATH']=str(espeakng_loader.get_data_path())
            from kokoro import KModel,KPipeline
            self.model=KModel(repo_id=self.pin['repo_id'],config=str(folder/'config.json'),model=str(folder/'kokoro-v1_0.pth')).to(self.device).eval()
            self.pipeline=KPipeline(lang_code='a',repo_id=self.pin['repo_id'],model=self.model,device=self.device)
            self.voice=torch.load(folder/'voices'/f"{self.profile['voice']}.pt",map_location='cpu',weights_only=True)
            self.sr=24000
            self.reference_sha256=None

    def synthesize(self,text,seed,question=False):
        import numpy as np,torch
        torch.manual_seed(seed);np.random.seed(seed)
        text=speech_text(text,self.kind,CONFIG['pronunciation'])
        with torch.inference_mode():
            if self.kind=='chatterbox':
                p=self.profile
                result=self.model.generate(text,exaggeration=p['exaggeration']+(.08 if question else 0),
                    cfg_weight=p['cfg_weight'],temperature=p['temperature'])
                data=result.squeeze().detach().cpu().numpy()
            else:
                data=np.concatenate([r.audio.detach().cpu().numpy() for r in self.pipeline(text,voice=self.voice,speed=self.profile['speed'])])
        data=np.asarray(data,dtype=np.float32).reshape(-1)
        if not np.all(np.isfinite(data)) or len(data)<self.sr*.3:raise RuntimeError('Invalid synthesized audio.')
        # Trim only long outer silence; retain 100 ms for consonants and breath.
        window=240;energy=np.array([np.sqrt(np.mean(data[i:i+window]**2)) for i in range(0,len(data),window)])
        active=np.flatnonzero(energy>.002)
        if len(active):
            begin=max(0,int(active[0]*window-self.sr*.10));end=min(len(data),int((active[-1]+1)*window+self.sr*.14));data=data[begin:end]
        return data

    def close(self):
        import torch
        for attr in ['pipeline','voice','model']:
            if hasattr(self,attr):delattr(self,attr)
        gc.collect()
        if torch.cuda.is_available():torch.cuda.empty_cache()

def load_asr():
    from faster_whisper import WhisperModel
    pins=json.loads((ROOT/'narration/model-lock.json').read_text(encoding='utf-8'))
    return WhisperModel(str(asset(pins['asr']['path'])),device='cpu',compute_type='int8',cpu_threads=6,local_files_only=True)

def recognize(asr,data,sr):
    import numpy as np
    from scipy.signal import resample_poly
    if sr!=16000:
        g=math.gcd(sr,16000);data=resample_poly(data,16000//g,sr//g)
    segments,info=asr.transcribe(np.asarray(data,dtype=np.float32),language='en',beam_size=5,
        word_timestamps=True,vad_filter=False,condition_on_previous_text=False,
        initial_prompt='Dirac notation. Hermitian operator. Pauli matrices. Hilbert space. Bra. Ket. Eigenstate. Born rule. H bar. Schrödinger equation.')
    words=[];text=[]
    for s in segments:
        text.append(s.text)
        words.extend({'word':w.word.strip(),'start':w.start,'end':w.end,'probability':w.probability} for w in (s.words or []))
    return {'text':' '.join(text).strip(),'words':words}

def samples():
    import numpy as np,soundfile as sf,pyloudnorm as pyln
    folder=ROOT/'outputs/voice_samples';folder.mkdir(parents=True,exist_ok=True)
    rows=[]
    for idx,name in enumerate(CONFIG['profiles'],1):
        target=folder/f'{idx:02d}_{name}.wav'
        signature=cache_key({'script':SAMPLE_TEXT,'profile':CONFIG['profiles'][name],'lexicon':CONFIG['pronunciation'],'seed':CONFIG['seed']})
        sidecar=target.with_suffix('.json')
        cached=json.loads(sidecar.read_text(encoding='utf-8')) if sidecar.exists() else {}
        if not target.exists() or cached.get('signature')!=signature:
            engine=Engine(name);data=engine.synthesize(SAMPLE_TEXT,CONFIG['seed'],question=True);sr=engine.sr;engine.close()
            loud=pyln.Meter(sr).integrated_loudness(data);data=pyln.normalize.loudness(data,loud,-18)
            peak=max(1.,float(np.max(abs(data)))/.84);data=data/peak
            sf.write(target,data,sr,subtype='PCM_24')
            write_json(sidecar,{'signature':signature,'profile':name,'sample_rate':sr,'script':SAMPLE_TEXT})
        rows.append({'profile':name,'label':CONFIG['profiles'][name]['label'],'file':str(target.relative_to(ROOT))})
    asr=load_asr()
    for row in rows:
        data,sr=sf.read(ROOT/row['file'],dtype='float32');decoded=recognize(asr,data,sr)
        row.update(duration_seconds=len(data)/sr,word_error_rate=word_error_rate(SAMPLE_TEXT,decoded['text']),asr=decoded['text'])
    write_json(folder/'comparison.json',{'script':SAMPLE_TEXT,'samples':rows,
        'selection_policy':'Prefer the warm Chatterbox reading if intelligibility is reliable; use Kokoro when primary fails. WER is an intelligibility proxy, not a perceptual naturalness score.'})
    import html
    blocks=''.join(f'<section><h2>{html.escape(r["label"])}</h2><audio controls preload="metadata" src="{Path(r["file"]).name}"></audio><p>Local recognition WER: {r["word_error_rate"]:.1%}; this is not a naturalness rating.</p></section>' for r in rows)
    (folder/'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Quantum narration voice comparison</title><style>body{max-width:850px;margin:40px auto;padding:20px;font:17px/1.6 system-ui;background:#f5f3eb;color:#102b36}section{padding:20px 0;border-top:1px solid #ccc}audio{width:100%}h2{font-size:23px}</style><h1>Three local narration samples</h1><p>'+html.escape(SAMPLE_TEXT)+'</p>'+blocks+'<p>Chatterbox MIT; Kokoro-82M official af_heart Apache 2.0. No named individual is imitated. Compare clarity, warmth, intonation and pacing directly.</p></html>',encoding='utf-8')
    balance_samples()
    print(json.dumps(rows,indent=2),flush=True)

def archive_original():
    # A new course has no old master to archive. Keep any prior edition intact.
    return

class TimingBudgetError(RuntimeError):pass

def asset(relative):
    own=ROOT/relative
    shared=Path(os.environ.get('PHYSICS_ASSET_ROOT',str(ROOT)))/relative
    return own if own.exists() else shared

def stamp(seconds,srt=False):
    ms=round(seconds*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);sec,ms=divmod(ms,1000)
    return f'{h:02}:{m:02}:{sec:02},{ms:03}' if srt else f'{m+h*60:02}:{sec:02}'

def align_expected(text,recognized,duration):
    """Map caption words onto ASR word timestamps, interpolate only unmatched words.

    The final caption text always uses the edited scientific script. ASR is a
    timing/intelligibility check, never an authority for changing the physics.
    """
    import numpy as np
    expected=re.findall(r'\S+',text);obs=recognized['words'];anchors={}
    # Flatten compounds/numerals on both sides: "wavefunction" can align to
    # "wave function", and spoken "zero point four five" to ASR's "0.45".
    a=[];owners=[];b=[];observed_times=[]
    for i,word in enumerate(expected):
        normalized=normalized_words(word);a.extend(normalized);owners.extend([i]*len(normalized))
    for word in obs:
        normalized=normalized_words(word['word']);count=len(normalized)
        for j,token in enumerate(normalized):
            b.append(token);observed_times.append((word['start']+(word['end']-word['start'])*j/count,
                word['start']+(word['end']-word['start'])*(j+1)/count))
    for block in difflib.SequenceMatcher(None,a,b,autojunk=False).get_matching_blocks():
        for j in range(block.size):
            owner=owners[block.a+j];start,end=observed_times[block.b+j]
            if owner in anchors:start,end=min(start,anchors[owner][0]),max(end,anchors[owner][1])
            anchors[owner]=(start,end)
    starts=np.linspace(.05,max(.06,duration-.1),len(expected));ends=starts.copy()
    if anchors:
        ks=sorted(anchors);starts=np.interp(np.arange(len(expected)),ks,[anchors[k][0] for k in ks]);ends=np.interp(np.arange(len(expected)),ks,[anchors[k][1] for k in ks])
    else:raise RuntimeError('ASR could not align any canonical words.')
    groups=[];begin=0
    while begin<len(expected):
        stop=begin;length=0
        while stop<len(expected):
            word=expected[stop]
            if stop>begin and (length+len(word)+1>88 or starts[stop]-starts[begin]>5.2):break
            length+=len(word)+1;stop+=1
            if word.endswith(('.', '?','!')):break
        start=float(starts[begin]);end=float(ends[stop-1])
        next_start=float(starts[stop]) if stop<len(expected) else duration
        end=min(duration,next_start,max(start+.12,end))
        if end<=start:end=min(duration,start+.12)
        groups.append((start,end,' '.join(expected[begin:stop])))
        begin=stop
    return groups,len(anchors),len(expected)

def render(profile=None):
    import numpy as np,soundfile as sf
    from course.lesson import SEGMENTS,CHAPTERS
    archive_original()
    profile=profile or CONFIG['selected_profile']
    fallback_reason=None
    try:engine=Engine(profile)
    except Exception as exc:
        fallback_reason=repr(exc);profile=CONFIG['fallback_profile'];engine=Engine(profile)
    asr=load_asr();sr=engine.sr
    folder=ROOT/'narration/neural';folder.mkdir(parents=True,exist_ok=True)
    timeline=[];all_audio=[];cues=[];clock=0;alignment=[];transcript=[]
    for s in SEGMENTS:
        pieces=[];local=.22;segment_cues=[];pieces.append(np.zeros(round(local*sr),dtype=np.float32))
        details=[]
        for j,text in enumerate(chunks(s['text'])):
            payload={'text':text,'profile':engine.profile,'model_revision':engine.pin['revision'],'reference_sha256':engine.reference_sha256,'seed':CONFIG['seed']+s['index']*100+j,
                     'question':s['kind']=='predict','lexicon':CONFIG['pronunciation'],'version':1}
            key=cache_key(payload);path=folder/f'{s["index"]:02d}_{j:02d}_{key}.wav';meta=path.with_suffix('.json')
            best=None;cached=False
            if path.exists() and meta.exists():
                data,_=sf.read(path,dtype='float32');audit=json.loads(meta.read_text(encoding='utf-8'))
                audit['wer']=word_error_rate(text,audit['asr']['text'])
                cached=audit['wer']<=.02 or audit.get('quality_screened_threshold')==.02
                best=(audit['wer'],data.copy(),audit)
                if cached:write_json(meta,audit)
            if not cached:
                attempts=range(1,4) if best is not None else range(3)
                for attempt in attempts:
                    data=engine.synthesize(text,payload['seed']+attempt*10007,question=payload['question'])
                    decoded=recognize(asr,data,sr);wer=word_error_rate(text,decoded['text'])
                    score={'payload':payload,'asr':decoded,'wer':wer,'duration':len(data)/sr,'attempt':attempt}
                    if best is None or wer<best[0]:best=(wer,data.copy(),score)
                    if wer<=.02:break
                    print('RETRY',s['index'],j,attempt,'WER',wer,decoded['text'],flush=True)
                wer,data,audit=best
                if wer>.22:raise RuntimeError(f'Chunk {s["index"]}/{j} failed intelligibility check: {wer:.1%}; {audit["asr"]["text"]}')
                audit['quality_screened_threshold']=.02
                sf.write(path,data,sr,subtype='FLOAT');write_json(meta,audit)
            duration=len(data)/sr
            chunk_cues,matched,total=align_expected(text,audit['asr'],duration)
            segment_cues.extend((local+a,local+b,t) for a,b,t in chunk_cues)
            details.append({'chunk':j,'start':local,'duration':duration,'text':text,'asr':audit['asr']['text'],
                            'wer':audit['wer'],'exact_word_anchors':matched,'caption_words':total,'file':str(path.relative_to(ROOT))})
            pieces.append(data);local+=duration
            if j<len(chunks(s['text']))-1:
                gap=CONFIG['chunk_pause_seconds'];pieces.append(np.zeros(round(gap*sr),dtype=np.float32));local+=gap
        speech_end=local
        hold=CONFIG['question_pause_seconds'] if s['kind']=='predict' else .65
        duration=frame_duration(max(s['duration'],speech_end+hold))
        pieces.append(np.zeros(max(0,round(duration*sr)-sum(len(p) for p in pieces)),dtype=np.float32))
        data=np.concatenate(pieces)
        # Round to exact video frames at the shared native sample rate.
        assert abs(len(data)/sr-duration)<1/sr
        all_audio.append(data);cues.extend((clock+a,clock+b,t) for a,b,t in segment_cues)
        timeline.append({**s,'start':clock,'duration':duration,'speech_end':clock+speech_end,'voice_profile':profile,'engine':engine.kind,'chunks':details})
        alignment.extend({'segment':s['index'],**d} for d in details)
        transcript.append(f"## {stamp(clock)} — {s['title']}\n\n{s['text']}\n")
        clock+=duration
        write_json(folder/'progress.json',{'completed_segments':s['index']+1,'seconds':clock,'profile':profile})
        print(f'SEGMENT {s["index"]:02d}: speech {speech_end:.2f}s, slot {duration:.2f}s, total {clock:.2f}s',flush=True)
    # Fit only visual holds; never accelerate speech to meet the requested duration.
    target=round(json.loads((ROOT/'course/config.json').read_text())['target_seconds']*30)
    total=round(clock*30)
    slots=[i for i,s in enumerate(timeline) if s['kind']!='predict']
    extra=[0]*len(timeline)
    if total<=target:
        for frame in range(target-total):extra[slots[frame%len(slots)]]+=1
    else:
        remaining=total-target
        for frame in range(remaining):
            eligible=[i for i in slots if timeline[i]['duration']+extra[i]/30-(timeline[i]['speech_end']-timeline[i]['start'])>1/30+.30]
            if not eligible:engine.close();raise TimingBudgetError('Speech and required reasoning holds exceed 720 seconds. Shorten the script; do not accelerate it.')
            extra[eligible[frame%len(eligible)]]-=1
    shifted=[];new_clock=0
    for i,s in enumerate(timeline):
        delta=new_clock-s['start']
        shifted.extend((a+delta,b+delta,t) for a,b,t in cues if s['start']<=a<s['start']+s['duration'])
        samples=extra[i]*(sr//30)
        all_audio[i]=np.pad(all_audio[i],(0,samples)) if samples>=0 else all_audio[i][:samples]
        s['speech_end']+=delta;s['start']=new_clock;s['duration']+=extra[i]/30
        new_clock+=s['duration']
    clock=target/30;cues=shifted
    engine.close()
    native=folder/'lecture-native-float.wav';sf.write(native,np.concatenate(all_audio),sr,subtype='FLOAT')
    master=ROOT/'outputs/Quantum_Formalism_Narration.wav'
    # EBU R128 two-pass mastering; preserve pitch and do not compress speech to fit.
    first=subprocess.run([ffmpeg(),'-hide_banner','-i',str(native),'-af','loudnorm=I=-16:TP=-1.5:LRA=7:print_format=json','-f','null','-'],capture_output=True,text=True,check=True)
    measured=json.loads(re.findall(r'\{[^{}]+"input_i"[^{}]+\}',first.stderr,re.S)[-1])
    filt=('loudnorm=I=-16:TP=-1.5:LRA=7:linear=true:'+
          ':'.join(f'{a}={measured[b]}' for a,b in [('measured_I','input_i'),('measured_TP','input_tp'),('measured_LRA','input_lra'),('measured_thresh','input_thresh'),('offset','target_offset')]))
    subprocess.run([ffmpeg(),'-hide_banner','-loglevel','error','-y','-i',str(native),'-af',filt,'-ar','48000','-ac','1','-c:a','pcm_s24le',str(master)],check=True)
    mastered,rate=sf.read(master,dtype='float32')
    for s in timeline:
        start=round(s['start']*rate);end=round((s['start']+s['duration'])*rate)
        sf.write(ROOT/f'narration/segment{s["index"]:02d}.wav',mastered[start:end],rate,subtype='PCM_24')
    write_json(ROOT/'narration/timeline.json',timeline)
    import textwrap
    (ROOT/'narration/lecture.srt').write_text('\n\n'.join(f'{i+1}\n{stamp(a,True)} --> {stamp(b,True)}\n'+ '\n'.join(textwrap.wrap(t,46,break_long_words=False,break_on_hyphens=False)) for i,(a,b,t) in enumerate(cues))+'\n',encoding='utf-8')
    (ROOT/'narration/transcript.md').write_text('# Formalism and Postulates of Quantum Mechanics\n\n'+'\n'.join(transcript),encoding='utf-8')
    shutil.copy(ROOT/'narration/lecture.srt',ROOT/'website/dist/lecture.srt')
    report={'profile':profile,'engine':CONFIG['profiles'][profile]['engine'],'offline_inference':True,'fallback_reason':fallback_reason,
            'model_revision':engine.pin['revision'],'reference_sha256':engine.reference_sha256,
            'reference_text':REFERENCE_TEXT if engine.reference_sha256 else None,
            'duration_seconds':clock,'native_sample_rate':sr,'delivery_sample_rate':rate,'delivery_bits':24,
            'chunk_count':len(alignment),'max_wer':max(d['wer'] for d in alignment),'mean_wer':float(np.mean([d['wer'] for d in alignment])),
            'mastering_measurements_first_pass':measured,'alignment':alignment,'note':'ASR checks intelligibility and word timing; it does not certify human perceptual naturalness.'}
    write_json(ROOT/'outputs/neural-narration-report.json',report)
    print('MASTER COMPLETE',clock,'seconds',profile,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['fetch','samples','render','balance-samples']);p.add_argument('--profile',choices=list(CONFIG['profiles']));args=p.parse_args()
    if args.stage=='render':
        try:
            with offline_guard():render(args.profile)
        except Exception as exc:
            if isinstance(exc,TimingBudgetError):raise
            requested=args.profile or CONFIG['selected_profile']
            if CONFIG['profiles'][requested]['engine']=='kokoro':raise
            print('PRIMARY FAILED; trying the configured Kokoro fallback:',repr(exc),flush=True)
            write_json(ROOT/'outputs/chatterbox-fallback-reason.json',{'error':repr(exc),'fallback_profile':CONFIG['fallback_profile']})
            import traceback
            traceback.clear_frames(exc.__traceback__)
            gc.collect()
            import torch
            if torch.cuda.is_available():torch.cuda.empty_cache()
            with offline_guard():render(CONFIG['fallback_profile'])
    elif args.stage=='samples':
        with offline_guard():samples()
    elif args.stage=='balance-samples':balance_samples()
    else:fetch()
