// Bedientest für strompreis-heute.html. Aufruf: node werkzeuge/strompreis-test.js [Basisadresse]  (ohne Adresse: http://localhost:8765)
// Prüft echte Daten und zwei gestellte Fälle (Preise für morgen da, Daten veraltet). Muss mit „ALLE TESTS BESTANDEN“ enden.
const { chromium } = require('playwright');
const BASE = process.argv[2] || 'http://localhost:8765', U = BASE + '/strompreis-heute.html';
let bad = 0; const ok = (c, t) => { console.log((c ? 'ok   ' : 'FEHLER ') + t); if (!c) bad++; };
const berlin = () => { const o = {}; new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Berlin', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', hourCycle: 'h23' }).formatToParts(new Date()).forEach(p => o[p.type] = p.value); return { d: `${o.year}-${o.month}-${o.day}`, h: +o.hour % 24 }; };
const plus = (d, n) => new Date(Date.UTC(+d.slice(0, 4), +d.slice(5, 7) - 1, +d.slice(8, 10) + n)).toISOString().slice(0, 10);
const de = (v, n) => v.toLocaleString('de-DE', { minimumFractionDigits: n, maximumFractionDigits: n }).replace('-', '−');
(async () => {
  const b = await chromium.launch(), now = berlin();
  // 1) echte Daten
  let p = await b.newPage({ viewport: { width: 390, height: 844 } }); const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto(U); await p.waitForTimeout(700);
  const data = await p.evaluate(() => fetch('/assets/strompreis.json').then(r => r.json()));
  const keys = Object.keys(data.tage).sort(), t = data.tage[now.d];
  ok(keys.length >= 2 && keys.every(k => data.tage[k].length === 24), 'Datei hat ' + keys.length + ' Tage mit je 24 Stunden');
  ok(/SMARD/.test(data.quelle), 'Quellenangabe in der Datei');
  ok((await p.textContent('#quellen')).includes('SMARD') && (await p.textContent('#verlauf')).includes('SMARD.de'), 'Quellenangabe SMARD auf der Seite');
  if (t) {
    ok((await p.textContent('#sp-now-v')) === de(t[now.h], 1), 'große Zahl = Preis der laufenden Stunde (' + de(t[now.h], 1) + ')');
    ok(await p.locator('#sp-chart svg path.b').count() === t.filter(x => x != null).length, 'ein Balken je Stunde');
  } else ok((await p.textContent('#sp-msg')).includes('noch keine Preise'), 'ohne Werte für heute: ehrlicher Hinweis');
  ok(await p.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), 'Handy: kein seitliches Scrollen');
  ok(errs.length === 0, 'keine Skriptfehler mit echten Daten ' + errs.join('|'));
  await p.close();
  // 2) gestellter Fall: heute und morgen bekannt
  const mk = f => Array.from({ length: 24 }, (_, i) => f(i));
  const fake = { stand: now.d + 'T14:05', quelle: 'Bundesnetzagentur | SMARD.de, CC BY 4.0', tage: {} };
  fake.tage[plus(now.d, -1)] = mk(i => 10);
  fake.tage[now.d] = mk(i => 20 + i);                      // steigt über den Tag
  fake.tage[plus(now.d, 1)] = mk(i => i === 3 || i === 4 ? -2 : 30);   // morgen 3 bis 5 Uhr negativ
  p = await b.newPage({ viewport: { width: 1280, height: 900 } }); const e2 = []; p.on('pageerror', e => e2.push(e.message));
  await p.route('**/assets/strompreis.json', r => r.fulfill({ contentType: 'application/json', body: JSON.stringify(fake) }));
  await p.goto(U); await p.waitForTimeout(700);
  ok(!(await p.isDisabled('#sp-t1')), 'Knopf „Morgen“ ist frei, wenn die Preise da sind');
  ok((await p.textContent('#sp-r-win')) === 'Morgen 3 Uhr bis 5 Uhr', 'günstigstes 2-Stunden-Fenster liegt morgen 3 bis 5 Uhr: ' + await p.textContent('#sp-r-win'));
  ok((await p.textContent('#sp-r-p')) === de(20 - 2 * 1.19, 1) + ' ct', 'Endpreis im Fenster = 20 − 2 × 1,19');
  ok((await p.getAttribute('#sp-t1', 'aria-pressed')) === 'false', 'Ansicht bleibt zunächst auf heute');
  await p.click('#sp-dur button[data-h="1"]');
  ok((await p.getAttribute('#sp-t1', 'aria-pressed')) === 'true' && await p.locator('#sp-chart .win').count() === 1, 'nach Wahl der Laufzeit zeigt das Diagramm den Tag mit dem Fenster');
  const neg = await p.evaluate(() => { const s = document.querySelector('#sp-chart svg'), z = s.querySelector('line.z').getBoundingClientRect().y; return [...s.querySelectorAll('path.b')].filter(x => x.getBoundingClientRect().y >= z - 1).length; });
  ok(neg === 2, 'negative Preise zeigen nach unten (2 Balken)');
  await p.fill('#sp-kwh', '20'); await p.fill('#sp-fix', '25,5');
  ok((await p.textContent('#sp-r-p')) === de(25.5 - 2 * 1.19, 1) + ' ct', 'fester Teil mit Komma wird übernommen');
  ok((await p.textContent('#sp-r-eur')) === de((43 - (-2)) * 1.19 * 20 / 100, 2) + ' €', 'Unterschied in Euro bei 20 kWh (teuerste Stunde heute 23 Uhr mit 43 ct)');
  await p.click('#sp-m1');
  ok((await p.textContent('#sp-msg')).includes('Endpreis ='), 'Umschalten auf Endpreis erklärt die Rechnung');
  await p.focus('#sp-chart'); await p.keyboard.press('ArrowRight'); await p.keyboard.press('ArrowRight');
  ok(/^1 bis 2 Uhr/.test(await p.textContent('#sp-tip')) && await p.evaluate(() => document.getElementById('sp-tip').classList.contains('on')), 'Pfeiltasten gehen durch die Stunden');
  await p.click('#sp-t0'); await p.hover('#sp-chart svg', { position: { x: 400, y: 100 } });
  ok(await p.evaluate(() => document.getElementById('sp-tip').classList.contains('on')), 'Maus über dem Diagramm zeigt die Stunde');
  ok((await p.locator('#sp-tbl tr').count()) === 25, 'Tabelle mit 24 Stunden');
  ok(e2.length === 0, 'keine Skriptfehler im gestellten Fall ' + e2.join('|'));
  await p.close();
  // 3) gestellter Fall: Daten veraltet (Abruf ausgefallen)
  const alt = { stand: plus(now.d, -2) + 'T14:05', quelle: 'x', tage: {} }; alt.tage[plus(now.d, -3)] = mk(i => 9); alt.tage[plus(now.d, -2)] = mk(i => 12);
  p = await b.newPage({ viewport: { width: 390, height: 844 } }); const e3 = []; p.on('pageerror', e => e3.push(e.message));
  await p.route('**/assets/strompreis.json', r => r.fulfill({ contentType: 'application/json', body: JSON.stringify(alt) }));
  await p.goto(U); await p.waitForTimeout(700);
  ok((await p.textContent('#sp-msg')).includes('noch keine Preise vor') && await p.isHidden('#sp-now'), 'veraltete Daten: Hinweis statt falscher „Jetzt“-Zahl');
  ok((await p.textContent('#sp-r-win')) === 'Zu spät für heute' || (await p.textContent('#sp-r-win')).length > 0, 'Zeitfenster-Rechner bleibt bedienbar');
  ok(e3.length === 0, 'keine Skriptfehler bei veralteten Daten ' + e3.join('|'));
  await p.close();
  // 4) Abruf schlägt fehl
  p = await b.newPage(); await p.route('**/assets/strompreis.json', r => r.abort()); await p.goto(U); await p.waitForTimeout(500);
  ok((await p.textContent('#sp-msg')).includes('nicht geladen'), 'Fehlermeldung, wenn die Datei fehlt');
  await b.close();
  console.log(bad ? '\n' + bad + ' FEHLER' : '\nALLE TESTS BESTANDEN'); process.exit(bad ? 1 : 0);
})();
