// Prüft „Frag den Ratgeber“ (frag.js, frag.json): Fragekasten am Seitenende und die Suche im Menü.  node frag-test.js [Basis-URL]
// Läuft auf beiden Websites: Die Beispiele werden nach der Adresse gewählt (strom-daheim oder Port 8765 = Strom, sonst Stil).
const {chromium}=require('playwright');const arg=process.argv[2]||'';const strom=/strom|8765/.test(arg)||(!arg&&/strom-daheim/.test(__dirname));const B=arg||(strom?'http://localhost:8765':'http://localhost:8766');let bad=0;
const ok=(c,t)=>{console.log((c?'ok   ':'FEHLER ')+t);if(!c)bad++};
const T=strom?{seite:'/kuehlschrank.html',menue:'[aria-controls="sh-sheet"]',
  fragen:[['Wie kalt muss der Kühlschrank sein?','/kuehlschrank.html'],['gibt es einen strompreisdeckel','/stromsteuer-2027.html'],['muss ich mein balkonkraftwerk anmelden','/'],['lohnt sich photovoltaik','/pv-anlage.html']],suche:['wann sinkt die stromsteuer','stromsteuer-2027'],wort:'kühlschrank'}
 :{seite:'/wohnzimmer.html',menue:'[aria-controls="msheet"]',
  fragen:[['wie hoch hängt man bilder auf','/bilderwand.html'],['welche farbe fürs schlafzimmer','/wandfarbe-schlafzimmer.html'],['Welche Wandfarbe passt zu einem grauen Sofa?','/wandfarbe-graues-sofa.html'],['wie hoch lampe über esstisch','/esszimmer.html']],suche:['welche farbe fürs schlafzimmer','wandfarbe-schlafzimmer'],wort:'teppich'};
(async()=>{const b=await chromium.launch();const c=await b.newContext({viewport:{width:390,height:780}});const p=await c.newPage();const errs=[],fremd=[];p.on('pageerror',e=>errs.push(e.message));
p.on('request',r=>{const u=r.url();if(!u.startsWith(B)&&!/^data:|^blob:/.test(u)&&!/gc\.zgo\.at|goatcounter/.test(u))fremd.push(u)});
await p.goto(B+T.seite,{waitUntil:'networkidle'});
ok(await p.evaluate(()=>!window.sdFrag),'frag.js wird nicht sofort geladen');
await p.evaluate(()=>window.scrollTo(0,document.body.scrollHeight));await p.waitForSelector('.fragk-c button',{timeout:8000});
const chips=await p.$$eval('.fragk-c button',B=>B.map(x=>x.textContent));ok(chips.length>=2&&chips.length<=4,'Fragekasten mit '+chips.length+' Vorschlägen');
for(const [q,u] of T.fragen){await p.fill('.fragk-f input',q);await p.click('.fragk-f button');await p.waitForTimeout(250);const h=await p.locator('.fragk-a a').getAttribute('href').catch(()=>'');ok(h&&new URL(h,B).pathname===u,'„'+q+'“ → '+h)}
// Die Antwort steht wörtlich in frag.json (nichts wird erzeugt)
const wort=await p.evaluate(async()=>{const a=document.querySelector('.fragk-a p').textContent,j=await (await fetch(window.sdFrag.url('/frag.json'))).json();return j.some(e=>e.a===a)});ok(wort,'Die Antwort steht wörtlich so auf einer Seite');
await p.fill('.fragk-f input','pizza rezept ohne hefe');await p.click('.fragk-f button');await p.waitForTimeout(250);ok(await p.locator('.fragk-a').count()===0&&/keine geprüfte Antwort/.test(await p.textContent('.fragk-o')),'Fremde Frage: ehrlich keine Antwort');
await p.locator('.fragk-c button').first().click();await p.waitForTimeout(250);ok((await p.textContent('.fragk-a b'))===chips[0],'Vorschlag antippen zeigt dessen Antwort');
// Suche im Menü
await p.evaluate(()=>window.scrollTo(0,0));await p.locator(T.menue).first().click();await p.waitForTimeout(500);await p.fill('#sq-in',T.suche[0]);await p.waitForSelector('#sq-out li.sq-ant',{timeout:5000});
ok((await p.locator('#sq-out li.sq-ant a').getAttribute('href')).includes(T.suche[1]),'Suche: ganze Frage bringt zuerst die geprüfte Antwort');ok(await p.locator('#sq-out li:not(.sq-ant)').count()>=1,'Darunter stehen passende Seiten');
await p.fill('#sq-in',T.wort);await p.waitForTimeout(400);ok(await p.locator('#sq-out li.sq-ant').count()===0&&await p.locator('#sq-out li a').count()>=1,'Ein einzelnes Wort sucht wie bisher');
ok(!fremd.length,'Keine Anfrage an fremde Server '+JSON.stringify(fremd.slice(0,3)));ok(!errs.length,'Keine Skriptfehler '+JSON.stringify(errs));
await b.close();console.log(bad?bad+' FEHLER':'ALLE TESTS BESTANDEN');process.exit(bad?1:0)})();
