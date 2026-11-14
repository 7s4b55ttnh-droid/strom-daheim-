// Bedientest fürs Lexikon (Übersicht, Begriffsseiten, Erklärung im Text). Aufruf: node werkzeuge/lexikon-test.js [Basisadresse]
const { chromium } = require('playwright'); const fs = require('fs'), path = require('path');
const BASE = process.argv[2] || 'http://localhost:8765';
let bad = 0; const ok = (c, t) => { console.log((c ? 'ok   ' : 'FEHLER ') + t); if (!c) bad++; };
(async () => {
  const D = JSON.parse(fs.readFileSync(path.join(__dirname, 'lexikon.json'), 'utf8')).begriffe;
  const b = await chromium.launch(), p = await b.newPage({ viewport: { width: 390, height: 844 } }); const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto(BASE + '/lexikon.html'); await p.waitForTimeout(500);
  ok(await p.locator('.lx-grid a').count() === D.length, 'Übersicht zeigt alle ' + D.length + ' Begriffe');
  await p.fill('#lx-find', 'wechselr'); ok(await p.locator('.lx-grid a:visible').count() >= 1 && await p.locator('.lx-grid a:visible').count() < 6, 'Suche filtert');
  await p.fill('#lx-find', 'xyzxyz'); ok(await p.isVisible('#lx-none'), 'Suche ohne Treffer: Hinweis');
  let miss = 0, dead = 0; const seen = {}, get = u => p.evaluate(u => fetch(u).then(r => r.ok ? r.text() : null).catch(() => null), u);   // Abruf im Browser, damit er denselben Weg nimmt wie die Seite
  for (const t of D) {
    const h = await get(BASE + '/lexikon/' + t.slug + '.html'); if (h === null) { miss++; continue; }
    if (!h.includes('"DefinedTerm"') || !h.includes('<h1>')) miss++;
    for (const m of h.matchAll(/class="lx-links">(.*?)<\/div>/gs)) for (const a of m[1].matchAll(/href="([^"#]+)/g)) { if (!seen[a[1]]) seen[a[1]] = (await get(BASE + a[1])) === null ? 'tot' : 'ok'; if (seen[a[1]] === 'tot') dead++; }
  }
  ok(miss === 0, 'jede Begriffsseite ist da, mit Überschrift und Auszeichnung'); ok(dead === 0, 'alle Links der Begriffsseiten gehen');
  await p.goto(BASE + '/lexikon/kilowatt-peak.html'); await p.waitForTimeout(400);
  ok((await p.textContent('h1')).includes('Kilowatt Peak') && await p.locator('.lx-grid a').count() >= 2, 'Begriffsseite mit verwandten Begriffen');
  ok(await p.locator('.lx').count() === 0, 'auf Lexikon-Seiten selbst keine Markierungen');
  ok(await p.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), 'Handy: kein seitliches Scrollen');
  await p.goto(BASE + '/pv-anlage.html'); await p.waitForTimeout(1200);
  const n = await p.locator('.lx').count(); ok(n >= 1 && n <= 8, 'Ratgeber: ' + n + ' Begriffe markiert (1 bis 8)');
  const words = await p.locator('.lx').allTextContents(); ok(new Set(words.map(w => w.toLowerCase())).size === words.length, 'jeder Begriff nur einmal: ' + words.join(', '));
  await p.locator('.lx').first().scrollIntoViewIfNeeded(); await p.locator('.lx').first().click(); await p.waitForTimeout(250);
  ok(await p.isVisible('.lx-pop') && (await p.textContent('.lx-pop p')).length > 30, 'Antippen zeigt die Erklärung');
  const box = await p.locator('.lx-pop').boundingBox(); ok(box.x >= 0 && box.x + box.width <= 391, 'Erklärung bleibt im Bild');
  ok(/\/lexikon\/[a-z-]+\.html$/.test(await p.getAttribute('.lx-pop a', 'href')), 'Erklärung verlinkt die Begriffsseite');
  await p.keyboard.press('Escape'); ok(!(await p.isVisible('.lx-pop')), 'Escape schließt');
  ok(errs.length === 0, 'keine Skriptfehler ' + errs.join('|'));
  await b.close(); console.log(bad ? '\n' + bad + ' FEHLER' : '\nALLE TESTS BESTANDEN'); process.exit(bad ? 1 : 0);
})();
