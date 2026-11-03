'use strict';
const Quantum=(()=>{
 const clamp=x=>Math.max(0,Math.min(1,x));
 function state(p,phi){if(!Number.isFinite(p)||!Number.isFinite(phi)||p<0||p>1)throw Error('Use finite p in [0,1] and a finite phase.');return [2*Math.sqrt(p*(1-p))*Math.cos(phi),2*Math.sqrt(p*(1-p))*Math.sin(phi),2*p-1];}
 function axis(alpha,beta){return [Math.sin(alpha)*Math.cos(beta),Math.sin(alpha)*Math.sin(beta),Math.cos(alpha)];}
 function predict(p,phi,alpha,beta){const r=state(p,phi),n=axis(alpha,beta),dot=r.reduce((s,x,i)=>s+x*n[i],0);return {r,n,plus:clamp((1+dot)/2),minus:clamp((1-dot)/2),spinOverHbar:dot/2};}
 return {state,axis,predict};
})();
if(typeof module!=='undefined')module.exports=Quantum;
