import React,{useEffect,useRef,useState} from 'react';
import {AbsoluteFill,Img,Sequence,interpolate,staticFile,useCurrentFrame,delayRender,continueRender} from 'remotion';
import {Video,Audio} from '@remotion/media';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import './style.css';
import events from './generated/events.json';
const color={bg:'#071A24',panel:'#102A36',ink:'#F3F6F0',muted:'#ABC4CD',teal:'#6EE0D1',amber:'#F4C06D',line:'#2B4853'};
const font='Arial, Helvetica, sans-serif';
const Eq:React.FC<{formula:string,index:number}>=({formula,index})=>{
 const f=useCurrentFrame();const opacity=interpolate(f,[12+index*18,30+index*18],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
 const size=formula.length>110?31:formula.length>75?36:43;
 const holder=useRef<HTMLDivElement>(null),equation=useRef<HTMLDivElement>(null);
 const [metrics,setMetrics]=useState({scale:1,height:100});const [handle]=useState(()=>delayRender('Measure scientific equation'));
 useEffect(()=>{let live=true;document.fonts.ready.then(()=>{if(!live)return;const width=equation.current!.getBoundingClientRect().width,height=equation.current!.getBoundingClientRect().height;const scale=Math.min(1,(holder.current!.clientWidth-16)/width);setMetrics({scale,height:height*scale});requestAnimationFrame(()=>continueRender(handle));});return()=>{live=false;continueRender(handle);};},[formula,handle]);
 return <div ref={holder} style={{height:metrics.height,position:'relative',opacity,margin:'14px 0',width:'100%'}}><div ref={equation} style={{position:'absolute',left:'50%',top:0,display:'inline-block',fontSize:size,whiteSpace:'nowrap',transform:`translateX(-50%) scale(${metrics.scale})`,transformOrigin:'top center'}} dangerouslySetInnerHTML={{__html:katex.renderToString(formula,{displayMode:true,throwOnError:true,strict:'warn'})}}/></div>;
};
type Scene=typeof events.scenes[number];
const Presentation:React.FC<{scene:Scene}>=({scene})=>{
 const f=useCurrentFrame();const quiz=events.quizzes.find(q=>q.scene===scene.index);
 const entering=interpolate(f,[0,15],[0,1],{extrapolateRight:'clamp'});
 const emphasize=scene.highlight_frame!==null&&f+scene.start_frame>=scene.highlight_frame&&f+scene.start_frame<scene.highlight_frame+75;
 return <AbsoluteFill style={{fontFamily:font,color:color.ink}}>
  <div style={{position:'absolute',left:70,right:70,top:35,display:'flex',justifyContent:'space-between',alignItems:'center'}}>
   <span style={{letterSpacing:3,fontSize:24,color:color.teal}}>ψ / THE QUANTUM FORMALISM LAB</span>
   <div style={{display:'flex',gap:25,fontSize:21,letterSpacing:2}}>{['PREDICT','EXPLAIN','COMPUTE','APPLY','CRITIQUE'].map(x=><span key={x} style={{color:scene.phase===x?color.amber:color.muted,borderBottom:scene.phase===x?`3px solid ${color.amber}`:'3px solid transparent',paddingBottom:8}}>{x}</span>)}</div>
  </div>
  <div style={{position:'absolute',left:70,right:70,top:108,opacity:entering,transform:`translateY(${(1-entering)*10}px)`}}>
   <div style={{fontSize:21,letterSpacing:3,color:color.muted,marginBottom:12}}>CHAPTER {String(scene.chapter+1).padStart(2,'0')} / {events.chapters[scene.chapter].title.toUpperCase()}</div>
   <div style={{fontSize:52,fontWeight:600,lineHeight:1.1}}>{scene.title}</div>
   <div style={{fontSize:29,color:color.muted,marginTop:13}}>{scene.focus}</div>
  </div>
  {quiz?<div style={{position:'absolute',left:65,right:65,top:285,height:650,padding:'35px 46px',background:color.panel,border:`1px solid ${color.line}`,borderRadius:18}}>
   <div style={{fontSize:26,color:color.amber,letterSpacing:3}}>{quiz.id} / PREDICT BEFORE THE ANSWER</div>
   <div style={{fontSize:47,fontWeight:600,lineHeight:1.17,margin:'26px 0 30px'}}>{quiz.question}</div>
   <div style={{display:'grid',gap:16}}>{quiz.options.map((option,i)=><div key={option} style={{display:'flex',alignItems:'center',gap:24,padding:'17px 22px',border:`1px solid ${color.line}`,borderRadius:10,fontSize:35,lineHeight:1.2}}><span style={{fontSize:27,color:color.teal}}>{String.fromCharCode(65+i)}</span><span>{option}</span></div>)}</div>
   <div style={{position:'absolute',bottom:30,left:46,right:46,fontSize:27,color:color.muted}}>Choose an answer and give a reason. Revise after the explanation.<div style={{height:4,background:color.line,marginTop:20}}><div style={{height:4,background:color.amber,width:`${interpolate(f+scene.start_frame,[quiz.hold_start_frame,quiz.reveal_frame],[0,100],{extrapolateLeft:'clamp',extrapolateRight:'clamp'})}%`}}/></div></div>
  </div>:scene.index===27?<div style={{position:'absolute',left:65,right:65,top:285,height:650,padding:'45px 55px',background:color.panel,border:`1px solid ${color.line}`,borderRadius:18}}>
   <div style={{fontSize:27,color:color.teal,letterSpacing:3}}>YOUR NEXT EXPERIMENT</div><div style={{fontSize:65,lineHeight:1.13,fontWeight:600,marginTop:22}}>Open the Python lab.<br/>Explain a new measurement.</div>
   <div style={{display:'flex',gap:30,marginTop:40}}>{['Vary states, phases and axes','Compare independent calculations','Investigate a three-level outcome'].map((x,i)=><div key={x} style={{flex:1,border:`1px solid ${color.line}`,borderRadius:12,padding:25,fontSize:31,lineHeight:1.3}}><div style={{color:color.amber,fontSize:24,marginBottom:14}}>0{i+1} / INVESTIGATE</div>{x}</div>)}</div>
   <div style={{fontSize:30,color:color.teal,marginTop:35}}>Follow the course link in the description. Predict before running the code.</div>
  </div>:<>
   <div style={{position:'absolute',left:65,top:285,width:890,height:650,background:color.panel,border:`1px solid ${color.line}`,borderRadius:18,overflow:'hidden'}}>
    <Img src={staticFile(`manim/chapter-${scene.chapter+1}.png`)} style={{width:890,height:623,objectFit:'contain'}}/>
    {scene.index%4===0&&<Sequence from={0} durationInFrames={Math.min(scene.duration_frames,events.chapters[scene.chapter].animation_frames)}><Video muted src={staticFile(`manim/chapter-${scene.chapter+1}.mp4`)} style={{width:890,height:623}}/></Sequence>}
   </div>
   <div style={{position:'absolute',left:1005,right:70,top:310,height:590,display:'flex',flexDirection:'column',justifyContent:'center'}}>
    <div style={{fontSize:24,letterSpacing:3,color:emphasize?color.amber:color.teal,marginBottom:14}}>{emphasize?'KEY IDEA / '+scene.highlight_term.toUpperCase():'THE REASONING'}</div>
    {scene.formulas.map((formula,i)=><Eq key={formula} formula={formula} index={i}/>)}
    <div style={{fontSize:30,color:color.muted,lineHeight:1.4,marginTop:22,borderTop:`1px solid ${color.line}`,paddingTop:24}}>{scene.note}</div>
   </div>
  </>}
  <div style={{position:'absolute',left:70,right:70,top:975,display:'flex',justifyContent:'space-between',borderTop:`1px solid ${color.line}`,paddingTop:22,color:color.muted,fontSize:24}}><span>{quiz?'PREDICTION FIRST / EXPLANATION NEXT':scene.index===27?events.website_url.replace('https://',''):'PURE STATES / IDEAL PROJECTIVE MEASUREMENTS / UNITS AND ASSUMPTIONS EXPLICIT'}</span><span style={{color:color.teal}}>SCENE {scene.index+1} / {events.scenes.length}</span></div>
 </AbsoluteFill>;
};
export const Lecture:React.FC<{showCaptions:boolean}>=({showCaptions})=>{
 const f=useCurrentFrame();const scene=events.scenes.find(s=>f>=s.start_frame&&f<s.end_frame)||events.scenes.at(-1)!;
 const captions=events.captions as Array<{start_frame:number;end_frame:number;text:string}>;
 const cue=showCaptions?captions.find(c=>f>=c.start_frame&&f<c.end_frame):null;
 return <AbsoluteFill style={{background:color.bg}}>
  <Sequence from={scene.start_frame} durationInFrames={scene.duration_frames}><Presentation scene={scene}/></Sequence>
  <Audio src={staticFile('media/narration.wav')}/>
  {cue&&<div style={{position:'absolute',left:130,right:130,bottom:135,font: '34px/1.3 '+font,textAlign:'center',color:'white',padding:18,background:'#071A24ed',borderRadius:10}}>{cue.text}</div>}
  <div style={{position:'absolute',bottom:0,left:0,height:5,width:`${100*f/(events.duration_frames-1)}%`,background:color.teal}}/>
 </AbsoluteFill>;
};
export const Thumbnail:React.FC=()=> <AbsoluteFill style={{background:color.bg,fontFamily:font,color:color.ink,padding:'58px 60px'}}>
 <div style={{fontSize:23,letterSpacing:4,color:color.teal}}>STATE • MEASURE • EVOLVE</div>
 <div style={{fontSize:77,fontWeight:700,lineHeight:1.06,marginTop:50,maxWidth:790}}>FROM A KET<br/>TO A <span style={{color:color.amber}}>PREDICTION</span></div>
 <div style={{fontSize:32,color:color.muted,marginTop:38,maxWidth:690}}>Formalism and postulates<br/>of quantum mechanics</div>
 <div style={{position:'absolute',right:65,top:235,width:310,height:310,borderRadius:'50%',border:`2px solid ${color.line}`,display:'flex',alignItems:'center',justifyContent:'center',background:color.panel}}><span style={{fontFamily:'serif',fontSize:120,color:color.teal}}>|ψ⟩</span></div>
 <div style={{position:'absolute',bottom:58,left:60,right:60,borderTop:`1px solid ${color.line}`,paddingTop:23,fontSize:25,color:color.muted}}>PREDICT FIRST • TEST THE POSTULATES • BUILD AN INDEPENDENT EXPLANATION</div>
</AbsoluteFill>;
