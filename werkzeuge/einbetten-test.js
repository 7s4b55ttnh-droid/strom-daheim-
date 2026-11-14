// Prüft den Einbett-Modus (?einbetten=1) aller Werkzeuge beider Seiten in einem fremden Rahmen.
// Aufruf: node werkzeuge/einbetten-test.js [Strom-Adresse] [Stil-Adresse]  (ohne Angaben: http://localhost:8765 und http://localhost:8766). Muss mit „EINBETTEN: ALLE BESTANDEN“ enden.
const { chromium } = require('playwright'), http = require('http');
const A = process.argv[2] || 'http://localhost:8765', B = process.argv[3] || 'http://localhost:8766';
const T = [[A + '/balkonkraftwerk-planer.html', '#bp-plz'], [A + '/solar-rechner.html', '#sr-plz'], [A + '/strompreis-heute.html', '#sp-chart'], [B + '/raumplaner.html', '#rp-plan'], [B + '/bilderwand.html', '#bw-draw'], [B + '/farbpalette.html', '#fp-pic']];
let bad = 0; const ok = (c, t) => { console.log((c ? 'ok ' : 'FEHLER ') + t); if (!c) bad++; };
(async () => {
  const srv = http.createServer((q, r) => { const u = decodeURIComponent(q.url.slice(4)); r.setHeader('content-type', 'text/html'); r.end('<!doctype html><body style="margin:0"><iframe id="f" src="' + u + '?einbetten=1" style="width:100%;height:300px;border:0"></iframe><script>addEventListener("message",function(e){if(e.data&&e.data.daheimHoehe){window.H=e.data.daheimHoehe;document.getElementById("f").style.height=e.data.daheimHoehe+"px"}})</script>'); }).listen(8799, '127.0.0.1');
  const b = await chromium.launch();
  for (const [u, sel] of T) {
    const p = await b.newPage({ viewport: { width: 420, height: 800 } }); const e = []; p.on('pageerror', x => e.push(x.message));
    await p.goto('http://127.0.0.1:8799/?u=' + encodeURIComponent(u)); await p.waitForTimeout(1800);
    const f = p.frameLocator('#f'), fr = p.frames().find(x => x.url().includes('einbetten=1'));
    const info = await fr.evaluate(sel => ({ tool: !!document.querySelector(sel) && document.querySelector(sel).getBoundingClientRect().height > 0, head: [...document.querySelectorAll('body>header,body>footer,.hero')].some(x => x.getBoundingClientRect().height > 0),
      amz: [...document.querySelectorAll('a[href*="amazon."]')].filter(x => x.getBoundingClientRect().height > 0).length, cr: !!document.querySelector('.emb-cr a'), sh: document.documentElement.scrollHeight, ext: [...document.querySelectorAll('.emb-keep a[href]')].filter(a => { if (a.getAttribute('href')[0] === '#') return false; a.addEventListener('click', e => e.preventDefault(), { once: true }); a.click(); return a.target !== '_blank'; }).length }), sel);
    const H = await p.evaluate(() => window.H);
    ok(info.tool && !info.head && info.amz === 0 && info.cr && info.ext === 0 && H > 300 && Math.abs(H - info.sh) < 40 && e.length === 0, u.split('/').pop() + ': nur das Werkzeug, kein Kopf, keine Partnerlinks, Verweis da, Höhe gemeldet (' + H + ' px)' + (e.length ? ' ' + e.join('|') : '') + ' ' + JSON.stringify(info));
    await p.close();
  }
  await b.close(); srv.close(); console.log(bad ? bad + ' FEHLER' : 'EINBETTEN: ALLE BESTANDEN'); process.exit(bad ? 1 : 0);
})();
