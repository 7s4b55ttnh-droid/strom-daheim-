// Test für strompreis-morgen.html und strompreis-ampel.html. Aufruf: node werkzeuge/morgen-test.js [Basisadresse]
const { chromium } = require('playwright');
const BASE = process.argv[2] || 'http://localhost:8765';
let bad = 0; const ok = (c, t) => { console.log((c ? 'ok   ' : 'FEHLER ') + t); if (!c) bad++; };
(async () => {
  const b = await chromium.launch(), p = await b.newPage({ viewport: { width: 390, height: 844 } }); const errs = []; p.on('pageerror', e => errs.push(e.message));
  const day = n => new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Berlin' }).format(new Date(Date.now() + n * 864e5));
  await p.goto(BASE + '/strompreis-morgen.html'); await p.waitForTimeout(700);
  const tag = await p.getAttribute('#sm', 'data-tag'), da = await p.getAttribute('#sm', 'data-da');
  ok(tag === day(1) || tag === day(0), 'Seite zeigt morgen oder heute: ' + tag + (da === '1' ? ' (Preise für morgen)' : ' (noch die von heute)'));
  ok(da === '1' ? tag >= day(0) : (await p.locator('.sm-wait').count()) === 1, da === '1' ? 'Preise für morgen sind da' : 'Hinweis „Preise für morgen stehen noch nicht fest“ steht da');
  ok(await p.locator('.pa-svg .b').count() === 24 && await p.locator('.pa-svg .b.gut').count() === 3, 'Verlauf mit 24 Stunden, günstigste 3 markiert');
  const D = await p.evaluate(() => fetch('/assets/strompreis.json').then(r => r.json()));
  const w = D.tage[tag], avg = w.reduce((a, x) => a + x, 0) / 24, txt = await p.textContent('.sm-l');
  ok(txt.includes(avg.toFixed(1).replace('.', ',')), 'Durchschnitt im Text stimmt mit den Daten: ' + avg.toFixed(1));
  let best = 0; for (let h = 0; h <= 22; h++) if (w[h] + w[h + 1] + (w[h + 2] ?? 99) < w[best] + w[best + 1] + w[best + 2] && h <= 21) best = h;
  ok(txt.includes('zwischen ' + best + ' und ' + (best + 3) + ' Uhr'), 'günstigstes Fenster stimmt: ' + best + ' bis ' + (best + 3) + ' Uhr');
  ok(await p.locator('.sm-g tbody tr').count() === 4, 'vier Geräte mit Startzeit');
  ok(await p.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), 'Handy: kein seitliches Scrollen');
  await p.goto(BASE + '/strompreis-ampel.html'); await p.waitForFunction(() => window.__amp || /Keine|nicht/.test(document.getElementById('amp-b').textContent), null, { timeout: 8000 });
  const A = await p.evaluate(() => window.__amp ? { st: __amp.st, h: __amp.h, v: __amp.v, shown: document.getElementById('amp').dataset.s, n: document.getElementById('amp-n').textContent, bars: document.querySelectorAll('#amp-bars i').length } : null);
  if (A) { const s = D.tage[day(0)].slice().sort((x, y) => x - y), soll = A.v <= s[7] ? 'gut' : A.v >= s[16] ? 'teuer' : 'mittel';
    ok(A.st === soll && A.shown === soll, 'Ampel zeigt ' + A.st + ' für ' + A.h + ' Uhr (' + A.v + ' ct), Drittel-Regel passt');
    ok(A.bars === 24 && A.n.length > 10, 'Tagesleiste und Hinweis: ' + A.n); }
  else ok((await p.textContent('#amp-b')).length > 5, 'ohne Daten von heute: ehrlicher Hinweis');
  await p.goto(BASE + '/strompreis-ampel.html?einbetten=1'); await p.waitForTimeout(700);
  ok(!(await p.isVisible('h1')) && await p.isVisible('#amp') && !(await p.isVisible('#einbinden')), 'eingebettet: nur die Ampel');
  ok(errs.length === 0, 'keine Skriptfehler ' + errs.join('|'));
  await b.close(); console.log(bad ? '\n' + bad + ' FEHLER' : '\nALLE TESTS BESTANDEN'); process.exit(bad ? 1 : 0);
})();
