const {chromium,devices}=require('playwright');
/* Bedientest des Balkonkraftwerk-Planers. Aufruf: node werkzeuge/planer-test.js [Basisadresse], Standard http://localhost:8765 */
const U=(process.argv[2]||'http://localhost:8765')+'/balkonkraftwerk-planer.html';
let fails=0;function ok(c,m){if(!c){fails++;console.log('FEHLER:',m)}else console.log('ok   ',m)}
(async()=>{const b=await chromium.launch();
// ---------- Handy mit Touch ----------
const c=await b.newContext({...devices['iPhone 13']});const p=await c.newPage();const errs=[];
p.on('pageerror',e=>errs.push(e.message));p.on('console',m=>{if(m.type()==='error')errs.push(m.text())});
await p.goto(U);await p.waitForTimeout(900);
const T=id=>p.evaluate(i=>document.getElementById(i).textContent,id);
const eur=async()=>parseInt((await T('bp-k-eur')).replace(/\D/g,''));
const e0=await eur();ok(e0>60&&e0<200,'Startwert plausibel: '+e0+' €');
ok((await T('bp-reg')).includes('Mitte Deutschlands'),'Hinweis ohne PLZ');
await p.fill('#bp-plz','80331');await p.waitForTimeout(900);
ok((await T('bp-reg')).includes('München'),'PLZ 80331 -> '+await T('bp-reg'));
const e1=await eur();ok(e1>e0,'München bringt mehr als Kassel: '+e1+' > '+e0);
await p.fill('#bp-plz','05123');await p.waitForTimeout(500);
ok((await T('bp-reg')).includes('kennen wir nicht'),'unbekannte PLZ wird gemeldet');
await p.fill('#bp-plz','97274');await p.waitForTimeout(900);
ok((await T('bp-reg')).includes('Würzburg'),'PLZ 97274 -> Würzburg');
// Module
await p.click('#bp-n button[data-v="4"]');await p.waitForTimeout(300);
ok((await T('bp-wp-sum')).includes('1.800'),'4 Module = 1.800 Wp');ok((await T('bp-wp-st')).includes('Einspeisesteckdose'),'Hinweis Einspeisesteckdose');
ok(await p.evaluate(()=>!document.getElementById('bp-clip').hidden),'Hinweis auf Abregelung sichtbar');
ok(await p.evaluate(()=>!document.getElementById('bp-leg-clip').hidden),'Legende Abgeregelt sichtbar');
ok((await p.inputValue('#bp-cost'))==='800','Richtpreis 4 Module = 800 € ('+await p.inputValue('#bp-cost')+')');
// Ost + West
await p.click('#bp-dir button[data-v="ow"]');await p.waitForTimeout(300);
ok(await p.evaluate(()=>document.getElementById('bp-comp').classList.contains('ow')),'Kompass zeigt Ost + West');
ok((await T('bp-txt')).includes('je zur Hälfte nach Osten und Westen'),'Satz nennt Ost und West');
// Kompass mit dem Finger drehen: auf Osten tippen und nach Süden ziehen
await p.evaluate(()=>document.getElementById('bp-comp').scrollIntoView({block:'center',behavior:'instant'}));await p.waitForTimeout(500);
const box=await p.evaluate(()=>{const r=document.getElementById('bp-comp').getBoundingClientRect();return {x:r.left,y:r.top,w:r.width,h:r.height}});
const cdp=await c.newCDPSession(p);const touch=(type,x,y)=>cdp.send('Input.dispatchTouchEvent',{type,touchPoints:type==='touchEnd'?[]:[{x,y,id:1}]});
const cx=box.x+box.w/2,cy=box.y+box.h/2,R=box.w*0.36;
await touch('touchStart',cx+R,cy);await p.waitForTimeout(60);
ok((await p.getAttribute('#bp-comp','aria-valuetext')).startsWith('Osten'),'Tipp auf Osten: '+await p.getAttribute('#bp-comp','aria-valuetext'));
for(let a=0;a<=90;a+=10){await touch('touchMove',cx+R*Math.cos(a*Math.PI/180),cy+R*Math.sin(a*Math.PI/180));await p.waitForTimeout(20)}
await touch('touchEnd');await p.waitForTimeout(200);
ok((await p.getAttribute('#bp-comp','aria-valuetext'))==='Süden','nach Süden gezogen: '+await p.getAttribute('#bp-comp','aria-valuetext'));
const sy1=await p.evaluate(()=>Math.round(document.getElementById('bp-comp').getBoundingClientRect().top));ok(Math.abs(sy1-box.y)<2,'Seite scrollt beim Drehen nicht mit');
// Neigung
await p.click('#bp-tiltc button[data-v="30"]');await p.waitForTimeout(300);
ok((await p.inputValue('#bp-tilt'))==='30','Neigung 30');ok((await p.getAttribute('#bp-tilt-m','transform')).includes('-60'),'Bild neigt sich');
const e2=await eur();
// Speicher
await p.click('#bp-bat button[data-v="2.7"]');await p.waitForTimeout(400);
const e3=await eur();ok(e3>e2,'Speicher erhöht Ersparnis: '+e2+' -> '+e3);
// Haushalt und Zeitvorwahl
await p.click('#bp-bat button[data-v="0"]');await p.click('#bp-kwhc button[data-v="2900"]');await p.waitForTimeout(300);const e4=await eur();
await p.check('#bp-shift');await p.waitForTimeout(300);const e5=await eur();ok(e5>e4,'Zeitvorwahl bringt mehr: '+e4+' -> '+e5);
// Schatten
await p.click('#bp-shade button[data-v="2"]');await p.waitForTimeout(300);const e6=await eur();ok(e6<e5,'Schatten senkt Ersparnis: '+e5+' -> '+e6);
await p.click('#bp-shade button[data-v="0"]');
// Vergleich antippen
await p.waitForTimeout(400);const n0=await p.evaluate(()=>document.querySelectorAll('.bp-vr').length);ok(n0>=5,'Vergleich hat '+n0+' Zeilen');
await p.evaluate(()=>{const r=[...document.querySelectorAll('.bp-vr')].find(x=>x.dataset.n==='2'&&x.dataset.b==='1.6');r.scrollIntoView({block:'center'});r.click()});await p.waitForTimeout(500);
ok((await T('bp-wp-sum')).includes('900')&&(await T('bp-txt')).includes('1,6 kWh Speicher'),'Variante übernommen: 2 Module + 1,6 kWh');
ok(await p.evaluate(()=>document.querySelector('.bp-vr.cur').dataset.b==='1.6'),'Auswahl im Vergleich markiert');
// Tabelle
await p.evaluate(()=>{document.querySelector('#bp-tab-m').closest('details').open=true});
ok(await p.evaluate(()=>document.querySelectorAll('#bp-tab-m tbody tr').length)===13,'Monatstabelle hat 12 Monate + Jahr');
const sumOk=await p.evaluate(()=>{const r=[...document.querySelectorAll('#bp-tab-m tbody tr')].map(tr=>[...tr.children].map(td=>parseInt(td.textContent.replace(/\D/g,''))));let s=0;for(let i=0;i<12;i++)s+=r[i][1];return [s,r[12][1]]});
ok(Math.abs(sumOk[0]-sumOk[1])<=12,'Summe der Monate passt zur Jahreszahl: '+sumOk);
// Tagesdiagramm
await p.click('#bp-mon button[data-v="11"]');await p.click('#bp-sky button[data-v="0"]');await p.waitForTimeout(300);
ok((await T('bp-day-t')).includes('Trüber Tag im Dezember'),'Tag gewählt: '+await T('bp-day-t'));
ok(await p.evaluate(()=>document.querySelectorAll('#bp-tab-d tbody tr').length)>=22,'Tagestabelle gefüllt');
// Teilen-Adresse wiederherstellen
const st=await p.evaluate(()=>JSON.parse(localStorage.getItem('bkwp')));ok(st.plz==='97274'&&st.bat===1.6,'Zustand gespeichert');
await p.evaluate(()=>localStorage.clear());
await p.goto(U+'?p=20095&n=3&wp=400&a=45&t=70&s=1&v=2500&w=2&z=1&b=1&ct=38.5&c=600');await p.waitForTimeout(1000);
const tx=await T('bp-txt');ok(tx.includes('Hamburg')&&tx.includes('3 Module')&&tx.includes('1.200 Wp')&&tx.includes('Südwesten')&&tx.includes('70 Grad')&&tx.includes('38,5 ct')&&tx.includes('1 kWh Speicher'),'Geteilte Adresse stellt alles her: '+tx.slice(0,170));
ok(await p.evaluate(()=>document.querySelector('#bp-cap button[data-v="600"]').getAttribute('aria-pressed')==='true'),'600-W-Wechselrichter übernommen');
// mit Speicher zeigt das Tagesdiagramm, was die Module liefern, und den Füllstand
ok((await T('bp-leg-pv')).includes('Strom der Module')&&(await T('bp-leg-self')).includes('aus dem Speicher'),'Legende mit Speicher: '+await T('bp-leg-pv')+' / '+await T('bp-leg-self'));
ok(/Die Module liefern .* kWh\. Du nutzt/.test(await T('bp-day-t')),'Tagessatz mit Speicher: '+await T('bp-day-t'));
ok(await p.evaluate(()=>document.querySelectorAll('#bp-tab-d thead th').length)===5,'Tagestabelle mit Spalte Speicher');
ok((await T('bp-txt')).includes('Verlust im Speicher'),'Satz nennt den Speicherverlust');
await p.evaluate(()=>document.getElementById('bp-chart-d').scrollIntoView({block:'center',behavior:'instant'}));await p.waitForTimeout(500);
{const r=await (await p.$('#bp-chart-d rect.bp-hit')).boundingBox();await p.touchscreen.tap(r.x+r.width*0.8,r.y+r.height*0.4);await p.waitForTimeout(300);
ok(await p.evaluate(()=>{const t=document.querySelector('#bp-chart-d .bp-tip');return t&&!t.hidden&&/Speicher gefüllt/.test(t.textContent)}),'Tippen im Tagesdiagramm zeigt Füllstand: '+await p.evaluate(()=>document.querySelector('#bp-chart-d .bp-tip').textContent));
ok(await p.evaluate(()=>getComputedStyle(document.querySelector('#bp-chart-d rect.bp-hit')).outlineStyle==='none'),'kein Rahmen ums Diagramm nach dem Tippen');}
// Link ohne Speicher darf den gemerkten Speicher nicht übernehmen
await p.goto(U+'?p=20095&n=2&wp=450&a=0&t=90&s=0&v=1900&w=1&ct=32');await p.waitForTimeout(1000);
{const t2=await T('bp-txt');ok(!t2.includes('Speicher')&&t2.includes('2 Module'),'Link ohne Speicher rechnet ohne Speicher: '+t2.slice(0,110));
ok(await p.evaluate(()=>document.querySelector('#bp-cap button[data-v="800"]').getAttribute('aria-pressed')==='true'),'Link ohne Angabe: 800 W');
ok((await T('bp-leg-pv')).trim()==='Solarstrom','Legende ohne Speicher: '+await T('bp-leg-pv'));}
// gemerkter Strompreis aus anderen Rechnern
await p.evaluate(()=>{localStorage.clear();localStorage.setItem('sp','41.5')});await p.goto(U);await p.waitForTimeout(1400);
ok((await p.inputValue('#bp-ct'))==='41,5'&&(await T('bp-txt')).includes('41,5 ct'),'Gemerkter Strompreis gilt: '+await p.inputValue('#bp-ct'));
// kleine Leiste
await p.evaluate(()=>document.getElementById('bp-n').scrollIntoView({block:'center'}));await p.waitForTimeout(500);
ok(await p.evaluate(()=>document.getElementById('bp-mini').classList.contains('on')),'kleine Ergebnis-Leiste sichtbar beim Eingeben');
await p.click('#bp-mini');await p.waitForTimeout(900);
ok(await p.evaluate(()=>{const r=document.getElementById('bp-out').getBoundingClientRect();return r.top<innerHeight*0.6&&r.bottom>0}),'Leiste springt zum Ergebnis');
ok(await p.evaluate(()=>!document.getElementById('bp-mini').classList.contains('on')),'Leiste verschwindet beim Ergebnis');
ok(errs.length===0,'keine JS-Fehler am Handy '+errs.join(' | '));
await c.close();
// ---------- Schmal 320 px ----------
const c3=await b.newContext({viewport:{width:320,height:640},deviceScaleFactor:1});const p3=await c3.newPage();await p3.goto(U);await p3.waitForTimeout(900);
ok(await p3.evaluate(()=>document.documentElement.scrollWidth-innerWidth)<=0,'kein Überlauf bei 320 px');await c3.close();
// ---------- Desktop: Tastatur und Maus ----------
const c2=await b.newContext({viewport:{width:1366,height:900}});const q=await c2.newPage();const e2s=[];q.on('pageerror',e=>e2s.push(e.message));
await q.goto(U);await q.waitForTimeout(900);
await q.focus('#bp-comp');for(let i=0;i<9;i++)await q.keyboard.press('ArrowRight');await q.waitForTimeout(200);
ok((await q.getAttribute('#bp-comp','aria-valuetext')).startsWith('Südwesten'),'Kompass per Tastatur: '+await q.getAttribute('#bp-comp','aria-valuetext'));
await q.fill('#bp-kwh','3.450');await q.keyboard.press('Tab');await q.waitForTimeout(300);ok((await q.inputValue('#bp-kwh'))==='3.450','Verbrauch getippt mit Tausenderpunkt: '+await q.inputValue('#bp-kwh'));
await q.fill('#bp-cost','499');await q.keyboard.press('Tab');await q.waitForTimeout(300);ok(await q.evaluate(()=>!document.getElementById('bp-cost-reset').hidden),'eigener Preis: Knopf Richtwert erscheint');
ok((await q.evaluate(()=>document.getElementById('bp-txt').textContent)).includes('499 €'),'eigener Preis im Satz');
await q.click('#bp-cost-reset');await q.waitForTimeout(200);ok((await q.inputValue('#bp-cost'))==='350','zurück zum Richtwert');
// Diagramm: Maus über Monat und Tageskurve
await q.evaluate(()=>document.getElementById('bp-chart-m').scrollIntoView({block:'center'}));await q.waitForTimeout(600);
const g=await q.$('#bp-chart-m .bp-col:nth-of-type(6)');const gb=await g.boundingBox();await q.mouse.move(gb.x+gb.width/2,gb.y+gb.height/2);await q.waitForTimeout(200);
ok(await q.evaluate(()=>{const t=document.querySelector('.bp-tip');return t&&!t.hidden&&/kWh/.test(t.textContent)}),'Tooltip am Monatsbalken: '+await q.evaluate(()=>document.querySelector('.bp-tip').textContent));
await q.evaluate(()=>document.getElementById('bp-chart-d').scrollIntoView({block:'center'}));await q.waitForTimeout(600);
const hb=await (await q.$('#bp-chart-d rect.bp-hit')).boundingBox();await q.mouse.move(hb.x+hb.width*0.5,hb.y+hb.height*0.4);await q.waitForTimeout(200);
ok(await q.evaluate(()=>{const t=document.querySelector('.bp-tip');return t&&!t.hidden&&/Uhr/.test(t.textContent)&&/Verbrauch/.test(t.textContent)}),'Fadenkreuz im Tagesdiagramm: '+await q.evaluate(()=>document.querySelector('.bp-tip').textContent));
await q.focus('#bp-chart-m .bp-col:nth-of-type(1)');await q.waitForTimeout(150);ok(await q.evaluate(()=>/Januar/.test(document.querySelector('.bp-tip').textContent)),'Tooltip auch per Tastatur-Fokus');
ok(e2s.length===0,'keine JS-Fehler am Desktop '+e2s.join(' | '));
await b.close();console.log(fails?('\n'+fails+' FEHLER'):'\nALLE TESTS BESTANDEN');process.exit(fails?1:0)})()
