"""Original model-derived Manim panels; no external LaTeX or stock artwork."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from manim import *
import numpy as np
from scipy.stats import binom
from course import physics as q

config.background_color='#102A36'
config.pixel_width=1000;config.pixel_height=700
config.frame_width=10;config.frame_height=7;config.frame_rate=30
TEAL='#6EE0D1';AMBER='#F4C06D';INK='#F3F6F0';MUTED='#ABC4CD'

def text(value,size=32,color=INK):return Text(value,font='Arial',font_size=size,color=color)
def bars(scene,values,labels,title):
    scene.add(text(title,33).to_edge(UP,buff=.45))
    line=Line([-3.8,-2.1,0],[3.8,-2.1,0],color=MUTED);scene.add(line)
    for i,(value,label) in enumerate(zip(values,labels)):
        x=-2.3+i*4.6
        rect=Rectangle(width=1.55,height=max(.01,value*3.6),fill_color=TEAL if i==0 else AMBER,fill_opacity=.85,stroke_width=0).align_to(line,DOWN).shift([x,0,0])
        rect.move_to([x,-2.1+value*1.8,0]);scene.play(GrowFromEdge(rect,DOWN),run_time=1)
        scene.add(text(label,31).move_to([x,-2.6,0]),text(f'{value:.3f}',37).move_to([x,value*3.6-1.75,0]))

def panel(scene,index):
    if index==0:
        scene.add(text('Complex amplitudes in the z basis',32).to_edge(UP,buff=.35))
        planes=[]
        for x,label in [(-2.4,'c+ = sqrt(0.6)'),(2.4,'c- = exp(i phi) sqrt(0.4)')]:
            plane=Axes(x_range=[-1,1,.5],y_range=[-1,1,.5],x_length=3.5,y_length=3.5,axis_config={'include_tip':False,'color':MUTED}).move_to([x,0,0]);planes.append(plane)
            scene.add(plane,text(label,25).move_to([x,-2.6,0]),text('Re',23).next_to(plane.x_axis,RIGHT,buff=.1),text('Im',23).next_to(plane.y_axis,UP,buff=.1))
        phi=ValueTracker(0)
        scene.add(Arrow(planes[0].c2p(0,0),planes[0].c2p(np.sqrt(.6),0),buff=0,color=TEAL))
        arrow=always_redraw(lambda:Arrow(planes[1].c2p(0,0),planes[1].c2p(np.sqrt(.4)*np.cos(phi.get_value()),np.sqrt(.4)*np.sin(phi.get_value())),buff=0,color=AMBER))
        scene.add(arrow);scene.play(phi.animate.set_value(np.pi/3),run_time=3,rate_func=smooth)
    elif index==1:
        bars(scene,[.5,.5],['+ hbar / 2','- hbar / 2'],'Prepare x+; measure physical z spin')
    elif index==2:
        scene.add(text('Condition on x+; then predict z',32).to_edge(UP,buff=.4))
        for offset,values,label in [(-2.4,[.6,.4],'Original preparation'),(2.4,[.5,.5],'After recorded x+')]:
            scene.add(text(label,27).move_to([offset,2,0]))
            for j,p in enumerate(values):
                x=offset-.65+j*1.3;rect=Rectangle(width=.85,height=p*3.7,fill_color=TEAL if j==0 else AMBER,fill_opacity=.9,stroke_width=0).move_to([x,-1.8+p*1.85,0])
                scene.play(GrowFromEdge(rect,DOWN),run_time=.5);scene.add(text(f'{p:.1f}',29).next_to(rect,UP,buff=.14),text('z+' if j==0 else 'z-',27).move_to([x,-2.25,0]))
        scene.add(text(f'P(first x+) = {q.fixtures()["p_x_plus"]:.3f}',28,MUTED).to_edge(DOWN,buff=.25))
    elif index==3:
        scene.add(text('Synthetic sampling: N = 1000, p = 0.6',30).to_edge(UP,buff=.4))
        axes=Axes(x_range=[540,661,30],y_range=[0,.031,.01],x_length=7.7,y_length=3.9,axis_config={'color':MUTED,'include_tip':False}).shift(DOWN*.2)
        curve=axes.plot(lambda n:float(binom.pmf(round(n),1000,.6)),x_range=[540,660,1],color=TEAL,use_smoothing=False)
        scene.add(axes,text('Number of plus results',28).move_to([0,-2.8,0]),text('Exact binomial probability',24,MUTED).move_to([0,2.3,0]))
        scene.play(Create(curve),run_time=2);scene.add(DashedLine(axes.c2p(600,0),axes.c2p(600,.028),color=AMBER),text('Mean 600; count SD 15.49',30).move_to([0,-2.2,0]))
    elif index==4:
        scene.add(text('An unrecorded measurement still matters',31).to_edge(UP,buff=.4))
        source=text('z+',38).move_to([-3.7,0,0]);scene.add(source)
        for y,label in [(1.35,'x+'),(-1.35,'x-')]:
            middle=text(label,35).move_to([-.5,y,0]);scene.play(Create(Arrow(source.get_right(),middle.get_left(),color=TEAL,buff=.15)),FadeIn(middle),run_time=.6)
            scene.add(text('1/2',24,MUTED).move_to([-2,y*.8,0]))
            for yy,label2 in [(y+.45,'z+'),(y-.45,'z-')]:
                target=text(label2+' : 1/4',26).move_to([3,yy,0]);scene.play(Create(Arrow(middle.get_right(),target.get_left(),color=AMBER,buff=.12)),FadeIn(target),run_time=.4)
        scene.add(text('Sum both z+ branches: 1/2',31).to_edge(DOWN,buff=.35))
    elif index==5:
        scene.add(text('Relative phase changes x probabilities',31).to_edge(UP,buff=.35))
        axes=Axes(x_range=[0,2*np.pi,np.pi],y_range=[0,1.01,.5],x_length=7.6,y_length=3.9,axis_config={'include_tip':False,'color':MUTED}).shift(DOWN*.2)
        curve=axes.plot(lambda t:np.cos(t/2)**2,color=TEAL);constant=DashedLine(axes.c2p(0,.5),axes.c2p(2*np.pi,.5),color=AMBER)
        scene.add(axes,text('Angle = omega × time (rad)',27).move_to([0,-2.8,0]),text('x+ : cos²(angle/2)',27,TEAL).move_to([-1.9,2.25,0]),text('z+ : 1/2',27,AMBER).move_to([2.6,2.25,0]))
        scene.play(Create(curve),Create(constant),run_time=1.5)
        t=ValueTracker(0);dot=always_redraw(lambda:Dot(axes.c2p(t.get_value(),np.cos(t.get_value()/2)**2),color=INK,radius=.09));scene.add(dot);scene.play(t.animate.set_value(np.pi),run_time=2);scene.add(text('pi rotation: P(x+) = 0',30).move_to([0,-2.15,0]))
    else:
        scene.add(text('Same z data; opposite relative phases',31).to_edge(UP,buff=.35))
        for x,phi,label in [(-2.35,np.pi/3,'State A: phi = +60°'),(2.35,-np.pi/3,'State B: phi = -60°')]:
            scene.add(text(label,27).move_to([x,2.1,0]))
            v=q.state(phi=phi)
            for j,(a,axis) in enumerate([(q.Z,'z+'),(q.Y,'y+')]):
                p=(1+q.expectation(v,a))/2;xx=x-.7+j*1.4
                rect=Rectangle(width=.9,height=p*3.5,stroke_width=0,fill_opacity=.9,fill_color=TEAL if j==0 else AMBER).move_to([xx,-2+p*1.75,0]);scene.play(GrowFromEdge(rect,DOWN),run_time=.5)
                scene.add(text(f'{p:.3f}',27).next_to(rect,UP,buff=.12),text(axis,27).move_to([xx,-2.4,0]))
    scene.wait(1)

for _i in range(7):
    def _construct(self,index=_i):panel(self,index)
    globals()[f'Chapter{_i+1}']=type(f'Chapter{_i+1}',(Scene,),{'construct':_construct})
