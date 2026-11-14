// Test für den Solar-Atlas. Aufruf: node werkzeuge/atlas-test.js [Basisadresse]  (ohne Adresse: http://localhost:8765)
// Prüft Karte, Postleitzahl-Suche, Umschalter und alle 95 Regionen-Seiten gegen werkzeuge/pvdaten/atlas.json. Muss mit „ALLE TESTS BESTANDEN“ enden.
const { chromium } = require('playwright'), fs = require('fs'), path = require('path');
const BASE = process.argv[2] || 'http://localhost:8765';
const A = JSON.parse(fs.readFileSync(path.join(__dirname, 'pvdaten', 'atlas.json'))).regionen;
let bad = 0; const ok = (c, t) => { console.log((c ? 'ok ' : 'FEHLER ') + t); if (!c) bad++; };
const de = n => Math.round(n).toLocaleString('de-DE');
(async () => {
  const b = await chromium.launch(), p = await b.newPage({ viewport: { width: 1280, height: 900 } }); const e = []; p.on('pageerror', x => e.push(x.message));
  await p.goto(BASE + '/solar-atlas.html'); await p.waitForTimeout(500);
  ok(await p.locator('#sa-map path[data-r]').count() === 95, 'Karte hat 95 Regionen');
  ok(await p.locator('#rangliste tr[data-r]').count() === 95, 'Rangliste hat 95 Zeilen');
  await p.fill('#sa-plz', '97070');
  let t = await p.textContent('#sa-card');
  ok(t.includes('Würzburg und Schweinfurt') && t.includes(de(A['97'].dach)), 'Postleitzahl 97070 zeigt Würzburg mit ' + de(A['97'].dach) + ' kWh je kWp');
  await p.click('#sa-met button[data-m="2"]'); t = await p.textContent('#sa-card');
  ok(t.includes(de(A['97'].bkw90)) && (await p.textContent('#sa-unit')) === 'kWh im Jahr', 'Umschalter: Balkon senkrecht zeigt ' + de(A['97'].bkw90) + ' kWh im Jahr');
  const fill0 = await p.getAttribute('#sa-map path[data-r="88"]', 'fill'); ok(fill0 === '#ffb81c', 'stärkste Region trägt die hellste Farbe');
  await p.fill('#sa-plz', '11011'); ok((await p.textContent('#sa-card')).includes('Berlin'), 'Postleitzahlen mit 11 gehören zu Berlin');
  await p.fill('#sa-plz', '00123'); ok((await p.textContent('#sa-card')).includes('keine Region'), 'unbekannte Region: verständliche Meldung');
  await p.click('#sa-map path[data-r="20"]'); ok((await p.textContent('#sa-card')).includes('Hamburg'), 'Tipp auf die Karte wählt die Region');
  await p.fill('#sa-plz', '970'); await p.click('#sa-form .sa-go'); ok(p.url().includes('solar-atlas') && (await p.textContent('#sa-card')).includes('fünf Ziffern'), 'unvollständige Postleitzahl geht nicht an den Planer');
  await p.fill('#sa-plz', '97070'); await Promise.all([p.waitForNavigation(), p.click('#sa-form .sa-go')]); await p.waitForTimeout(600);
  ok(p.url().includes('/balkonkraftwerk-planer.html?p=97070') && (await p.inputValue('#bp-plz')) === '97070', 'vollständige Postleitzahl öffnet den Planer mit dieser Postleitzahl');
  const m = await b.newPage({ viewport: { width: 390, height: 844 } }); await m.goto(BASE + '/solar-atlas.html'); await m.waitForTimeout(400);
  ok(await m.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), 'Handy: kein seitliches Scrollen');
  // alle Regionen-Seiten
  const links = await p.evaluate(async base => { const h = await (await fetch(base + '/solar-atlas.html')).text(); return [...new Set([...h.matchAll(/href="(\/solar\/(\d\d)-[^"]+\.html)"/g)].map(x => x[2] + '|' + x[1]))]; }, BASE);
  ok(links.length === 95, '95 Regionen-Seiten verlinkt');
  const sm = await p.evaluate(async base => (await (await fetch(base + '/sitemap.xml')).text()), BASE);
  let fehl = [];
  for (const l of links) {
    const [plz, u] = l.split('|'), r = A[plz];
    const h = await p.evaluate(async x => { const q = await fetch(x); return q.ok ? await q.text() : ''; }, BASE + u);
    const good = h.includes('<b>' + de(r.dach) + ' kWh</b>') && h.includes('<b>' + de(r.bkw90) + ' kWh</b>') && h.includes('<b>' + de(r.bkw30) + ' kWh</b>') && h.includes('PVGIS © Europäische Union') && h.includes('href="/solar-atlas.html"') && h.includes('<link rel="canonical" href="https://strom-daheim.de' + u + '">') && sm.includes('https://strom-daheim.de' + u);
    if (!good) fehl.push(plz);
  }
  ok(fehl.length === 0, 'alle Regionen-Seiten zeigen die Werte aus atlas.json, Quelle, eigene Adresse und stehen in der Sitemap' + (fehl.length ? ': ' + fehl.join(',') : ''));
  await m.goto(BASE + links[40].split('|')[1]); await m.waitForTimeout(400);
  ok(await m.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1) && await m.locator('.sa-chart svg.k').isVisible(), 'Regionen-Seite am Handy: kein seitliches Scrollen, Monatsbalken passen');
  ok(e.length === 0, 'keine Skriptfehler ' + e.join('|'));
  await b.close(); console.log(bad ? '\n' + bad + ' FEHLER' : '\nALLE TESTS BESTANDEN'); process.exit(bad ? 1 : 0);
})();
