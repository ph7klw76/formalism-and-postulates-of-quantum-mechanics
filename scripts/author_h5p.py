"""Author real native parameters; an explicit final Summary shares the measured clock."""
from pathlib import Path
import sys,json,copy,argparse
from uuid import uuid5,NAMESPACE_URL
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from course.assessment import QUESTIONS,SUMMARY
def defaults(fields):
    out={}
    for f in fields:
        if 'default' in f:out[f['name']]=copy.deepcopy(f['default'])
        elif f['type']=='group':out[f['name']]=defaults(f['fields'])
        elif f['type']=='list':out[f['name']]=[]
    return out
def params(name):return defaults(json.loads((ROOT/'tools/h5p/libraries'/name/'semantics.json').read_text(encoding='utf-8')))
def action(library,p,title):
    name,version=library.rsplit('-',1)
    return dict(library=name+' '+version,params=p,subContentId=str(uuid5(NAMESPACE_URL,'quantum-formalism/'+title)),metadata=dict(title=title,contentType=name,license='CC BY',licenseVersion='4.0',authors=[dict(name='Quantum Formalism Lab',role='Author')]))
def choice(q):
    p=params('H5P.MultiChoice-1.16');p['question']='<p>'+q['question']+'</p>'
    p['answers']=[dict(text='<p>'+o+'</p>',correct=i==q['correct'],tipsAndFeedback=dict(tip='',chosenFeedback=q['explanation'] if i==q['correct'] else q['wrong'][str(i)] if str(i) in q['wrong'] else q['wrong'][i],notChosenFeedback='')) for i,o in enumerate(q['options'])]
    p['behaviour'].update(type='single',randomAnswers=False,enableRetry=True,enableSolutionsButton=True,enableCheckButton=True,showScorePoints=True)
    p['overallFeedback']=[{'from':0,'to':100,'feedback':'Explain your reasoning. Review the relevant explanation or test the prediction in the laboratory.'}]
    return p
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--preview-url');a=parser.parse_args()
    cfg=json.loads((ROOT/'course/config.json').read_text());events=json.loads((ROOT/'course/publication_events.json').read_text(encoding='utf-8'))
    questions=events['quizzes'];standalone=[choice(q) for q in questions]
    (ROOT/'h5p/questions.json').write_text(json.dumps(standalone,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    metadata=dict(title=cfg['title'],language='en',mainLibrary='H5P.InteractiveVideo',embedTypes=['div'],license='CC BY',licenseVersion='4.0',authors=[dict(name='Quantum Formalism Lab',role='Author')],preloadedDependencies=[dict(machineName=name,majorVersion=major,minorVersion=minor) for name,major,minor in [('H5P.InteractiveVideo',1,27),('H5P.MultiChoice',1,16),('H5P.Summary',1,10)]])
    (ROOT/'h5p/h5p.json').write_text(json.dumps(metadata,indent=2)+'\n')
    url=a.preview_url or cfg['youtube_url']
    if not url:print('Standalone questions prepared. Interactive video requires a real public URL or an explicit local preview URL.');return
    if a.preview_url:assert url.startswith('http://127.0.0.1:8778/'+cfg['slug']+'/')
    p=params('H5P.InteractiveVideo-1.27');iv=p['interactiveVideo'];iv.pop('summary',None)
    iv['video']['files']=[dict(path=url,mime='video/mp4' if a.preview_url else 'video/YouTube',copyright=dict(license='CC BY',licenseVersion='4.0'))]
    iv['video']['startScreenOptions'].update(title=cfg['title'],shortStartDescription='Predict, explain and test. Seven original checkpoints and a final concept summary.')
    iv['video']['textTracks']=dict(videoTrack=[dict(label='English',kind='subtitles',srcLang='en',track=dict(path='subtitles/lecture.vtt',mime='text/vtt'))],defaultTrackLabel='English')
    iv['assets']['interactions']=[]
    for q,mc in zip(questions,standalone):
        iv['assets']['interactions'].append(dict(duration={'from':q['time_seconds'],'to':q['time_seconds']+5},pause=True,displayType='poster',buttonOnMobile=True,label=q['id'],x=5,y=8,width=90,height=80,libraryTitle='Multiple Choice',action=action('H5P.MultiChoice-1.16',mc,q['id']),adaptivity=dict(wrong=dict(seekTo=q['review_seconds'],allowOptOut=True,message='Review the explanation, then return to this question and revise your reasoning.',seekLabel='Review explanation'),requireCompletion=False),visuals=dict(backgroundColor='rgb(255,255,255)',boxShadow=True)))
    summary=params('H5P.Summary-1.10');summary['intro']='<p>Choose the statement you can defend. Then complete the independent transfer task.</p>'
    summary['summaries']=[dict(summary=['<p>'+s+'</p>' for s in group],tip='Use the postulates and explicit assumptions, then test your prediction in the lab.') for group in SUMMARY]
    summary['overallFeedback']=[{'from':0,'to':100,'feedback':'Formative practice is a starting point. Submit an independent explanation and computational evidence.'}]
    last=events['scenes'][-1];at=(last['speech_end_frame']+5)/events['fps'];assert at<events['duration_seconds']
    iv['assets']['interactions'].append(dict(duration={'from':at,'to':events['duration_seconds']},pause=True,displayType='button',buttonOnMobile=True,label='Final concepts',x=70,y=70,width=25,height=20,bigDialog=True,libraryTitle='Summary',action=action('H5P.Summary-1.10',summary,'Final concepts')))
    iv['assets']['bookmarks']=[dict(time=c['start_seconds'],label=c['title']) for c in events['chapters']]
    iv['assets']['endscreens']=[dict(time=events['duration_seconds']-.05,label='Review formative answers')]
    p['override'].update(autoplay=False,loop=False,showRewind10=True,preventSkippingMode='none')
    target=ROOT/'outputs/h5p-preview/params.json' if a.preview_url else ROOT/'h5p/content.json';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(p,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Authored',len(questions),'native questions and the measured final Summary:',target)
if __name__=='__main__':main()
