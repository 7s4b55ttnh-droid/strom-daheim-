// Test für solar-rechner.html. Aufruf: node werkzeuge/solar-rechner-test.js [Basisadresse]  (ohne Adresse: http://localhost:8765)
// Prüft den Rechenweg (Bilanz, E-Auto, Wärmepumpe, Speicher) und die Bedienung. Muss mit „ALLE TESTS BESTANDEN“ enden.
const { chromium } = require('playwright');
const U = (process.argv[2] || 'http://localhost:8765') + '/solar-rechner.html';
let bad = 0; const ok = (c, t) => { console.log((c ? 'ok ' : 'FEHLER ') + t); if (!c) bad++; };
(async () => {
  const b = await chromium.launch(), p = await b.newPage({ viewport: { width: 1280, height: 900 } }); const e = []; p.on('pageerror', x => e.push(x.message));
  await p.goto(U); await p.waitForFunction(() => document.getElementById('sr-pv').textContent.includes('kWh'), null, { timeout: 10000 });
  const r = await p.evaluate(async () => {
    const data = BKW.decode(await (await fetch('/assets/pv/34.json')).json());
    const base = { plz: '', kwp: 8, dir: 0, tilt: 35, shade: 0, kwh: 3500, pres: 1, ev: 0, km: 12000, vb: 18, em: 0, wp: 0, wpk: 4000, bat: 0, ct: 37, fit: 7.7, cost: null };
    const R = s => { const x = SR.result(data, s, s.bat); return { pv: x.y.pv, self: x.y.self, feed: x.y.feed, load: x.y.load, saved: x.y.saved, clip: x.y.clip, cost: x.cost, nutzen: x.nutzen, pay: x.pay, aut: x.autark, share: x.share }; };
    const sum = a => { let s = 0; for (const v of a) s += v; return s / 1000; };
    const xe = SR.extra(data, { ...base, ev: 1 }), xw = SR.extra(data, { ...base, wp: 1 }), win = [0, 0];
    for (let h = 0; h < 8760; h++) { const m = Math.floor(h / 24); if (m < 59 || m >= 334) win[0] += xw[h]; if (m >= 151 && m < 243) win[1] += xw[h]; }
    return { a: R(base), ow: R({ ...base, dir: 'ow', tilt: 15 }), big: R({ ...base, kwp: 16 }), bat: R({ ...base, bat: 10 }), ev0: R({ ...base, ev: 1, em: 0 }), ev1: R({ ...base, ev: 1, em: 1 }), wp: R({ ...base, wp: 1 }),
      none: SR.extra(data, base), evSum: sum(xe), wpSum: sum(xw), winter: win[0] / 1000, sommer: win[1] / 1000, shade: R({ ...base, shade: 2 }) };
  });
  const near = (a, b, t) => Math.abs(a - b) <= t;
  ok(near(r.a.self + r.a.feed, r.a.pv, 0.5) && r.a.clip < r.a.pv * 0.005 && near(r.a.load, 3500, 3), 'Bilanz: selbst genutzt + eingespeist = Solarstrom, fast nichts abgeregelt, Verbrauch 3.500 kWh');
  ok(r.a.pv > 7000 && r.a.pv < 9500 && r.a.share > 0.12 && r.a.share < 0.3 && r.a.aut > 0.3 && r.a.aut < 0.5, '8 kWp in Kassel: ' + Math.round(r.a.pv) + ' kWh, ' + Math.round(r.a.share * 100) + ' % selbst genutzt, ' + Math.round(r.a.aut * 100) + ' % vom Dach');
  ok(r.a.cost === 9600 && near(r.a.nutzen, r.a.saved * 0.37 + r.a.feed * 0.077, 0.01) && near(r.a.pay, r.a.cost / r.a.nutzen, 1e-9), 'Kosten 1.200 € je kWp, Nutzen und „bezahlt nach“ wie beschrieben');
  ok(r.ow.pv < r.a.pv && r.ow.pv > r.a.pv * 0.75, 'Ost + West liefert weniger als Süd (' + Math.round(r.ow.pv) + ' zu ' + Math.round(r.a.pv) + ' kWh)');
  ok(near(r.big.pv, r.a.pv * 2, 5) && r.big.share < r.a.share && r.big.aut > r.a.aut, 'doppelte Anlage: doppelter Ertrag, kleinerer Anteil selbst genutzt, mehr vom Dach');
  ok(r.bat.aut > r.a.aut + 0.2 && r.bat.cost === 9600 + 5000 && r.bat.feed < r.a.feed, '10 kWh Speicher: deutlich mehr vom Dach, 5.000 € mehr Kosten, weniger Einspeisung');
  ok(r.none === null && near(r.evSum, 12000 * 18 / 100, 1) && near(r.wpSum, 4000, 1), 'E-Auto 2.160 kWh und Wärmepumpe 4.000 kWh landen vollständig in der Last');
  ok(near(r.ev0.load, 3500 + 2160, 4) && r.ev1.self > r.ev0.self + 300, 'tagsüber laden nutzt mehr Solarstrom als abends (' + Math.round(r.ev1.self) + ' zu ' + Math.round(r.ev0.self) + ' kWh)');
  ok(r.winter > r.sommer * 3 && r.sommer >= 4000 * 0.15 * 92 / 365 - 1, 'Wärmepumpe braucht im Winter ein Vielfaches vom Sommer (' + Math.round(r.winter) + ' zu ' + Math.round(r.sommer) + ' kWh)');
  ok(r.shade.pv < r.a.pv * 0.9, 'viel Schatten senkt den Ertrag');
  // Bedienung
  await p.fill('#sr-plz', '97070'); await p.waitForFunction(() => document.getElementById('sr-reg').textContent.includes('Würzburg'), null, { timeout: 8000 });
  ok(true, 'Postleitzahl lädt die Sonnendaten der Region');
  const pv0 = await p.textContent('#sr-pv'); await p.fill('#sr-kwp', '12'); await p.waitForTimeout(300);
  ok((await p.textContent('#sr-pv')) !== pv0 && (await p.inputValue('#sr-cost')) === '14.400', 'größere Anlage: neues Ergebnis, Kosten 14.400 €');
  await p.click('#sr-ev'); ok(await p.isVisible('#sr-ev-box') && (await p.getAttribute('#sr-ev', 'aria-checked')) === 'true', 'E-Auto zuschalten zeigt die Angaben');
  await p.click('#sr-wp'); await p.fill('#sr-wpk', '5000'); await p.waitForTimeout(300);
  ok((await p.textContent('#sr-txt')).includes('E-Auto und Wärmepumpe'), 'Text nennt E-Auto und Wärmepumpe');
  await p.click('#sr-var button[data-b="10"]'); await p.waitForTimeout(300);
  ok((await p.getAttribute('#sr-bat button[data-v="10"]', 'aria-pressed')) === 'true' && (await p.inputValue('#sr-cost')) === '19.400', 'Speicher aus der Vergleichstabelle wählen');
  await p.locator('details.more summary').click(); await p.fill('#sr-cost', '21000'); await p.locator('#sr-cost').blur(); await p.click('#sr-fitc button[data-v="0"]'); await p.waitForTimeout(300);
  ok((await p.textContent('#sr-pay-t')).includes('21.000') && (await p.inputValue('#sr-fit')) === '0', 'eigener Preis und Vergütung 0 werden übernommen');
  const link = await p.evaluate(() => { const S = SR.state(); return location.pathname + '?p=' + S.plz + '&k=' + S.kwp + '&e=1&h=1&hk=' + S.wpk + '&b=' + S.bat + '&f=0&c=' + S.cost; });
  const q = await b.newPage({ viewport: { width: 390, height: 844 } }); const e2 = []; q.on('pageerror', x => e2.push(x.message));
  await q.goto(U.replace('/solar-rechner.html', '') + link); await q.waitForFunction(() => document.getElementById('sr-pv').textContent.includes('kWh'), null, { timeout: 10000 }); await q.waitForTimeout(300);
  ok((await q.textContent('#sr-pay-t')) === (await p.textContent('#sr-pay-t')) && (await q.textContent('#sr-aut')) === (await p.textContent('#sr-aut')), 'geteilter Link zeigt dasselbe Ergebnis');
  ok(await q.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), 'Handy: kein seitliches Scrollen');
  await q.fill('#sr-plz', '00999'); await q.waitForTimeout(300); ok((await q.textContent('#sr-reg')).includes('kennen wir nicht'), 'unbekannte Postleitzahl: verständliche Meldung');
  ok(e.length + e2.length === 0, 'keine Skriptfehler ' + e.concat(e2).join('|'));
  await b.close(); console.log(bad ? '\n' + bad + ' FEHLER' : '\nALLE TESTS BESTANDEN'); process.exit(bad ? 1 : 0);
})();
