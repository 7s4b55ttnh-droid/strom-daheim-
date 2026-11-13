/* Gegenprobe: Ertrag des Planers gegen gespeicherte PVGIS-Werte (referenz.json).
   Aufruf im Ordner werkzeuge/pvdaten:  node gegenprobe.js
   Erwartet: mittlere Abweichung unter 1,5 %, größte unter 8 %. Sonst stimmt etwas am Rechenkern oder an den Daten nicht. */
const fs = require('fs'), path = require('path');
const { BKW } = require(path.join(__dirname, '..', '..', 'bkw-planer.js'));
const ref = JSON.parse(fs.readFileSync(path.join(__dirname, 'referenz.json'))).werte;
let all = [];
for (const plz of Object.keys(ref).sort()) {
  const data = BKW.decode(JSON.parse(fs.readFileSync(path.join(__dirname, '..', '..', 'assets', 'pv', plz + '.json'))));
  for (const key of Object.keys(ref[plz])) {
    const [tilt, azim] = key.split('_').map(Number);
    const P = BKW.dcPower(data, { wp: 1000, tilt, azim });
    let e = 0; for (let i = 0; i < 8760; i++) e += P[i] / 1000 * 0.9;
    all.push({ plz, key, e, ref: ref[plz][key], d: (e / ref[plz][key] - 1) * 100 });
  }
}
const abs = all.map(x => Math.abs(x.d)), mae = abs.reduce((a, b) => a + b) / abs.length, max = Math.max(...abs);
const worst = all.slice().sort((a, b) => Math.abs(b.d) - Math.abs(a.d)).slice(0, 3).map(x => x.plz + ' ' + x.key + ' ' + x.d.toFixed(1) + '%').join(', ');
console.log(all.length + ' Vergleiche, mittlere Abweichung ' + mae.toFixed(2) + ' %, größte ' + max.toFixed(1) + ' % (' + worst + ')');
/* Haushalt: Jahressumme und Bilanz müssen aufgehen */
const d = BKW.decode(JSON.parse(fs.readFileSync(path.join(__dirname, '..', '..', 'assets', 'pv', '34.json'))));
let bad = 0;
for (const cfg of [{ groups: [{ wp: 900, tilt: 90, azim: 0 }], kwh: 1900, presence: 'teils' }, { groups: [{ wp: 1800, tilt: 30, azim: 0 }], kwh: 4000, presence: 'weg', bat: { kwh: 2.7 } }, { groups: [{ wp: 900, tilt: 90, azim: -90 }, { wp: 900, tilt: 90, azim: 90 }], kwh: 2900, presence: 'viel', shift: true, bat: { kwh: 1.6, sensor: false } }]) {
  const r = BKW.simulate(d, cfg), y = r.y, extra = cfg.bat ? 4 * 8.76 : 0;
  const okLoad = Math.abs(y.load - cfg.kwh - extra) < 2, okBal = y.self <= y.load + 0.5 && y.self + y.feed + y.clip <= y.pot + 0.5 && y.self >= 0 && y.feed >= -0.01;
  if (!okLoad || !okBal) { bad++; console.log('FEHLER Bilanz', JSON.stringify(cfg), y); }
}
console.log(bad ? bad + ' Bilanzfehler' : 'Bilanzen stimmen');
process.exit(mae < 1.5 && max < 8 && !bad ? 0 : 1);
