const fs=require('node:fs/promises'),fss=require('node:fs'),path=require('node:path');const {once}=require('node:events');
const H5P=require('@lumieducation/h5p-server'),HtmlExporter=require('@lumieducation/h5p-html-exporter').default;
const root=path.resolve(__dirname,'..'),work=path.join(root,'tools/h5p');
const viewport=html=>html.replace('<meta charset="utf-8">','<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">');
async function main(){
 const cfg=JSON.parse(await fs.readFile(path.join(root,'course/config.json'),'utf8'));
 const preview=process.argv.includes('--preview'),onlyLibraries=process.argv.includes('--libraries-only');
 const {FileLibraryStorage,FileContentStorage,DirectoryTemporaryFileStorage,InMemoryStorage}=H5P.fsImplementations;
 for(const name of ['content','temp'])await fs.mkdir(path.join(work,name),{recursive:true});
 const libraries=new FileLibraryStorage(path.join(work,'libraries')),content=new FileContentStorage(path.join(work,'content'));
 const config=new H5P.H5PConfig(new InMemoryStorage(),{coreApiVersion:{major:1,minor:28},h5pVersion:'1.28.0',maxTotalSize:128*1024*1024,maxFileSize:64*1024*1024});
 const editor=new H5P.H5PEditor(new InMemoryStorage(),config,libraries,content,new DirectoryTemporaryFileStorage(path.join(work,'temp')),undefined,undefined,{permissionSystem:new H5P.LaissezFairePermissionSystem()});
 const user={id:'author',name:'Quantum Formalism Lab',email:'',type:'local'};
 const preserved=path.join(root,'h5p/Quantum_Formalism_Interactive.h5p');
 if(await fs.stat(preserved).catch(()=>null))await editor.uploadPackage(preserved,user,{onlyInstallLibraries:true});
 else for(const name of ['H5P.InteractiveVideo','H5P.MultiChoice','H5P.Summary'])await editor.uploadPackage(path.join(work,name+'.h5p'),user,{onlyInstallLibraries:true});
 const upstream=path.join(work,'video-upstream'),v=JSON.parse(await fs.readFile(path.join(upstream,'library.json'),'utf8'));
 if(v.machineName!=='H5P.Video'||v.majorVersion!==1||v.minorVersion!==6||v.patchVersion!==81)throw Error('Expected the pinned official Video 1.6.81 adapter');
 await editor.libraryManager.installFromDirectory(upstream);if(onlyLibraries)return;
 const exporter=new HtmlExporter(libraries,content,config,path.join(work,'core'),path.join(work,'editor'));
 const metadata=JSON.parse(await fs.readFile(path.join(root,'h5p/h5p.json'),'utf8'));
 const questions=JSON.parse(await fs.readFile(path.join(root,'h5p/questions.json'),'utf8'));
 const publicDir=path.join(root,'website/dist/h5p');await fs.mkdir(publicDir,{recursive:true});
 for(let i=0;i<questions.length;i++){
  const id=String(i+2);await content.addContent({...metadata,mainLibrary:'H5P.MultiChoice',title:'Original formative question '+(i+1),preloadedDependencies:[{machineName:'H5P.MultiChoice',majorVersion:1,minorVersion:16}]},questions[i],user,id);
  await fs.writeFile(path.join(publicDir,`question-${i+1}.html`),viewport(await exporter.createSingleBundle(id,user,{showLicenseButton:true,showFrame:true})));
 }
 if(!cfg.youtube_url&&!preview){console.log('Exported standalone practice; public interactive video awaits its confirmed upload URL.');return;}
 const params=JSON.parse(await fs.readFile(path.join(root,preview?'outputs/h5p-preview/params.json':'h5p/content.json'),'utf8'));
 const id=preview?'99':'1';await content.addContent(metadata,params,user,id);
 await content.addFile(id,'subtitles/lecture.vtt',fss.createReadStream(path.join(root,'website/dist/lecture.vtt')),user);
 const directory=preview?path.join(root,'outputs/h5p-preview/h5p'):publicDir;await fs.mkdir(directory,{recursive:true});
 await fs.writeFile(path.join(directory,'formalism.html'),viewport(await exporter.createSingleBundle(id,user,{showLicenseButton:true,showFrame:true})));
 const packager=new H5P.PackageExporter(editor.libraryManager,content,{exportMaxContentPathLength:255,permissionSystem:new H5P.LaissezFairePermissionSystem()});
 const target=path.join(preview?directory:path.join(root,'h5p'),'Quantum_Formalism_Interactive.h5p');const stream=fss.createWriteStream(target),finished=once(stream,'finish');await packager.createPackage(id,stream,user);await finished;
 if(!preview){const crypto=require('node:crypto');cfg.video_revision=crypto.createHash('sha256').update(await fs.readFile(path.join(directory,'formalism.html'))).digest('hex').slice(0,12);await fs.writeFile(path.join(root,'course/config.json'),JSON.stringify(cfg,null,2)+'\n');}
 console.log('Exported native package and Lumi HTML:',target);
}
main().catch(e=>{console.error(e);process.exitCode=1;});
