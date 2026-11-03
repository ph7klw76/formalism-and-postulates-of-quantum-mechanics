/* Every real timed question, review/reset path and final Summary. */
const {chromium}=require('playwright'),fs=require('node:fs/promises'),path=require('node:path'),assert=require('node:assert/strict');const {spawn}=require('node:child_process');
const root=path.resolve(__dirname,'..');
async function main(){
 const cfg=JSON.parse(await fs.readFile(path.join(root,'course/config.json'),'utf8')),events=JSON.parse(await fs.readFile(path.join(root,'course/publication_events.json'),'utf8'));
 const preview=process.env.H5P_PREVIEW==='true',phone=process.env.H5P_PHONE==='true',embedded=process.env.H5P_EMBEDDED==='true';
 const base=process.env.H5P_URL||'http://127.0.0.1:8778'+cfg.base_path+(embedded?'':'h5p/formalism.html');
 const out=path.join(root,'outputs/browser');await fs.mkdir(out,{recursive:true});const label=(preview?'local-mp4':'youtube')+(phone?'-phone':'-desktop')+(embedded?'-embedded':'');
 const server=process.env.H5P_URL?null:spawn(process.env.PYTHON||'python',['scripts/serve.py','--directory',preview?'outputs/h5p-preview':'outputs/pages','--base-path',cfg.base_path,'--port','8778'],{cwd:root,stdio:'ignore',windowsHide:true});
 let browser,page,player;let phase='startup';const paths=[],errors=[],mediaInterruptions=[];
 try{
  for(let i=0;i<50;i++){try{if((await fetch(base)).ok)break;}catch{}await new Promise(r=>setTimeout(r,200));}
  browser=await chromium.launch({headless:true});page=await browser.newPage({viewport:phone?{width:390,height:844}:{width:1280,height:900}});
  page.on('pageerror',e=>{if(preview&&e.name==='AbortError'&&e.message==='The play() request was interrupted by a call to pause(). https://goo.gl/LdLk22')mediaInterruptions.push({name:e.name,message:e.message,phase});else errors.push(e.message);});
  await page.goto(base,{waitUntil:'domcontentloaded'});player=page;
  if(embedded){await page.locator('#lectureH5p').scrollIntoViewIfNeeded();player=await(await page.locator('#lectureH5p').elementHandle()).contentFrame();assert.ok(player);}
  await player.waitForFunction(()=>window.H5P?.instances[0]?.video?.getDuration?.()>600,{},{timeout:60000,polling:250});
  const source=await player.evaluate(()=>H5P.instances[0].options.video.files[0].path);if(preview)assert.ok(source.includes('127.0.0.1:8778'));else assert.equal(source,cfg.youtube_url);
  if(await player.locator('.h5p-splash').isVisible())await player.locator('.h5p-splash').click();else await player.locator('.h5p-controls .h5p-pause').click();
  await player.waitForFunction(()=>H5P.instances[0].video.getCurrentTime()>.5,{},{timeout:45000,polling:250});
  const fullscreen=player.locator('.h5p-controls .h5p-fullscreen');
  await fullscreen.click();await player.waitForFunction(()=>!!document.fullscreenElement,{},{timeout:10000,polling:250});
  await page.screenshot({path:path.join(out,label+'-fullscreen.png')});
  await fullscreen.click();await player.waitForFunction(()=>!document.fullscreenElement,{},{timeout:10000,polling:250});
  await page.screenshot({path:path.join(out,label+'-playing.png'),fullPage:true});
  let parentChapterSeek=null;
  if(embedded){await page.locator('#chapters button').nth(1).click();await player.waitForFunction(t=>Math.abs(H5P.instances[0].video.getCurrentTime()-t)<2,events.chapters[1].start_seconds,{timeout:15000,polling:250});parentChapterSeek=await player.evaluate(()=>H5P.instances[0].video.getCurrentTime());}
  const seekPlay=async time=>{await player.evaluate(()=>H5P.instances[0].pause());await page.waitForTimeout(250);await player.evaluate(t=>H5P.instances[0].seek(t),time);await player.waitForFunction(t=>Math.abs(H5P.instances[0].video.getCurrentTime()-t)<.25,time,{timeout:15000,polling:250});await page.waitForTimeout(250);await player.evaluate(()=>H5P.instances[0].play());};
  for(let i=0;i<events.quizzes.length;i++){
   const q=events.quizzes[i];phase=q.id;await seekPlay(q.time_seconds-.7);
   const task=player.locator('.h5p-multichoice:visible').filter({hasText:q.question});
   const open=async()=>{if(phone){const launch=player.locator('.h5p-interaction[role="button"]:visible').filter({hasText:q.id});await launch.waitFor({state:'visible',timeout:20000});await launch.click();}await task.waitFor({state:'visible',timeout:20000});};await open();
   const at=await player.evaluate(()=>H5P.instances[0].video.getCurrentTime());await page.waitForTimeout(650);const after=await player.evaluate(()=>H5P.instances[0].video.getCurrentTime());assert.ok(Math.abs(after-at)<.25);assert.ok(Math.abs(at-q.time_seconds)<.5);
   const wrong=(q.correct+1)%q.options.length;await task.locator('.h5p-alternative-container').nth(wrong).click();await task.locator('.h5p-question-check-answer').click();assert.ok((await task.innerText()).includes(q.wrong[String(wrong)]));
   await task.locator('.h5p-question-iv-adaptivity-wrong').click();await player.waitForFunction(t=>Math.abs(H5P.instances[0].video.getCurrentTime()-t)<2,q.review_seconds,{timeout:15000,polling:250});const review=await player.evaluate(()=>H5P.instances[0].video.getCurrentTime());
   await seekPlay(q.time_seconds-.7);await open();assert.equal(await task.locator('[aria-checked=true]').count(),0);await task.locator('.h5p-alternative-container').nth(q.correct).click();await task.locator('.h5p-question-check-answer').click();const score=await player.evaluate(index=>H5P.instances[0].interactions[index].getInstance().getScore(),i);assert.equal(score,1);assert.ok((await task.innerText()).includes(q.explanation));
   paths.push({id:q.id,pausedAt:at,wrongFeedback:true,reviewTime:review,targetReview:q.review_seconds,retry:true,correctScore:score});await page.screenshot({path:path.join(out,label+'-'+q.id+'.png'),fullPage:true});await task.locator('.h5p-question-iv-continue').click();await page.waitForTimeout(300);
  }
  phase='summary';const summaryTime=(events.scenes.at(-1).speech_end_frame+5)/events.fps;await seekPlay(summaryTime-.4);
  const launcher=player.locator('.h5p-interaction[role="button"]:visible').filter({hasText:'Final concepts'});await launcher.waitFor({state:'visible',timeout:15000});await launcher.click();
  for(const statements of events.summary)await player.getByRole('radio',{name:statements[0],exact:true}).click();
  const summary=await player.evaluate(()=>{const task=H5P.instances[0].interactions.at(-1).getInstance();return {score:task.getScore(),maxScore:task.getMaxScore()};});assert.equal(summary.score,events.summary.length);assert.equal(summary.maxScore,events.summary.length);
  await page.screenshot({path:path.join(out,label+'-summary.png'),fullPage:true});assert.deepEqual(errors,[]);assert.ok(mediaInterruptions.length<=events.quizzes.length+2);
  await player.locator('.h5p-dialog-close:visible').click();await launcher.waitFor({state:'visible'});await player.evaluate(()=>H5P.instances[0].play());
  await player.waitForFunction(t=>H5P.instances[0].video.getCurrentTime()>t+.2,summaryTime,{timeout:15000,polling:250});
  const report={status:'PASS',verifiedAt:new Date().toISOString(),url:base,source,embedded,viewport:page.viewportSize(),fullscreenReturn:true,summaryContinuation:true,parentChapterSeek,paths,summary,errors,mediaInterruptions};await fs.writeFile(path.join(out,'learning-'+label+'.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
 }catch(e){if(page){await fs.writeFile(path.join(out,'learning-'+label+'-failure.json'),JSON.stringify({message:e.message,completed:paths,errors,text:await page.locator('body').innerText()},null,2));await page.screenshot({path:path.join(out,'learning-'+label+'-failure.png'),fullPage:true});}throw e;}finally{await browser?.close();server?.kill();}
}
main().catch(e=>{console.error(e);process.exitCode=1;});
