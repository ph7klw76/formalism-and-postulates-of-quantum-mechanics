const fs=require('fs'),path=require('path'),assert=require('assert/strict'),child=require('child_process');
const root=path.resolve(__dirname,'..'),dist=path.join(root,'outputs/pages'),q=require(path.join(dist,'physics.js'));
const fixtures=JSON.parse(fs.readFileSync(path.join(root,'outputs/physics-fixtures.json'),'utf8'));
for(const f of fixtures){const actual=q.predict(f.population,f.phase,f.polar,f.azimuth);assert.ok(Math.abs(actual.plus-f.plus)<1e-12);assert.ok(Math.abs(actual.spinOverHbar-f.spinOverHbar)<1e-12);assert.ok(Math.abs(actual.plus+actual.minus-1)<1e-12);}
for(const file of ['app.js','physics.js','config.js'])child.execFileSync(process.execPath,['--check',path.join(dist,file)]);
let links=0;for(const name of fs.readdirSync(dist).filter(x=>x.endsWith('.html'))){const html=fs.readFileSync(path.join(dist,name),'utf8');for(const m of html.matchAll(/(?:src|href)="([^"#]+)"/g)){const target=m[1].split(/[?#]/)[0];if(/^(https?:|data:|mailto:)/.test(target))continue;if(target.endsWith('.h5p')&&!JSON.parse(fs.readFileSync(path.join(root,'course/config.json'),'utf8')).youtube_url)continue;assert.ok(fs.existsSync(path.join(dist,target)),name+': '+target);links++;}}
console.log(JSON.stringify({status:'PASS',independent_python_javascript_cases:fixtures.length,local_links:links}));
