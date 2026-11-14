// Test „als App“: Manifest, Symbole, Helfer sw.js (Seiten ohne Netz). Aufruf: node werkzeuge/app-test.js [Basisadresse] [zweite Seite]
// Geht für beide Websites: node werkzeuge/app-test.js http://localhost:8766 raumplaner.html
const { chromium } = require('playwright');
const BASE = process.argv[2] || 'http://localhost:8765', P2 = '/' + (process.argv[3] || 'strompreis-heute.html');
let bad = 0; const ok = (c, t) => { console.log((c ? 'ok   ' : 'FEHLER ') + t); if (!c) bad++; };
(async () => {
  const b = await chromium.launch(), ctx = await b.newContext({ viewport: { width: 390, height: 844 } }), p = await ctx.newPage(); const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto(BASE + '/'); await p.waitForTimeout(600);
  const href = await p.getAttribute('link[rel=manifest]', 'href'); ok(!!href, 'Startseite verlinkt das Manifest');
  const man = await p.evaluate(u => fetch(u).then(r => r.json()), new URL(href, BASE + '/').href);
  ok(man.name && man.display === 'standalone' && man.icons.length >= 3 && man.icons.some(i => i.purpose === 'maskable'), 'Manifest vollständig: ' + man.name);
  let miss = 0; for (const i of man.icons) { const r = await p.evaluate(u => fetch(u).then(r => [r.status, r.headers.get('content-type') || '']), new URL(i.src, BASE + '/').href); if (r[0] !== 200 || !/png/.test(r[1])) miss++; }
  ok(miss === 0, 'alle App-Symbole sind da');
  for (const s of man.shortcuts || []) if ((await p.evaluate(u => fetch(u).then(r => r.status), new URL(s.url, BASE + '/').href)) !== 200) ok(false, 'Kurzbefehl ' + s.url);
  ok(await p.evaluate(() => navigator.serviceWorker.getRegistrations().then(r => r.length === 0)), 'im Browser meldet sich der Helfer nicht an (nur in der installierten App)');
  ok(await p.locator('footer .app-i button').count() === 1, 'Knopf „Als App installieren“ in der Fußzeile');
  await p.click('footer .app-i button'); await p.waitForTimeout(200); ok(await p.isVisible('dialog[open] #app-h'), 'Knopf zeigt die Anleitung'); await p.keyboard.press('Escape');
  // Helfer von Hand anmelden (so wie in der installierten App) und ohne Netz prüfen
  await p.evaluate(() => navigator.serviceWorker.register('/sw.js').then(() => navigator.serviceWorker.ready)); await p.waitForTimeout(800);
  await p.reload(); await p.waitForTimeout(800); await p.goto(BASE + P2); await p.waitForTimeout(1200);
  await ctx.setOffline(true);
  await p.goto(BASE + P2).catch(() => { }); await p.waitForTimeout(600);
  ok((await p.locator('h1').count()) === 1 && !(await p.textContent('body')).includes('Gerade kein Netz'), 'ohne Netz: besuchte Seite öffnet aus der Ablage');
  ok(await p.evaluate(() => getComputedStyle(document.body).fontFamily.length > 0 && document.styleSheets.length > 0), 'ohne Netz: Gestaltung ist da');
  await p.goto(BASE + '/impressum.html').catch(() => { }); await p.waitForTimeout(400);
  ok((await p.textContent('body')).includes('Gerade kein Netz'), 'ohne Netz: nicht besuchte Seite zeigt einen ehrlichen Hinweis');
  await ctx.setOffline(false);
  ok(errs.length === 0, 'keine Skriptfehler ' + errs.join('|'));
  await b.close(); console.log(bad ? '\n' + bad + ' FEHLER' : '\nALLE TESTS BESTANDEN'); process.exit(bad ? 1 : 0);
})();
