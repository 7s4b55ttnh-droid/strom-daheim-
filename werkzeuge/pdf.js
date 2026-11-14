// Baut die Checklisten als PDF (A4) aus den Anleitungs-Seiten: Schritte, Checkliste zum Abhaken, Einkaufsliste.
// Aufruf: node werkzeuge/pdf.js [Basisadresse]   (ohne Adresse: http://localhost:8765; vorher im Ordner „python3 -m http.server 8765“ starten)
// Nach jeder Änderung an Schritten, Checkliste oder Einkaufsliste einer Anleitung neu laufen lassen und die PDFs mit einchecken.
const { chromium } = require('playwright'); const path = require('path');
const BASE = process.argv[2] || 'http://localhost:8765', OUT = path.join(__dirname, '..', 'assets', 'pdf');
const SEITEN = [['anleitung-balkonkraftwerk.html', 'checkliste-balkonkraftwerk.pdf', 'Balkonkraftwerk montieren'], ['anleitung-wallbox.html', 'checkliste-wallbox.pdf', 'Wallbox installieren']];
const esc = s => s.replace(/[&<>]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
(async () => {
  require('fs').mkdirSync(OUT, { recursive: true });
  const b = await chromium.launch(), p = await b.newPage();
  for (const [seite, datei, titel] of SEITEN) {
    await p.goto(BASE + '/' + seite); await p.waitForTimeout(800);
    const d = await p.evaluate(() => {
      const t = e => e ? e.textContent.replace(/\s+/g, ' ').trim() : '';
      return {
        lede: t(document.querySelector('#schritte .lede')),
        steps: [...document.querySelectorAll('#schritte ol.steps > li')].map(li => ({ who: t(li.querySelector('.who')), h: t(li.querySelector('h3')) })),
        checks: [...document.querySelectorAll('#ck label, #ck li, #ck .row')].map(t).filter((x, i, a) => x && a.indexOf(x) === i),
        shop: [...document.querySelectorAll('#einkauf .shop h3')].map(h => { const items = []; let n = h.nextElementSibling; while (n && n.tagName !== 'H3') { n.querySelectorAll && n.querySelectorAll('.item b, .item strong').forEach(x => items.push(t(x))); n = n.nextElementSibling; } return { h: t(h).replace(/^\d+\s*·\s*/, ''), items }; }),
        stand: (document.body.textContent.match(/Stand:?\s*(\d{1,2}\.\s?\d{1,2}\.\s?\d{4}|\d{1,2}\. [A-Za-zä]+ \d{4})/) || [])[1] || ''
      };
    });
    if (!d.steps.length || !d.checks.length) { console.log('FEHLER', seite, 'Schritte', d.steps.length, 'Checkliste', d.checks.length); process.exitCode = 1; continue; }
    const html = `<!doctype html><html lang="de"><meta charset="utf-8"><title>Checkliste: ${esc(titel)} – Strom-Daheim</title><style>
@page{size:A4;margin:16mm 16mm 18mm}body{font:10.5pt/1.45 system-ui,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;color:#111;margin:0}
header{display:flex;justify-content:space-between;align-items:baseline;border-bottom:2pt solid #111;padding-bottom:6pt;margin-bottom:12pt}
header b{font-size:11pt}header span{font-size:9pt;color:#444}
h1{font-size:21pt;line-height:1.15;margin:0 0 4pt;letter-spacing:-.01em}.lede{color:#444;margin:0 0 12pt}
h2{font-size:12.5pt;margin:16pt 0 6pt;padding-bottom:3pt;border-bottom:.75pt solid #999;break-after:avoid}
ol,ul{margin:0;padding:0;list-style:none}li{break-inside:avoid}
.st li{display:grid;grid-template-columns:18pt 1fr auto;gap:8pt;padding:4pt 0;border-bottom:.5pt solid #ddd}.st i{font-style:normal;font-weight:700}.st span{color:#555;font-size:9pt;white-space:nowrap}
.ck li,.sh li{display:grid;grid-template-columns:14pt 1fr;gap:8pt;padding:3.5pt 0;align-items:start}.ck li::before,.sh li::before{content:"";width:10pt;height:10pt;border:1pt solid #111;border-radius:2pt;margin-top:2pt}
.cols{columns:2;column-gap:20pt}.cols h3{font-size:10.5pt;margin:8pt 0 2pt;break-after:avoid}.cols div{break-inside:avoid}
footer{margin-top:14pt;font-size:8.5pt;color:#555;border-top:.5pt solid #999;padding-top:5pt}
</style><header><b>Strom-Daheim</b><span>strom-daheim.de/${seite}</span></header>
<h1>Checkliste: ${esc(titel)}</h1><p class="lede">${esc(d.lede || 'Zum Ausdrucken und Abhaken.')}</p>
<h2>Die Schritte</h2><ol class="st">${d.steps.map((s, i) => `<li><i>${i + 1}</i><b>${esc(s.h)}</b><span>${esc(s.who)}</span></li>`).join('')}</ol>
<h2>Hast du an alles gedacht?</h2><ul class="ck">${d.checks.map(c => `<li>${esc(c)}</li>`).join('')}</ul>
${d.shop.some(g => g.items.length) ? `<h2>Einkaufsliste</h2><div class="cols">${d.shop.filter(g => g.items.length).map(g => `<div><h3>${esc(g.h)}</h3><ul class="sh">${g.items.map(x => `<li>${esc(x)}</li>`).join('')}</ul></div>`).join('')}</div>` : ''}
<footer>Die ausführliche Anleitung mit Erklärungen, Quellen und Sicherheitshinweisen steht auf strom-daheim.de/${seite}. Alle Angaben ohne Gewähr${d.stand ? ', Stand ' + esc(d.stand) : ''}. Arbeiten an der Elektroinstallation gehören in die Hände einer Elektrofachkraft.</footer></html>`;
    const q = await b.newPage(); await q.setContent(html); await q.pdf({ path: path.join(OUT, datei), format: 'A4', printBackground: true }); await q.close();
    console.log('ok', datei, d.steps.length, 'Schritte,', d.checks.length, 'Punkte,', d.shop.reduce((s, g) => s + g.items.length, 0), 'Einkäufe');
  }
  await b.close();
})();
