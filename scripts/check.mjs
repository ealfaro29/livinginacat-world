import fs from 'node:fs/promises';
import path from 'node:path';
import {rootPath} from './lib.mjs';
const base=path.join(rootPath,'dist/');
await fs.access(path.join(base,'index.html'));
async function files(dir){let result=[];for(const x of await fs.readdir(dir,{withFileTypes:true})){const p=path.join(dir,x.name);result.push(...(x.isDirectory()?await files(p):[p]));}return result;}
const all=await files(base),errors=[];
for(const file of all){if(!/\.(html|js|css|json|md|csv|xml|txt|svg)$/.test(file))continue;const text=await fs.readFile(file,'utf8');if(/\/Users\/|\/var\/folders\/|access_token|[\w.+-]+@(?:gmail|outlook|hotmail)\.com|\b\d{3}-\d{7}-\d{7}\b/i.test(text))errors.push(`Private data marker: ${path.relative(base,file)}`);if(file.endsWith('.html')){if(!text.includes('<html lang="en">'))errors.push(`Missing language: ${file}`);for(const m of text.matchAll(/(?:href|src)="(\/[^"#]*)(?:#[^"]*)?"/g)){const target=m[1].split('?')[0];try{await fs.access(path.join(base,target.endsWith('/')?target+'index.html':target));}catch{errors.push(`Broken local link: ${path.relative(base,file)} -> ${target}`);}}}}
if(errors.length){console.error(errors.join('\n'));process.exit(1);}console.log(`Checked ${all.length} generated files: internal routes and privacy markers OK.`);
