/* Strom-Daheim: Strompreis heute. Liest assets/strompreis.json (Börsenpreise von SMARD, geholt von werkzeuge/strompreis.py)
   und zeichnet Tagesverlauf, günstigstes Zeitfenster und Rückblick. Kein fremder Server, alles im Browser. */
(function () {
  'use strict';
  var $ = function (id) { return document.getElementById(id); };
  if (!$('sp-chart')) return;
  var NS = 'http://www.w3.org/2000/svg', MWST = 1.19;
  var WT = ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa'], WTL = ['Sonntag', 'Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag'];
  var D = null, S = { day: 0, mode: 0, dur: 2, kwh: 1, fix: 20, sel: -1 }, NOW, DAYS = [], WIN = null;

  function berlin() {
    var o = {};
    try {
      new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Berlin', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', hourCycle: 'h23' })
        .formatToParts(new Date()).forEach(function (p) { o[p.type] = p.value; });
      return { d: o.year + '-' + o.month + '-' + o.day, h: +o.hour % 24 };
    } catch (e) {
      var n = new Date();
      return { d: n.getFullYear() + '-' + ('0' + (n.getMonth() + 1)).slice(-2) + '-' + ('0' + n.getDate()).slice(-2), h: n.getHours() };
    }
  }
  function plus(d, n) { var t = new Date(Date.UTC(+d.slice(0, 4), +d.slice(5, 7) - 1, +d.slice(8, 10) + n)); return t.toISOString().slice(0, 10); }
  function wday(d) { return new Date(Date.UTC(+d.slice(0, 4), +d.slice(5, 7) - 1, +d.slice(8, 10))).getUTCDay(); }
  function dde(d) { return d.slice(8, 10) + '.' + d.slice(5, 7) + '.' + d.slice(0, 4); }
  function num(v, n) { return v.toLocaleString('de-DE', { minimumFractionDigits: n, maximumFractionDigits: n }).replace('-', '−'); }
  function parse(el, lo, hi, def) { var v = parseFloat(String(el.value).replace(',', '.')); return isFinite(v) ? Math.min(hi, Math.max(lo, v)) : def; }
  function end(v) { return S.fix + v * MWST; }
  function shown(v) { return S.mode ? end(v) : v; }
  function el(n, a, t) { var e = document.createElementNS(NS, n); for (var k in a) e.setAttribute(k, a[k]); if (t != null) e.textContent = t; return e; }
  function hh(h) { return (h % 24) + ' bis ' + ((h % 24) + 1) + ' Uhr'; }

  /* Reihe ab jetzt: restliche Stunden von heute, dazu morgen, wenn schon veröffentlicht */
  function future() {
    var out = [], t = D.tage[NOW.d] || [], m = D.tage[plus(NOW.d, 1)], i;
    for (i = NOW.h; i < 24; i++) if (t[i] != null) out.push({ day: 0, h: i, v: t[i] });
    if (m) for (i = 0; i < 24; i++) if (m[i] != null) out.push({ day: 1, h: i, v: m[i] });
    return out;
  }
  function windows(n) {
    var f = future(), best = null, worst = null, i, j, sum, ok;
    for (i = 0; i + n <= f.length; i++) {
      sum = 0; ok = true;
      for (j = 0; j < n; j++) {
        sum += f[i + j].v;
        if (j && (f[i + j].day * 24 + f[i + j].h) !== (f[i + j - 1].day * 24 + f[i + j - 1].h) + 1) ok = false;
      }
      if (!ok) continue;
      if (!best || sum / n < best.avg - 1e-9) best = { i: i, avg: sum / n, a: f[i], n: n };
      if (!worst || sum / n > worst.avg + 1e-9) worst = { i: i, avg: sum / n, a: f[i], n: n };
    }
    var first = null;
    if (f.length >= n) { sum = 0; for (j = 0; j < n; j++) sum += f[j].v; first = { avg: sum / n, a: f[0] }; }
    return { best: best, worst: worst, first: first, len: f.length };
  }
  function when(w) {
    var e = w.a.day * 24 + w.a.h + w.n, ed = Math.floor(e / 24), eh = e % 24;
    var a = (w.a.day ? 'morgen ' : 'heute ') + w.a.h + ' Uhr', b = (ed !== w.a.day ? (ed === 1 ? 'morgen ' : 'übermorgen ') : '') + eh + ' Uhr';
    return a + ' bis ' + b;
  }

  function drawChart() {
    var box = $('sp-chart'), date = DAYS[S.day], vals = (D.tage[date] || []).slice(0, 24), old = box.querySelector('svg');
    if (old) box.removeChild(old);
    var W = Math.max(300, box.clientWidth || 720), H = W < 520 ? 230 : 300, L = 34, R = 4, T = 26, B = 26, pw = W - L - R, ph = H - T - B;
    var v = vals.map(function (x) { return x == null ? null : shown(x); }), real = v.filter(function (x) { return x != null; });
    var hi = Math.max.apply(null, real.concat([1])), lo = Math.min.apply(null, real.concat([0]));
    var step = [0.5, 1, 2, 5, 10, 20, 50].filter(function (s) { return (hi - lo) / s <= 6; })[0] || 100;
    hi = Math.ceil(hi / step) * step; lo = Math.floor(lo / step) * step;
    var y = function (x) { return T + ph * (1 - (x - lo) / (hi - lo)); }, bw = pw / 24, svg = el('svg', { viewBox: '0 0 ' + W + ' ' + H, 'aria-hidden': 'true' }), g, i;
    for (g = lo; g <= hi + 1e-9; g += step) {
      svg.appendChild(el('line', { x1: L, x2: W - R, y1: y(g), y2: y(g), 'class': Math.abs(g) < 1e-9 ? 'z' : 'g' }));
      svg.appendChild(el('text', { x: L - 6, y: y(g) + 4, 'text-anchor': 'end' }, num(g, step < 1 ? 1 : 0)));
    }
    svg.appendChild(el('text', { x: L - 6, y: 12, 'text-anchor': 'end' }, 'ct'));
    var sorted = vals.filter(function (x) { return x != null; }).sort(function (a, b) { return a - b; });
    var t1 = sorted[Math.floor(sorted.length / 3)], t2 = sorted[Math.floor(sorted.length * 2 / 3)];
    var isToday = date === NOW.d, minI = -1, maxI = -1;
    vals.forEach(function (x, k) { if (x == null) return; if (minI < 0 || x < vals[minI]) minI = k; if (maxI < 0 || x > vals[maxI]) maxI = k; });
    var ws = WIN ? WIN.a.day * 24 + WIN.a.h : -1, we = WIN ? ws + WIN.n : -1, off = S.day * 24;
    if (WIN && isFinite(ws) && we > off && ws < off + 24 && DAYS[0] === NOW.d) {
      var a = Math.max(ws, off) - off, b = Math.min(we, off + 24) - off;
      svg.appendChild(el('rect', { x: L + a * bw + 1, y: T - 8, width: (b - a) * bw - 2, height: ph + 12, rx: 6, 'class': 'win' }));
    }
    for (i = 0; i < 24; i++) {
      if (v[i] == null) continue;
      var y0 = y(Math.max(0, lo)), y1 = y(v[i]), top = Math.min(y0, y1), h = Math.max(2, Math.abs(y1 - y0));
      var c = 'b' + (vals[i] < t1 ? ' lo' : vals[i] >= t2 ? ' hi' : '') + (isToday && i < NOW.h ? ' off' : '') + (i === S.sel ? ' sel' : '');
      var r = Math.min(4, (bw - 3) / 2), x = L + i * bw + 1.5, w = bw - 3, up = v[i] >= 0;
      var d = up ? 'M' + x + ' ' + (top + h) + 'V' + (top + r) + 'q0 ' + (-r) + ' ' + r + ' ' + (-r) + 'h' + (w - 2 * r) + 'q' + r + ' 0 ' + r + ' ' + r + 'V' + (top + h) + 'z'
        : 'M' + x + ' ' + top + 'V' + (top + h - r) + 'q0 ' + r + ' ' + r + ' ' + r + 'h' + (w - 2 * r) + 'q' + r + ' 0 ' + r + ' ' + (-r) + 'V' + top + 'z';
      svg.appendChild(el('path', { d: d, 'class': c }));
      if (i === minI || i === maxI) svg.appendChild(el('text', { x: x + w / 2, y: (up ? top : top + h + 14) - 5, 'text-anchor': i < 2 ? 'start' : i > 21 ? 'end' : 'middle', 'class': 'lab' }, num(v[i], 1)));
      if (isToday && i === NOW.h) {
        svg.appendChild(el('path', { d: 'M' + (x + w / 2 - 5) + ' ' + (H - B + 3) + 'l5 -6l5 6z', 'class': 'now' }));
      }
    }
    for (i = 0; i < 24; i += 3) svg.appendChild(el('text', { x: L + i * bw + bw / 2, y: H - 6, 'text-anchor': 'middle', 'class': isToday && i === NOW.h ? 'nowt' : '' }, bw > 26 ? i + ' Uhr' : String(i)));
    box.insertBefore(svg, box.firstChild);
    box._geo = { L: L, bw: bw, W: W, vals: vals, date: date };
  }

  function tip(i, px) {
    var box = $('sp-chart'), t = $('sp-tip'), g = box._geo;
    if (!g || i < 0 || i > 23 || g.vals[i] == null) { t.classList.remove('on'); S.sel = -1; return; }
    if (S.sel !== i) { S.sel = i; drawChart(); g = box._geo; }
    t.innerHTML = '<b>' + hh(i) + '</b>Börse ' + num(g.vals[i], 1) + ' ct · Endpreis ' + num(end(g.vals[i]), 1) + ' ct';
    var w = box.clientWidth, x = (g.L + (i + .5) * g.bw) / g.W * w, tw = t.offsetWidth;
    t.style.transform = 'translate(' + Math.round(Math.min(w - tw - 2, Math.max(2, x - tw / 2))) + 'px,-4px)';
    t.classList.add('on');
  }
  function hourAt(ev) {
    var box = $('sp-chart'), g = box._geo, r = box.getBoundingClientRect();
    return Math.floor(((ev.clientX - r.left) / r.width * g.W - g.L) / g.bw);
  }

  function drawTable() {
    var date = DAYS[S.day], vals = D.tage[date] || [], h = '<table><thead><tr><th scope="col">Stunde</th><th scope="col">Börsenpreis</th><th scope="col">Endpreis</th></tr></thead><tbody>';
    for (var i = 0; i < 24; i++) if (vals[i] != null) h += '<tr' + (date === NOW.d && i === NOW.h ? ' class="cur"' : '') + '><td>' + hh(i) + '</td><td>' + num(vals[i], 1) + ' ct</td><td>' + num(end(vals[i]), 1) + ' ct</td></tr>';
    $('sp-tbl').innerHTML = h + '</tbody></table>';
  }

  function drawWeek() {
    var keys = Object.keys(D.tage).sort().filter(function (k) { return k <= NOW.d; }).slice(-9), max = 0, rows = keys.map(function (k) {
      var a = D.tage[k].filter(function (x) { return x != null; }), m = a.reduce(function (s, x) { return s + x; }, 0) / a.length;
      max = Math.max(max, m); return { k: k, m: m };
    });
    $('sp-wk').style.gridTemplateColumns = 'repeat(' + rows.length + ',1fr)';
    $('sp-wk').innerHTML = rows.map(function (r) {
      return '<div' + (r.k === NOW.d ? ' class="t"' : '') + '><b>' + num(r.m, 1) + '</b><i style="height:' + Math.max(3, Math.round(r.m / max * 68)) + '%"></i><span>' + (r.k === NOW.d ? 'heute' : WT[wday(r.k)] + ' ' + r.k.slice(8, 10) + '.') + '</span></div>';
    }).join('');
    $('sp-wk').setAttribute('aria-label', 'Durchschnittlicher Börsenpreis je Tag: ' + rows.map(function (r) { return dde(r.k) + ' ' + num(r.m, 1) + ' Cent'; }).join(', '));
  }

  function drawHero() {
    var t = D.tage[NOW.d], v = t && t[NOW.h];
    if (v == null) return;
    $('sp-date').textContent = WTL[wday(NOW.d)] + ', ' + dde(NOW.d);
    $('sp-now-v').textContent = num(v, 1);
    $('sp-now-h').textContent = 'jetzt, ' + hh(NOW.h) + ' · mit festem Teil rund ' + num(end(v), 0) + ' ct';
    var s = t.filter(function (x) { return x != null; }).sort(function (a, b) { return a - b; }), t1 = s[Math.floor(s.length / 3)], t2 = s[Math.floor(s.length * 2 / 3)];
    var p = $('sp-pill'), k = v < t1 ? 'lo' : v >= t2 ? 'hi' : '';
    p.className = 'sp-pill ' + k;
    p.lastChild.textContent = k === 'lo' ? 'Gerade günstig für heute' : k === 'hi' ? 'Gerade teuer für heute' : 'Gerade im Mittelfeld für heute';
  }

  function calc() {
    S.kwh = parse($('sp-kwh'), 0.1, 200, 1); S.fix = parse($('sp-fix'), 0, 80, 20);
    try { localStorage.setItem('spfix', String(S.fix)); } catch (e) { }
    var w = windows(S.dur), b = w.best;
    WIN = null;
    if (!b) {
      $('sp-r-win').textContent = 'Zu spät für heute'; $('sp-r-wt').textContent = 'Für ' + S.dur + ' Stunden am Stück reichen die bekannten Preise nicht mehr. Am Nachmittag kommen die Preise für morgen.';
      ['p', 'max', 'eur', 'now'].forEach(function (k) { $('sp-r-' + k).textContent = '–'; });
      return;
    }
    b.n = S.dur; w.worst.n = S.dur; WIN = b;
    $('sp-r-win').textContent = when(b).replace(/^./, function (c) { return c.toUpperCase(); });
    $('sp-r-wt').textContent = 'günstigstes Zeitfenster für ' + S.dur + (S.dur === 1 ? ' Stunde' : ' Stunden') + (w.len > 24 - NOW.h ? ', heute und morgen geprüft' : ', bis Mitternacht geprüft');
    $('sp-r-p').textContent = num(end(b.avg), 1) + ' ct'; $('sp-r-pt').textContent = 'Endpreis pro kWh im Fenster (Börse ' + num(b.avg, 1) + ' ct)';
    $('sp-r-max').textContent = num(end(w.worst.avg), 1) + ' ct'; $('sp-r-maxt').textContent = 'im teuersten Fenster, ' + when(w.worst);
    var diff = (w.worst.avg - b.avg) * MWST * S.kwh / 100;
    $('sp-r-eur').textContent = num(diff, 2) + ' €'; $('sp-r-eurt').textContent = 'Unterschied zwischen bestem und teuerstem Fenster bei ' + num(S.kwh, S.kwh % 1 ? 1 : 0) + ' kWh';
    var dn = (w.first.avg - b.avg) * MWST * S.kwh / 100;
    $('sp-r-now').textContent = dn < 0.005 ? 'Jetzt starten' : num(dn, 2) + ' €';
    $('sp-r-nowt').textContent = dn < 0.005 ? 'Das günstigste Fenster beginnt jetzt.' : 'sparst du gegenüber sofort starten';
  }

  function render() {
    calc(); drawChart(); drawTable();
    var date = DAYS[S.day], stale = DAYS[0] !== NOW.d;
    $('sp-msg').textContent = stale ? 'Für heute liegen noch keine Preise vor. Du siehst die letzten verfügbaren Werte vom ' + dde(date) + '.'
      : (S.mode ? 'Endpreis = ' + num(S.fix, 1) + ' ct fester Teil + Börsenpreis mit Mehrwertsteuer. ' : '') + (WTL[wday(date)] + ', ' + dde(date)) + '. Stand der Daten: ' + D.stand.slice(11) + ' Uhr.';
  }

  function press(ids, on) { ids.forEach(function (id, i) { $(id).setAttribute('aria-pressed', i === on ? 'true' : 'false'); }); }

  function start(data) {
    D = data; NOW = berlin();
    var keys = Object.keys(D.tage).sort(), tom = plus(NOW.d, 1);
    DAYS = D.tage[NOW.d] ? [NOW.d] : [keys[keys.length - 1]];
    if (D.tage[NOW.d] && D.tage[tom]) { DAYS.push(tom); $('sp-t1').disabled = false; }
    else $('sp-t1').title = 'Die Preise für morgen kommen am Nachmittag.';
    try { var f = parseFloat(localStorage.getItem('spfix')); if (isFinite(f)) { S.fix = f; $('sp-fix').value = String(f).replace('.', ','); } } catch (e) { }
    if (D.tage[NOW.d]) drawHero(); else { $('sp-now').hidden = true; $('sp-pill').hidden = true; }
    drawWeek(); render();
    $('sp-t0').onclick = function () { S.day = 0; S.sel = -1; press(['sp-t0', 'sp-t1'], 0); render(); };
    $('sp-t1').onclick = function () { if (DAYS[1]) { S.day = 1; S.sel = -1; press(['sp-t0', 'sp-t1'], 1); render(); } };
    $('sp-m0').onclick = function () { S.mode = 0; press(['sp-m0', 'sp-m1'], 0); render(); };
    $('sp-m1').onclick = function () { S.mode = 1; press(['sp-m0', 'sp-m1'], 1); render(); };
    $('sp-dur').onclick = function (e) {
      var b = e.target.closest('button'); if (!b) return; S.dur = +b.dataset.h;
      [].forEach.call(this.children, function (c) { c.setAttribute('aria-pressed', c === b ? 'true' : 'false'); });
      render();
      if (WIN && DAYS[WIN.a.day] && WIN.a.day !== S.day) { S.day = WIN.a.day; press(['sp-t0', 'sp-t1'], S.day); render(); }
    };
    $('sp-kwhc').onclick = function (e) { var b = e.target.closest('button'); if (!b) return; $('sp-kwh').value = b.dataset.k; render(); };
    $('sp-kwh').oninput = render; $('sp-fix').oninput = function () { render(); if (D.tage[NOW.d]) drawHero(); };
    var box = $('sp-chart');
    box.addEventListener('pointermove', function (e) { tip(hourAt(e)); });
    box.addEventListener('pointerdown', function (e) { tip(hourAt(e)); });
    box.addEventListener('pointerleave', function (e) { if (e.pointerType === 'mouse') { $('sp-tip').classList.remove('on'); S.sel = -1; drawChart(); } });
    box.addEventListener('keydown', function (e) {
      var d = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0; if (!d) return;
      e.preventDefault(); tip(Math.min(23, Math.max(0, (S.sel < 0 ? (DAYS[S.day] === NOW.d ? NOW.h : 0) - d : S.sel) + d)));
    });
    box.addEventListener('blur', function () { $('sp-tip').classList.remove('on'); S.sel = -1; drawChart(); });
    var rz; window.addEventListener('resize', function () { clearTimeout(rz); rz = setTimeout(drawChart, 150); });
    /* zur vollen Stunde und beim Zurückkehren neu zeichnen */
    setInterval(function () { var n = berlin(); if (n.h !== NOW.h || n.d !== NOW.d) location.reload(); }, 60000);
  }

  fetch('/assets/strompreis.json', { cache: 'no-cache' }).then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(start).catch(function () {
    $('sp-msg').textContent = 'Die Preise konnten gerade nicht geladen werden. Bitte lade die Seite neu.';
  });
})();
