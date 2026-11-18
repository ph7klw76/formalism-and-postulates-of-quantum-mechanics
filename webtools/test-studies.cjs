'use strict';
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const path = require('node:path');
const {chromium} = require('playwright');

async function checkStudies(browser, base) {
  // Use spectral projectors and unitary evolution independently of browser Bloch geometry.
  const reference = JSON.parse(execFileSync(process.env.PYTHON || 'python', ['-c', [
    'import json, numpy as np',
    'from course.physics import Z_PLUS, X_PLUS, X, Z, I, dephase, observable, evolve, probabilities',
    'angles = np.deg2rad(np.arange(181))',
    'middle = [observable([np.sin(a), 0, np.cos(a)]) for a in angles]',
    'states = [evolve(X_PLUS, np.pi*Z/2, i/40) for i in range(81)]',
    'print(json.dumps(dict(analyzer=[[float(np.trace(dephase(Z_PLUS,m) @ ((I+Z)/2)).real),1] for m in middle],',
    '                      clock=[[probabilities(v,X)[1][1],probabilities(v,Z)[1][1]] for v in states])))'
  ].join('\n')], {cwd:path.resolve(__dirname,'..'),encoding:'utf8'}));

  for (const phone of [false,true]) {
    const page = await browser.newPage({viewport:phone ? {width:390,height:844} : {width:1280,height:900},
      hasTouch:phone, reducedMotion:'reduce'});
    try {
      for (const [id,anchor,target] of [['analyzer','unread-measurement',90],['clock','spin-clock',1]]) {
        await page.goto('about:blank');
        await page.goto(base + '#' + anchor, {waitUntil:'domcontentloaded'});
        const host = page.locator(`[data-study="${id}"]`);
        const select = host.getByRole('combobox'), run = host.locator('[data-run]');
        const slider = host.locator('input'), figure = host.locator('svg').first(), graph = host.locator('svg').last();
        assert.ok(await run.isDisabled());
        assert.equal(await graph.locator('polyline').count(),0);
        assert.ok(await host.locator('details').isHidden());
        const initial = await figure.innerHTML();
        await select.selectOption(phone ? '0' : '1');
        if (phone) await run.tap(); else await run.press('Enter');
        assert.equal(Number(await slider.inputValue()),target);
        assert.notEqual(await figure.innerHTML(),initial);
        assert.equal((await host.locator('[data-feedback]').innerText()).startsWith('Yes.'),!phone);
        const reading = await host.locator('[data-reading]').innerText();
        assert.ok(reading.includes(id === 'clock' ? '0.0% of an x' : '50.0% finish z-up'),reading);
        const rows = await host.evaluate(el => {
          const input=el.querySelector('input'), saved=input.value, result=[];
          const tickCount=Math.round(Number(input.max)/Number(input.step));
          for (let i=0;i<=tickCount;i++) {
            input.value=i*Number(input.step);
            input.dispatchEvent(new Event('input'));
            const y=Number(el.querySelector('[data-point]').getAttribute('cy'));
            const baseline=Number(el.querySelector('[data-reference]').getAttribute('y'))+4;
            result.push([(142-y)/112,(142-baseline)/112]);
          }
          input.value=saved;
          input.dispatchEvent(new Event('input'));
          return result;
        });
        assert.equal(rows.length,reference[id].length);
        rows.forEach((pair,i)=>pair.forEach((v,j)=>assert.ok(Math.abs(v-reference[id][i][j])<1e-10)));
        if (phone) {
          const bounds=await slider.boundingBox();
          await slider.tap({position:{x:bounds.width*.79,y:bounds.height/2}});
        } else { await slider.press('End'); }
        assert.notEqual(Number(await slider.inputValue()),target);
        assert.ok(!await host.locator('details').evaluate(node=>node.open));
        await host.locator('summary').click();
        assert.ok(await host.getByRole('link',{name:/Reproduce/}).isVisible());
        assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
        await host.locator('[data-reset]').click();
        assert.equal(await figure.innerHTML(),initial);
        assert.ok(await run.isDisabled());
        assert.ok(await host.locator('details').isHidden());
      }
    } finally { await page.close(); }
  }
  return {studies:2,parameterSettings:reference.analyzer.length+reference.clock.length,layouts:['desktop keyboard','phone touch']};
}
module.exports={checkStudies};
if (require.main===module) (async()=>{
  const browser=await chromium.launch({executablePath:process.env.CHROME_PATH || undefined});
  try { console.log(await checkStudies(browser,process.argv[2])); }
  finally { await browser.close(); }
})().catch(e=>{console.error(e);process.exitCode=1;});
