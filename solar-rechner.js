/* Strom-Daheim: Solar-Rechner fürs Dach. Nutzt den Rechenkern BKW aus bkw-planer.js (Sonne, Module, Haushalt, Speicher)
   und ergänzt E-Auto und Wärmepumpe als zusätzliche Last. Annahmen stehen im Abschnitt #annahmen der Seite: bei Änderungen beides anpassen.
   Kern für Tests: window.SR (extra, config, result). */
(function () {
  'use strict';
  var d = document, $ = function (id) { return d.getElementById(id); }, BKW = window.BKW;
  if (!$('sr-plz') || !BKW) return;
  var REG = '01 02 03 04 06 07 08 09 10 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86 87 88 89 90 91 92 93 94 95 96 97 98 99'.split(' ');
  var DEF_REG = '34', KEY = 'sdsr', NS = 'http://www.w3.org/2000/svg';
  var SHADE = [{ horizon: 0, sky: 1 }, { horizon: 15, sky: 0.9 }, { horizon: 28, sky: 0.75 }], PRES = ['weg', 'teils', 'viel'];
  var MO = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez'];
  var P_KWP = 1200, P_BAT = 500;                 /* Euro je kWp und je kWh Speicher, wenn kein Angebot eingetragen ist */
  var WP_HEAT = 0.85, T_LIMIT = 15, T_NIGHT = 2; /* Wärmepumpe: Anteil Heizen, Heizgrenze in °C, Abzug für die Nacht vom Mittel der Tagstunden */
  var DEF = { plz: '', kwp: 8, dir: 0, tilt: 35, shade: 0, kwh: 3500, pres: 1, ev: 0, km: 12000, vb: 18, em: 0, wp: 0, wpk: 4000, bat: 0, ct: 37, fit: 7.7, cost: null };
  var S = {}, k; for (k in DEF) S[k] = DEF[k];
  var cache = {}, data = null, reg = null, raf = 0, last = null;

  function lim(v, a, b, def) { v = +v; return isFinite(v) ? Math.min(b, Math.max(a, v)) : def; }
  function num(v) { var t = String(v).trim().replace(/\s|€|kWh|kWp|km|ct|°/gi, ''); if (t.indexOf(',') > -1) t = t.replace(/\./g, '').replace(',', '.'); else if (/^\d{1,3}(\.\d{3})+$/.test(t)) t = t.replace(/\./g, ''); return parseFloat(t); }
  function f(n, dg) { return n.toLocaleString('de-DE', { minimumFractionDigits: dg || 0, maximumFractionDigits: dg || 0 }); }
  function r10(n) { return Math.round(n / 10) * 10; }

  /* Zusätzliche Last je Stunde in Watt: Wärmepumpe nach Außentemperatur, E-Auto nach Ladefenster */
  function extra(data, s) {
    if (!s.ev && !s.wp) return null;
    var x = new Float32Array(8760), h, day;
    if (s.wp && s.wpk > 0) {
      var w = new Float32Array(365), sum = 0, lastT = 5;
      for (day = 0; day < 365; day++) {
        var t = 0, n = 0; for (h = 0; h < 24; h++) if (data.g[day * 24 + h] > 0) { t += data.t[day * 24 + h]; n++; }
        if (n) lastT = t / n; w[day] = Math.max(0, T_LIMIT - (lastT - T_NIGHT)); sum += w[day];
      }
      var heat = s.wpk * 1000 * WP_HEAT, ww = s.wpk * 1000 * (1 - WP_HEAT) / 8760;
      for (h = 0; h < 8760; h++) x[h] += ww + (sum ? heat * w[Math.floor(h / 24)] / sum / 24 : heat / 8760);
    }
    if (s.ev && s.km > 0) {
      var perDay = s.km * s.vb / 100 * 1000 / 365, a = s.em ? 10 : 18, b = s.em ? 16 : 22;
      for (h = 0; h < 8760; h++) { var lh = BKW.localHour(h); if (lh >= a && lh < b) x[h] += perDay / (b - a); }
    }
    return x;
  }
  function groups(s) { var wp = s.kwp * 1000; return s.dir === 'ow' ? [{ wp: wp / 2, tilt: s.tilt, azim: -90 }, { wp: wp / 2, tilt: s.tilt, azim: 90 }] : [{ wp: wp, tilt: s.tilt, azim: +s.dir }]; }
  function config(data, s, bat) { return { groups: groups(s), shade: SHADE[s.shade], cap: s.kwp * 1000, kwh: s.kwh, presence: PRES[s.pres], bat: bat > 0 ? { kwh: bat, sensor: true } : null, extra: extra(data, s) }; }
  function autoCost(s, bat) { return Math.round((s.kwp * P_KWP + bat * P_BAT) / 100) * 100; }
  function result(data, s, bat) {
    var r = BKW.simulate(data, config(data, s, bat)), y = r.y, cost = s.cost != null && bat === s.bat ? s.cost : autoCost(s, bat);
    var nutzen = y.saved * s.ct / 100 + y.feed * s.fit / 100;
    return { y: y, m: r.m, cost: cost, nutzen: nutzen, pay: nutzen > 0 ? cost / nutzen : Infinity, autark: y.load > 0 ? y.saved / y.load : 0, share: y.pv > 0 ? y.self / y.pv : 0 };
  }
  /* Durchschnittstag eines Monats (0 = Januar): je Ortsstunde die mittlere Leistung in Watt. gen = Solarstrom am Wechselrichter, direct = davon sofort im Haus genutzt,
     load = Verbrauch, bat = aus dem Speicher, soc = Füllstand in Prozent, feed = ins Netz, grid = aus dem Netz. */
  var MD = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  function day(data, s, bat, month) {
    var c = config(data, s, bat); c.keep = true;
    var r = BKW.simulate(data, c).hourly, h0 = 0, i, k, n = [], o = { gen: [], direct: [], load: [], bat: [], soc: [], feed: [], grid: [] }, cap = bat > 0 ? bat * 1000 * 0.9 : 0;
    for (i = 0; i < month; i++) h0 += MD[i] * 24;
    for (k = 0; k < 24; k++) { n.push(0); for (i in o) o[i].push(0); }
    for (i = h0; i < h0 + MD[month] * 24; i++) {
      k = Math.floor(BKW.localHour(i)) % 24; if (k < 0) k += 24; n[k]++;
      o.gen[k] += r.gen[i]; o.direct[k] += r.self[i] - r.bat[i]; o.load[k] += r.load[i]; o.bat[k] += r.bat[i]; o.soc[k] += cap ? r.soc[i] / cap * 100 : 0;
      o.feed[k] += r.pv[i] - r.self[i]; o.grid[k] += Math.max(0, r.load[i] - r.self[i]);
    }
    for (k = 0; k < 24; k++) for (i in o) o[i][k] = n[k] ? o[i][k] / n[k] : 0;
    return o;
  }
  window.SR = { extra: extra, config: config, result: result, autoCost: autoCost, day: day, state: function () { return S; } };

  /* ---------- Daten ---------- */
  function regOf(plz) { var r = (plz || '').slice(0, 2); if (r === '11') r = '10'; return REG.indexOf(r) >= 0 ? r : null; }
  function load(r, cb) {
    if (cache[r]) return cb(cache[r]);
    fetch('/assets/pv/' + r + '.json').then(function (q) { if (!q.ok) throw 0; return q.json(); }).then(function (j) { cache[r] = BKW.decode(j); cb(cache[r]); }).catch(function () { regMsg('Die Sonnendaten konnten nicht geladen werden. Bitte lade die Seite neu.', true); });
  }
  function regMsg(t, bad) { var p = $('sr-reg'); p.textContent = t; p.classList.toggle('bad', !!bad); }

  /* ---------- Oberfläche ---------- */
  var FIELDS = [['sr-kwp', 'kwp', 3, 30, 1], ['sr-tilt', 'tilt', 5, 60, 0], ['sr-kwh', 'kwh', 1500, 9000, 0], ['sr-km', 'km', 1000, 60000, 0], ['sr-vb', 'vb', 10, 35, 1], ['sr-wpk', 'wpk', 500, 15000, 0], ['sr-ct', 'ct', 10, 80, 1], ['sr-fit', 'fit', 0, 20, 1]];
  function show(key, dg) { var v = S[key]; return dg ? String(Math.round(v * 10) / 10).replace('.', ',') : f(v); }
  function press(id, val) { [].forEach.call($(id).querySelectorAll('button'), function (b) { b.setAttribute('aria-pressed', String(b.getAttribute('data-v')) === String(val) ? 'true' : 'false'); }); }
  function sync(skip) {
    FIELDS.forEach(function (F) { if (F[0] !== skip) $(F[0]).value = show(F[1], F[4]); var r = $(F[0] + '-r'); if (r) r.value = S[F[1]]; });
    if (skip !== 'sr-plz') $('sr-plz').value = S.plz;
    if (skip !== 'sr-cost') $('sr-cost').value = f(S.cost != null ? S.cost : autoCost(S, S.bat));
    $('sr-cost-t').textContent = S.cost != null ? 'dein Preis laut Angebot' : 'geschätzt: 1.200 € je kWp' + (S.bat ? ' und 500 € je kWh Speicher' : '');
    press('sr-dir', S.dir); press('sr-shade', S.shade); press('sr-pres', S.pres); press('sr-bat', S.bat); press('sr-em', S.em); press('sr-fitc', S.fit);
    $('sr-ev').setAttribute('aria-checked', S.ev ? 'true' : 'false'); $('sr-ev-box').hidden = !S.ev;
    $('sr-wp').setAttribute('aria-checked', S.wp ? 'true' : 'false'); $('sr-wp-box').hidden = !S.wp;
  }
  function update() { if (!raf) raf = requestAnimationFrame(run); }
  function run() {
    raf = 0; save();
    var r = regOf(S.plz) || DEF_REG;
    if (S.plz.length === 5 && !regOf(S.plz)) regMsg('Diese Postleitzahl kennen wir nicht. Wir rechnen mit Kassel.', true);
    load(r, function (dt) {
      data = dt; reg = r;
      if (regOf(S.plz)) regMsg('Sonnendaten für ' + dt.name + ' (Postleitzahlen ' + r + '…).');
      else if (S.plz.length < 5) regMsg('Ohne Postleitzahl rechnen wir mit Kassel, etwa in der Mitte Deutschlands.');
      render();
    });
  }
  function yrs(v) { return !isFinite(v) || v > 60 ? 'nie' : f(v, v < 10 ? 1 : 0).replace(',0', '') + (Math.round(v * 10) === 10 ? ' Jahr' : ' Jahren'); }
  function render() {
    var R = result(data, S, S.bat), y = R.y; last = R;
    $('sr-pay').textContent = isFinite(R.pay) && R.pay <= 60 ? 'Nach ' + yrs(R.pay) : 'Rechnet sich so nicht';
    $('sr-pay-t').textContent = isFinite(R.pay) && R.pay <= 60 ? 'ist die Anlage bezahlt, bei ' + f(R.cost) + ' € Kosten' : 'Der Nutzen im Jahr ist zu klein für ' + f(R.cost) + ' € Kosten.';
    $('sr-hi').classList.toggle('neg', !(R.pay <= 25));
    $('sr-eur').textContent = f(r10(R.nutzen)) + ' €'; $('sr-pv').textContent = f(r10(y.pv)) + ' kWh';
    $('sr-own').textContent = f(Math.round(R.share * 100)) + ' %'; $('sr-aut').textContent = f(Math.round(R.autark * 100)) + ' %';
    $('sr-txt').textContent = 'Von ' + f(r10(y.pv)) + ' kWh Solarstrom nutzt du ' + f(r10(y.self)) + ' kWh selbst und speist ' + f(r10(y.feed)) + ' kWh ein. Dein Verbrauch liegt bei ' + f(r10(y.load)) + ' kWh im Jahr' + (S.ev || S.wp ? ', mit ' + [S.ev ? 'E-Auto' : '', S.wp ? 'Wärmepumpe' : ''].filter(Boolean).join(' und ') : '') + '. Aus dem Netz holst du noch ' + f(r10(y.load - y.saved)) + ' kWh.';
    chart(R); variants(R); dayDraw(true);
  }
  function E(n, a, p, t) { var e = d.createElementNS(NS, n); for (var q in a) e.setAttribute(q, a[q]); if (t != null) e.textContent = t; if (p) p.appendChild(e); return e; }
  /* Ein Tag mit deiner Anlage: Durchschnittstag des gewählten Monats als Verlauf, mit Abspielen und Schieber */
  var DAY = { m: 5, t: 12, d: null, play: 0, raf: 0, seen: 0, geo: null }, MN = { 5: 'Juni', 2: 'März', 11: 'Dezember' };
  function at(a, t) { var x = ((t - .2) % 24 + 24) % 24, i = Math.floor(x), j = (i + 1) % 24, u = x - i; return a[i] * (1 - u) + a[j] * u; }   /* die Messwerte gelten für etwa 10 Minuten nach der vollen Stunde */
  function kw(w) { return w >= 995 ? f(Math.round(w / 100) / 10, 1) + ' kW' : f(Math.round(w / 10) * 10) + ' W'; }
  function dayDraw(recalc) {
    var box = $('sr-day-chart'); if (!box || !data) return;
    if (recalc || !DAY.d) DAY.d = day(data, S, S.bat, DAY.m);
    var d = DAY.d, W = Math.max(280, box.clientWidth || 480), H = W < 420 ? 200 : 230, L = 40, T = 34, B = 22, pw = W - L - 6, ph = H - T - B, mx = 0, k;
    for (k = 0; k < 24; k++) mx = Math.max(mx, d.gen[k], d.load[k]);
    var step = [100, 200, 500, 1000, 2000, 5000].filter(function (s) { return mx / s <= 4; })[0] || 10000, top = Math.max(step, Math.ceil(mx / step) * step);
    var x = function (t) { return L + pw * t / 24; }, y = function (v) { return T + ph * (1 - v / top); }, svg = E('svg', { viewBox: '0 0 ' + W + ' ' + H, 'aria-hidden': 'true' }), g, t;
    for (g = 0; g <= top; g += step) { E('line', { x1: L, x2: W - 6, y1: y(g), y2: y(g), 'class': 'g' }, svg); E('text', { x: L - 5, y: y(g) + 4, 'text-anchor': 'end' }, svg, g >= 1000 ? f(g / 1000, g % 1000 ? 1 : 0) + ' kW' : f(g) + ' W'); }
    [0, 6, 12, 18, 24].forEach(function (h) { E('text', { x: x(h), y: H - 5, 'text-anchor': h === 0 ? 'start' : h === 24 ? 'end' : 'middle' }, svg, h + ' Uhr'); });
    function line(a) { var p = []; for (t = 0; t <= 24.001; t += .25) p.push(x(t).toFixed(1) + ' ' + y(Math.max(0, at(a, t))).toFixed(1)); return p; }
    function area(a) { return 'M' + x(0) + ' ' + y(0) + 'L' + line(a).join('L') + 'L' + x(24) + ' ' + y(0) + 'z'; }
    var id = 'srdc', defs = E('defs', {}, svg), cp = E('clipPath', { id: id }, defs); DAY.clip = E('rect', { x: L, y: 0, width: 0, height: H }, cp);
    /* blass: der ganze Tag; kräftig: der schon abgespielte Teil */
    var dim = E('g', { 'class': 'dim' }, svg), lit = E('g', { 'clip-path': 'url(#' + id + ')' }, svg);
    [dim, lit].forEach(function (grp) { E('path', { d: area(d.gen), 'class': 'ga' }, grp); E('path', { d: area(d.direct), 'class': 'da' }, grp); E('path', { d: 'M' + line(d.gen).join('L'), 'class': 'gl' }, grp); E('path', { d: 'M' + line(d.load).join('L'), 'class': 'l' }, grp); });
    /* Sonnenbogen über dem Diagramm: von der ersten bis zur letzten Stunde mit Ertrag */
    var up = -1, dn = -1; for (k = 0; k < 24; k++) if (d.gen[k] > 1) { if (up < 0) up = k; dn = k + 1; }
    DAY.geo = { x: x, y: y, L: L, T: T, pw: pw, up: up, dn: dn, top: top };
    if (up >= 0) E('path', { d: 'M' + x(up) + ' ' + (T - 4) + 'Q' + x((up + dn) / 2) + ' ' + (T - 52) + ' ' + x(dn) + ' ' + (T - 4), 'class': 'sunp' }, svg);
    DAY.orb = E('circle', { r: 7, 'class': 'sun' }, svg); DAY.cur = E('line', { y1: T - 2, y2: y(0), 'class': 'cur' }, svg);
    DAY.dg = E('circle', { r: 4.5, 'class': 'dot', fill: 'var(--sun)' }, svg); DAY.dl = E('circle', { r: 4.5, 'class': 'dot', fill: 'var(--sky)' }, svg);
    box.textContent = ''; box.appendChild(svg);
    var sum = function (a) { return a.reduce(function (s, v) { return s + v; }, 0) / 1000; };
    $('sr-day-sub').textContent = 'Durchschnittstag im ' + MN[DAY.m] + ': ' + f(sum(d.gen), 1) + ' kWh vom Dach, ' + f(sum(d.load), 1) + ' kWh Verbrauch, ' + f(sum(d.grid), 1) + ' kWh aus dem Netz.';
    box.setAttribute('aria-label', 'Durchschnittstag im ' + MN[DAY.m] + ': Solarstrom vom Dach ' + f(sum(d.gen), 1) + ' Kilowattstunden, Verbrauch ' + f(sum(d.load), 1) + ', aus dem Netz ' + f(sum(d.grid), 1) + ', ins Netz ' + f(sum(d.feed), 1) + '.');
    $('sr-d-bw').hidden = !(S.bat > 0);
    dayTime(DAY.t);
  }
  function dayTime(t) {
    var d = DAY.d, G = DAY.geo; if (!d || !G) return; DAY.t = t;
    var gen = Math.max(0, at(d.gen, t)), ld = Math.max(0, at(d.load, t)), feed = Math.max(0, at(d.feed, t)), grid = Math.max(0, at(d.grid, t)), X = G.x(Math.min(24, t));
    DAY.clip.setAttribute('width', Math.max(0, X - G.L)); DAY.cur.setAttribute('x1', X); DAY.cur.setAttribute('x2', X);
    DAY.dg.setAttribute('cx', X); DAY.dg.setAttribute('cy', G.y(gen)); DAY.dl.setAttribute('cx', X); DAY.dl.setAttribute('cy', G.y(ld));
    var sunUp = G.up >= 0 && t >= G.up && t <= G.dn, u = sunUp ? (t - G.up) / (G.dn - G.up) : 0;
    DAY.orb.setAttribute('class', sunUp ? 'sun' : 'moon'); DAY.orb.setAttribute('r', sunUp ? 7 : 5);
    DAY.orb.setAttribute('cx', sunUp ? G.x(G.up) + (G.x(G.dn) - G.x(G.up)) * u : X); DAY.orb.setAttribute('cy', sunUp ? G.T - 4 - 48 * 2 * u * (1 - u) : G.T - 16);
    var hh = Math.floor(t) % 24, mm = Math.floor((t % 1) * 60 / 15) * 15;
    $('sr-d-h').textContent = hh + ':' + (mm < 10 ? '0' : '') + mm + ' Uhr';
    $('sr-d-pv').textContent = kw(gen); $('sr-d-ld').textContent = kw(ld);
    if (feed > grid && feed >= 5) { $('sr-d-nt').textContent = kw(feed); $('sr-d-ntt').textContent = 'gehen ins Netz'; }
    else if (grid >= 5) { $('sr-d-nt').textContent = kw(grid); $('sr-d-ntt').textContent = 'kommen aus dem Netz'; }
    else { $('sr-d-nt').textContent = '0 W'; $('sr-d-ntt').textContent = 'Netz: nichts nötig'; }
    if (S.bat > 0) { var sc = Math.max(0, Math.min(100, at(d.soc, t))); $('sr-d-bt').textContent = f(Math.round(sc)) + ' %'; $('sr-d-bb').style.width = sc + '%'; }
    var rg = $('sr-day-t'); if (document.activeElement !== rg || DAY.play) rg.value = Math.min(24, t);
    rg.setAttribute('aria-valuetext', $('sr-d-h').textContent + ': Dach ' + kw(gen) + ', Verbrauch ' + kw(ld));
  }
  function dayPlay(on) {
    DAY.play = on ? 1 : 0; cancelAnimationFrame(DAY.raf);
    var b = $('sr-day-play'); b.setAttribute('aria-pressed', on ? 'true' : 'false'); b.querySelector('span').textContent = on ? 'Anhalten' : 'Abspielen';
    if (!on) return;
    if (DAY.t >= 23.95) DAY.t = 0;
    var t0 = performance.now(), s0 = DAY.t;
    (function step(now) { var t = s0 + (now - t0) / 1000 * 24 / 10; if (t >= 24) { dayTime(24); dayPlay(false); return; } dayTime(t); DAY.raf = requestAnimationFrame(step); })(t0);
  }
  function dayInit() {
    if (!$('sr-day')) return;
    $('sr-day-m').onclick = function (e) { var b = e.target.closest('button'); if (!b) return; DAY.m = +b.dataset.m; [].forEach.call(this.children, function (c) { c.setAttribute('aria-pressed', c === b ? 'true' : 'false'); }); dayDraw(true); };
    $('sr-day-play').onclick = function () { DAY.seen = 1; dayPlay(!DAY.play); };
    $('sr-day-t').oninput = function () { DAY.seen = 1; if (DAY.play) dayPlay(false); dayTime(+this.value); };
    var rz; window.addEventListener('resize', function () { clearTimeout(rz); rz = setTimeout(function () { dayDraw(false); }, 150); });
    if ('IntersectionObserver' in window && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
      var io = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting && !DAY.seen && DAY.d) { DAY.seen = 1; io.disconnect(); DAY.t = 4; dayPlay(true); } }); }, { threshold: .6 });
      io.observe($('sr-day-chart'));
    }
  }

  function chart(R) {
    var box = $('sr-chart'), W = Math.max(300, box.clientWidth || 520), H = W < 480 ? 220 : 260, L = 36, T = 12, B = 24, pw = W - L - 4, ph = H - T - B, mx = 0, i;
    for (i = 0; i < 12; i++) mx = Math.max(mx, R.m[i].self + R.m[i].feed, R.m[i].load);
    var step = [50, 100, 200, 250, 500, 1000, 2000].filter(function (s) { return mx / s <= 5; })[0] || 5000, top = Math.ceil(mx / step) * step;
    var svg = E('svg', { viewBox: '0 0 ' + W + ' ' + H, 'aria-hidden': 'true' }), y = function (v) { return T + ph * (1 - v / top); }, bw = pw / 12, g, pts = [];
    for (g = 0; g <= top; g += step) { E('line', { x1: L, x2: W - 4, y1: y(g), y2: y(g), 'class': 'g' }, svg); E('text', { x: L - 5, y: y(g) + 4, 'text-anchor': 'end' }, svg, f(g)); }
    for (i = 0; i < 12; i++) {
      var m = R.m[i], x = L + i * bw + bw * .16, w = bw * .68, ys = y(m.self), yf = y(m.self + m.feed), r = Math.min(4, w / 2);
      if (m.self > 0) E('rect', { x: x, y: ys, width: w, height: Math.max(0, y(0) - ys), 'class': 's' }, svg);
      if (m.feed > 0) E('path', { d: 'M' + x + ' ' + (ys - 2) + 'V' + (yf + r) + 'q0 ' + (-r) + ' ' + r + ' ' + (-r) + 'h' + (w - 2 * r) + 'q' + r + ' 0 ' + r + ' ' + r + 'V' + (ys - 2) + 'z', 'class': 'f' }, svg);
      E('text', { x: x + w / 2, y: H - 7, 'text-anchor': 'middle' }, svg, bw > 30 ? MO[i] : MO[i][0]);
      pts.push([x + w / 2, y(m.load)]);
    }
    E('path', { d: 'M' + pts.map(function (p) { return p[0].toFixed(1) + ' ' + p[1].toFixed(1); }).join('L'), 'class': 'l' }, svg);
    pts.forEach(function (p) { E('circle', { cx: p[0], cy: p[1], r: 3.5, 'class': 'ld' }, svg); });
    box.textContent = ''; box.appendChild(svg);
    box.setAttribute('aria-label', 'Solarstrom und Verbrauch je Monat. Die Werte stehen in der Tabelle darunter.');
    $('sr-mt').innerHTML = '<table class="sr-var"><thead><tr><th scope="col">Monat</th><th scope="col">selbst genutzt</th><th scope="col">eingespeist</th><th scope="col">Verbrauch</th></tr></thead><tbody>' +
      R.m.map(function (m, i) { return '<tr><td>' + MO[i] + '</td><td>' + f(Math.round(m.self)) + ' kWh</td><td>' + f(Math.round(m.feed)) + ' kWh</td><td>' + f(Math.round(m.load)) + ' kWh</td></tr>'; }).join('') + '</tbody></table>';
  }
  function variants(cur) {
    $('sr-var').innerHTML = [0, 5, 10, 15].map(function (b) {
      var R = b === S.bat ? cur : result(data, S, b), is = b === S.bat;
      return '<tr' + (is ? ' class="cur"' : '') + '><td>' + (is ? (b ? b + ' kWh' : 'ohne') : '<button type="button" data-b="' + b + '">' + (b ? b + ' kWh' : 'ohne') + '</button>') + '</td><td>' + f(Math.round(R.autark * 100)) + ' %</td><td>' + f(r10(R.nutzen)) + ' €</td><td>' + f(R.cost) + ' €</td><td>' + (isFinite(R.pay) && R.pay <= 60 ? yrs(R.pay) : 'nie') + '</td></tr>';
    }).join('');
  }

  /* ---------- Speichern und Teilen ---------- */
  var MAP = { p: 'plz', k: 'kwp', d: 'dir', t: 'tilt', s: 'shade', v: 'kwh', w: 'pres', e: 'ev', km: 'km', vb: 'vb', em: 'em', h: 'wp', hk: 'wpk', b: 'bat', ct: 'ct', f: 'fit', c: 'cost' };
  function take(o) {
    if (!o) return;
    if (/^\d{5}$/.test(o.plz || '')) S.plz = o.plz;
    if (o.kwp != null) S.kwp = Math.round(lim(o.kwp, 3, 30, S.kwp) * 2) / 2;
    if (o.dir === 'ow') S.dir = 'ow'; else if (o.dir != null && o.dir !== '') S.dir = [-90, -45, 0, 45, 90].indexOf(+o.dir) >= 0 ? +o.dir : 0;
    if (o.tilt != null) S.tilt = Math.round(lim(o.tilt, 5, 60, S.tilt));
    if (o.shade != null) S.shade = Math.round(lim(o.shade, 0, 2, 0));
    if (o.kwh != null) S.kwh = Math.round(lim(o.kwh, 1500, 9000, S.kwh) / 50) * 50;
    if (o.pres != null) S.pres = Math.round(lim(o.pres, 0, 2, 1));
    if (o.ev != null) S.ev = +o.ev ? 1 : 0; if (o.km != null) S.km = Math.round(lim(o.km, 1000, 60000, S.km) / 100) * 100;
    if (o.vb != null) S.vb = Math.round(lim(o.vb, 10, 35, S.vb) * 10) / 10; if (o.em != null) S.em = +o.em ? 1 : 0;
    if (o.wp != null) S.wp = +o.wp ? 1 : 0; if (o.wpk != null) S.wpk = Math.round(lim(o.wpk, 500, 15000, S.wpk) / 50) * 50;
    if (o.bat != null) S.bat = [0, 5, 10, 15].indexOf(+o.bat) >= 0 ? +o.bat : 0;
    if (o.ct != null) S.ct = Math.round(lim(o.ct, 10, 80, S.ct) * 10) / 10; if (o.fit != null) S.fit = Math.round(lim(o.fit, 0, 20, S.fit) * 10) / 10;
    if (o.cost != null && o.cost !== '') S.cost = Math.round(lim(o.cost, 1000, 100000, 12000) / 100) * 100;
  }
  function save() { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) { } }
  function link() {
    var q = [], a; for (a in MAP) { var v = S[MAP[a]]; if (v == null || v === '' || v === DEF[MAP[a]]) continue; q.push(a + '=' + encodeURIComponent(v)); }
    return location.origin + location.pathname + (q.length ? '?' + q.join('&') : '');
  }
  function toast(t) { var e = $('sr-share'), o = e.lastChild.nodeValue; e.lastChild.nodeValue = t; setTimeout(function () { e.lastChild.nodeValue = o; }, 1800); }

  /* ---------- Start ---------- */
  try { var st = JSON.parse(localStorage.getItem(KEY) || 'null'); if (st) take(st); } catch (e) { }
  try { var sp = parseFloat(localStorage.getItem('sp')); if (isFinite(sp) && sp >= 10 && sp <= 80) S.ct = sp; } catch (e) { }
  var qs = new URLSearchParams(location.search), fromUrl = {}, any = false, a;
  for (a in MAP) if (qs.has(a)) { fromUrl[MAP[a]] = qs.get(a); any = true; }
  if (any) { for (a in MAP) if (MAP[a] !== 'plz' && MAP[a] !== 'ct') S[MAP[a]] = DEF[MAP[a]]; take(fromUrl); }
  FIELDS.forEach(function (F) {
    var el = $(F[0]), rg = $(F[0] + '-r');
    el.addEventListener('input', function () { var v = num(el.value); if (isFinite(v) && v >= F[2] && v <= F[3]) { S[F[1]] = F[4] ? Math.round(v * 10) / 10 : Math.round(v); if (F[1] === 'kwp') S.kwp = Math.round(S.kwp * 2) / 2; if (rg) rg.value = S[F[1]]; sync(F[0]); update(); } });
    el.addEventListener('change', function () { var v = num(el.value); S[F[1]] = isFinite(v) ? lim(F[4] ? Math.round(v * 10) / 10 : Math.round(v), F[2], F[3], S[F[1]]) : S[F[1]]; if (F[1] === 'kwp') S.kwp = Math.round(S.kwp * 2) / 2; sync(); update(); });
    if (rg) rg.addEventListener('input', function () { S[F[1]] = +rg.value; sync(); update(); });
  });
  $('sr-plz').addEventListener('input', function () { S.plz = this.value.replace(/\D/g, '').slice(0, 5); if (this.value !== S.plz) this.value = S.plz; if (S.plz.length === 5 || S.plz.length === 0) update(); });
  $('sr-cost').addEventListener('change', function () { var v = num(this.value); S.cost = isFinite(v) && v >= 1000 ? Math.round(lim(v, 1000, 100000, 12000)) : null; sync(); update(); });
  [['sr-dir', 'dir'], ['sr-shade', 'shade'], ['sr-pres', 'pres'], ['sr-bat', 'bat'], ['sr-em', 'em'], ['sr-fitc', 'fit']].forEach(function (c) {
    $(c[0]).addEventListener('click', function (e) { var b = e.target.closest('button'); if (!b) return; var v = b.getAttribute('data-v'); S[c[1]] = v === 'ow' ? 'ow' : +v; if (c[1] === 'bat') S.cost = null; if (c[1] === 'dir' && v === 'ow' && S.tilt > 25) S.tilt = 15; sync(); update(); });
  });
  ['ev', 'wp'].forEach(function (key) { $('sr-' + key).addEventListener('click', function () { S[key] = S[key] ? 0 : 1; sync(); update(); }); });
  $('sr-var').addEventListener('click', function (e) { var b = e.target.closest('button'); if (!b) return; S.bat = +b.getAttribute('data-b'); S.cost = null; sync(); update(); });
  $('sr-share').addEventListener('click', function () {
    var u = link(), t = last ? 'Solaranlage mit ' + String(S.kwp).replace('.', ',') + ' kWp: ' + $('sr-pay').textContent.toLowerCase() + ' bezahlt, ' + $('sr-aut').textContent + ' meines Stroms vom Dach.' : '';
    if (navigator.share) { navigator.share({ title: d.title, text: t, url: u }).catch(function () { }); return; }
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(u).then(function () { toast('Link kopiert'); }, function () { prompt('Link zum Ergebnis:', u); }); else prompt('Link zum Ergebnis:', u);
  });
  var rz; window.addEventListener('resize', function () { clearTimeout(rz); rz = setTimeout(function () { if (last) chart(last); }, 150); });
  dayInit(); sync(); update();
})();
