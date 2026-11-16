/* Stromkosten-Rechner für stromkosten.html und die Geräte-Seiten in stromkosten/ (erzeugt von werkzeuge/stromkosten.py).
   Der Rechner steht als .skc im HTML; data-art: w = Watt mal Zeit, gang = kWh je Durchgang, jahr = kWh im Jahr.
   Das Feld für den Strompreis macht bei „Mein Zuhause“ mit (site.js). window.SK = {kwhJahr, lesen}. */
(function () {
  'use strict';
  var d = document, box = d.querySelector('.skc'); if (!box) return;
  var $ = function (n) { return box.querySelector('[data-f="' + n + '"]'); }, out = function (n) { return box.querySelector('[data-o="' + n + '"]'); };
  function num(el, lo, hi) { if (!el) return null; var v = String(el.value).trim(); if (/^\d{1,3}\.\d{3}$/.test(v)) v = v.replace('.', ''); v = parseFloat(v.replace(',', '.')); return isFinite(v) && v >= lo && v <= hi ? v : null; }
  function f(v, n) { return v.toLocaleString('de-DE', { minimumFractionDigits: n || 0, maximumFractionDigits: n || 0 }); }
  function geld(eur) { return eur < 1 ? f(eur * 100, eur < 0.1 ? 1 : 0) + ' ct' : f(eur, eur < 100 ? 2 : 0) + ' €'; }
  /* Jahresverbrauch in kWh und Verbrauch je Einheit (Stunde, Durchgang oder Tag) */
  function kwhJahr(o) {
    if (o.art === 'w') { var std = o.min != null ? o.min / 60 : o.h, kw = o.w * (o.anteil == null ? 100 : o.anteil) / 100 / 1000; return { jahr: kw * std * o.tage, einheit: kw, tag: kw * std }; }
    if (o.art === 'gang') return { jahr: o.kwh * o.proWoche * 52, einheit: o.kwh, tag: o.kwh * o.proWoche / 7 };
    return { jahr: o.kwh, einheit: o.kwh / 365, tag: o.kwh / 365 };
  }
  function lesen() {
    var a = box.dataset.art, o = { art: a, ct: num($('ct'), 5, 150) };
    if (a === 'w') { o.w = num($('w'), 0.1, 30000); o.anteil = +(box.dataset.anteil || 100); if ($('min')) o.min = num($('min'), 0, 1440); else o.h = num($('h'), 0, 24); o.tage = num($('tage'), 0, 366); }
    else if (a === 'gang') { o.kwh = num($('kwh'), 0.001, 200); o.proWoche = num($('proWoche'), 0, 200); }
    else o.kwh = num($('kwh'), 1, 100000);
    return o;
  }
  function draw() {
    var o = lesen(), bad = Object.keys(o).some(function (k) { return o[k] === null; }), er = box.querySelector('.skc-err');
    if (er) er.hidden = !bad; if (bad) return;
    var r = kwhJahr(o), p = o.ct / 100;
    out('einheit').textContent = geld(r.einheit * p); out('jahr').textContent = geld(r.jahr * p); out('monat').textContent = geld(r.jahr * p / 12); out('kwh').textContent = f(r.jahr, r.jahr < 10 ? 1 : 0) + ' kWh';
    var bar = box.querySelector('.skc-bar i'); if (bar) bar.style.width = Math.max(2, Math.min(100, r.jahr / 1500 * 100)) + '%';
    var cmp = out('vergleich'); if (cmp) cmp.textContent = r.jahr >= 1 ? 'Das sind etwa ' + f(r.jahr / 1900 * 100, r.jahr < 19 ? 1 : 0) + ' % des Jahresverbrauchs eines Zwei-Personen-Haushalts in einer Wohnung (1.900 kWh).' : '';
    d.querySelectorAll('[data-sk-jahr]').forEach(function (e) { e.textContent = geld(+e.dataset.skJahr * p); });   /* Liste auf der Sammelseite folgt dem Strompreis */
  }
  box.addEventListener('input', draw); box.addEventListener('change', draw);
  /* Sammelseite: Geräteauswahl füllt die Felder */
  var sel = d.getElementById('sk-sel'), G = window.SKG;
  if (sel && G) sel.addEventListener('change', function () {
    var g = G[sel.value]; if (!g) return; box.dataset.art = g.art; box.dataset.anteil = g.anteil == null ? 100 : g.anteil;
    box.querySelectorAll('[data-for]').forEach(function (e) { e.hidden = e.dataset.for.split(' ').indexOf(g.art) < 0; });
    if (g.art === 'w') { $('w').value = g.w; $('h').value = String(g.min != null ? Math.round(g.min / 6) / 10 : g.h).replace('.', ','); $('tage').value = g.tage; }
    else { box.querySelectorAll('[data-f="kwh"]').forEach(function (e) { e.value = String(g.kwh).replace('.', ','); }); if (g.art === 'gang') $('proWoche').value = g.proWoche; }
    var n = d.getElementById('sk-note'); if (n) n.innerHTML = (g.art === 'w' && g.anteil < 100 ? 'Gerechnet mit ' + g.anteil + ' % der Leistung, weil das Gerät nicht durchgehend heizt. ' : '') + 'Üblich: ' + g.spanne + '. <a href="/stromkosten/' + sel.value + '.html">Mehr zu diesem Gerät</a>';
    var kl = d.getElementById('sk-kwh-l'); if (kl) kl.textContent = g.art === 'gang' ? 'Verbrauch je ' + g.wort + ' (kWh)' : 'Verbrauch im Jahr (kWh)';
    var el = out('einheit-l'); if (el) el.textContent = g.art === 'w' ? 'pro Stunde' : g.art === 'gang' ? 'pro ' + g.wort : 'pro Tag';
    draw();
  });
  window.SK = { kwhJahr: kwhJahr, lesen: lesen, geld: geld };
  /* erst rechnen, wenn „Mein Zuhause“ den Strompreis eingetragen hat */
  draw(); addEventListener('load', function () { setTimeout(draw, 150); });
})();
