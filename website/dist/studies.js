/* Learner-paced model comparisons. All probabilities describe ideal ensembles. */
(() => {
  'use strict';
  const halfTurn = Math.PI;
  const teal = '#086e67', gold = '#865608', ink = '#12313d';
  const pct = n => (100 * n).toFixed(1) + '%';
  const label = (x, y, text, align = 'start') =>
    `<text x="${x}" y="${y}" text-anchor="${align}">${text}</text>`;
  function arrow(id, x, y, dx, dy) {
    return `<defs><marker id="${id}-tip" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="3.5" markerHeight="3.5" orient="auto"><path fill="${teal}" d="M0 0 L10 5 L0 10 Z"/></marker></defs>
      <path d="M${x} ${y} l${dx} ${dy}" stroke="${teal}" stroke-width="4" marker-end="url(#${id}-tip)"/>`;
  }
  const studies = {
    analyzer: {
      choices:['All still finish up', 'Half finish up', 'None finish up'],
      action:'Turn the middle analyzer to 90°', control:'Middle analyzer tilt from +z',
      max:180, step:1, target:90, format:v => v + '°', xLabel:'Middle tilt (degrees)',
      figure:'Middle analyzer and its two outputs', graph:'Final z-up probability',
      series:'With middle measurement', reference:'Bypass',
      model(degrees) {
        const tilt = degrees * halfTurn / 180;
        const middle = Quantum.predict(1, 0, tilt, 0);
        // Post-measurement states point along ±n. Add their final probabilities incoherently.
        const upFromPlus = (1 + middle.n[2]) / 2;
        const upFromMinus = (1 - middle.n[2]) / 2;
        return {primary:middle.plus * upFromPlus + middle.minus * upFromMinus,
          reference:1, plus:middle.plus, minus:middle.minus, dx:middle.n[0], dz:middle.n[2]};
      },
      draw(v, s) {
        const bar = (y, fraction, sign) => `${label(176,y-6,sign + ' port · ' + pct(fraction))}
          <rect x="176" y="${y}" width="136" height="8" fill="#d4dfda"/>
          <rect x="176" y="${y}" width="${136 * fraction}" height="8" fill="${teal}"/>`;
        return `<circle cx="80" cy="97" r="50" fill="white" stroke="#bbc9c4"/>
          <path d="M80 42 V152 M25 97 H135" fill="none" stroke="#a6b8b2"/>
          ${label(80,34,'+z','middle')}${label(139,102,'+x')}
          ${arrow('middle',80,97,49*s.dx,-49*s.dz)}
          ${bar(68,s.plus,'+')}${bar(119,s.minus,'−')}
          ${label(80,178,v + '° tilt','middle')}${label(176,178,'Both ports retained')}`;
      },
      reading:(v,s) => `Middle tilt ${v}°. The middle + and − groups contain ${pct(s.plus)} and ${pct(s.minus)} of preparations. Across both groups, ${pct(s.primary)} finish z-up. Bypassing the middle measurement gives 100%.`,
      feedback:['Ignoring a reading still leaves the ensemble changed by the measuring device.', 'Yes. Each middle output is equally likely to finish z-up.', 'A perpendicular middle axis makes the final reading uncertain. It does not force z-down.'],
      prompt:'Turn the middle analyzer to 180°. Why does the final z result become certain again even though the middle port label changes?',
      equation:'If θ is the middle tilt, the unread measurement gives P(final z+) = cos⁴(θ/2) + sin⁴(θ/2). The two terms are the probabilities of mutually exclusive recorded paths. The middle device performs an ideal projective measurement with both groups retained and no coherent recombination.'
    },
    clock: {
      choices:['Only the z-up fraction', 'Only the x-up fraction', 'Both up fractions'],
      action:'Advance the preparation to 1 s', control:'Evolution time',
      max:2, step:.025, target:1, format:v => v.toFixed(3) + ' s', xLabel:'Elapsed time (s)',
      figure:'State direction viewed from +z', graph:'Two choices of final detector',
      series:'Measure x', reference:'Measure z',
      model(t) {
        const phase = halfTurn * t;
        const x = Quantum.predict(.5, phase, halfTurn / 2, 0);
        return {primary:x.plus, reference:Quantum.predict(.5,phase,0,0).plus, dx:x.r[0], dy:x.r[1]};
      },
      draw(t,s) {
        return `<circle cx="107" cy="98" r="52" fill="white" stroke="#96ada5"/>
          <path d="M45 98 H169 M107 36 V160" fill="none" stroke="#a6b8b2"/>
          ${label(174,103,'+x')}${label(107,28,'+y','middle')}
          ${arrow('clock',107,98,51*s.dx,-51*s.dy)}
          ${label(212,78,'Elapsed time')}${label(212,101,t.toFixed(3) + ' s')}
          ${label(18,181,'Equatorial Bloch vector · abstract state direction')}`;
      },
      reading:(t,s) => `At ${t.toFixed(3)} s, ${pct(s.primary)} of an x detector’s outcomes are predicted up and ${pct(s.reference)} of a z detector’s outcomes are predicted up.`,
      feedback:['The state stays in the equatorial plane, so the z populations stay equal.', 'Yes. The state now points along −x. Its projection along z is still zero.', 'A change of state can be invisible to a particular observable. Compare the two detector traces.'],
      prompt:'Scrub to 0.5 s and 1.5 s. Both detectors give the same fractions at those two times. Which additional detector could distinguish the states?',
      equation:'For H = ℏωσz/2 with ω = π rad/s, the relative phase advances by ωt. Starting from x-up gives P(x+) = [1 + cos(ωt)]/2 and P(z+) = 1/2. Assume isolated spin-½ preparations and one final projective measurement per preparation.'
    }
  };

  function plot(s, v, state, reveal) {
    const x = value => 48 + 258 * value / s.max;
    const y = p => 142 - 112 * p;
    const points = Array.from({length:121}, (_,i) => {
      const at = s.max * i / 120;
      return x(at).toFixed(2) + ',' + y(s.model(at).primary).toFixed(2);
    }).join(' ');
    const traces = reveal ? `<line x1="48" x2="306" y1="${y(state.reference)}" y2="${y(state.reference)}" stroke="${gold}" stroke-width="2" stroke-dasharray="6 4"/>
      <polyline points="${points}" fill="none" stroke="${teal}" stroke-width="3"/>` : '';
    return `<path d="M48 24 V142 H306" fill="none" stroke="#889b95"/>
      ${[0,.5,1].map(p=>label(39,y(p)+4,100*p+'%','end')).join('')}
      ${[0,s.max/2,s.max].map(v=>label(x(v),163,v,'middle')).join('')}
      ${label(177,186,s.xLabel,'middle')}${traces}
      <rect data-reference x="${x(v)-4}" y="${y(state.reference)-4}" width="8" height="8" fill="white" stroke="${gold}" stroke-width="2"/>
      <circle data-point cx="${x(v)}" cy="${y(state.primary)}" r="3.8" fill="${teal}"/>`;
  }

  function mount(host) {
    const id = host.dataset.study, s = studies[id];
    host.innerHTML = `<div class="prediction-choice"><label>My prediction
      <select><option value="">Choose an outcome</option>${s.choices.map((q,i)=>`<option value="${i}">${q}</option>`).join('')}</select></label>
      <button data-run type="button" disabled>${s.action}</button></div>
      <div class="prediction-pair"><figure><figcaption>${s.figure}</figcaption><svg viewBox="0 0 330 196" role="img" aria-label="${s.figure}"></svg></figure>
      <figure><figcaption>${s.graph}</figcaption><svg viewBox="0 0 330 196" role="img" aria-label="${s.graph}"></svg>
      <div class="trace-key"><span>● ${s.series}</span><span>□ ${s.reference}</span></div></figure></div>
      <p data-reading></p><p data-feedback role="status"></p>
      <div data-experiment hidden><label for="${id}-value">${s.control} <output for="${id}-value"></output></label>
      <input id="${id}-value" type="range" min="0" max="${s.max}" value="0" step="${s.step}"/>
      <p>${s.prompt}</p><details><summary>Explain with the equation</summary><p>${s.equation}</p>
      <a href="lab/lab/index.html?path=Quantum_Formalism_Lab.ipynb">Reproduce the experiment in Python</a></details>
      <button data-reset type="button">Try the prediction again</button></div>`;
    const select = host.querySelector('select'), run = host.querySelector('[data-run]');
    const slider = host.querySelector('input'), explore = host.querySelector('[data-experiment]');
    const feedback = host.querySelector('[data-feedback]'), [diagram, graph] = host.querySelectorAll('svg');
    function render() {
      const v = Number(slider.value), state = s.model(v), reading = s.reading(v,state);
      diagram.innerHTML = s.draw(v,state);
      graph.innerHTML = plot(s,v,state,!explore.hidden);
      host.querySelector('[data-reading]').textContent = reading;
      host.querySelector('output').value = s.format(v);
      slider.setAttribute('aria-valuetext', s.format(v) + '. ' + reading);
    }
    select.onchange = () => { run.disabled = select.value === ''; };
    run.onclick = () => {
      explore.hidden = false;
      select.disabled = run.disabled = true;
      slider.value = s.target;
      feedback.textContent = s.feedback[Number(select.value)];
      render();
      slider.focus({preventScroll:true});
    };
    slider.oninput = render;
    host.querySelector('[data-reset]').onclick = () => {
      slider.value = 0;
      explore.hidden = true;
      host.querySelector('details').open = false;
      select.value = '';
      select.disabled = false;
      run.disabled = true;
      feedback.textContent = '';
      render();
      select.focus();
    };
    render();
  }
  document.querySelectorAll('[data-study]').forEach(mount);
})();
