// Test für stromkosten.html und die Geräte-Seiten. Aufruf: node werkzeuge/stromkosten-test.js [Basisadresse]
const { chromium } = require('playwright'); const fs = require('fs'), path = require('path');
const BASE = process.argv[2] || 'http://localhost:8765';
let bad = 0; const ok = (c, t) => { console.log((c ? 'ok   ' : 'FEHLER ') + t); if (!c) bad++; };
const near = (a, b, tol) => Math.abs(a - b) <= tol;
(async () => {
  const D = JSON.parse(fs.readFileSync(path.join(__dirname, 'stromkosten.json'), 'utf8')), G = D.geraete;
  const b = await chromium.launch(), p = await b.newPage({ viewport: { width: 390, height: 844 } }); const errs = []; p.on('pageerror', e => errs.push(e.message));
  const eur = s => { s = s.replace(/\s/g, ' '); const v = parseFloat(s.replace(/\./g, '').replace(',', '.')); return / ct/.test(s) ? v / 100 : v; };
  await p.goto(BASE + '/stromkosten.html'); await p.waitForTimeout(800);
  ok(await p.locator('.sk-list a').count() === G.length, 'Sammelseite listet alle ' + G.length + ' Geräte');
  ok(near(eur(await p.textContent('[data-o="jahr"]')), 2 * 2 * 120 * 0.32, 0.6), 'Start: Heizlüfter 2.000 W, 2 h, 120 Tage, 32 ct = 153,60 €: ' + await p.textContent('[data-o="jahr"]'));
  await p.selectOption('#sk-sel', 'waschmaschine'); await p.waitForTimeout(200);
  ok(near(eur(await p.textContent('[data-o="jahr"]')), 0.6 * 4 * 52 * 0.32, 0.3) && (await p.textContent('[data-o="einheit-l"]')) === 'pro Waschgang', 'Auswahl Waschmaschine rechnet je Waschgang: ' + await p.textContent('[data-o="jahr"]'));
  await p.selectOption('#sk-sel', 'kuehlschrank'); await p.waitForTimeout(200);
  ok(near(eur(await p.textContent('[data-o="jahr"]')), 130 * 0.32, 0.3) && !(await p.isVisible('[data-f="w"]')), 'Auswahl Kühlschrank rechnet mit dem Jahresverbrauch');
  await p.fill('[data-f="ct"]', '40'); await p.waitForTimeout(600);
  ok(near(eur(await p.textContent('[data-o="jahr"]')), 52, 0.3), 'Strompreis 40 ct wirkt: ' + await p.textContent('[data-o="jahr"]'));
  ok(near(eur(await p.locator('.sk-list a[href$="/heizluefter.html"] em').textContent()), 480 * 0.4, 1), 'Liste folgt dem Strompreis');
  ok(await p.evaluate(() => localStorage.getItem('sp')) === '40', 'Strompreis geht ins Profil „Mein Zuhause“');
  await p.fill('[data-f="kwh"]', 'abc'); ok(await p.isVisible('.skc-err'), 'Unsinn im Feld: Hinweis statt falscher Zahl');
  ok(await p.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), 'Handy: kein seitliches Scrollen');
  await p.evaluate(() => localStorage.clear());
  let miss = 0, falsch = [];
  for (const g of G) {
    await p.goto(BASE + '/stromkosten/' + g.slug + '.html'); await p.waitForTimeout(350);
    if ((await p.locator('h1').count()) !== 1 || (await p.locator('.skc').count()) !== 1) { miss++; continue; }
    const soll = (g.art === 'w' ? g.w * (g.anteil ?? 100) / 100 / 1000 * (g.min != null ? g.min / 60 : g.h) * g.tage : g.art === 'gang' ? g.kwh * g.proWoche * 52 : g.kwh) * 0.32;
    const ist = eur(await p.textContent('[data-o="jahr"]')), text = eur((await p.locator('.sk-a b').last().textContent()).replace(' im Jahr', ''));
    if (!near(ist, soll, Math.max(0.02, soll * 0.01)) || !near(text, soll, Math.max(0.02, soll * 0.01))) falsch.push(g.slug + ' ' + ist + '/' + text + ' statt ' + soll.toFixed(2));
  }
  ok(miss === 0, 'jede Geräte-Seite hat Überschrift und Rechner'); ok(falsch.length === 0, 'Rechner und Text stimmen auf allen Seiten mit den Daten überein ' + falsch.join('; '));
  ok(errs.length === 0, 'keine Skriptfehler ' + errs.join('|'));
  await b.close(); console.log(bad ? '\n' + bad + ' FEHLER' : '\nALLE TESTS BESTANDEN'); process.exit(bad ? 1 : 0);
})();
