/* Actual responsive course, genuine H5P practice and executable Pyodide checks. */
const {chromium}=require('playwright');const fs=require('node:fs/promises'),path=require('node:path'),assert=require('node:assert/strict');const {spawn}=require('node:child_process');
const root=path.resolve(__dirname,'..');
async function main(){
 const cfg=JSON.parse(await fs.readFile(path.join(root,'course/config.json'),'utf8')),events=JSON.parse(await fs.readFile(path.join(root,'course/publication_events.json'),'utf8'));
 const out=path.join(root,'outputs/browser');await fs.mkdir(out,{recursive:true});
 const base=process.env.COURSE_TEST_URL||'http://127.0.0.1:8776'+cfg.base_path;
 const server=process.env.COURSE_TEST_URL?null:spawn(process.env.PYTHON||'python',['scripts/serve.py','--directory','outputs/pages','--base-path',cfg.base_path,'--port','8776'],{cwd:root,stdio:'ignore',windowsHide:true});
 let browser,page;const report={base,layouts:[],h5pPractice:[],video:null,notebook:null};const errors=[];
 try{
  for(let i=0;i<50;i++){try{if((await fetch(base)).ok)break;}catch{}await new Promise(r=>setTimeout(r,200));}
  browser=await chromium.launch({headless:true});page=await browser.newPage();page.on('pageerror',e=>errors.push(e.message));
  for(const [name,width,height] of [['desktop',1440,960],['tablet',820,1180],['phone',390,844]]){
   await page.setViewportSize({width,height});await page.goto(base,{waitUntil:'domcontentloaded'});await page.locator('#chapters button').nth(events.chapters.length-1).waitFor();
   assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),name+' overflow');assert.equal(await page.locator('#chapters button').count(),events.chapters.length);
   assert.equal(await page.locator('#probability').innerText(),'0.600000');
   await page.locator('[data-axis="x"]').click();assert.ok(Math.abs(parseFloat(await page.locator('#probability').innerText())-.744948974)<1e-6);
   await page.locator('#rotate').click();assert.ok(Math.abs(parseFloat(await page.locator('#probability').innerText())-.255051026)<1e-6);
   await page.locator('#condition').click();assert.ok(Math.abs(parseFloat(await page.locator('#probability').innerText())-1)<1e-6);
   await page.locator('#reset').click();await page.screenshot({path:path.join(out,name+'.png'),fullPage:true});report.layouts.push({name,width,noOverflow:true,stateMeasurementControls:true});
  }
  await page.setViewportSize({width:1280,height:900});
  for(const q of events.quizzes){
   await page.goto(base+'h5p/question-'+q.id.slice(1)+'.html',{waitUntil:'domcontentloaded'});const task=page.locator('.h5p-multichoice');await task.waitFor();const wrong=(q.correct+1)%q.options.length;
   await task.locator('.h5p-alternative-container').nth(wrong).click();await task.locator('.h5p-question-check-answer').click();assert.ok((await task.innerText()).includes(q.wrong[String(wrong)]));
   await task.locator('.h5p-question-try-again').click();await task.locator('.h5p-alternative-container').nth(q.correct).click();await task.locator('.h5p-question-check-answer').click();
   const score=await page.evaluate(()=>H5P.instances[0].getScore());assert.equal(score,1);assert.ok((await task.innerText()).includes(q.explanation));report.h5pPractice.push({id:q.id,wrongFeedback:true,retry:true,score});
  }
  if(cfg.youtube_url){
   await page.goto(base,{waitUntil:'domcontentloaded'});await page.locator('#lectureH5p').scrollIntoViewIfNeeded();const frame=await(await page.locator('#lectureH5p').elementHandle()).contentFrame();
   await frame.waitForFunction(()=>window.H5P?.instances[0]?.video?.getDuration?.()>600,{},{timeout:60000,polling:250});
   const source=await frame.evaluate(()=>H5P.instances[0].options.video.files[0].path);assert.equal(source,cfg.youtube_url);
   const geometry=await frame.locator('.h5p-video-wrapper iframe').evaluate(e=>{const b=e.getBoundingClientRect(),p=e.parentElement.getBoundingClientRect();return {x:b.x-p.x,y:b.y-p.y,width:b.width,height:b.height};});assert.ok(Math.abs(geometry.y)<2&&geometry.width>200);
   report.video={mode:'startup-only',source,geometry,streaming:'Separate real streaming and all-learning-path tests are required.'};
  }else report.video={mode:'NOT_RUN',reason:'No confirmed public video URL; this build is not deployable yet.'};
  await page.setViewportSize({width:1440,height:960});await page.goto(base+'lab/lab/index.html?path=Quantum_Formalism_Lab.ipynb',{waitUntil:'domcontentloaded'});await page.waitForSelector('.jp-Notebook',{timeout:120000});
  const choose=async()=>{const b=page.getByRole('button',{name:'Select',exact:true});try{await b.waitFor({state:'visible',timeout:3500});}catch(e){if(e.name==='TimeoutError')return false;throw e;}await page.locator('.jp-Dialog select').selectOption({label:'Python (Pyodide)'});await b.click();return true;};
  let selected=await choose();await page.getByRole('menuitem',{name:'Run',exact:true}).click();await page.getByText('Run All Cells',{exact:true}).click();selected=(await choose())||selected;
  await page.waitForFunction(()=>document.querySelectorAll('.jp-OutputArea-error').length||[...document.querySelectorAll('.jp-OutputArea-output')].some(e=>e.textContent.includes('Three-level observable eigenvalues:')),{},{timeout:300000,polling:500});
  assert.equal(await page.locator('.jp-OutputArea-error').count(),0);await page.waitForFunction(()=>document.querySelectorAll('.jp-OutputArea-output img').length>=4,{},{timeout:30000,polling:250});
  const results=await page.locator('.jp-OutputArea-output').allTextContents();assert.ok(results.some(x=>x.includes('emscripten')));assert.ok(results.some(x=>x.includes('LAB_COMPLETE')));
  // Change a preparation in the actual notebook UI, then execute the new cell.
  const last=page.locator('.jp-CodeCell').last();await last.scrollIntoViewIfNeeded();await last.locator('.jp-InputArea-editor').click();await page.keyboard.press('Escape');await page.keyboard.press('b');await page.keyboard.press('Enter');
  await page.keyboard.insertText("probe=state(np.arccos(0.2),np.pi)\nprint('PARAMETER_CHECK',round((1+expectation(probe,X))/2,9),round((1+expectation(probe,Z))/2,9))");await page.keyboard.press('Control+Enter');
  await page.waitForFunction(()=>[...document.querySelectorAll('.jp-OutputArea-output')].some(e=>e.textContent.includes('PARAMETER_CHECK 0.010102051 0.6')),{},{timeout:30000,polling:250});
  report.notebook={errors:0,plots:await page.locator('.jp-OutputArea-output img').count(),kernelChoiceHandled:selected,parameterChange:true,outputs:await page.locator('.jp-OutputArea-output').allTextContents()};
  await page.screenshot({path:path.join(out,'jupyterlite.png'),fullPage:true});assert.deepEqual(errors,[]);report.pageErrors=errors;report.status='PASS';await fs.writeFile(path.join(out,'course-results.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({status:report.status,layouts:report.layouts.length,h5pPractice:report.h5pPractice.length,notebook:report.notebook}));
 }catch(e){if(page){await fs.writeFile(path.join(out,'failure.json'),JSON.stringify({message:e.message,errors,text:await page.locator('body').innerText()},null,2));await page.screenshot({path:path.join(out,'failure.png'),fullPage:true});}throw e;}finally{await browser?.close();server?.kill();}
}
main().catch(e=>{console.error(e);process.exitCode=1;});
