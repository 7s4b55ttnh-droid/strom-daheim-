// Prüft die Zusatzbausteine aus mehr.js: node werkzeuge/mehr-test.js [Basis-URL]
const {chromium}=require('playwright');const B=process.argv[2]||'http://localhost:8765';let bad=0;const ok=(c,t)=>{console.log((c?'ok   ':'FEHLER ')+t);if(!c)bad++};
(async()=>{const b=await chromium.launch();const ctx=await b.newContext({viewport:{width:390,height:800},reducedMotion:'reduce'});const p=await ctx.newPage();const errs=[];p.on('pageerror',e=>errs.push(String(e)));
// Schnell-Check auf der Startseite, Ergebnis muss zum Planer passen
await p.goto(B+'/',{waitUntil:'load'});await p.waitForTimeout(700);await p.screenshot({path:'/tmp/hero.png'});await p.evaluate(()=>document.querySelector('[data-check]').click());await p.waitForTimeout(300);
ok(await p.evaluate(()=>{const d=document.querySelector('dialog.mx-dlg');return !!d&&d.open}),'Schnell-Check öffnet als Dialog');
await p.fill('#mx-plz','97274');await p.waitForFunction(()=>document.querySelector('.mx-out b'),null,{timeout:15000});
const c=await p.evaluate(()=>({eur:document.querySelector('.mx-out b').textContent,t:document.querySelector('.mx-out p').textContent,href:document.querySelector('.mx-go a').getAttribute('href'),bild:!document.querySelector('.mx-go [data-b]').hidden}));
ok(/^\d+ €$/.test(c.eur)&&/kWh/.test(c.t)&&/p=97274&n=2&a=0&v=2500/.test(c.href)&&c.bild,'Ergebnis für 97274: '+c.eur+' | '+c.href);
await p.click('.mx-chips[data-k="dir"] button[data-v="180"]');await p.waitForTimeout(900);const nord=await p.evaluate(()=>parseInt(document.querySelector('.mx-out b').textContent));ok(nord<parseInt(c.eur),'Norden bringt weniger ('+nord+' € statt '+c.eur+')');
const [dl]=await Promise.all([p.waitForEvent('download',{timeout:15000}),p.click('.mx-go [data-b]')]);const fs=require('fs');ok(fs.statSync(await dl.path()).size>30000&&/\.png$/.test(dl.suggestedFilename()),'Schnell-Check als Bild: '+dl.suggestedFilename());if(process.argv[3])await dl.saveAs(process.argv[3]);
ok(await p.evaluate(()=>{const s=document.querySelector('.mx-go [data-set]');return !s.hidden&&s.getAttribute('href')==='/#vergleich'}),'Schnell-Check führt zu den geprüften Sets');
await p.click('.mx-x');ok(await p.evaluate(()=>!document.querySelector('dialog.mx-dlg').open),'Dialog schließt');
await p.goto(B+c.href,{waitUntil:'load'});await p.waitForFunction(()=>/€/.test(document.getElementById('bp-k-eur').textContent),null,{timeout:20000});const pe=await p.evaluate(()=>document.getElementById('bp-k-eur').textContent);
ok(Math.abs(parseInt(pe)-parseInt(c.eur))<=1,'Planer kommt mit denselben Angaben auf denselben Betrag ('+pe+')');
// Balkon-Vorschau
const v0=await p.evaluate(()=>({st:sdVorschau.stand(),w:document.querySelector('#bv img.alt').naturalWidth,ki:!!document.querySelector('#bv .ki-marke')}));ok(v0.st[0]==='balkon'&&v0.st[1]===2&&v0.w>1000,'Vorschau zeigt Balkon mit 2 Modulen '+JSON.stringify(v0));
await p.click('#bv [data-k="ort"] button[data-v="garten"]');await p.waitForTimeout(1500);const v1=await p.evaluate(()=>({st:sdVorschau.stand(),src:document.querySelector('#bv img.alt').getAttribute('src')}));ok(v1.st[1]===2&&/bv-garten-2/.test(v1.src)&&/n=2&t=30#planer/.test(v1.st[2]),'Garten: Bild und Link wechseln '+JSON.stringify(v1));
await p.click('#bv [data-k="n"] button:last-child');await p.waitForTimeout(1500);ok(/bv-garten-4/.test(await p.evaluate(()=>document.querySelector('#bv img.alt').getAttribute('src'))),'4 Module im Garten');
ok(v0.ki||await p.evaluate(()=>/KI/.test(document.body.textContent.slice(-4000))||!!document.querySelector('.ki-marke')),'KI-Hinweis vorhanden');
const [d2]=await Promise.all([p.waitForEvent('download',{timeout:15000}),p.click('#planer [data-bild]')]);ok(fs.statSync(await d2.path()).size>30000,'Planer-Ergebnis als Bild: '+d2.suggestedFilename());if(process.argv[4])await d2.saveAs(process.argv[4]);
// Stromfresser: Tausch-Rechner und Bild
await p.goto(B+'/stromfresser.html',{waitUntil:'load'});await p.waitForTimeout(800);
const t=await p.evaluate(()=>{const k=document.querySelector('.mx-t');return k?{n:k.querySelectorAll('option').length,o:k.querySelector('.mx-t-o').textContent,b:document.querySelectorAll('[data-bild]').length}:null});
ok(t&&t.n>3&&/spart etwa \d+ € im Jahr/.test(t.o)&&/Jahren wieder drin/.test(t.o)&&t.b===2,'Tausch-Rechner rechnet: '+(t&&t.o));
const kl=await p.evaluate(()=>{const a=document.querySelector('.mx-t-k a');return a?[a.href,a.rel,!!document.querySelector('.mx-anz')]:null});ok(kl&&/amazon\.de\/s\?k=.+&tag=stromdaheim-21$/.test(kl[0])&&/sponsored/.test(kl[1])&&kl[2],'Tausch-Rechner: gekennzeichneter Partnerlink '+(kl&&kl[0]));
await p.fill('#mx-t-k','9999');await p.waitForTimeout(200);ok(/spart keinen Strom/.test(await p.textContent('.mx-t-o')),'Sparsamer muss es schon sein');
await p.goto(B+'/solar-rechner.html',{waitUntil:'load'});await p.waitForTimeout(800);ok(await p.locator('[data-bild]').count()>=1,'Solar-Rechner hat „Als Bild speichern“');
// Weitermachen
await p.goto(B+'/',{waitUntil:'load'});await p.waitForTimeout(600);const w=await p.evaluate(()=>[...document.querySelectorAll('.mx-w a')].map(a=>a.textContent));ok(w.includes('Dein Balkonkraftwerk-Plan')&&w.includes('Deine Stromfresser'),'Weitermachen zeigt die benutzten Rechner '+JSON.stringify(w));
const ctx2=await b.newContext();const q=await ctx2.newPage();await q.goto(B+'/',{waitUntil:'load'});await q.waitForTimeout(500);ok(await q.locator('.mx-w').count()===0,'Neue Besucher sehen keinen Weitermachen-Hinweis');
ok(!errs.length,'Keine Skriptfehler '+errs.join(' | '));
await b.close();console.log(bad?bad+' FEHLER':'ALLE TESTS BESTANDEN');process.exit(bad?1:0)})();
