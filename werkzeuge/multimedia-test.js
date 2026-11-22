// Prüft multimedia.html und die Verweise zwischen Multimedia und Smarthome.  node werkzeuge/multimedia-test.js [Basis-URL]
const {chromium,devices}=require('playwright');const B=process.argv[2]||'http://localhost:8765';let bad=0;
const ok=(c,t)=>{console.log((c?'ok   ':'FEHLER ')+t);if(!c)bad++};
(async()=>{const b=await chromium.launch();const errs=[],fremd=[];
const neu=async o=>{const c=await b.newContext(o);const p=await c.newPage();p.on('pageerror',e=>errs.push(e.message));
 p.on('request',r=>{const u=r.url();if(!u.startsWith(B)&&!/^data:|^blob:/.test(u)&&!/goatcounter/.test(u))fremd.push(u)});return [c,p]};
let [c,p]=await neu({viewport:{width:1440,height:900}});
const r=await p.goto(B+'/multimedia.html',{waitUntil:'networkidle'});ok(r.status()===200,'Seite lädt');
ok(await p.evaluate(()=>document.querySelectorAll('h1').length===1&&document.querySelector('link[rel="canonical"]').href==='https://strom-daheim.de/multimedia.html'&&!!document.getElementById('kurz-gesagt')&&/FAQPage/.test(document.getElementById('ld').textContent)),'Eine h1, kanonische Adresse, Kurz gesagt, strukturierte Daten');
ok(await p.evaluate(I=>I.every(i=>{const s=document.getElementById(i);return s&&s.querySelector('.sm-f img[src^="assets/multimedia-"]')&&s.querySelectorAll('.sm-l li').length>=6&&document.querySelector('.sm-nav a[href="#'+i+'"]')}),['fernseher','soundbar','streaming','multiroom','beamer']),'Fünf Bereiche, je mit Foto, Listen und Sprungmarke');
ok(await p.$$eval('.sm-m',A=>A.length===6&&A.every(a=>{const l=a.querySelector('.sm-go a.btn');return /amazon\.de\/s\?k=.+tag=stromdaheim-21/.test(l.href)&&/sponsored/.test(l.rel)&&l.target==='_blank'&&a.querySelector('.tag')&&a.querySelectorAll('.sm-pc ul li').length>=2})),'Sechs Modelle mit Dafür, Dagegen und Partnerlink als Anzeige');
ok(await p.$$eval('a[href*="amazon."]',A=>A.length>=14&&A.every(a=>/sponsored/.test(a.rel)&&a.target==='_blank'&&/tag=stromdaheim-21/.test(a.href))),'Alle Amazon-Links mit Kennung und sponsored');
const wahl=async w=>{await p.evaluate(w=>{for(const [n,v] of Object.entries(w)){const i=document.querySelector(`#sm-form input[name="${n}"][value="${v}"]`);i.checked=true;i.dispatchEvent(new Event('change',{bubbles:true}))}},w);return p.evaluate(()=>[...document.querySelectorAll('#sm-out li a')].map(a=>a.getAttribute('href')).join(' '))};
let o=await wahl({tv:'neu',raum:'mittel',atmos:'ja',handy:'android'});ok(o==='#m-sonos-beam #m-google-streamer #m-sonos-era100','Finder Wohnzimmer: '+o);
o=await wahl({tv:'alt',raum:'gross',atmos:'ja',handy:'iphone'});ok(o.startsWith('#m-sonos-ray #m-apple-tv'),'Finder optischer Ausgang, iPhone: '+o);
o=await wahl({tv:'neu',raum:'gross',atmos:'ja',handy:'android'});ok(o.startsWith('#m-sonos-arc'),'Finder großer Raum: '+o);
o=await wahl({tv:'neu',raum:'klein',atmos:'nein',handy:'android'});ok(o==='#m-sonos-ray #m-google-streamer','Finder kleiner Raum: '+o);
ok(await p.evaluate(()=>[...document.querySelectorAll('#sm-out li a,.sm-pk li a')].every(a=>!!document.querySelector(a.getAttribute('href')))),'Sprünge aus Finder und Startpaketen führen zu einem Modell');
ok(await p.evaluate(()=>document.querySelectorAll('a[href="/smarthome.html"]').length>=3&&/kein Gerät selbst getestet/.test(document.getElementById('quellen').textContent)&&!/Testsieger|Testnote/.test(document.querySelector('main').textContent))&&await p.$$eval('#quellen .src li',A=>A.length>=9),'Verweist auf den Smarthome-Ratgeber, Quellen genannt, kein eigener Test behauptet');
for(const u of ['/stromkosten/fernseher.html','/stromkosten/spielkonsole.html','/stromkosten/wlan-router.html','/energielabel.html']){const st=await p.evaluate(u=>fetch(u).then(r=>r.status),u);ok(st===200,'Verlinkte Seite gibt es: '+u)}
await p.goto(B+'/smarthome.html',{waitUntil:'networkidle'});ok(await p.evaluate(()=>document.querySelectorAll('a[href="/multimedia.html"]').length>=2),'Smarthome-Ratgeber verweist auf Multimedia');
await p.goto(B+'/');ok(await p.evaluate(()=>!!document.querySelector('#alles a[href="/multimedia.html"] img')),'Kachel auf der Startseite');
await p.goto(B+'/sitemap.xml');ok((await p.content()).includes('/multimedia.html'),'Steht in der Sitemap');await c.close();
[c,p]=await neu({...devices['iPhone 13']});await p.goto(B+'/multimedia.html',{waitUntil:'networkidle'});await p.waitForTimeout(300);
ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'Handy: kein seitliches Scrollen');
ok(await p.evaluate(()=>[...document.querySelectorAll('.sm-go a.btn,.sm-ch span,.sm-nav a,.jump a,.sm-pk li a')].every(e=>e.getBoundingClientRect().height>=38)),'Handy: Tippflächen groß genug');await c.close();
ok(errs.length===0,'Keine Skriptfehler'+(errs.length?': '+errs.join(' | '):''));ok(fremd.length===0,'Keine Anfrage an fremde Server'+(fremd.length?': '+fremd.slice(0,3).join(', '):''));
await b.close();console.log(bad?('\n'+bad+' FEHLER'):'\nALLE TESTS BESTANDEN');process.exit(bad?1:0)})();
