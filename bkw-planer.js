/* Balkonkraftwerk-Planer: Rechenkern (läuft in Node für Tests und im Browser).
   Eingabe: Stundenwerte eines typischen Jahres (GHI, DHI, Lufttemperatur) aus PVGIS, Ort, Modulgruppen, Wechselrichter, Speicher, Haushalt.
   Ausgabe: Ertrag, Eigenverbrauch, Einspeisung je Monat und als Jahressumme. */
(function (root) {
  'use strict';
  var RAD = Math.PI / 180;
  var MDAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  /* Koeffizienten für kristallines Silizium nach Huld et al. (wie PVGIS) */
  var K = [-0.017237, -0.040465, -0.004702, 0.000149, 0.000170, 0.000005];
  var AR = 0.16;                    /* Martin & Ruiz: Reflexion bei flachem Lichteinfall */
  var ALBEDO = 0.2;
  var SPEC = 1.016;                 /* spektraler Gewinn für kristallines Silizium in Mitteleuropa (PVGIS: +1,4 bis +2 %) */
  var U0 = 26.9, U1 = 6.2 * 0.78;   /* Wärmeabgabe des Moduls in W/m²K: fester Teil und Teil je m/s Wind (Faiman, frei hinterlüftet) */

  /* Sonnenstand (NOAA-Näherung). doy 1..365, utc in Stunden. Liefert cos(Zenit) und Azimut (0 = Süd, + = West) in rad. */
  function sun(doy, utc, lat, lon) {
    var g = 2 * Math.PI / 365 * (doy - 1 + (utc - 12) / 24);
    var eq = 229.18 * (0.000075 + 0.001868 * Math.cos(g) - 0.032077 * Math.sin(g) - 0.014615 * Math.cos(2 * g) - 0.040849 * Math.sin(2 * g));
    var dec = 0.006918 - 0.399912 * Math.cos(g) + 0.070257 * Math.sin(g) - 0.006758 * Math.cos(2 * g) + 0.000907 * Math.sin(2 * g) - 0.002697 * Math.cos(3 * g) + 0.00148 * Math.sin(3 * g);
    var tst = utc * 60 + eq + 4 * lon;           /* wahre Sonnenzeit in Minuten */
    var ha = (tst / 4 - 180) * RAD;
    var la = lat * RAD;
    var cz = Math.sin(la) * Math.sin(dec) + Math.cos(la) * Math.cos(dec) * Math.cos(ha);
    var sz = Math.sqrt(Math.max(0, 1 - cz * cz));
    /* Azimut von Süd, West positiv */
    var az = Math.atan2(Math.sin(ha), Math.cos(ha) * Math.sin(la) - Math.tan(dec) * Math.cos(la));
    return { cz: cz, sz: sz, az: az, i0: 1361 * (1 + 0.033 * Math.cos(2 * Math.PI * doy / 365)) };
  }

  /* Reflexionsverluste für diffuses Licht und Bodenreflexion (Martin & Ruiz) */
  function iamDiffuse(beta) {
    var c1 = 4 / (3 * Math.PI), c2 = -0.074, sb = Math.sin(beta), cb = Math.cos(beta);
    var td = sb + (Math.PI - beta - sb) / (1 + cb);
    var fd = 1 - Math.exp(-(c1 * td + c2 * td * td) / AR);
    var fg = 1;
    if (beta > 1e-3) { var tg = sb + (beta - sb) / (1 - cb); fg = 1 - Math.exp(-(c1 * tg + c2 * tg * tg) / AR); }
    return [fd, fg];
  }

  /* Vorbereitung je Ort: Sonnenstand für jede Stunde des Jahres. data: {lat, lon, off, g[8760], d[8760], t[8760]} */
  function prepare(data) {
    var n = 8760, cz = new Float32Array(n), az = new Float32Array(n), sz = new Float32Array(n), i0 = new Float32Array(n);
    for (var h = 0; h < n; h++) {
      if (data.g[h] <= 0) continue;
      var doy = Math.floor(h / 24) + 1, utc = h % 24 + (data.off || 0);
      var s = sun(doy, utc, data.lat, data.lon);
      cz[h] = s.cz; az[h] = s.az; sz[h] = s.sz; i0[h] = s.i0;
    }
    data.cz = cz; data.az = az; data.sz = sz; data.i0 = i0;
    return data;
  }

  /* Einstrahlung auf die geneigte Fläche, Stunde für Stunde.
     Himmelslicht nach Muneer (wie PVGIS/r.sun): sonnenzugewandte Flächen bekommen bei klarem Himmel mehr,
     abgewandte Flächen deutlich weniger als bei gleichmäßig hellem Himmel.
     Liefert [direkt, Himmel, Boden, cos(Einfallswinkel)] je Stunde über cb(h, B, Dsky, R, ct). */
  function plane(data, grp, opt, cb) {
    opt = opt || {};
    var beta = grp.tilt * RAD, gam = grp.azim * RAD, cosb = Math.cos(beta), sinb = Math.sin(beta);
    var iso = (1 + cosb) / 2, shape = sinb - beta * cosb - Math.PI * Math.pow(Math.sin(beta / 2), 2);
    var Fshade = iso + shape * 0.25227;
    var sinHor = Math.sin((opt.horizon || 0) * RAD), sky = opt.sky == null ? 1 : opt.sky;
    for (var h = 0; h < 8760; h++) {
      var G = data.g[h];
      if (G <= 0) continue;
      var D = Math.min(data.d[h], G), cz = data.cz[h], Bh = G - D;
      var kr = ALBEDO * (1 - cosb) / 2;
      if (cz <= 0.01) { cb(h, 0, D * Fshade * sky, D * kr, 0); continue; }
      var ct = cosb * cz + sinb * data.sz[h] * Math.cos(data.az[h] - gam);
      /* Bodenreflexion: liegt die Fläche im Eigenschatten, zählt wie bei PVGIS nur das Himmelslicht */
      var R = (ct > 0 ? G : D) * kr;
      var blocked = cz < sinHor;
      if (blocked) Bh = 0;
      var Kb = Math.min(Bh / (data.i0[h] * cz), 0.85);
      if (ct <= 0 || Bh <= 0) {
        /* Fläche im Eigenschatten oder Sonne verdeckt */
        cb(h, 0, D * (ct <= 0 ? Fshade : (iso + shape * 0.00263)) * sky, R, 0);
        continue;
      }
      var N = 0.00263 - 0.712 * Kb - 0.6883 * Kb * Kb;
      var F = iso + shape * N;
      var h0 = Math.asin(cz), rb;
      if (h0 >= 0.1) rb = ct / cz;
      else rb = sinb * Math.cos(data.az[h] - gam) / (0.1 - 0.008 * h0);
      if (rb < 0) rb = 0;
      var Dt = D * (F * (1 - Kb) * sky + Kb * rb);
      var Bt = Bh / Math.max(cz, 0.05) * ct;
      var cap = data.i0[h] * 0.9 * ct;          /* nie mehr als die Sonne außerhalb der Atmosphäre hergibt */
      if (Bt > cap) Bt = cap;
      cb(h, Bt, Dt, R, ct);
    }
  }

  /* Gleichstromleistung einer Modulgruppe für jede Stunde, in Watt.
     grp: {wp, tilt (Grad, 0 = flach, 90 = senkrecht), azim (Grad, 0 = Süd, 90 = West, -90 = Ost)}
     opt: {horizon: Grad, unter dieser Sonnenhöhe fällt kein direktes Licht aufs Modul; sky: Anteil des freien Himmels 0..1} */
  function dcPower(data, grp, opt) {
    var out = new Float32Array(8760), f = iamDiffuse(grp.tilt * RAD), fd = f[0], fg = f[1], e1 = 1 - Math.exp(-1 / AR);
    var uth = U0 + U1 * (data.wind || 2.8);
    plane(data, grp, opt, function (h, B, D, R, ct) {
      var fb = ct > 0 ? (1 - Math.exp(-ct / AR)) / e1 : 0;
      out[h] = power(B * fb + D * fd + R * fg, data.t[h], grp.wp, uth) * SPEC;
    });
    return out;
  }

  /* Modulleistung aus wirksamer Einstrahlung und Lufttemperatur */
  function power(Ge, ta, wp, uth) {
    if (Ge < 1) return 0;
    var g = Ge / 1000, tm = ta + Ge / uth, T = tm - 25, lg = Math.log(g);
    var rel = 1 + K[0] * lg + K[1] * lg * lg + T * (K[2] + K[3] * lg + K[4] * lg * lg) + K[5] * T * T;
    return rel > 0 ? wp * g * rel : 0;
  }

  /* Einstrahlung auf die Modulebene ohne Reflexions- und Modulverluste (für die Gegenprobe mit PVGIS) */
  function planeIrradiance(data, grp, opt) {
    var out = new Float32Array(8760);
    plane(data, grp, opt, function (h, B, D, R) { out[h] = B + D + R; });
    return out;
  }

  /* ---------- Haushalt ----------
     Tagesgang des Verbrauchs (Mittel = 1), Ortszeit 0 bis 23 Uhr: werktags je nach Anwesenheit, dazu Wochenende.
     Die Form lehnt sich an das Standardlastprofil für Haushalte an; „weg“ verschiebt Verbrauch in den Abend, „viel“ in den Tag. */
  var PROF = {
    weg:   [.42, .42, .42, .42, .42, .45, .9, 1.1, .7, .5, .5, .5, .5, .5, .5, .5, .7, 1.2, 1.8, 2.1, 2.0, 1.7, 1.2, .7],
    teils: [.42, .42, .42, .42, .42, .45, .8, 1.0, .9, .85, .85, .95, 1.15, 1.0, .85, .85, .9, 1.2, 1.6, 1.75, 1.65, 1.4, 1.05, .7],
    viel:  [.42, .42, .42, .42, .42, .45, .7, .95, 1.05, 1.1, 1.15, 1.3, 1.5, 1.25, 1.05, 1.0, 1.0, 1.15, 1.45, 1.5, 1.4, 1.2, .95, .65],
    we:    [.45, .45, .45, .45, .45, .45, .5, .6, .9, 1.2, 1.3, 1.4, 1.6, 1.4, 1.1, 1.0, 1.0, 1.2, 1.5, 1.5, 1.4, 1.2, 1.0, .7]
  };
  /* Anteil der starken Geräte (Herd, Wasserkocher, Waschmaschine, Spülmaschine, rund 2.000 W) am Verbrauch über der Grundlast */
  var FH = [.05, .05, .05, .05, .05, .1, .4, .5, .35, .35, .35, .5, .65, .5, .3, .3, .3, .45, .6, .55, .35, .3, .2, .1];
  var P_HIGH = 2000;

  /* Zerlegt den Jahresverbrauch in Grundlast und zwei Arten von Aktivität je Stunde.
     hh: {kwh, base (W, optional), presence: 'weg'|'teils'|'viel', shift: Geräte mit Zeitvorwahl mittags} */
  function household(hh) {
    var mean = hh.kwh / 8.76;                                   /* mittlere Leistung in W */
    var base = hh.base != null ? hh.base : Math.round(hh.kwh * 0.038);
    base = Math.min(base, mean * 0.9);
    var rest = mean - base;                                     /* mittlere Aktivität in W */
    var out = { base: base, mean: mean, mid: 300 * Math.sqrt(Math.max(hh.kwh, 500) / 2500), day: {} };
    ['wd', 'we'].forEach(function (k) {
      var p = PROF[k === 'we' ? 'we' : (hh.presence || 'teils')], m = 0, i;
      for (i = 0; i < 24; i++) m += p[i] / 24;
      var act = [], sum = 0;
      for (i = 0; i < 24; i++) { act[i] = Math.max(p[i] / m * mean - base, 0); sum += act[i] / 24; }
      var aM = [], aH = [], hs = 0;
      for (i = 0; i < 24; i++) { var a = sum > 0 ? act[i] * rest / sum : 0; aH[i] = a * FH[i]; aM[i] = a - aH[i]; hs += aH[i]; }
      if (hh.shift) {                                           /* Wasch- und Spülmaschine laufen zwischen 11 und 15 Uhr */
        var s = 0.4;
        for (i = 0; i < 24; i++) aH[i] *= 1 - s;
        for (i = 11; i < 15; i++) aH[i] += s * hs / 4;
      }
      out.day[k] = { m: aM, h: aH };
    });
    return out;
  }

  function localHour(h) {                                        /* h = Stunde des Jahres in UTC */
    var doy = Math.floor(h / 24), sommer = doy >= 87 && doy < 298;  /* Sommerzeit Ende März bis Ende Oktober */
    return (h % 24 + (sommer ? 2 : 1)) % 24;
  }
  function isWeekend(h) { var d = Math.floor((h + 1) / 24) % 7; return d >= 5; }

  /* Erwartete Last in einer Stunde als Mischung von Zuständen: [Wahrscheinlichkeit, Leistung in W] × 6 */
  function states(H, h, extraBase, buf) {
    var lh = localHour(h), d = H.day[isWeekend(h) ? 'we' : 'wd'], doy = Math.floor(h / 24);
    var season = 1 + 0.2 * Math.cos(2 * Math.PI * (doy - 10) / 365);
    var aM = d.m[lh] * season, aH = d.h[lh];
    var ph = Math.min(aH / P_HIGH, 0.95), lev = H.mid, pon = aM / lev;
    if (pon > 1) { lev *= pon; pon = 1; }
    var b = H.base + (extraBase || 0), q = 1 - ph;
    buf[0] = (1 - pon) * q; buf[1] = b;
    buf[2] = pon / 2 * q; buf[3] = b + 0.5 * lev;
    buf[4] = pon / 2 * q; buf[5] = b + 1.5 * lev;
    buf[6] = (1 - pon) * ph; buf[7] = b + P_HIGH;
    buf[8] = pon / 2 * ph; buf[9] = b + 0.5 * lev + P_HIGH;
    buf[10] = pon / 2 * ph; buf[11] = b + 1.5 * lev + P_HIGH;
    return b + aM + ph * P_HIGH;                                 /* mittlere Last */
  }

  /* ---------- Jahressimulation ----------
     cfg: {groups:[{wp,tilt,azim}], shade:{horizon,sky}, cap (W), kwh, base, presence, shift,
           bat:{kwh, sensor}, keep: Stundenwerte zurückgeben (pv = was aus der Steckdose kommt, gen = was die Module liefern,
           self = selbst genutzt, bat = davon aus dem Speicher, soc = Füllstand in Wh, load = mittlerer Verbrauch)}
     Ergebnis in kWh: y und m[12] mit pv (am Stecker nutzbar), self, feed, clip (abgeregelt), loss (Speicherverluste). */
  var DC_LOSS = 0.055, ETA_INV = 0.955;       /* Verluste vor dem Wechselrichter (Schmutz, Kabel, Toleranz) und im Wechselrichter: zusammen rund 10 % */
  var ETA_C = 0.94, ETA_D = 0.90;             /* Speicher laden und entladen (kleine Leistungen entlädt er mit schlechterem Wirkungsgrad) */
  var REG = 0.96;                             /* Regelung trifft den Verbrauch nie ganz: 4 % des Speicherstroms gehen ins Netz */
  var STANDBY = 4;                            /* Eigenverbrauch der Speicherelektronik in W, rund um die Uhr */
  function simulate(data, cfg) {
    var n = 8760, i, h, g, dc = new Float32Array(n);
    for (g = 0; g < cfg.groups.length; g++) {
      if (!(cfg.groups[g].wp > 0)) continue;
      var p = dcPower(data, cfg.groups[g], cfg.shade);
      for (h = 0; h < n; h++) dc[h] += p[h] * (1 - DC_LOSS);
    }
    var H = household(cfg), cap = cfg.cap || 800, bat = cfg.bat && cfg.bat.kwh > 0 ? cfg.bat : null;
    var C = bat ? bat.kwh * 1000 * 0.9 : 0, soc = 0, pmaxC = bat ? bat.kwh * 1000 : 0, pmaxD = bat ? Math.min(cap / ETA_INV, bat.kwh * 1000) : 0;
    var sensor = bat ? bat.sensor !== false : false, pset = bat && !sensor ? (bat.set || H.base + STANDBY) : 0;
    var buf = new Float64Array(12), M = [], mi = 0, mEnd = MDAYS[0] * 24;
    for (i = 0; i < 12; i++) M.push({ pv: 0, self: 0, feed: 0, clip: 0, loss: 0, load: 0, pot: 0 });
    var keep = cfg.keep ? { pv: new Float32Array(n), self: new Float32Array(n), load: new Float32Array(n), soc: new Float32Array(n), gen: new Float32Array(n), bat: new Float32Array(n) } : null;
    for (h = 0; h < n; h++) {
      if (h >= mEnd) { mi++; mEnd += MDAYS[mi] * 24; }
      var Pdc = dc[h], mm = M[mi], self = 0, feed = 0, clip = 0, fromBat = 0, k;
      var Lm = states(H, h, bat ? STANDBY : 0, buf);
      mm.load += Lm; mm.pot += Pdc * ETA_INV;
      if (!bat) {
        if (Pdc > 0) {
          var Pac = Math.min(Pdc * ETA_INV, cap);
          for (k = 0; k < 12; k += 2) self += buf[k] * Math.min(Pac, buf[k + 1]);
          feed = Pac - self; clip = Pdc * ETA_INV - Pac;
        }
      } else if (sensor) {
        /* Speicher regelt nach dem Zähler: Solarstrom deckt erst den Verbrauch, der Rest lädt den Akku, erst der volle Akku speist ein */
        var PacMax = Math.min(Pdc * ETA_INV, cap), direct = 0, deficit = 0;
        for (k = 0; k < 12; k += 2) { var L = buf[k + 1], dir = Math.min(PacMax, L); direct += buf[k] * dir; deficit += buf[k] * (Math.min(L, cap) - dir); }
        var surplus = Pdc - direct / ETA_INV; if (surplus < 0) surplus = 0;
        var chg = Math.min(surplus, pmaxC, (C - soc) / ETA_C); if (chg < 0) chg = 0;
        soc += chg * ETA_C;
        var dis = Math.min(deficit / (ETA_D * ETA_INV * REG), soc, pmaxD); if (dis < 0) dis = 0;
        soc -= dis;
        var out = dis * ETA_D * ETA_INV, left = surplus - chg;
        feed = Math.max(0, Math.min(left * ETA_INV, cap - direct));
        clip = left * ETA_INV - feed;
        self = direct + out * REG; feed += out * (1 - REG); fromBat = out * REG;
      } else {
        /* Speicher ohne Messgerät: gibt rund um die Uhr eine feste Leistung ab (hier die Grundlast) */
        var pv = Math.min(Pdc * ETA_INV, cap), outAc;
        if (pv >= pset) {
          var sp = Pdc - pset / ETA_INV, ch = Math.min(sp, pmaxC, (C - soc) / ETA_C); if (ch < 0) ch = 0;
          soc += ch * ETA_C;
          var extra = Math.max(0, Math.min((sp - ch) * ETA_INV, cap - pset));
          outAc = pset + extra; clip = (sp - ch) * ETA_INV - extra;
        } else {
          var di = Math.min((pset - pv) / (ETA_D * ETA_INV), soc, pmaxD); if (di < 0) di = 0;
          soc -= di; outAc = pv + di * ETA_D * ETA_INV;
        }
        for (k = 0; k < 12; k += 2) self += buf[k] * Math.min(outAc, buf[k + 1]);
        feed = outAc - self; if (outAc > pv) fromBat = self * (outAc - pv) / outAc;
      }
      mm.self += self; mm.feed += feed; mm.clip += clip; mm.pv += self + feed;
      if (keep) { keep.pv[h] = self + feed; keep.self[h] = self; keep.load[h] = Lm; keep.soc[h] = soc; keep.gen[h] = Pdc * ETA_INV; keep.bat[h] = fromBat; }
    }
    var y = { pv: 0, self: 0, feed: 0, clip: 0, loss: 0, load: 0, pot: 0 };
    for (i = 0; i < 12; i++) {
      M[i].loss = Math.max(0, M[i].pot - M[i].self - M[i].feed - M[i].clip);
      for (var key in y) { M[i][key] /= 1000; y[key] += M[i][key]; }
    }
    y.standby = bat ? STANDBY * 8.76 : 0;
    y.saved = y.self - y.standby;                 /* kWh, die du weniger aus dem Netz holst */
    y.share = y.pv > 0 ? y.self / y.pv : 0;       /* Anteil des Solarstroms, den du selbst nutzt */
    y.autark = y.saved / cfg.kwh;                 /* Anteil deines Verbrauchs, den die Anlage deckt */
    return { y: y, m: M, base: H.base, hourly: keep, dc: cfg.keep ? dc : null };
  }

  /* Daten eines Ortes aus der Datei (drei Base64-Felder mit je 8760 Bytes) entpacken */
  function decode(file) {
    function bytes(b64) {
      if (typeof atob === 'function') { var s = atob(b64), a = new Uint8Array(s.length); for (var i = 0; i < s.length; i++) a[i] = s.charCodeAt(i); return a; }
      return new Uint8Array(Buffer.from(b64, 'base64'));
    }
    var G = bytes(file.g), F = bytes(file.f), T = bytes(file.t), n = 8760;
    var g = new Float32Array(n), d = new Float32Array(n), t = new Float32Array(n);
    for (var h = 0; h < n; h++) {
      if (!G[h]) continue;
      var v = G[h] / 7.5; g[h] = v * v; d[h] = g[h] * F[h] / 255; t[h] = T[h] / 2 - 30;
    }
    return prepare({ lat: file.lat, lon: file.lon, off: file.off, wind: file.w, g: g, d: d, t: t, name: file.name, ghi: file.ghi, plz: file.plz });
  }

  root.BKW = { sun: sun, prepare: prepare, dcPower: dcPower, planeIrradiance: planeIrradiance, power: power, household: household, states: states, simulate: simulate, decode: decode, localHour: localHour, isWeekend: isWeekend, MDAYS: MDAYS };
})(typeof module !== 'undefined' ? module.exports : window);

