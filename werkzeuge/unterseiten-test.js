// Prüft die 19 Unterseiten (smarthome/*.html, multimedia/*.html) und die Titelfilme der beiden großen Ratgeber.  node werkzeuge/unterseiten-test.js [Basis-URL]
const {chromium,devices}=require('playwright');const B=process.argv[2]||'http://localhost:8765';let bad=0;
const ok=(c,t)=>{console.log((c?'ok   ':'FEHLER ')+t);if(!c)bad++};
const S={smarthome:['zentrale','licht','steckdose','heizung','tuerschloss','kamera','rollladen','saugroboter','sensoren','schalter','garten'],multimedia:['fernseher','soundbar','streaming','multiroom','beamer','kopfhoerer','receiver','konsole']};
(async()=>{const b=await chromium.launch();const errs=[],fremd=[];
const neu=async o=>{const c=await b.newContext(o);const p=await c.newPage();p.on('pageerror',e=>errs.push(e.message));
 p.on('request',r=>{const u=r.url();if(!u.startsWith(B)&&!/^data:|^blob:/.test(u)&&!/goatcounter/.test(u))fremd.push(u)});return [c,p]};
let [c,p]=await neu({viewport:{width:1440,height:900}});let [c2,q]=await neu({...devices['iPhone 13']});
for(const g of Object.keys(S)){
 await p.goto(B+'/'+g+'.html',{waitUntil:'networkidle'});
 ok(await p.evaluate(a=>a[1].every(i=>!!document.querySelector('#'+i+' a[href="/'+a[0]+'/'+i+'.html"]')),[g,S[g]]),g+': jeder Bereich verlinkt seine Unterseite');
 await p.waitForTimeout(2500);
 ok(await p.evaluate(()=>{const v=document.querySelector('.hero-film'),k=document.querySelector('.hero-stop');return !!v&&!v.paused&&v.classList.contains('an')&&v.muted&&v.loop&&k.classList.contains('da')&&!!document.querySelector('.hero .ki-marke')}),g+': Titelfilm läuft stumm in Schleife, Standbild trägt die KI-Marke');
 await p.click('.hero-stop');ok(await p.evaluate(()=>document.querySelector('.hero-film').paused&&/abspielen/.test(document.querySelector('.hero-stop').textContent)),g+': Film lässt sich anhalten');
 for(const i of S[g]){const u='/'+g+'/'+i+'.html';const r=await p.goto(B+u,{waitUntil:'networkidle'});
  const o=await p.evaluate(a=>{const t=document.querySelector('main').textContent;return {h1:document.querySelectorAll('h1').length,can:document.querySelector('link[rel="canonical"]').href,ld:document.getElementById('ld').textContent,st:document.querySelectorAll('.us-st li').length,fe:document.querySelectorAll('.us-f li').length,fq:document.querySelectorAll('#fragen details').length,img:!!document.querySelector('.hero img[src^="/assets/"]')&&document.querySelector('.hero img').naturalWidth>0,ki:!!document.querySelector('.hero .ki-marke'),bc:!!document.querySelector('.us-bc a[href="/'+a+'.html"]'),nb:document.querySelectorAll('.us-w a').length,src:document.querySelectorAll('.src li').length,
   amz:[...document.querySelectorAll('a[href*="amazon.de/s?"]')].every(l=>/sponsored/.test(l.rel)&&l.target==='_blank'&&/tag=stromdaheim-21/.test(l.href)&&(l.closest('.sm-m')?l.closest('.sm-m').querySelector('.tag'):l.closest('.sm-roh').querySelector('.tag'))),nam:document.querySelectorAll('a[href*="amazon.de/s?"]').length,
   film:!!document.querySelector('.hero-film'),test:/Testsieger|Testnote/.test(t),tot:[...document.querySelectorAll('main a[href^="#"]')].filter(l=>l.getAttribute('href').length>1&&!document.querySelector(l.getAttribute('href'))).map(l=>l.getAttribute('href'))}},g);
  ok(r.status()===200&&o.h1===1&&o.can==='https://strom-daheim.de'+u&&/FAQPage/.test(o.ld)&&/BreadcrumbList/.test(o.ld)&&o.st===5&&o.fe===3&&o.fq===3&&o.img&&o.ki&&o.bc&&o.nb===S[g].length-1&&o.src>=1&&o.amz&&o.nam>=(i==='fernseher'||i==='beamer'||i==='saugroboter'?3:1)&&!o.film&&!o.test&&o.tot.length===0,u+': Aufbau, Foto mit KI-Marke, fünf Schritte, drei Fehler, drei Fragen, Partnerlinks als Anzeige'+(o.tot.length?' (tote Sprünge: '+o.tot.join(',')+')':'')+((o.st!==5||o.fe!==3||o.fq!==3||!o.img||!o.ki||!o.bc||!o.amz||o.test)?' '+JSON.stringify({...o,ld:undefined}):''));
  const tot=await p.evaluate(async()=>{const L=[...new Set([...document.querySelectorAll('main a[href^="/"]')].map(a=>a.getAttribute('href').split('#')[0]))];const R=[];for(const u of L){const s=await fetch(u).then(r=>r.status).catch(()=>0);if(s!==200)R.push(u)}return R});
  ok(tot.length===0,u+': alle internen Links führen zu einer Seite'+(tot.length?': '+tot.join(', '):''));
  await q.goto(B+u,{waitUntil:'networkidle'});
  ok(await q.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1&&[...document.querySelectorAll('.jump a,.us-w a,.sm-go a.btn')].every(e=>e.getBoundingClientRect().height>=38)),u+': Handy ohne seitliches Scrollen, Tippflächen groß genug');}}
await p.goto(B+'/sitemap.xml');const sm=await p.content();ok(Object.keys(S).every(g=>S[g].every(i=>sm.includes('/'+g+'/'+i+'.html'))),'Alle 19 Unterseiten in der Sitemap');
[c,p]=await neu({viewport:{width:1280,height:800},reducedMotion:'reduce'});await p.goto(B+'/smarthome.html',{waitUntil:'networkidle'});await p.waitForTimeout(1500);
ok(await p.evaluate(()=>{const v=document.querySelector('.hero-film');return v.paused&&!v.querySelector('source')&&getComputedStyle(v).display==='none'}),'Bei „Bewegung reduzieren“ lädt und läuft kein Film');
ok(errs.length===0,'Keine Skriptfehler'+(errs.length?': '+errs.slice(0,3).join(' | '):''));ok(fremd.length===0,'Keine Anfrage an fremde Server'+(fremd.length?': '+fremd.slice(0,3).join(', '):''));
await b.close();console.log(bad?('\n'+bad+' FEHLER'):'\nALLE TESTS BESTANDEN');process.exit(bad?1:0)})();
