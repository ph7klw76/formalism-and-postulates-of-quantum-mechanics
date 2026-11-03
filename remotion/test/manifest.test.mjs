import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
const e=JSON.parse(fs.readFileSync(new URL('../src/generated/events.json',import.meta.url),'utf8'));
test('composition uses the measured twelve-minute schedule',()=>{assert.equal(e.status,'MEASURED');assert.equal(e.duration_frames,e.fps*720);assert.equal(e.scenes.reduce((n,s)=>n+s.duration_frames,0),e.duration_frames);});
test('prediction options carry no leading reveal and precede explanation',()=>{for(const q of e.quizzes){assert.ok(q.options.length>=3);assert.ok(q.frame<q.reveal_frame);assert.equal(e.scenes[q.scene].kind,'predict');assert.equal(e.scenes[q.scene].formulas.length,0);}});
