// Bedientest für was-lohnt-sich.html. Aufruf: node werkzeuge/einstieg-test.js [Basisadresse]. Muss mit „ALLE TESTS BESTANDEN“ enden.
const { chromium } = require('playwright');
const BASE = process.argv[2] || 'http://localhost:8765', SHOT = process.argv[3];
let bad = 0; const ok = (c, t) => { console.log((c ? 'ok   ' : 'FEHLER ') + t); if (!c) bad++; };
(async () => {
  const b = await chromium.launch(), p = await (await b.newContext({ viewport: { width: 390, height: 844 } })).newPage(); const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto(BASE + '/was-lohnt-sich.html'); await p.waitForTimeout(600);
  ok(await p.isVisible('.wl-step[data-q=wohn]') && !(await p.isVisible('#wl-res')), 'Start bei Frage 1');
  await p.click('.wl-step[data-q=wohn] button[data-v=eh]'); await p.waitForTimeout(400);
  ok(await p.isVisible('.wl-step[data-q=platz]'), 'Antwort führt zu Frage 2');
  await p.click('button[data-v=dach]'); await p.click('button[data-v=stell]'); await p.click('.wl-step[data-q=platz] .wl-next'); await p.waitForTimeout(300);
  await p.click('button[data-v=plan]'); await p.waitForTimeout(400);
  await p.click('.wl-step[data-q=heiz] .wl-back'); await p.waitForTimeout(300);
  ok(await p.getAttribute('button[data-v=plan]', 'aria-pressed') === 'true', 'Zurück zeigt die gegebene Antwort');
  await p.click('button[data-v=plan]'); await p.waitForTimeout(400); await p.click('button[data-v=gas]'); await p.waitForTimeout(400);
  await p.fill('#wl-plz', '12'); await p.click('#wl-done');
  ok(await p.isVisible('#wl-err'), 'falsche Postleitzahl: Hinweis');
  await p.fill('#wl-plz', '97274'); await p.click('.wl-chips button[data-k="4500"]'); await p.fill('#wl-ct', '33'); await p.click('#wl-done'); await p.waitForTimeout(700);
  const titles = await p.locator('#wl-list h3').allTextContents();
  ok(titles[0] === 'Solaranlage aufs Dach rechnen' && titles.includes('Zuhause laden mit Wallbox') && titles.includes('Wärmepumpe prüfen') && titles.includes('Stromtarif prüfen'), 'Plan fürs eigene Haus mit Dach, Stellplatz, geplantem E-Auto, Gas: ' + titles.join(' | '));
  ok(titles.length <= 6, 'höchstens 6 Schritte');
  ok(await p.evaluate(() => localStorage.getItem('mzp') === '97274' && localStorage.getItem('mzk') === '4500' && localStorage.getItem('sp') === '33'), 'Zahlen stehen im Profil „Mein Zuhause“');
  const links = await p.locator('#wl-list a').evaluateAll(a => a.map(x => x.getAttribute('href').split('#')[0]));
  for (const l of [...new Set(links)]) { const st = await p.evaluate(u => fetch(u).then(r => r.status), BASE + l); if (st !== 200) ok(false, 'Link ' + l + ' → ' + st); }
  ok(true, links.length + ' Links im Plan geprüft');
  if (SHOT) await p.screenshot({ path: SHOT, fullPage: true });
  await p.reload(); await p.waitForTimeout(500);
  ok(await p.isVisible('#wl-res'), 'beim Wiederkommen steht der Plan sofort da');
  await p.click('#wl-again'); await p.waitForTimeout(300);
  ok(await p.isVisible('.wl-step[data-q=wohn]') && await p.getAttribute('button[data-v=eh]', 'aria-pressed') === 'true', 'Antworten ändern startet vorn mit den alten Antworten');
  // Mieter ohne alles
  const t2 = await p.evaluate(() => { WL.set({ wohn: 'mw', platz: [], auto: 'nein', heiz: 'sonst' }); return WL.plan().map(x => x.t); });
  ok(t2[0] === 'Stromtarif prüfen' && t2[1] === 'Stromfresser finden' && t2.length === 2, 'Mieter ohne Platz: Tarif und Stromfresser (' + t2.join(' | ') + ')');
  const t3 = await p.evaluate(() => { WL.set({ wohn: 'mw', platz: ['balkon'], auto: 'ja', heiz: 'sonst' }); return WL.plan().map(x => x.t); });
  ok(t3[0] === 'Balkonkraftwerk planen' && t3.includes('Ladekosten deines E-Autos kennen'), 'Mieter mit Balkon und E-Auto: ' + t3.join(' | '));
  ok(await p.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), 'Handy: kein seitliches Scrollen');
  ok(errs.length === 0, 'keine Skriptfehler ' + errs.join('|'));
  await b.close(); console.log(bad ? '\n' + bad + ' FEHLER' : '\nALLE TESTS BESTANDEN'); process.exit(bad ? 1 : 0);
})();
