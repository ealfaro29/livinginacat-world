import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {build} from 'esbuild';
const here=path.dirname(fileURLToPath(import.meta.url));
const root=path.resolve(here,'../..');
const result=await build({entryPoints:[path.join(here,'app.mjs')],bundle:true,write:false,format:'iife',platform:'browser',target:'es2022',minify:true,legalComments:'inline',logLevel:'warning'});
const [template,css,license]=await Promise.all([fs.readFile(path.join(here,'index.template.html'),'utf8'),fs.readFile(path.join(here,'style.css'),'utf8'),fs.readFile(path.join(root,'node_modules/three/LICENSE'),'utf8')]);
const js=('/*! Three.js and OrbitControls — '+license+' */\n'+result.outputFiles[0].text).replace(/<\/script/gi,'<\\/script');
const html=template.replace('/*__STYLE__*/',()=>css).replace('/*__APP__*/',()=>js);
for(const dest of ['public/tools/control-module/index.html','public/downloads/ft412-control-module-designer.html']){await fs.mkdir(path.dirname(path.join(root,dest)),{recursive:true});await fs.writeFile(path.join(root,dest),html);}
console.log(`Built standalone offline control-module editor (${Math.round(Buffer.byteLength(html)/1024)} KB).`);
