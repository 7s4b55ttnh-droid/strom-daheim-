// Bedientest für „Mein Zuhause“ (site.js) und den Geräte-Planer. Aufruf: node werkzeuge/zuhause-test.js [Basisadresse]
// Muss mit „ALLE TESTS BESTANDEN“ enden.
const { chromium } = require('playwright');
const BASE = process.argv[2] || 'http://localhost:8765';
let bad = 0; const ok = (c, t) => { console.log((c ? 'ok   ' : 'FEHLER ') + t); if (!c) bad++; };
(async () => {
  const b = await chromium.launch(), ctx = await b.newContext({ viewport: { width: 390, height: 844 } });
  const p = await ctx.newPage(); const errs = []; p.on('pageerror', e => errs.push(e.message));
  const go = async u => { await p.goto(BASE + u); await p.waitForTimeout(900); };
  await go('/solar-rechner.html');
  ok(await p.locator('.mz-bar').count() === 0, 'ohne Angaben keine Leiste');
  await p.fill('#sr-plz', '80331'); await p.fill('#sr-kwh', '4200'); await p.dispatchEvent('#sr-kwh', 'change'); await p.waitForTimeout(400);
  ok(await p.evaluate(() => localStorage.getItem('mzp')) === '80331' && await p.evaluate(() => localStorage.getItem('mzk')) === '4200', 'Postleitzahl und Verbrauch werden gemerkt');
  ok((await p.textContent('.mz-bar')).includes('80331') && (await p.textContent('.mz-bar')).includes('4.200 kWh'), 'Leiste zeigt die Angaben');
  await go('/balkonkraftwerk-planer.html');
  ok(await p.inputValue('#bp-plz') === '80331', 'Planer übernimmt die Postleitzahl');
  ok((await p.inputValue('#bp-kwh')).replace('.', '') === '4200', 'Planer übernimmt den Verbrauch: ' + await p.inputValue('#bp-kwh'));
  await go('/stromtarif.html');
  ok((await p.locator('input.vin[aria-label="Jahresverbrauch in Kilowattstunden"]').first().inputValue()).replace('.', '') === '4200', 'Stromtarif-Rechner übernimmt den Verbrauch');
  await go('/solar-atlas.html');
  ok(await p.inputValue('#sa-plz') === '80331', 'Solar-Atlas übernimmt die Postleitzahl');
  // Dialog
  await p.click('.mz-e'); await p.fill('.mz-dlg [name=ct]', '31,5'); await p.fill('.mz-dlg [name=plz]', '123'); await p.click('.mz-ok');
  ok(await p.isVisible('.mz-err'), 'falsche Postleitzahl wird abgelehnt');
  await p.fill('.mz-dlg [name=plz]', '04109'); await p.click('.mz-ok'); await p.waitForTimeout(300);
  ok(await p.evaluate(() => localStorage.getItem('sp')) === '31.5' && await p.inputValue('#sa-plz') === '04109', 'Dialog speichert und füllt die Felder');
  await go('/waschmaschine.html');
  ok((await p.locator('input.vin[aria-label^="Strompreis in"]').first().inputValue()) === '31,5', 'Strompreis steht im nächsten Rechner');
  // geteilter Link gewinnt
  await go('/solar-rechner.html?p=20095&v=2500&k=6');
  ok(await p.inputValue('#sr-plz') === '20095' && (await p.inputValue('#sr-kwh')).replace('.', '') === '2500', 'geteilter Link gewinnt gegen das Profil');
  ok(await p.evaluate(() => localStorage.getItem('mzp')) === '04109', 'geteilter Link überschreibt das Profil nicht');
  await go('/solar-atlas.html'); await p.click('.mz-e'); await p.click('.mz-del'); await p.waitForTimeout(200);
  ok(await p.locator('.mz-bar').count() === 0 && await p.evaluate(() => localStorage.getItem('mzp')) === null, 'Alles löschen entfernt Angaben und Leiste');
  ok(await p.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), 'Handy: kein seitliches Scrollen');
  // Geräte-Planer
  await go('/strompreis-heute.html');
  await p.click('#sp-dev button[data-n="Spülmaschine"]');
  ok(await p.getAttribute('#sp-dur button[data-h="3"]', 'aria-pressed') === 'true' && await p.inputValue('#sp-kwh') === '1', 'Gerät setzt Laufzeit und Strommenge');
  const n = await p.locator('#sp-dl option').count();
  ok(n >= 1, 'Auswahl „fertig bis“ hat ' + n + ' Einträge');
  const ics = await p.evaluate(() => window.__spIcs());
  if (ics) {
    ok(/BEGIN:VEVENT[\s\S]*SUMMARY:Spülmaschine starten[\s\S]*TRIGGER:-PT10M[\s\S]*END:VCALENDAR\r\n$/.test(ics), 'Kalendereintrag ist vollständig');
    const m = ics.match(/DTSTART:(\d{8}T\d{6}Z)[\s\S]*DTEND:(\d{8}T\d{6}Z)/), t = s => Date.UTC(+s.slice(0, 4), +s.slice(4, 6) - 1, +s.slice(6, 8), +s.slice(9, 11));
    ok(m && t(m[2]) - t(m[1]) === 3 * 3600000 && t(m[1]) > Date.now() - 3600000, 'Kalendereintrag dauert 3 Stunden und liegt nicht in der Vergangenheit');
    const win = await p.textContent('#sp-r-win'), h = +win.match(/(\d+) Uhr/)[1];
    const bh = +new Intl.DateTimeFormat('en-GB', { timeZone: 'Europe/Berlin', hour: '2-digit', hourCycle: 'h23' }).format(new Date(t(m[1])));
    ok(bh === h, 'Startzeit im Kalender = angezeigte Startzeit (' + h + ' Uhr)');
  } else ok((await p.textContent('#sp-r-win')).length > 3, 'kein Fenster mehr: Hinweis statt Kalender');
  if (n > 2) {
    await p.selectOption('#sp-dl', { index: 1 }); await p.waitForTimeout(200);
    ok(/zu knapp/.test(await p.textContent('#sp-r-win')) && await p.isDisabled('#sp-ics'), 'zu frühe Uhrzeit: ehrlicher Hinweis, Kalender gesperrt');
    await p.selectOption('#sp-dl', { index: n - 1 }); await p.waitForTimeout(200);
    ok(/fertig bis/.test(await p.textContent('#sp-r-wt')), 'mit Uhrzeit: Ergebnis nennt die Frist');
  }
  ok(errs.length === 0, 'keine Skriptfehler ' + errs.join('|'));
  await b.close();
  console.log(bad ? '\n' + bad + ' FEHLER' : '\nALLE TESTS BESTANDEN'); process.exit(bad ? 1 : 0);
})();
