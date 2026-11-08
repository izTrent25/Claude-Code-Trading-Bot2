// Standard Node.js VM test of dashboard behavior with a mock DOM/canvas.
// This checks rendering logic and controls, not real-browser layout or CSS.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(__dirname+'/dashboard.html','utf8');
const source=html.match(/<script>([\s\S]*)<\/script>/)[1];
const snapshot=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const els={},calls=[];const context2d=new Proxy({},{get:(o,k)=>o[k]??(()=>{}),set:(o,k,v)=>(o[k]=v,true)});
for(const match of html.matchAll(/id="([^"]+)"/g))els[match[1]]={textContent:'',innerHTML:'',clientWidth:600,clientHeight:250,getContext:()=>context2d};
const sandbox={document:{getElementById:id=>{assert(els[id],'Missing element '+id);return els[id]}},devicePixelRatio:1,addEventListener:()=>{},setInterval:()=>{},console,fetch:async(path,opts)=>{calls.push({path,opts});return {ok:true,json:async()=>path==='/api/state'?snapshot:{ok:true}}}};
vm.createContext(sandbox);vm.runInContext(source,sandbox);
(async()=>{await new Promise(r=>setTimeout(r,0));assert(els.source.textContent.includes('SYNTHETIC'));assert(els.stats.innerHTML.includes('Paper equity'));assert(els.trades.innerHTML.includes('EXIT')===false);assert(els.trades.innerHTML.includes('<tr>'));assert(!els.error.textContent,els.error.textContent);await vm.runInContext("act('pause')",sandbox);assert(calls.some(x=>x.path==='/api/pause'&&x.opts.headers['X-Control-Token']===snapshot.token));console.log('Dashboard JavaScript rendering + authenticated control tests passed (mock DOM).')})().catch(e=>{console.error(e);process.exitCode=1});
