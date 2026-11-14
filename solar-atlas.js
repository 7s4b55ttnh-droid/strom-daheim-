/* Strom-Daheim: Solar-Atlas. Karte, Postleitzahl-Suche und Kennzahl-Umschalter. Daten stehen als JSON in der Seite (von werkzeuge/solaratlas.py). */
(function () {
  'use strict';
  var $ = function (id) { return document.getElementById(id); }, src = $('sa-data'), map = $('sa-map');
  if (!src || !map) return;
  var D = JSON.parse(src.textContent), REG = D.reg, META = D.meta, M = 0, SEL = null, paths = {};
  [].forEach.call(map.querySelectorAll('path[data-r]'), function (p) { paths[p.getAttribute('data-r')] = p; });
  function z(n) { return Math.round(n).toLocaleString('de-DE'); }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function range() { var lo = 1e9, hi = -1e9; for (var k in REG) { lo = Math.min(lo, REG[k].v[M]); hi = Math.max(hi, REG[k].v[M]); } return [lo, hi]; }
  function paint() {
    var r = range();
    for (var k in paths) paths[k].setAttribute('fill', META.pal[Math.min(4, Math.floor((REG[k].v[M] - r[0]) / (r[1] - r[0] + 1e-9) * 5))]);
    $('sa-lo').textContent = z(r[0]); $('sa-hi').textContent = z(r[1]); $('sa-unit').textContent = META.met[M][2];
    map.setAttribute('aria-label', 'Karte von Deutschland: ' + META.met[M][1] + ' je Postleitregion, von ' + z(r[0]) + ' bis ' + z(r[1]) + ' ' + META.met[M][2] + '. Die Werte stehen auch in der Tabelle.');
  }
  function card(msg) {
    var c = $('sa-card');
    if (msg) { c.innerHTML = '<p class="bad">' + msg + '</p>'; return; }
    if (!SEL) return;
    var r = REG[SEL], v = r.v[M], d = (v / META.mean[M] - 1) * 100, t = Math.abs(d) < 0.5 ? 'genau im Schnitt' : z(Math.max(1, Math.abs(d))) + ' % ' + (d > 0 ? 'über' : 'unter') + ' dem Schnitt';
    c.innerHTML = '<p><span class="n">' + esc(r.n) + '</span> · Postleitzahlen ' + SEL + '…<span class="v">' + z(v) + '<small>' + META.met[M][2] + '</small></span>' + esc(META.met[M][1]) + '. Platz ' + r.r[M] + ' von 95, ' + t + '. <a href="' + r.u + '">Alle Werte der Region</a></p>';
  }
  function select(k, scroll) {
    if (!REG[k]) return false;
    SEL = k; $('sa-sel').setAttribute('d', paths[k].getAttribute('d')); card();
    [].forEach.call(document.querySelectorAll('.sa-t tr.on'), function (t) { t.classList.remove('on'); });
    [].forEach.call(document.querySelectorAll('.sa-t tr[data-r="' + k + '"]'), function (t) { t.classList.add('on'); });
    return true;
  }
  function regOf(plz) { var r = String(plz).replace(/\D/g, '').slice(0, 2); if (r === '11') r = '10'; return r.length === 2 ? r : null; }
  $('sa-met').addEventListener('click', function (e) {
    var b = e.target.closest('button'); if (!b) return; M = +b.getAttribute('data-m');
    [].forEach.call(this.children, function (c) { c.setAttribute('aria-pressed', c === b ? 'true' : 'false'); }); paint(); card();
  });
  var tip = $('sa-tip'), box = map.parentNode;
  function showTip(e) {
    var k = e.target.getAttribute && e.target.getAttribute('data-r'); if (!k || e.pointerType === 'touch') { tip.hidden = true; return; }
    tip.innerHTML = '<b>' + esc(REG[k].n) + '</b>' + z(REG[k].v[M]) + ' ' + META.met[M][2]; tip.hidden = false;
    var r = box.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top, w = tip.offsetWidth;
    tip.style.transform = 'translate(' + Math.round(Math.min(r.width - w, Math.max(0, x - w / 2))) + 'px,' + Math.round(y - 52) + 'px)';
  }
  map.addEventListener('pointermove', showTip);
  map.addEventListener('pointerleave', function () { tip.hidden = true; });
  map.addEventListener('click', function (e) { var k = e.target.getAttribute('data-r'); if (k) { select(k); $('sa-plz').value = ''; } });
  var inp = $('sa-plz');
  inp.addEventListener('input', function () {
    var k = regOf(this.value);
    if (k && !select(k)) card('Zu dieser Postleitzahl haben wir keine Region. Prüf die ersten zwei Ziffern.');
  });
  $('sa-form').addEventListener('submit', function (e) {
    if (!/^\d{5}$/.test(inp.value.trim())) { e.preventDefault(); card('Für den Planer brauchen wir alle fünf Ziffern deiner Postleitzahl.'); inp.focus(); }
  });
  paint();
})();