/* ================= Oberfläche des Planers =================
   Liest die Eingaben, lädt die Sonnendaten der Region (assets/pv/<erste zwei Ziffern der PLZ>.json),
   rechnet mit dem Rechenkern oben und zeichnet Ergebnis, Monats- und Tagesdiagramm und den Vergleich.
   Alle Eingaben bleiben im Browser (localStorage "bkwp"); geladen wird nur die Datei der Region. */
(function () {
  'use strict';
  if (typeof document === 'undefined') return;
  var BKW = window.BKW, d = document;
  function $(id) { return d.getElementById(id); }
  if (!$('bp-plz')) return;

  var REG = '01 02 03 04 06 07 08 09 10 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86 87 88 89 90 91 92 93 94 95 96 97 98 99'.split(' ');
  var GHI_MIN = 1030, GHI_MAX = 1265, DEF_REG = '34';
  var MON = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'];
  var MO = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez'];
  var WIND = ['Norden', 'Nordosten', 'Osten', 'Südosten', 'Süden', 'Südwesten', 'Westen', 'Nordwesten'];
  var SHADE = [{ horizon: 0, sky: 1 }, { horizon: 15, sky: 0.9 }, { horizon: 28, sky: 0.75 }];
  var SHADE_TXT = ['Nichts im Weg: Die Sonne erreicht die Module den ganzen Tag.', 'Häuser oder Bäume verdecken die tief stehende Sonne, vor allem im Winter.', 'Die Sonne kommt erst hoch am Himmel über Dächer oder Bäume.'];
  var PRES = ['weg', 'teils', 'viel'];
  var YEARS = 15, PRICE_UP = 0.02, DEGR = 0.005, BAT_FADE = 0.02;   /* Strompreis +2 %, Module -0,5 %, Speicherwirkung -2 % pro Jahr */

  /* ---------- Zustand ---------- */
  var DEF = { plz: '', n: 2, wp: 450, dir: 0, tilt: 90, shade: 0, kwh: 1900, pres: 1, shift: 0, bat: 0, sensor: 1, ct: 32, cost: null, base: null, cap: 800, pmod: 125, pinv: 100, pbat: 300, pel: 200, mon: 5, sky: 1 };
  var S = {}, k;
  for (k in DEF) S[k] = DEF[k];
  function lim(v, a, b, dflt) { v = +v; return isFinite(v) ? Math.min(b, Math.max(a, v)) : dflt; }
  function take(o) {
    if (!o) return;
    if (/^\d{5}$/.test(o.plz || '')) S.plz = o.plz;
    if (o.n != null) S.n = Math.round(lim(o.n, 1, 4, S.n));
    if (o.wp != null) S.wp = Math.round(lim(o.wp, 250, 550, S.wp) / 5) * 5;
    if (o.dir === 'ow') S.dir = 'ow'; else if (o.dir != null && o.dir !== '') S.dir = Math.round(lim(o.dir, -180, 180, 0) / 5) * 5;
    if (o.tilt != null) S.tilt = Math.round(lim(o.tilt, 0, 90, S.tilt));
    if (o.shade != null) S.shade = Math.round(lim(o.shade, 0, 2, 0));
    if (o.kwh != null) S.kwh = Math.round(lim(o.kwh, 600, 9000, S.kwh) / 50) * 50;
    if (o.pres != null) S.pres = Math.round(lim(o.pres, 0, 2, 1));
    if (o.shift != null) S.shift = +o.shift ? 1 : 0;
    if (o.bat != null) S.bat = Math.round(lim(o.bat, 0, 8, 0) * 10) / 10;
    if (o.sensor != null) S.sensor = +o.sensor ? 1 : 0;
    if (o.ct != null) S.ct = lim(o.ct, 5, 150, S.ct);
    if (o.cost != null && o.cost !== '') S.cost = Math.round(lim(o.cost, 0, 20000, 0));
    if (o.base != null && o.base !== '') S.base = Math.round(lim(o.base, 0, 1500, 0));
    if (o.cap != null) S.cap = +o.cap === 600 ? 600 : 800;
    ['pmod', 'pinv', 'pbat', 'pel'].forEach(function (p) { if (o[p] != null) S[p] = Math.round(lim(o[p], 0, 5000, S[p])); });
  }
  try { take(JSON.parse(localStorage.getItem('bkwp') || 'null')); } catch (e) { }
  (function () {            /* Adresse mit Angaben (geteiltes Ergebnis) geht vor */
    var q = new URLSearchParams(location.search), o = {}, map = { p: 'plz', n: 'n', wp: 'wp', a: 'dir', t: 'tilt', s: 'shade', v: 'kwh', w: 'pres', z: 'shift', b: 'bat', m: 'sensor', ct: 'ct', k: 'cost', g: 'base', c: 'cap' }, any = 0, a;
    for (a in map) if (q.has(a)) { o[map[a]] = q.get(a); any = 1; }
    if (any) {              /* was im Link fehlt, gilt als Standard und nicht als das, was zuletzt auf diesem Gerät stand */
      for (a in map) if (map[a] !== 'plz' && map[a] !== 'ct') S[map[a]] = DEF[map[a]];
      take(o);
    }
  })();

  /* ---------- Hilfen ---------- */
  function f(n, dgt) { return n.toLocaleString('de-DE', { minimumFractionDigits: dgt || 0, maximumFractionDigits: dgt || 0 }); }
  function r10(n) { return Math.round(n / 10) * 10; }
  function num(v) {
    var s = String(v).trim().replace(/\s|€|ct|kwh|wp|w|%/gi, '');
    if (!s) return NaN;
    if (s.indexOf(',') >= 0) s = s.replace(/\./g, '').replace(',', '.'); else if (/^\d{1,3}(\.\d{3})+$/.test(s)) s = s.replace(/\./g, '');
    return /^-?\d*\.?\d+$/.test(s) ? parseFloat(s) : NaN;
  }
  function el(tag, attrs, txt) {
    var svg = /^(svg|g|rect|path|line|text|circle|title|tspan)$/.test(tag), e = svg ? d.createElementNS('http://www.w3.org/2000/svg', tag) : d.createElement(tag);
    for (var a in attrs) if (attrs[a] != null) e.setAttribute(a, attrs[a]);
    if (txt != null) e.textContent = txt;
    return e;
  }
  function dirName(az) { return WIND[Math.round((((180 + az) % 360) + 360) % 360 / 45) % 8]; }
  function dirText() {
    if (S.dir === 'ow') return S.n > 1 ? 'je zur Hälfte nach Osten und Westen' : 'nach Osten';
    return 'nach ' + dirName(S.dir);
  }
  function tiltText() { return S.tilt >= 85 ? 'senkrecht montiert' : S.tilt <= 5 ? 'flach liegend' : 'mit ' + S.tilt + ' Grad Neigung'; }
  function wpTotal(n) { return (n == null ? S.n : n) * S.wp; }
  function groups(n) {
    n = n == null ? S.n : n;
    if (S.dir === 'ow') { var a = Math.ceil(n / 2), b = n - a; return [{ wp: a * S.wp, tilt: S.tilt, azim: -90 }, { wp: b * S.wp, tilt: S.tilt, azim: 90 }]; }
    return [{ wp: n * S.wp, tilt: S.tilt, azim: S.dir }];
  }
  function costOf(n, bat) { return S.pinv + n * S.pmod + bat * S.pbat + (n * S.wp > 960 ? S.pel : 0); }
  function cfgOf(n, bat, keep) {
    return { groups: groups(n), shade: SHADE[S.shade], cap: S.cap, kwh: S.kwh, base: S.base, presence: PRES[S.pres], shift: !!S.shift, bat: bat > 0 ? { kwh: bat, sensor: !!S.sensor } : null, keep: keep };
  }
  /* Geld: Ersparnis im ersten Jahr, Jahre bis bezahlt, Gewinn nach 15 Jahren (Strompreis +2 %, Module -0,5 % pro Jahr) */
  function money(savedKwh, cost, batKwh) {
    var y1 = savedKwh * S.ct / 100, b1 = (batKwh || 0) * S.ct / 100, cum = 0, pay = Infinity, gain = -cost;
    for (var y = 0; y < 40; y++) {
      var v = ((y1 - b1) + b1 * Math.pow(1 - BAT_FADE, y)) * Math.pow(1 - DEGR, y) * Math.pow(1 + PRICE_UP, y);
      if (pay === Infinity && cum + v >= cost && v > 0) pay = y + (cost - cum) / v;
      cum += v;
      if (y === YEARS - 1) gain = cum - cost;
    }
    return { y1: y1, pay: pay, gain: gain };
  }

  /* ---------- Daten der Region ---------- */
  var cache = {}, data = null, pending = null;
  function regOf(plz) { var r = (plz || '').slice(0, 2); if (r === '11') r = '10'; return REG.indexOf(r) >= 0 ? r : null; }
  function load(reg, cb) {
    if (cache[reg]) { cb(cache[reg]); return; }
    pending = reg; root.classList.add('bp-wait');
    fetch('/assets/pv/' + reg + '.json').then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(function (j) {
      cache[reg] = BKW.decode(j);
      if (pending === reg) { pending = null; root.classList.remove('bp-wait'); cb(cache[reg]); }
    }).catch(function () { pending = null; root.classList.remove('bp-wait'); regMsg('Die Sonnendaten konnten nicht geladen werden. Prüf deine Verbindung und versuch es noch einmal.', 1); });
  }
  function regMsg(t, bad) { var p = $('bp-reg'); p.textContent = t; p.classList.toggle('bad', !!bad); }

  /* ---------- Eingaben ---------- */
  var root = $('planer'), FIELDS = {
    wp: ['bp-wp', 'bp-wp-r', 0], tilt: ['bp-tilt', 'bp-tilt-r', 0], kwh: ['bp-kwh', 'bp-kwh-r', 0], ct: ['bp-ct', 'bp-ct-r', 2], cost: ['bp-cost', 'bp-cost-r', 0],
    base: ['bp-base', null, 0], pmod: ['bp-pmod', null, 0], pinv: ['bp-pinv', null, 0], pbat: ['bp-pbat', null, 0], pel: ['bp-pel', null, 0]
  };
  function shown(key) { return key === 'cost' ? (S.cost == null ? costOf(S.n, S.bat) : S.cost) : key === 'base' ? (S.base == null ? Math.round(S.kwh * 0.038) : S.base) : S[key]; }
  function fmt(key) { var v = shown(key); return key === 'ct' ? String(Math.round(v * 100) / 100).replace('.', ',') : f(v); }
  Object.keys(FIELDS).forEach(function (key) {
    var F = FIELDS[key], inp = $(F[0]), rg = F[1] && $(F[1]);
    if (!inp) return;
    function set(v, fromField) {
      var o = {}; o[key] = v; take(o);
      if (!fromField) inp.value = fmt(key);
      update();
    }
    inp.addEventListener('input', function () { var v = num(inp.value); if (isFinite(v)) { if (rg && (v < +rg.min || v > +rg.max)) return; set(v, 1); } });
    inp.addEventListener('change', function () { var v = num(inp.value); if (isFinite(v)) set(v); else { if (key === 'cost') S.cost = null; if (key === 'base') S.base = null; inp.value = fmt(key); update(); } });
    if (rg) rg.addEventListener('input', function () { set(+rg.value); });
  });
  function chips(id, key, conv) {
    var box = $(id); if (!box) return;
    box.addEventListener('click', function (e) {
      var b = e.target.closest('button'); if (!b) return;
      var v = b.getAttribute('data-v'), o = {}; o[key] = conv ? conv(v) : v;
      if (key === 'n' || key === 'bat') S.cost = null;
      if (key === 'kwh') S.base = null;
      take(o); update();
    });
  }
  chips('bp-n', 'n'); chips('bp-dir', 'dir'); chips('bp-tiltc', 'tilt'); chips('bp-shade', 'shade'); chips('bp-kwhc', 'kwh'); chips('bp-pres', 'pres'); chips('bp-bat', 'bat'); chips('bp-cap', 'cap');
  ['bp-shift', 'bp-sensor'].forEach(function (id) { var c = $(id); if (c) c.addEventListener('change', function () { S[id === 'bp-shift' ? 'shift' : 'sensor'] = c.checked ? 1 : 0; update(); }); });
  var rs = $('bp-cost-reset'); if (rs) rs.addEventListener('click', function () { S.cost = null; update(); });
  chips('bp-mon', 'mon', function (v) { S.mon = +v; return null; }); chips('bp-sky', 'sky', function (v) { S.sky = +v; return null; });

  var plz = $('bp-plz');
  plz.value = S.plz;
  plz.addEventListener('input', function () {
    var v = plz.value.replace(/\D/g, '').slice(0, 5); if (v !== plz.value) plz.value = v;
    if (v.length === 5) { S.plz = v; update(); } else if (!v.length) { S.plz = ''; update(); }
  });

  /* Kompass: Finger oder Maus auf den Ring setzen und drehen; Pfeiltasten drehen in 5-Grad-Schritten */
  var comp = $('bp-comp'), needle = $('bp-needle');
  if (comp) {
    var drag = false;
    var at = function (e) {
      var r = comp.getBoundingClientRect(), x = e.clientX - (r.left + r.width / 2), y = e.clientY - (r.top + r.height / 2);
      if (x * x + y * y < 64) return;
      var bearing = Math.atan2(x, -y) * 180 / Math.PI, az = bearing - 180;             /* Kompass: 0 = Norden oben; Azimut: 0 = Süden */
      az = Math.round(az / 5) * 5; if (az <= -180) az += 360; if (az > 180) az -= 360;
      [-135, -90, -45, 0, 45, 90, 135, 180].forEach(function (s) { if (Math.abs(az - s) <= 7) az = s; });
      if (S.dir !== az) { S.dir = az; update(); }
    };
    comp.addEventListener('pointerdown', function (e) { if (e.pointerType === 'mouse' && e.button !== 0) return; drag = true; try { comp.setPointerCapture(e.pointerId); } catch (x) { } at(e); e.preventDefault(); });
    comp.addEventListener('pointermove', function (e) { if (drag) at(e); });
    ['pointerup', 'pointercancel', 'lostpointercapture'].forEach(function (n) { comp.addEventListener(n, function () { drag = false; }); });
    comp.addEventListener('keydown', function (e) {
      var st = e.key === 'ArrowRight' || e.key === 'ArrowUp' ? 5 : e.key === 'ArrowLeft' || e.key === 'ArrowDown' ? -5 : 0; if (!st) return;
      e.preventDefault(); var az = (S.dir === 'ow' ? 0 : S.dir) + st; if (az > 180) az -= 360; if (az <= -180) az += 360; S.dir = az; update();
    });
  }

  /* ---------- Rechnen und Anzeigen ---------- */
  var raf = 0, last = null, varT = 0;
  function update() { if (!raf) raf = requestAnimationFrame(run); }
  function press(id, test) { var b = $(id); if (b) [].forEach.call(b.querySelectorAll('button'), function (x) { x.setAttribute('aria-pressed', test(x.getAttribute('data-v')) ? 'true' : 'false'); }); }
  function syncInputs() {
    Object.keys(FIELDS).forEach(function (key) {
      var F = FIELDS[key], inp = $(F[0]), rg = F[1] && $(F[1]); if (!inp) return;
      if (d.activeElement !== inp) inp.value = fmt(key);
      if (rg) rg.value = shown(key);
    });
    press('bp-n', function (v) { return +v === S.n; });
    press('bp-dir', function (v) { return v === 'ow' ? S.dir === 'ow' : S.dir !== 'ow' && +v === S.dir; });
    press('bp-tiltc', function (v) { return +v === S.tilt; }); press('bp-shade', function (v) { return +v === S.shade; });
    press('bp-kwhc', function (v) { return +v === S.kwh; }); press('bp-pres', function (v) { return +v === S.pres; });
    press('bp-bat', function (v) { return +v === S.bat; }); press('bp-cap', function (v) { return +v === S.cap; });
    press('bp-mon', function (v) { return +v === S.mon; }); press('bp-sky', function (v) { return +v === S.sky; });
    var c = $('bp-shift'); if (c) c.checked = !!S.shift; c = $('bp-sensor'); if (c) c.checked = !!S.sensor;
    var ow = root.querySelector('#bp-dir button[data-v="ow"]'); if (ow) ow.disabled = S.n < 2;
    if (S.dir === 'ow' && S.n < 2) S.dir = -90;
    /* Kompass und Neigungsbild */
    if (comp) {
      var az = S.dir === 'ow' ? null : S.dir;
      comp.classList.toggle('ow', az == null);
      if (az != null) needle.setAttribute('transform', 'rotate(' + (180 + az) + ' 100 100)');
      comp.setAttribute('aria-valuenow', az == null ? 0 : az);
      comp.setAttribute('aria-valuetext', az == null ? 'Osten und Westen' : dirName(az) + (az % 45 ? ', ' + (az > 0 ? az + ' Grad nach Westen' : -az + ' Grad nach Osten') : ''));
      $('bp-dir-t').textContent = az == null ? 'Halb nach Osten, halb nach Westen' : 'Die Module zeigen nach ' + dirName(az) + (az % 45 ? ' (' + Math.abs(az) + '° von Süden nach ' + (az > 0 ? 'Westen' : 'Osten') + ')' : '') + '.';
    }
    var tm = $('bp-tilt-m'); if (tm) tm.setAttribute('transform', 'rotate(' + (S.tilt - 90) + ' 86 84)');
    $('bp-shade-t').textContent = SHADE_TXT[S.shade];
    /* Leistung und Steckdose */
    var w = wpTotal(), st = $('bp-wp-st');
    $('bp-wp-sum').textContent = f(w) + ' Wp';
    st.className = 'pill ' + (w <= 960 ? 'ok' : w <= 2000 ? 'warn' : 'warn');
    st.textContent = w <= 960 ? 'Normale Steckdose' : w <= 2000 ? 'Einspeisesteckdose nötig' : 'Über 2.000 Wp';
    $('bp-wp-t').textContent = w <= 960 ? 'Bis 960 Wp darfst du selbst in die normale Steckdose stecken.' : w <= 2000 ? 'Über 960 Wp setzt ein Elektriker eine Einspeisesteckdose. Der Wechselrichter gibt trotzdem höchstens ' + S.cap + ' W ab.' : 'Mehr als 2.000 Wp sind für ein Balkonkraftwerk nicht erlaubt. Nimm weniger oder kleinere Module.';
    var cr = $('bp-cost-reset'); if (cr) cr.hidden = S.cost == null;
    var bt = $('bp-bat-t'); if (bt) bt.textContent = S.bat > 0 ? 'Gerechnet mit ' + f(S.bat * 0.9, 1) + ' kWh nutzbar, gut 15 % Verlust beim Laden und Entladen und 4 W Eigenverbrauch.' : 'Ohne Speicher fließt ungenutzter Strom ohne Vergütung ins Netz.';
  }
  function run() {
    raf = 0;
    syncInputs();
    var reg = regOf(S.plz);
    if (S.plz && !reg) { regMsg('Diese Postleitzahl kennen wir nicht. Stimmen die ersten beiden Ziffern?', 1); }
    var use = reg || DEF_REG;
    load(use, function (dt) {
      data = dt;
      if (reg) regMsg('Region ' + dt.name + ': ' + f(dt.ghi) + ' kWh Sonne pro Quadratmeter im Jahr.');
      else if (!S.plz) regMsg('Noch keine Postleitzahl: Wir rechnen mit der Mitte Deutschlands (Region ' + dt.name + ').');
      var m = $('bp-sun-i'); if (m) m.style.width = Math.round(lim((dt.ghi - GHI_MIN) / (GHI_MAX - GHI_MIN), 0, 1, 0) * 86 + 14) + '%';
      var mt = $('bp-sun-t'); if (mt) mt.textContent = 'Deutschland: ' + f(GHI_MIN) + ' kWh im Norden bis ' + f(GHI_MAX) + ' kWh am Bodensee';
      render(reg);
    });
    save();
  }
  function save() {
    try { localStorage.setItem('bkwp', JSON.stringify(S)); } catch (e) { }
    var q = new URLSearchParams();
    if (S.plz) q.set('p', S.plz);
    q.set('n', S.n); q.set('wp', S.wp); q.set('a', S.dir); q.set('t', S.tilt); q.set('s', S.shade); q.set('v', S.kwh); q.set('w', S.pres);
    if (S.shift) q.set('z', 1); if (S.bat) q.set('b', S.bat); if (S.bat && !S.sensor) q.set('m', 0); q.set('ct', Math.round(S.ct * 100) / 100);
    var ownPrices = S.pmod !== DEF.pmod || S.pinv !== DEF.pinv || S.pbat !== DEF.pbat || S.pel !== DEF.pel;   /* eigene Richtpreise reisen als fertiger Preis mit */
    if (S.cost != null || ownPrices) q.set('k', shown('cost')); if (S.base != null) q.set('g', S.base); if (S.cap !== 800) q.set('c', S.cap);
    shareUrl = location.origin + location.pathname + '?' + q.toString() + '#planer';
  }
  var shareUrl = location.href;

  function render(reg) {
    var cost = shown('cost'), res = BKW.simulate(data, cfgOf(S.n, S.bat, true)), y = res.y;
    var noBat = S.bat > 0 ? BKW.simulate(data, cfgOf(S.n, 0)).y.saved : y.saved, mny = money(y.saved, cost, Math.max(0, y.saved - noBat));
    last = { res: res, cost: cost, mny: mny, reg: reg };
    root.classList.add('bp-on');
    /* Kennzahlen */
    $('bp-k-eur').textContent = f(Math.round(mny.y1)) + ' €';
    $('bp-k-pv').textContent = f(r10(y.pv)) + ' kWh';
    $('bp-k-self').textContent = f(r10(y.self)) + ' kWh';
    $('bp-k-share').textContent = Math.round(y.share * 100) + ' % deines Solarstroms';
    var pb = $('bp-k-pay');
    pb.textContent = mny.pay <= 30 ? f(mny.pay, 1) + ' Jahre' : 'über 30 Jahre';
    $('bp-k-gain').textContent = (mny.gain >= 0 ? '+' : '−') + f(Math.abs(Math.round(mny.gain / 10) * 10)) + ' €';
    $('bp-k-aut').textContent = Math.round(Math.max(0, y.autark) * 100) + ' %';
    /* Satz */
    var name = data.name, t = (reg ? 'Region ' + name : 'Beispiel für die Mitte Deutschlands') + ': ' + (S.n === 1 ? 'Ein Modul' : S.n + ' Module') + ' mit zusammen ' + f(wpTotal()) + ' Wp, ' + dirText() + ', ' + tiltText() + (S.bat > 0 ? ', mit ' + f(S.bat, S.bat % 1 ? 1 : 0) + ' kWh Speicher' : '') + '. ';
    t += 'Das bringt rund ' + f(r10(y.pv)) + ' kWh Solarstrom im Jahr' + (S.bat > 0 && y.loss >= 10 ? ', rund ' + f(r10(y.loss)) + ' kWh Verlust im Speicher schon abgezogen' : '') + '. Davon nutzt du etwa ' + f(r10(y.self)) + ' kWh selbst (' + Math.round(y.share * 100) + ' %) und sparst bei ' + String(Math.round(S.ct * 100) / 100).replace('.', ',') + ' ct rund ' + f(Math.round(mny.y1)) + ' € im Jahr. ';
    t += mny.pay <= 30 ? 'Bei ' + f(cost) + ' € Anschaffung ist die Anlage nach etwa ' + f(mny.pay, 1) + ' Jahren bezahlt.' : 'So rechnet sich die Anlage kaum: Prüf Ausrichtung, Schatten und Preis.';
    $('bp-txt').textContent = t;
    var mb = $('bp-mini-t'); if (mb) { mb.textContent = '≈ ' + f(Math.round(mny.y1)) + ' € im Jahr'; $('bp-mini-s').textContent = mny.pay <= 30 ? 'bezahlt nach ' + f(mny.pay, 1) + ' Jahren' : 'rechnet sich so nicht'; }
    var cl = $('bp-clip');
    if (cl) { var sh = y.clip / (y.pv + y.clip + 1e-9); cl.hidden = !(sh > 0.03); cl.textContent = 'Der Wechselrichter gibt höchstens ' + S.cap + ' W ab. Dadurch gehen bei dir rund ' + f(r10(y.clip)) + ' kWh im Jahr verloren (' + Math.round(sh * 100) + ' %)' + (S.bat > 0 ? ', obwohl der Speicher einen Teil auffängt.' : '. Ein Speicher oder eine Ost-West-Aufteilung fängt einen Teil davon auf.'); }
    drawMonths(res); drawDay(res);
    clearTimeout(varT); varT = setTimeout(variants, 60);
  }

  /* ---------- Diagramme ---------- */
  var tip = el('div', { 'class': 'bp-tip', role: 'status' }); tip.hidden = true;
  function showTip(host, x, y, rows, head) {
    tip.textContent = '';
    if (head) tip.appendChild(el('b', null, head));
    rows.forEach(function (r) { var p = el('span'); if (r[2]) p.appendChild(el('i', { 'class': r[2] })); p.appendChild(el('strong', null, r[0])); p.appendChild(d.createTextNode(' ' + r[1])); tip.appendChild(p); });
    if (tip.parentNode !== host) host.appendChild(tip);
    tip.hidden = false;
    var w = host.clientWidth, tw = tip.offsetWidth, lx = Math.min(Math.max(4, x - tw / 2), w - tw - 4);
    tip.style.left = lx + 'px'; tip.style.top = Math.max(0, y - tip.offsetHeight - 10) + 'px';
  }
  function hideTip() { tip.hidden = true; }
  function nice(max, n) { var raw = max / n, p = Math.pow(10, Math.floor(Math.log10(raw))), m = raw / p, s = m <= 1 ? 1 : m <= 2 ? 2 : m <= 2.5 ? 2.5 : m <= 5 ? 5 : 10; return s * p; }
  function leg(id, txt) { var e = $(id); if (e && e.lastChild) e.lastChild.nodeValue = txt; }
  function table(id, head, rows) {
    var t = $(id); if (!t) return; t.textContent = '';
    var tr = el('tr'); head.forEach(function (h) { tr.appendChild(el('th', { scope: 'col' }, h)); }); var th = el('thead'); th.appendChild(tr); t.appendChild(th);
    var tb = el('tbody'); rows.forEach(function (r) { var x = el('tr'); r.forEach(function (c, i) { x.appendChild(el(i ? 'td' : 'th', i ? null : { scope: 'row' }, c)); }); tb.appendChild(x); }); t.appendChild(tb);
  }

  function drawMonths(res) {
    var host = $('bp-chart-m'); if (!host) return;
    var W = Math.max(280, host.clientWidth), Hh = 230, L = 38, R = 8, T = 22, B = 26, pw = W - L - R, ph = Hh - T - B;
    var M = res.m, showClip = res.y.clip > 0.03 * (res.y.pv + res.y.clip), max = 0, i;
    for (i = 0; i < 12; i++) max = Math.max(max, M[i].self + M[i].feed + (showClip ? M[i].clip : 0));
    var step = nice(Math.max(max, 1), 4), top = Math.ceil(max / step) * step || step;
    var svg = el('svg', { viewBox: '0 0 ' + W + ' ' + Hh, width: W, height: Hh, role: 'group', 'aria-label': 'Solarstrom je Monat in Kilowattstunden, aufgeteilt in selbst genutzt und ins Netz' });
    for (var v = 0; v <= top + 1e-6; v += step) {
      var gy = T + ph - v / top * ph;
      svg.appendChild(el('line', { x1: L, x2: W - R, y1: gy, y2: gy, 'class': v ? 'bp-grid' : 'bp-axis' }));
      svg.appendChild(el('text', { x: L - 6, y: gy + 4, 'text-anchor': 'end', 'class': 'bp-tick' }, f(v)));
    }
    svg.appendChild(el('text', { x: L - 6, y: 10, 'text-anchor': 'end', 'class': 'bp-tick' }, 'kWh'));
    var band = pw / 12, bw = Math.min(24, Math.max(8, band * 0.58)), best = 0;
    for (i = 1; i < 12; i++) if (M[i].self + M[i].feed > M[best].self + M[best].feed) best = i;
    for (i = 0; i < 12; i++) {
      var x = L + band * i + (band - bw) / 2, base = T + ph, parts = [[M[i].self, 'bp-f-self'], [M[i].feed, 'bp-f-feed']], yy = base, g = el('g', { 'class': 'bp-col', tabindex: 0, role: 'img', 'aria-label': MON[i] + ': ' + f(Math.round(M[i].self + M[i].feed)) + ' Kilowattstunden Solarstrom, davon ' + f(Math.round(M[i].self)) + ' selbst genutzt und ' + f(Math.round(M[i].feed)) + ' ins Netz' });
      if (showClip) parts.push([M[i].clip, 'bp-f-clip']);
      var drawn = parts.filter(function (p) { return p[0] / top * ph >= 1; });
      drawn.forEach(function (p, j) {
        var h = p[0] / top * ph, gap = j ? 2 : 0, hh = Math.max(1, h - gap), y0 = yy - h, lastSeg = j === drawn.length - 1, r = lastSeg ? Math.min(4, hh / 2, bw / 2) : 0;
        var dpath = 'M' + x + ' ' + (y0 + hh) + 'V' + (y0 + r) + (r ? 'q0 ' + (-r) + ' ' + r + ' ' + (-r) : '') + 'H' + (x + bw - r) + (r ? 'q' + r + ' 0 ' + r + ' ' + r : '') + 'V' + (y0 + hh) + 'Z';
        g.appendChild(el('path', { d: dpath, 'class': p[1] }));
        yy -= h;
      });
      g.appendChild(el('rect', { x: L + band * i, y: T, width: band, height: ph + B, 'class': 'bp-hit' }));
      svg.appendChild(g);
      svg.appendChild(el('text', { x: L + band * i + band / 2, y: Hh - 8, 'text-anchor': 'middle', 'class': 'bp-tick' }, band >= 34 ? MO[i] : MO[i].charAt(0)));
      if (i === best) svg.appendChild(el('text', { x: Math.min(Math.max(L + band * i + band / 2, L + 24), W - R - 24), y: yy - 6, 'text-anchor': 'middle', 'class': 'bp-lab' }, f(Math.round(M[i].self + M[i].feed)) + ' kWh'));
      (function (i, g, cx, ty) {
        var show = function () {
          var rows = [[f(Math.round(M[i].self)) + ' kWh', 'selbst genutzt', 'bp-f-self'], [f(Math.round(M[i].feed)) + ' kWh', 'ins Netz', 'bp-f-feed']];
          if (showClip) rows.push([f(Math.round(M[i].clip)) + ' kWh', 'abgeregelt', 'bp-f-clip']);
          showTip(host, cx, ty, rows, MON[i]);
        };
        g.addEventListener('pointerenter', show); g.addEventListener('focus', show); g.addEventListener('click', show);
        g.addEventListener('pointerleave', hideTip); g.addEventListener('blur', hideTip);
      })(i, g, L + band * i + band / 2, yy);
    }
    var old = host.querySelector('svg'); if (old) host.replaceChild(svg, old); else host.insertBefore(svg, host.firstChild);
    var lc = $('bp-leg-clip'); if (lc) lc.hidden = !showClip;
    var rows = M.map(function (m, i) { var r = [MON[i], f(Math.round(m.self + m.feed)), f(Math.round(m.self)), f(Math.round(m.feed))]; if (showClip) r.push(f(Math.round(m.clip))); return r; });
    var sum = ['Jahr', f(Math.round(res.y.pv)), f(Math.round(res.y.self)), f(Math.round(res.y.feed))]; if (showClip) sum.push(f(Math.round(res.y.clip)));
    rows.push(sum);
    table('bp-tab-m', ['Monat', 'Solarstrom (kWh)', 'Selbst genutzt', 'Ins Netz'].concat(showClip ? ['Abgeregelt'] : []), rows);
  }

  /* Tag im gewählten Monat: sonnig = Tag mit dem neunthöchsten Zehntel an Ertrag, trüb = Tag aus dem unteren Fünftel */
  function pickDay(res) {
    var start = 0, i, m = S.mon; for (i = 0; i < m; i++) start += BKW.MDAYS[i];
    var days = [];
    for (i = 0; i < BKW.MDAYS[m]; i++) { var s = 0, h0 = (start + i) * 24; for (var h = 0; h < 24; h++) s += res.dc[h0 + h]; days.push([s, start + i]); }
    days.sort(function (a, b) { return a[0] - b[0]; });
    return days[Math.round((days.length - 1) * (S.sky ? 0.9 : 0.2))][1];
  }
  function drawDay(res) {
    var host = $('bp-chart-d'); if (!host || !res.hourly) return;
    var W = Math.max(280, host.clientWidth), Hh = 230, L = 38, R = 10, T = 22, B = 26, pw = W - L - R, ph = Hh - T - B;
    var day = pickDay(res), K = res.hourly, off = (data.off || 0), tz = day >= 87 && day < 298 ? 2 : 1, pts = [], max = 0, i, bat = S.bat > 0, capWh = S.bat * 900;
    for (i = -3; i <= 24; i++) {
      var h = day * 24 + i; if (h < 0 || h >= 8760) continue;
      var lt = i + off + tz; if (lt < -0.5 || lt > 24.5) continue;
      /* Mit Speicher zeigt die Linie, was die Module liefern: Was aus der Steckdose kommt, folgt dann dem Verbrauch und nicht der Sonne */
      var pvh = bat ? K.gen[h] : K.pv[h];
      pts.push({ t: lt, pv: pvh, self: K.self[h], load: K.load[h], bat: bat ? K.bat[h] : 0, soc: bat ? Math.min(1, K.soc[h] / capWh) : 0, h: h });
      max = Math.max(max, pvh, K.self[h], Math.min(K.load[h], 1500));
    }
    var capLine = S.cap, step = nice(Math.max(max, capLine * (max > capLine * 0.6 ? 1.05 : 0.5), 100), 4), top = Math.ceil(Math.max(max, max > capLine * 0.6 ? capLine : 0) / step) * step || step;
    function X(t) { return L + Math.min(24, Math.max(0, t)) / 24 * pw; }
    function Y(v) { return T + ph - Math.min(v, top) / top * ph; }
    var svg = el('svg', { viewBox: '0 0 ' + W + ' ' + Hh, width: W, height: Hh, role: 'group', 'aria-label': 'Tagesverlauf an einem ' + (S.sky ? 'sonnigen' : 'trüben') + ' Tag im ' + MON[S.mon] + ': ' + (bat ? 'Strom der Module, selbst genutzter Strom direkt und aus dem Speicher' : 'Solarstrom, selbst genutzter Anteil') + ' und mittlerer Verbrauch in Watt' });
    for (var v = 0; v <= top + 1e-6; v += step) { var gy = Y(v); svg.appendChild(el('line', { x1: L, x2: W - R, y1: gy, y2: gy, 'class': v ? 'bp-grid' : 'bp-axis' })); svg.appendChild(el('text', { x: L - 6, y: gy + 4, 'text-anchor': 'end', 'class': 'bp-tick' }, f(v))); }
    svg.appendChild(el('text', { x: L - 6, y: 10, 'text-anchor': 'end', 'class': 'bp-tick' }, 'Watt'));
    [0, 6, 12, 18, 24].forEach(function (hh) { svg.appendChild(el('text', { x: X(hh), y: Hh - 8, 'text-anchor': hh === 0 ? 'start' : hh === 24 ? 'end' : 'middle', 'class': 'bp-tick' }, pw < 330 && hh !== 24 ? String(hh) : hh + ' Uhr')); });
    function path(key, close) {          /* glatte Kurve ohne Überschwinger (monotone Glättung nach Fritsch und Carlson) */
      var n = pts.length, xs = [], ys = [], dl = [], m = [], j, s;
      for (j = 0; j < n; j++) { xs.push(X(pts[j].t)); ys.push(Y(pts[j][key])); }
      for (j = 0; j < n - 1; j++) dl.push(xs[j + 1] > xs[j] ? (ys[j + 1] - ys[j]) / (xs[j + 1] - xs[j]) : 0);
      m[0] = dl[0] || 0; m[n - 1] = dl[n - 2] || 0;
      for (j = 1; j < n - 1; j++) m[j] = dl[j - 1] * dl[j] <= 0 ? 0 : (dl[j - 1] + dl[j]) / 2;
      for (j = 0; j < n - 1; j++) {
        if (!dl[j]) { m[j] = 0; m[j + 1] = 0; continue; }
        var a = m[j] / dl[j], b = m[j + 1] / dl[j], q = a * a + b * b;
        if (q > 9) { var t = 3 / Math.sqrt(q); m[j] = t * a * dl[j]; m[j + 1] = t * b * dl[j]; }
      }
      s = 'M' + xs[0].toFixed(1) + ' ' + ys[0].toFixed(1);
      for (j = 0; j < n - 1; j++) { var hx = (xs[j + 1] - xs[j]) / 3; s += 'C' + (xs[j] + hx).toFixed(1) + ' ' + (ys[j] + m[j] * hx).toFixed(1) + ' ' + (xs[j + 1] - hx).toFixed(1) + ' ' + (ys[j + 1] - m[j + 1] * hx).toFixed(1) + ' ' + xs[j + 1].toFixed(1) + ' ' + ys[j + 1].toFixed(1); }
      if (close) s += 'L' + xs[n - 1].toFixed(1) + ' ' + Y(0) + 'L' + xs[0].toFixed(1) + ' ' + Y(0) + 'Z';
      return s;
    }
    svg.appendChild(el('path', { d: path('pv', 1), 'class': 'bp-a-pv' }));
    svg.appendChild(el('path', { d: path('self', 1), 'class': 'bp-a-self' }));
    if (max > capLine * 0.6) { svg.appendChild(el('line', { x1: L, x2: W - R, y1: Y(capLine), y2: Y(capLine), 'class': 'bp-cap' })); svg.appendChild(el('text', { x: W - R, y: Y(capLine) - 5, 'text-anchor': 'end', 'class': 'bp-tick' }, 'Grenze ' + capLine + ' W')); }
    svg.appendChild(el('path', { d: path('load'), 'class': 'bp-l-load' }));
    svg.appendChild(el('path', { d: path('pv'), 'class': 'bp-l-pv' }));
    var cross = el('line', { y1: T, y2: T + ph, 'class': 'bp-cross' }), dots = ['bp-d-pv', 'bp-d-load'].map(function (c) { return el('circle', { r: 4.5, 'class': c }); });
    cross.style.display = 'none'; dots.forEach(function (c) { c.style.display = 'none'; svg.appendChild(c); }); svg.appendChild(cross);
    var hit = el('rect', { x: L, y: T, width: pw, height: ph + B, 'class': 'bp-hit', tabindex: 0, role: 'img', 'aria-label': 'Tagesverlauf: mit den Pfeiltasten Stunde für Stunde ablesen' }), cur = -1;
    function showAt(j) {
      j = Math.min(pts.length - 1, Math.max(0, j)); cur = j; var p = pts[j], x = X(p.t);
      cross.setAttribute('x1', x); cross.setAttribute('x2', x); cross.style.display = '';
      dots[0].setAttribute('cx', x); dots[0].setAttribute('cy', Y(p.pv)); dots[1].setAttribute('cx', x); dots[1].setAttribute('cy', Y(p.load)); dots.forEach(function (c) { c.style.display = ''; });
      var hh = Math.floor(p.t + 1e-6), mm = Math.round((p.t - hh) * 60);
      var rows = bat ? [[f(Math.round(p.pv)) + ' W', 'liefern die Module', 'bp-k-pv'], [f(Math.round(p.self)) + ' W', 'nutzt du selbst', 'bp-f-self'], [f(Math.round(p.load)) + ' W', 'Verbrauch im Mittel', 'bp-k-load'], [Math.round(p.soc * 100) + ' %', 'Speicher gefüllt']] : [[f(Math.round(p.pv)) + ' W', 'Solarstrom', 'bp-k-pv'], [f(Math.round(p.self)) + ' W', 'davon selbst genutzt', 'bp-f-self'], [f(Math.round(p.load)) + ' W', 'Verbrauch im Mittel', 'bp-k-load']];
      showTip(host, x, Math.min(Y(p.pv), Y(p.load), Y(p.self)), rows, hh + ':' + (mm < 10 ? '0' : '') + mm + ' Uhr');
    }
    function near(e) { var r = svg.getBoundingClientRect(), t = (e.clientX - r.left - L) / pw * 24, b = 0, bd = 99; pts.forEach(function (p, j) { var dd = Math.abs(p.t - t); if (dd < bd) { bd = dd; b = j; } }); showAt(b); }
    function off2() { cross.style.display = 'none'; dots.forEach(function (c) { c.style.display = 'none'; }); hideTip(); }
    hit.addEventListener('pointermove', near); hit.addEventListener('pointerdown', near); hit.addEventListener('pointerleave', off2); hit.addEventListener('blur', off2);
    hit.addEventListener('focus', function () { showAt(cur < 0 ? Math.round(pts.length / 2) : cur); });
    hit.addEventListener('keydown', function (e) { if (e.key === 'ArrowRight') { showAt(cur + 1); e.preventDefault(); } else if (e.key === 'ArrowLeft') { showAt(cur - 1); e.preventDefault(); } });
    svg.appendChild(hit);
    var old = host.querySelector('svg'); if (old) host.replaceChild(svg, old); else host.insertBefore(svg, host.firstChild);
    var sum = 0, sf = 0, sb = 0; pts.forEach(function (p) { if (p.t >= 0 && p.t <= 24) { sum += p.pv; sf += p.self; sb += p.bat; } });
    var head = (S.sky ? 'Sonniger' : 'Trüber') + ' Tag im ' + MON[S.mon] + ': ';
    $('bp-day-t').textContent = bat ? head + 'Die Module liefern ' + f(sum / 1000, 1) + ' kWh. Du nutzt ' + f(sf / 1000, 1) + ' kWh selbst' + (sb >= 50 ? ', davon ' + f(sb / 1000, 1) + ' kWh aus dem Speicher.' : '. Der Speicher wird an so einem Tag kaum voll.') : head + f(sum / 1000, 1) + ' kWh Solarstrom, davon ' + f(sf / 1000, 1) + ' kWh selbst genutzt.';
    leg('bp-leg-pv', bat ? 'Strom der Module' : 'Solarstrom'); leg('bp-leg-self', bat ? 'selbst genutzt, direkt oder aus dem Speicher' : 'davon selbst genutzt');
    table('bp-tab-d', ['Uhrzeit', bat ? 'Module liefern (W)' : 'Solarstrom (W)', 'Selbst genutzt (W)', 'Verbrauch im Mittel (W)'].concat(bat ? ['Speicher gefüllt'] : []), pts.filter(function (p) { return p.t >= 0 && p.t <= 24; }).map(function (p) { var hh = Math.floor(p.t + 1e-6), mm = Math.round((p.t - hh) * 60), r = [hh + ':' + (mm < 10 ? '0' : '') + mm, f(Math.round(p.pv)), f(Math.round(p.self)), f(Math.round(p.load))]; if (bat) r.push(Math.round(p.soc * 100) + ' %'); return r; }));
  }

  /* ---------- Vergleich: Was wäre, wenn? ---------- */
  function variants() {
    var host = $('bp-var'); if (!host || !data) return;
    var list = [[1, 0], [2, 0], [4, 0], [2, 1.6], [4, 2.7], [4, 5]], cur = S.n + '|' + S.bat, seen = {}, rows = [], base0 = {};
    if (!list.some(function (v) { return v[0] + '|' + v[1] === cur; })) list.push([S.n, S.bat]);
    list.forEach(function (v) {
      var n = v[0], bat = v[1], key = n + '|' + bat; if (seen[key] || n * S.wp > 2000) return; seen[key] = 1;
      var isCur = key === cur, cost = isCur ? shown('cost') : costOf(n, bat), r = isCur && last ? last.res : BKW.simulate(data, cfgOf(n, bat));
      if (bat > 0 && base0[n] == null) base0[n] = BKW.simulate(data, cfgOf(n, 0)).y.saved;
      if (!bat) base0[n] = r.y.saved;
      var m = money(r.y.saved, cost, bat > 0 ? Math.max(0, r.y.saved - base0[n]) : 0);
      rows.push({ n: n, bat: bat, cur: isCur, cost: cost, y1: m.y1, pay: m.pay, gain: m.gain, self: r.y.self });
    });
    rows.sort(function (a, b) { return b.gain - a.gain; });
    var max = Math.max.apply(null, rows.map(function (r) { return Math.max(r.gain, 1); })), fast = rows.reduce(function (a, b) { return b.pay < a.pay ? b : a; });
    function nm0(r) { return (r.n === 1 ? '1 Modul' : r.n + ' Module') + (r.bat ? ' mit ' + f(r.bat, r.bat % 1 ? 1 : 0) + ' kWh Speicher' : ' ohne Speicher'); }
    host.textContent = '';
    rows.forEach(function (r, i) {
      var row = el('button', { type: 'button', 'class': 'bp-vr' + (r.cur ? ' cur' : '') + (i === 0 ? ' best' : ''), 'data-n': r.n, 'data-b': r.bat, 'aria-pressed': r.cur ? 'true' : 'false' });
      var name = (r.n === 1 ? '1 Modul' : r.n + ' Module') + (r.bat ? ' + ' + f(r.bat, r.bat % 1 ? 1 : 0) + ' kWh Speicher' : '');
      var tp = el('span', { 'class': 'tp' }), nm = el('b', null, name);
      if (i === 0 && r.gain > 0) nm.appendChild(el('span', { 'class': 'rec' }, 'Größter Gewinn'));
      if (r === fast && r.pay <= 30) nm.appendChild(el('span', { 'class': 'rec alt' }, 'Am schnellsten bezahlt'));
      if (r.cur) nm.appendChild(el('span', { 'class': 'you' }, 'Deine Auswahl'));
      tp.appendChild(nm); tp.appendChild(el('em', null, (r.gain >= 0 ? '+' : '−') + f(Math.abs(Math.round(r.gain / 10) * 10)) + ' €'));
      row.appendChild(tp);
      var mt = el('span', { 'class': 'mtr' }), bar = el('i'); bar.style.width = Math.max(0, r.gain) / max * 100 + '%'; mt.appendChild(bar); row.appendChild(mt);
      row.appendChild(el('span', { 'class': 'st' }, f(Math.round(r.y1)) + ' € im Jahr gespart · ' + f(r.cost) + ' € Anschaffung · ' + (r.pay <= 30 ? 'bezahlt nach ' + f(r.pay, 1) + ' Jahren' : 'rechnet sich nicht')));
      host.appendChild(row);
    });
    var best = rows[0], me = rows.filter(function (r) { return r.cur; })[0], tx = $('bp-var-t');
    if (tx && me) tx.textContent = (best.gain <= 0 ? 'Mit diesen Angaben rechnet sich keine der Größen in ' + YEARS + ' Jahren.' : best.cur ? 'Deine Auswahl bringt bei dir über ' + YEARS + ' Jahre den größten Gewinn.' : 'Den größten Gewinn über ' + YEARS + ' Jahre bringen bei dir ' + nm0(best) + ': rund ' + f(Math.round((best.gain - me.gain) / 10) * 10) + ' € mehr als deine Auswahl.') + (fast.pay <= 30 ? ' Am schnellsten bezahlt ' + (fast.n === 1 ? 'ist' : 'sind') + ' ' + nm0(fast) + '.' : '') + ' Tipp eine Zeile an, um sie zu übernehmen.';
  }
  var vh = $('bp-var');
  if (vh) vh.addEventListener('click', function (e) { var b = e.target.closest('.bp-vr'); if (!b) return; S.n = +b.getAttribute('data-n'); S.bat = +b.getAttribute('data-b'); S.cost = null; update(); });

  /* ---------- Teilen, kleine Leiste am Handy, Größe ---------- */
  var sb = $('bp-share');
  if (sb) sb.addEventListener('click', function () {
    var text = $('bp-txt').textContent + ' Rechne selbst nach:';
    if (navigator.share) { navigator.share({ title: d.title, text: text, url: shareUrl }).catch(function () { }); return; }
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text + ' ' + shareUrl).then(function () { if (window.__toast) window.__toast('Ergebnis und Link kopiert'); }, function () { if (window.__toast) window.__toast('Kopieren nicht möglich'); });
  });
  var mini = $('bp-mini'), outBox = $('bp-out'), qBox = $('bp-in');
  if (mini && 'IntersectionObserver' in window) {
    var seeOut = false, seeIn = false, tog = function () { mini.classList.toggle('on', seeIn && !seeOut && root.classList.contains('bp-on')); d.documentElement.classList.toggle('bp-mini-on', mini.classList.contains('on')); };
    new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.target === outBox) seeOut = e.isIntersecting; else seeIn = e.isIntersecting; }); tog(); }, { rootMargin: '-80px 0px -40px 0px' }).observe(outBox);
    new IntersectionObserver(function (es) { es.forEach(function (e) { seeIn = e.isIntersecting; }); tog(); }).observe(qBox);
    mini.addEventListener('click', function () { outBox.scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' }); });
  }
  var rsT = 0, lastW = innerWidth;
  addEventListener('resize', function () { if (innerWidth === lastW) return; lastW = innerWidth; clearTimeout(rsT); rsT = setTimeout(function () { if (last) { drawMonths(last.res); drawDay(last.res); } }, 150); });
  d.addEventListener('keydown', function (e) { if (e.key === 'Escape') hideTip(); });

  update();
})();
